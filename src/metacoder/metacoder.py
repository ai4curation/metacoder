import logging
from pathlib import Path
from typing import Optional

import click
import yaml
from pydantic import ValidationError

from metacoder.configuration import CoderConfig, MCPCollectionConfig
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
def run(
    prompt: str,
    coder: str,
    config: Optional[str],
    mcp_collection: Optional[str],
    enable_mcp: tuple[str, ...],
    workdir: str,
    provider: Optional[str],
    model: Optional[str],
    verbose: bool,
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
    # Custom working directory
    metacoder run "Analyze the code" --workdir ./my_project

    \b
    # Override AI model
    metacoder run "Write a function" --provider openai --model gpt-4

    \b
    # Use Claude with specific model
    metacoder run "Explain this code" --coder claude --provider anthropic --model claude-3-opus
    """
    # Setup logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
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

    # Merge MCP extensions into coder config
    if mcp_collection_config:
        coder_config = merge_mcp_extensions(
            coder_config,
            mcp_collection_config,
            list(enable_mcp) if enable_mcp else None,
        )

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

    # Create coder instance
    try:
        coder_instance = create_coder(coder, str(workdir), coder_config)
    except Exception as e:
        raise click.ClickException(f"Failed to create coder: {e}")

    # Run the coder
    click.echo(f"🚀 Running prompt: {prompt}")
    try:
        result = coder_instance.run(prompt)

        # Display results
        click.echo("\n" + "=" * 50)
        click.echo("📊 RESULTS")
        click.echo("=" * 50)

        if result.result_text:
            click.echo("\n📝 Result:")
            click.echo(result.result_text)

        if result.stdout:
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

        if verbose and result.structured_messages:
            click.echo(
                f"\n📋 Structured messages ({len(result.structured_messages)} total)"
            )
            for i, msg in enumerate(result.structured_messages):
                click.echo(f"  {i+1}. {msg}")

    except Exception as e:
        raise click.ClickException(f"Coder execution failed: {e}")


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

    try:
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

    except Exception as e:
        raise click.ClickException(f"Evaluation failed: {e}")


# Make main point to cli for backward compatibility
main = cli


if __name__ == "__main__":
    cli()
