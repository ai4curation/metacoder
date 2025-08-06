import logging
from pathlib import Path
from typing import Optional, Union

import click
import yaml
from pydantic import ValidationError

from metacoder.configuration import CoderConfig, MCPCollectionConfig, MCPConfig
from metacoder.coders.base_coder import BaseCoder
from metacoder.registry import AVAILABLE_CODERS
from metacoder.evals.runner import EvalRunner


logger = logging.getLogger(__name__)


def load_coder_config(config_path: Path) -> CoderConfig:
    """Load coder configuration from YAML file."""
    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML: {e}")

    try:
        return CoderConfig(**data)
    except ValidationError as e:
        raise click.ClickException(f"Invalid config format: {e}")


def load_mcp_collection(collection_path: Path) -> MCPCollectionConfig:
    """Load MCP collection configuration from YAML file."""
    if not collection_path.exists():
        raise click.ClickException(f"MCP collection file not found: {collection_path}")

    try:
        with open(collection_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML: {e}")

    try:
        return MCPCollectionConfig(**data)
    except ValidationError as e:
        raise click.ClickException(f"Invalid MCP collection format: {e}")


def load_mcp_registry(registry_path: str) -> MCPCollectionConfig:
    """Load MCPs from the registry based on a path pattern.
    
    Args:
        registry_path: Path pattern like 'metacoder' (all) or 'metacoder.basics'
    
    Returns:
        MCPCollectionConfig containing all matched MCPs
    """
    # Base directory for registry
    registry_base = Path(__file__).parent / "mcps" / "registry"
    
    # Convert dot notation to file path
    if registry_path == "metacoder":
        # Load all yaml files in registry
        yaml_files = list(registry_base.glob("*.yaml"))
    else:
        # Convert metacoder.basics to basics.yaml
        if registry_path.startswith("metacoder."):
            registry_path = registry_path[len("metacoder."):]
        yaml_files = [registry_base / f"{registry_path}.yaml"]
    
    # Collect all MCPs
    all_mcps = []
    for yaml_file in yaml_files:
        if not yaml_file.exists():
            raise click.ClickException(f"Registry file not found: {yaml_file}")
        
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise click.ClickException(f"Invalid YAML in {yaml_file}: {e}")
        
        # The registry files contain a list of MCP extensions directly
        if isinstance(data, list):
            for mcp_data in data:
                try:
                    mcp = MCPConfig(**mcp_data)
                    all_mcps.append(mcp)
                except ValidationError as e:
                    logger.warning(f"Invalid MCP in {yaml_file}: {e}")
        elif isinstance(data, dict):
            try:
                mcp_collection = MCPCollectionConfig(**data)
                all_mcps.extend(mcp_collection.servers)
            except ValidationError as e:
                logger.warning(f"Invalid MCP in {yaml_file}: {e}")
    for mcp in all_mcps:
        mcp.enabled = False
    
    # Create a collection config
    collection_name = f"Registry: {registry_path}"
    return MCPCollectionConfig(name=collection_name, description=None, servers=all_mcps)


def merge_mcp_extensions(
    coder_config: Optional[CoderConfig],
    mcp_collection: Optional[MCPCollectionConfig],
    enabled_mcps: Optional[list[str]] = None,
) -> Optional[CoderConfig]:
    """Merge MCP extensions from collection into coder config."""
    if not mcp_collection:
        return coder_config

    # If no coder config, create a minimal one
    if not coder_config:
        # Create a default config with empty extensions
        from metacoder.configuration import AIModelConfig

        coder_config = CoderConfig(
            ai_model=AIModelConfig(name="gpt-4"),  # Default model
            extensions=[],
        )

    # Filter MCPs based on enabled list
    mcps_to_add = []
    for mcp in mcp_collection.servers:
        if enabled_mcps is None:
            # If no specific MCPs requested, add all enabled ones
            if mcp.enabled:
                mcps_to_add.append(mcp)
        else:
            # Add only if explicitly requested
            if mcp.name in enabled_mcps:
                mcps_to_add.append(mcp)

    # Merge extensions (avoid duplicates by name)
    existing_names = {ext.name for ext in coder_config.extensions}
    for mcp in mcps_to_add:
        if mcp.name not in existing_names:
            coder_config.extensions.append(mcp)

    return coder_config


def create_coder(
    coder_name: str, workdir: str, config: Optional[CoderConfig] = None
) -> BaseCoder:
    """Create a coder instance."""
    if coder_name not in AVAILABLE_CODERS:
        available = ", ".join(AVAILABLE_CODERS.keys())
        raise click.ClickException(
            f"Unknown coder: {coder_name}. Available: {available}"
        )

    coder_class = AVAILABLE_CODERS[coder_name]

    # Create coder with workdir and config
    coder = coder_class(workdir=workdir, config=config)

    return coder


class DefaultGroup(click.Group):
    """A Click group that allows a default command."""

    def __init__(self, *args, default_command="run", **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default_command

    def resolve_command(self, ctx, args):
        # Try to resolve as a normal command first
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If no command matches and we have args, use default command
            if args and args[0] not in self.list_commands(ctx):
                # Insert the default command
                args.insert(0, self.default_command)
                return super().resolve_command(ctx, args)
            raise


@click.group(cls=DefaultGroup, invoke_without_command=True)
@click.pass_context
@click.version_option()
def cli(ctx):
    """
    Metacoder - Pick a coder and run commands with optional configuration.

    If no command is specified, the 'run' command is used by default.
    """
    # If no command was invoked and no args, show help
    if ctx.invoked_subcommand is None and not ctx.args:
        click.echo(ctx.get_help())
        ctx.exit()


@cli.command()
@click.argument("prompt", type=str)
@click.option(
    "--coder",
    "-c",
    type=click.Choice(list(AVAILABLE_CODERS.keys())),
    default="goose",
    help="Coder to use",
)
@click.option(
    "--config", "-f", type=click.Path(exists=True), help="Path to CoderConfig YAML file"
)
@click.option(
    "--mcp-collection",
    "-m",
    type=click.Path(exists=True),
    help="Path to MCPCollectionConfig YAML file",
)
@click.option(
    "--registry",
    "-r",
    type=str,
    help="Load MCPs from registry (e.g., 'metacoder', 'metacoder.basics')",
)
@click.option(
    "--enable-mcp",
    "-e",
    multiple=True,
    help="Enable specific MCP by name (can be used multiple times)",
)
@click.option(
    "--workdir",
    "-w",
    type=click.Path(),
    default="./workdir",
    help="Working directory for the coder",
)
@click.option(
    "--provider", "-p", type=str, help="AI provider (e.g., openai, anthropic, google)"
)
@click.option(
    "--model", type=str, help="AI model name (e.g., gpt-4, claude-3-opus, gemini-pro)"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
def run(
    prompt: str,
    coder: str,
    config: Optional[str],
    mcp_collection: Optional[str],
    registry: Optional[str],
    enable_mcp: tuple[str, ...],
    workdir: str,
    provider: Optional[str],
    model: Optional[str],
    verbose: bool,
    quiet: bool,
):
    """
    Run a prompt with the specified coder.

    This is the default command when no subcommand is specified.

    Examples:

    \b
    # Simple usage with goose
    metacoder "Write a hello world program in Python"

    \b
    # Use specific coder with config
    metacoder run "Fix the bug in main.py" --coder goose --config goose_config.yaml

    \b
    # Use MCP collection
    metacoder run "Search for papers on LLMs" --mcp-collection mcps.yaml

    \b
    # Enable specific MCPs from collection
    metacoder run "Find PMID:12345" --mcp-collection mcps.yaml --enable-mcp pubmed

    \b
    # Load MCPs from registry
    metacoder run "Fetch a webpage" --registry metacoder.basics --enable-mcp fetch

    \b
    # Load all MCPs from registry
    metacoder run "Process PDF" --registry metacoder --enable-mcp pdfreader

    \b
    # Custom working directory
    metacoder run "Analyze the code" --workdir ./my_project

    \b
    # Override AI model
    metacoder run "Write a function" --provider openai --model gpt-4

    \b
    # Use Claude with specific model
    metacoder run "Explain this code" --coder claude --provider anthropic --model claude-3-opus

    \b
    # Quiet mode
    metacoder run "Explain this code" --quiet
    """
    # Setup logging
    if verbose and quiet:
        raise click.ClickException("Cannot use both verbose and quiet mode")
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet: # quiet mode is a bit different, it's just no output
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)

    click.echo(f"🤖 Using coder: {coder}")
    click.echo(f"📁 Working directory: {workdir}")

    # Load config if provided
    coder_config = None
    if config:
        click.echo(f"📄 Loading config from: {config}")
        coder_config = load_coder_config(Path(config))

    # Load MCP collection if provided
    mcp_collection_config = None
    if mcp_collection:
        click.echo(f"🔌 Loading MCP collection from: {mcp_collection}")
        mcp_collection_config = load_mcp_collection(Path(mcp_collection))

        # Show which MCPs are available
        available_mcps = [mcp.name for mcp in mcp_collection_config.servers]
        click.echo(f"   Available MCPs: {', '.join(available_mcps)}")

        # Show which MCPs will be enabled
        if enable_mcp:
            enabled_list = list(enable_mcp)
            click.echo(f"   Enabling MCPs: {', '.join(enabled_list)}")
        else:
            enabled_list = [
                mcp.name for mcp in mcp_collection_config.servers if mcp.enabled
            ]
            click.echo(
                f"   Enabling MCPs: {', '.join(enabled_list)} (all enabled by default)"
            )
    
    # Load MCPs from registry if provided
    if registry:
        click.echo(f"📚 Loading MCPs from registry: {registry}")
        registry_config = load_mcp_registry(registry)
        
        # Merge with existing MCP collection if any
        if mcp_collection_config:
            # Merge the servers lists
            for mcp in registry_config.servers:
                # Avoid duplicates by name
                if not any(existing.name == mcp.name for existing in mcp_collection_config.servers):
                    mcp_collection_config.servers.append(mcp)
        else:
            mcp_collection_config = registry_config
        
        # Show available MCPs from registry
        registry_mcps = [mcp.name for mcp in registry_config.servers]
        click.echo(f"   Registry MCPs: {', '.join(registry_mcps)}")
        
        # Note that registry MCPs are not enabled by default
        if not enable_mcp:
            click.echo("   Use -e/--enable-mcp to enable specific MCPs")

    # Merge MCP extensions into coder config
    # TODO: de-opaquify the claude-code generated spaghetti code here
    if mcp_collection_config:
        coder_config = merge_mcp_extensions(
            coder_config,
            mcp_collection_config,
            list(enable_mcp) if enable_mcp else None,
        )
    if enable_mcp and mcp_collection_config:
        for mcp_config in mcp_collection_config.servers:
            if mcp_config.name in enable_mcp:
                mcp_config.enabled = True

    # Apply provider and model overrides
    if provider or model:
        # Create or update the coder config with AI model settings
        if not coder_config:
            # Create a new config with just the AI model
            from metacoder.configuration import CoderConfig, AIModelConfig

            coder_config = CoderConfig(
                ai_model=AIModelConfig(
                    name=model or "gpt-4", provider=provider or "openai"
                ),
                extensions=[],
            )
        else:
            # Update existing config
            if provider:
                coder_config.ai_model.provider = provider
            if model:
                coder_config.ai_model.name = model

        # Show the model configuration
        click.echo(
            f"🧠 AI Model: {coder_config.ai_model.name} (provider: {coder_config.ai_model.provider})"
        )

    if coder_config and coder_config.extensions:
        for mcp in coder_config.extensions :
            # use emoji to indicate enabled/disabled
            if mcp.enabled:
                click.echo(f" ✅ MCP: {mcp.name}")
            else:
                click.echo(f" ❌ MCP: {mcp.name}")

    # Create coder instance
    try:
        coder_instance = create_coder(coder, str(workdir), coder_config)
    except Exception as e:
        raise click.ClickException(f"Failed to create coder: {e}")

    # Run the coder
    click.echo(f"🚀 Running prompt: {prompt}")
    result = coder_instance.run(prompt)

    # Display results
    click.echo("\n" + "=" * 50)
    click.echo("📊 RESULTS")
    click.echo("=" * 50)

    if result.result_text:
        click.echo("\n📝 Result:")
        click.echo(result.result_text)

    if verbose and result.stdout:
        click.echo("\n📤 Standard Output:")
        click.echo(result.stdout)

    if result.stderr:
        click.echo("\n⚠️ Standard Error:")
        click.echo(result.stderr)

    if result.total_cost_usd:
        click.echo(f"\n💰 Total cost: ${result.total_cost_usd:.4f}")

    if result.success is not None:
        status = "✅ Success" if result.success else "❌ Failed"
        click.echo(f"\n{status}")

    if result.tool_uses:
        click.echo("\n📋 Tool uses:")
        for tool_use in result.tool_uses:
            success = "✅" if tool_use.success else "❌"
            click.echo(f"  {success} {tool_use.name} with arguments: {tool_use.arguments}")
            if tool_use.error:
                click.echo(f"    Error: {tool_use.error}")

    if verbose and result.structured_messages:
        click.echo(
            f"\n📋 Structured messages ({len(result.structured_messages)} total)"
        )
        for i, msg in enumerate(result.structured_messages):
            click.echo(f"  {i+1}. {msg}")


@cli.command("list-coders")
def list_coders():
    """List available coders and their installation status."""
    click.echo("Available coders:")
    for coder_name, coder_class in AVAILABLE_CODERS.items():
        available = "✅" if coder_class.is_available() else "❌"
        click.echo(f"  {available} {coder_name}")


@cli.command("eval")
@click.argument("config", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="eval_results.yaml",
    help="Output file for results (default: eval_results.yaml)",
)
@click.option(
    "-w",
    "--workdir",
    type=click.Path(),
    default="./eval_workdir",
    help="Working directory for evaluations (default: ./eval_workdir)",
)
@click.option(
    "-c",
    "--coders",
    multiple=True,
    help="Specific coders to test (can be specified multiple times)",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def eval_command(config: str, output: str, workdir: str, coders: tuple, verbose: bool):
    """
    Run evaluations from a configuration file.

    This command runs evaluations across all combinations of models, coders,
    cases, and metrics defined in the configuration file.

    Example:
        metacoder eval tests/input/example_eval_config.yaml
        metacoder eval evals.yaml -o results.yaml -c goose -c claude
    """
    # Convert Path objects to proper Path type (click returns strings)
    config_path = Path(config)
    output_path = Path(output)
    workdir_path = Path(workdir)

    # Convert coders tuple to list (empty tuple if not specified)
    coders_list = list(coders) if coders else None

    # Setup logging
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s"
        )
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    click.echo(f"🔬 Running evaluations from: {config_path}")

    # Create runner
    runner = EvalRunner(verbose=verbose)

    # Load dataset
    dataset = runner.load_dataset(config_path)
    click.echo(f"📊 Loaded dataset: {dataset.name}")
    click.echo(f"   Models: {', '.join(dataset.models.keys())}")
    if coders_list:
        click.echo(f"   Coders: {', '.join(coders_list)}")
    else:
        available = [
            name for name, cls in AVAILABLE_CODERS.items() if cls.is_available()
        ]
        click.echo(f"   Coders: {', '.join(available)} (all available)")
    click.echo(f"   Cases: {len(dataset.cases)}")

    # Calculate total evaluations
    num_coders = (
        len(coders_list)
        if coders_list
        else sum(1 for _, cls in AVAILABLE_CODERS.items() if cls.is_available())
    )
    num_metrics = sum(len(case.metrics) for case in dataset.cases)
    total = len(dataset.models) * num_coders * num_metrics
    click.echo(f"   Total evaluations: {total}")

    # Run evaluations
    click.echo("\n🚀 Starting evaluations...")
    results = runner.run_all_evals(dataset, workdir_path, coders_list)

    # Save results
    runner.save_results(results, output_path)
    click.echo(f"\n💾 Results saved to: {output_path}")

    # Print summary
    summary = runner.generate_summary(results)
    click.echo("\n📈 Summary:")
    click.echo(f"   Total: {summary['total_evaluations']}")
    click.echo(
        f"   Passed: {summary['passed']} ({summary['passed']/summary['total_evaluations']*100:.1f}%)"
    )
    click.echo(
        f"   Failed: {summary['failed']} ({summary['failed']/summary['total_evaluations']*100:.1f}%)"
    )
    if summary["errors"] > 0:
        click.echo(f"   Errors: {summary['errors']} ⚠️")

    # Print by-coder summary
    if len(summary["by_coder"]) > 1:
        click.echo("\n   By Coder:")
        for coder, stats in summary["by_coder"].items():
            pass_rate = (
                stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            )
            click.echo(
                f"     {coder}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)"
            )

    # Print by-model summary
    if len(summary["by_model"]) > 1:
        click.echo("\n   By Model:")
        for model, stats in summary["by_model"].items():
            pass_rate = (
                stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            )
            click.echo(
                f"     {model}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)"
            )

    click.echo("\n✅ Evaluation complete!")


@cli.command("introspect-mcp")
@click.argument("mcp_spec", type=str)
@click.option(
    "--registry",
    "-r",
    type=str,
    help="Load MCP from registry (e.g., 'metacoder.basics')",
)
@click.option(
    "--timeout",
    "-t",
    type=int,
    default=30,
    help="Connection timeout in seconds (default: 30)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def introspect_mcp(mcp_spec: str, registry: Optional[str], timeout: int, verbose: bool):
    """
    Introspect an MCP server to list its available tools, resources, and prompts.
    
    MCP_SPEC can be:
    - A URL (http://localhost:8080)
    - A command (uvx mcp-server-fetch)
    - An MCP name when used with --registry
    
    Examples:
    
    \b
    # Introspect a running MCP server
    metacoder introspect-mcp http://localhost:8080
    
    \b
    # Introspect an MCP from registry
    metacoder introspect-mcp fetch --registry metacoder.basics
    
    \b
    # Introspect a command-based MCP
    metacoder introspect-mcp "uvx mcp-server-fetch"
    """
    # Setup logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Run the introspection with proper cleanup
    import os
    import sys
    
    # Suppress the specific asyncio warning by running with -W flag
    env = os.environ.copy()
    env['PYTHONWARNINGS'] = 'ignore::RuntimeWarning:asyncio.base_subprocess'
    
    # Run in a subprocess to isolate the asyncio event loop
    import subprocess
    args = [sys.executable, "-W", "ignore::RuntimeWarning:asyncio.base_subprocess", "-c", f"""
import asyncio
import sys
sys.path.insert(0, {repr(str(Path(__file__).parent.parent))})

from metacoder.metacoder import _introspect_mcp_async

try:
    asyncio.run(_introspect_mcp_async({repr(mcp_spec)}, {repr(registry)}, {timeout}, {verbose}))
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""]
    
    try:
        # Run with stderr captured to filter out asyncio warnings
        result = subprocess.run(
            args, 
            env=env, 
            timeout=timeout + 5,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Filter out the specific asyncio warning from stderr
        if result.stderr:
            error_lines = []
            skip_next = 0
            lines = result.stderr.splitlines()
            
            for i, line in enumerate(lines):
                if "Exception ignored in: <function BaseSubprocessTransport.__del__" in line:
                    # Skip this line and the rest of the traceback
                    skip_next = 100  # Skip many lines to catch the full traceback
                elif skip_next > 0:
                    skip_next -= 1
                    # Check if we've reached the end of the traceback
                    if "RuntimeError: Event loop is closed" in line:
                        skip_next = 0  # Stop skipping after this line
                else:
                    error_lines.append(line)
            
            # Print any remaining stderr
            if error_lines:
                for line in error_lines:
                    click.echo(line, err=True)
        
        if result.returncode != 0:
            raise click.ClickException("Failed to introspect MCP server")
    except subprocess.TimeoutExpired:
        raise click.ClickException(f"Introspection timed out after {timeout} seconds")
    except Exception as e:
        raise click.ClickException(f"Failed to introspect MCP: {e}")


async def _introspect_mcp_async(
    mcp_spec: str, registry: Optional[str], timeout: int, verbose: bool
):
    """Async implementation of MCP introspection."""
    from fastmcp import Client
    
    mcp_config = None
    spec_to_use: Union[str, list[str]] = mcp_spec
    
    # If registry is specified, load the MCP config
    if registry:
        click.echo(f"📚 Loading MCP '{mcp_spec}' from registry: {registry}")
        registry_config = load_mcp_registry(registry)
        
        # Find the MCP in the registry
        mcp_config = None
        for mcp in registry_config.servers:
            if mcp.name == mcp_spec:
                mcp_config = mcp
                break
        
        if not mcp_config:
            available = [mcp.name for mcp in registry_config.servers]
            raise click.ClickException(
                f"MCP '{mcp_spec}' not found in registry. Available: {', '.join(available)}"
            )
        
        # Build the command from MCP config
        if mcp_config.command and mcp_config.args:
            spec_to_use = [mcp_config.command] + mcp_config.args
        else:
            raise click.ClickException(f"MCP '{mcp_spec}' has incomplete command configuration")
    
    click.echo(f"🔍 Introspecting MCP: {spec_to_use}")
    
    # Create client based on the spec type
    if isinstance(spec_to_use, list):
        # Command-based MCP - FastMCP expects a single server config dict
        server_config = {
            "server_name": {
                "command": spec_to_use[0],
                "args": spec_to_use[1:] if len(spec_to_use) > 1 else []
            }
        }
        if mcp_config and mcp_config.env:
            server_config["server_name"]["env"] = mcp_config.env  # type: ignore
        
        # FastMCP expects the full config with mcpServers key
        full_config = {"mcpServers": server_config}
        client = Client(full_config)
    elif spec_to_use.startswith("http://") or spec_to_use.startswith("https://"):
        # URL-based MCP
        client = Client(spec_to_use)  # type: ignore[assignment]
    else:
        # Try as command
        import shlex
        parts = shlex.split(spec_to_use)
        server_config = {
            "server_name": {
                "command": parts[0],
                "args": parts[1:] if len(parts) > 1 else []
            }
        }
        full_config = {"mcpServers": server_config}
        client = Client(full_config)
    
    async with client:
        click.echo("✅ Connected to MCP server")
        
        # Get server info if available
        if hasattr(client, 'server_info'):
            info = client.server_info
            click.echo("\n📋 Server Info:")
            click.echo(f"   Name: {info.name}")
            click.echo(f"   Version: {info.version}")
            if hasattr(info, 'description') and info.description:
                click.echo(f"   Description: {info.description}")
        
        # List tools
        click.echo("\n🔧 Available Tools:")
        try:
            tools = await client.list_tools()
            if tools:
                for tool in tools:
                    click.echo(f"\n   📌 {tool.name}")
                    if tool.description:
                        click.echo(f"      Description: {tool.description}")
                    if verbose and hasattr(tool, 'inputSchema') and tool.inputSchema:
                        click.echo(f"      Input Schema: {yaml.dump(tool.inputSchema, default_flow_style=False, indent=8).strip()}")
            else:
                click.echo("   (No tools available)")
        except Exception as e:
            click.echo(f"   ⚠️ Error listing tools: {e}")
        
        # List resources
        click.echo("\n📁 Available Resources:")
        try:
            resources = await client.list_resources()
            if resources:
                for resource in resources:
                    click.echo(f"\n   📄 {resource.name}")
                    click.echo(f"      URI: {resource.uri}")
                    if resource.description:
                        click.echo(f"      Description: {resource.description}")
                    if resource.mimeType:
                        click.echo(f"      MIME Type: {resource.mimeType}")
            else:
                click.echo("   (No resources available)")
        except Exception as e:
            click.echo(f"   ⚠️ Error listing resources: {e}")
        
        # List prompts
        click.echo("\n💬 Available Prompts:")
        try:
            prompts = await client.list_prompts()
            if prompts:
                for prompt in prompts:
                    click.echo(f"\n   💡 {prompt.name}")
                    if prompt.description:
                        click.echo(f"      Description: {prompt.description}")
                    if verbose and hasattr(prompt, 'arguments') and prompt.arguments:
                        click.echo("      Arguments:")
                        for arg in prompt.arguments:
                            req = "required" if arg.required else "optional"
                            click.echo(f"        - {arg.name} ({req}): {arg.description}")
            else:
                click.echo("   (No prompts available)")
        except Exception as e:
            click.echo(f"   ⚠️ Error listing prompts: {e}")
        
        click.echo("\n✅ Introspection complete!")


# Make main point to cli for backward compatibility
main = cli


if __name__ == "__main__":
    cli()
