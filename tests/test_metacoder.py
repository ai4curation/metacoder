import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from metacoder import main, load_coder_config, create_coder, AVAILABLE_CODERS
from coders.config import CoderConfig, AIModelConfig, AIModelProvider, ToolExtension
from coders.base_coder import CoderOutput


@pytest.fixture
def runner():
    """Click test runner fixture."""
    return CliRunner()


def test_main_help(runner):
    """Test main command help output."""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'Metacoder - Pick a coder and run commands' in result.output
    assert '--coder' in result.output
    assert '--config' in result.output
    assert '--workdir' in result.output
    assert '--verbose' in result.output


def test_available_coders():
    """Test that available coders are properly configured."""
    assert 'goose' in AVAILABLE_CODERS
    assert len(AVAILABLE_CODERS) > 0


def test_load_coder_config_nonexistent_file():
    """Test loading config from non-existent file."""
    with pytest.raises(Exception) as exc_info:
        load_coder_config(Path('nonexistent.yaml'))
    assert 'Config file not found' in str(exc_info.value)


def test_load_coder_config_valid_file():
    """Test loading valid config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'ai_model': {
                'name': 'gpt-4o',
                'provider': {
                    'name': 'openai',
                    'api_key': 'test-key'
                }
            },
            'extensions': [
                {
                    'name': 'developer',
                    'display_name': 'Developer',
                    'enabled': True,
                    'bundled': True,
                    'type': 'builtin',
                    'timeout': 300
                }
            ]
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        config = load_coder_config(config_path)
        assert config is not None
        assert config.ai_model.name == 'gpt-4o'
        assert config.ai_model.provider.name == 'openai'
        assert len(config.extensions) == 1
        assert config.extensions[0].name == 'developer'
    finally:
        config_path.unlink()


def test_load_coder_config_invalid_yaml():
    """Test loading invalid YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write('invalid: yaml: content: [')
        config_path = Path(f.name)
    
    try:
        with pytest.raises(Exception) as exc_info:
            load_coder_config(config_path)
        assert 'Invalid YAML' in str(exc_info.value)
    finally:
        config_path.unlink()


def test_load_coder_config_invalid_structure():
    """Test loading YAML with invalid structure."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'ai_model': 'invalid_structure',  # Should be dict
            'extensions': []
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)
    
    try:
        with pytest.raises(Exception) as exc_info:
            load_coder_config(config_path)
        assert 'Invalid config format' in str(exc_info.value)
    finally:
        config_path.unlink()


def test_create_coder_unknown_coder():
    """Test creating coder with unknown name."""
    with pytest.raises(Exception) as exc_info:
        create_coder('unknown_coder', '/tmp/workdir')
    assert 'Unknown coder' in str(exc_info.value)


def test_create_coder_valid():
    """Test creating valid coder."""
    with tempfile.TemporaryDirectory() as temp_dir:
        coder = create_coder('goose', temp_dir)
        assert coder is not None
        assert coder.workdir == temp_dir


def test_create_coder_with_config():
    """Test creating coder with config."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = CoderConfig(
            ai_model=AIModelConfig(
                name='gpt-4o',
                provider=AIModelProvider(name='openai', api_key='test-key')
            ),
            extensions=[
                ToolExtension(
                    name='developer',
                    display_name='Developer',
                    enabled=True,
                    bundled=True,
                    type='builtin',
                    timeout=300
                )
            ]
        )
        coder = create_coder('goose', temp_dir, config)
        assert coder is not None
        assert coder.config == config


def test_main_missing_prompt(runner):
    """Test main command without prompt."""
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert 'Missing argument' in result.output


def test_main_invalid_coder(runner):
    """Test main command with invalid coder."""
    result = runner.invoke(main, ['test prompt', '--coder', 'invalid'])
    assert result.exit_code != 0
    assert 'Invalid value' in result.output


def test_main_missing_config_file(runner):
    """Test main command with non-existent config file."""
    result = runner.invoke(main, ['test prompt', '--config', 'nonexistent.yaml'])
    assert result.exit_code != 0
    assert 'does not exist' in result.output.lower()


@patch('metacoder.create_coder')
def test_main_success(mock_create_coder, runner):
    """Test successful main command execution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock coder
        mock_coder = MagicMock()
        mock_output = CoderOutput(
            stdout='Test output',
            stderr='',
            result_text='Test result',
            total_cost_usd=0.01,
            success=True
        )
        mock_coder.run.return_value = mock_output
        mock_create_coder.return_value = mock_coder
        
        result = runner.invoke(main, [
            'test prompt',
            '--coder', 'goose',
            '--workdir', temp_dir,
            '--verbose'
        ])
        
        assert result.exit_code == 0
        assert 'Using coder: goose' in result.output
        assert 'Running prompt: test prompt' in result.output
        assert 'RESULTS' in result.output
        assert 'Test result' in result.output
        assert 'Test output' in result.output
        assert '$0.0100' in result.output
        assert 'Success' in result.output


@patch('metacoder.create_coder')
def test_main_with_config(mock_create_coder, runner):
    """Test main command with config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config file
        config_file = Path(temp_dir) / 'config.yaml'
        config_data = {
            'ai_model': {
                'name': 'gpt-4o',
                'provider': {
                    'name': 'openai',
                    'api_key': 'test-key'
                }
            },
            'extensions': [
                {
                    'name': 'developer',
                    'display_name': 'Developer',
                    'enabled': True,
                    'bundled': True,
                    'type': 'builtin',
                    'timeout': 300
                }
            ]
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Mock coder
        mock_coder = MagicMock()
        mock_output = CoderOutput(
            stdout='Test output',
            stderr='',
            result_text='Test result'
        )
        mock_coder.run.return_value = mock_output
        mock_create_coder.return_value = mock_coder
        
        result = runner.invoke(main, [
            'test prompt',
            '--config', str(config_file),
            '--workdir', temp_dir
        ])
        
        assert result.exit_code == 0
        assert 'Loading config from:' in result.output
        assert 'Test result' in result.output
        
        # Verify config was passed to create_coder
        mock_create_coder.assert_called_once()
        call_args = mock_create_coder.call_args
        assert call_args[0][0] == 'goose'  # coder name
        assert call_args[0][1] == temp_dir  # workdir
        assert call_args[0][2] is not None  # config


@patch('metacoder.create_coder')
def test_main_coder_failure(mock_create_coder, runner):
    """Test main command when coder execution fails."""
    mock_coder = MagicMock()
    mock_coder.run.side_effect = Exception('Coder execution failed')
    mock_create_coder.return_value = mock_coder
    
    result = runner.invoke(main, ['test prompt'])
    
    assert result.exit_code != 0
    assert 'Coder execution failed' in result.output


@patch('metacoder.create_coder')
def test_main_structured_messages(mock_create_coder, runner):
    """Test main command with structured messages in verbose mode."""
    mock_coder = MagicMock()
    mock_output = CoderOutput(
        stdout='Test output',
        stderr='',
        result_text='Test result',
        structured_messages=[
            {'role': 'user', 'content': 'test'},
            {'role': 'assistant', 'content': 'response'}
        ]
    )
    mock_coder.run.return_value = mock_output
    mock_create_coder.return_value = mock_coder
    
    result = runner.invoke(main, ['test prompt', '--verbose'])
    
    assert result.exit_code == 0
    assert 'Structured messages (2 total)' in result.output
    assert "{'role': 'user', 'content': 'test'}" in result.output


def test_version_option(runner):
    """Test --version option."""
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0