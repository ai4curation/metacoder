import logging
from pathlib import Path
from typing import Optional

import click
import yaml
from pydantic import ValidationError

from coders.config import CoderConfig
from coders.goose import GooseCoder
from coders.base_coder import BaseCoder


logger = logging.getLogger(__name__)


AVAILABLE_CODERS = {
    "goose": GooseCoder,
}


def load_coder_config(config_path: Optional[Path]) -> Optional[CoderConfig]:
    """Load CoderConfig from YAML file."""
    if not config_path:
        return None
    
    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return CoderConfig.model_validate(config_data)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML in config file: {e}")
    except ValidationError as e:
        raise click.ClickException(f"Invalid config format: {e}")


def create_coder(coder_name: str, workdir: str, config: Optional[CoderConfig] = None) -> BaseCoder:
    """Create a coder instance."""
    if coder_name not in AVAILABLE_CODERS:
        available = ", ".join(AVAILABLE_CODERS.keys())
        raise click.ClickException(f"Unknown coder: {coder_name}. Available: {available}")
    
    coder_class = AVAILABLE_CODERS[coder_name]
    
    # Create coder with workdir
    coder = coder_class(workdir=workdir)
    
    # Apply config if provided
    if config:
        coder.config = config
    
    return coder


@click.command()
@click.argument('prompt', type=str)
@click.option('--coder', '-c', type=click.Choice(list(AVAILABLE_CODERS.keys())), 
              default='goose', help='Coder to use')
@click.option('--config', '-f', type=click.Path(exists=True, path_type=Path),
              help='Path to CoderConfig YAML file')
@click.option('--workdir', '-w', type=click.Path(path_type=Path), default='./workdir',
              help='Working directory for the coder')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.version_option()
def main(prompt: str, coder: str, config: Optional[Path], workdir: Path, verbose: bool):
    """
    Metacoder - Pick a coder and run commands with optional configuration.
    
    PROMPT is the text prompt to send to the coder.
    
    Examples:
    
    \b
    # Simple usage with goose
    metacoder "Write a hello world program in Python"
    
    \b
    # Use specific coder with config
    metacoder "Fix the bug in main.py" --coder goose --config goose_config.yaml
    
    \b
    # Custom working directory
    metacoder "Analyze the code" --workdir ./my_project
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
        coder_config = load_coder_config(config)
    
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
        click.echo("\n" + "="*50)
        click.echo("📊 RESULTS")
        click.echo("="*50)
        
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
            click.echo(f"\n📋 Structured messages ({len(result.structured_messages)} total)")
            for i, msg in enumerate(result.structured_messages):
                click.echo(f"  {i+1}. {msg}")
        
    except Exception as e:
        raise click.ClickException(f"Coder execution failed: {e}")


if __name__ == '__main__':
    main()