"""Tests for coder availability checking."""
import pytest
from unittest.mock import patch

from metacoder.coders.goose import GooseCoder
from metacoder.coders.claude import ClaudeCoder
from metacoder.coders.codex import CodexCoder
from metacoder.coders.gemini import GeminiCoder
from metacoder.coders.qwen import QwenCoder
from metacoder.coders.dummy import DummyCoder


def test_dummy_always_available():
    """Test that DummyCoder is always available."""
    assert DummyCoder.is_available() is True


@patch('shutil.which')
def test_goose_availability_check(mock_which):
    """Test GooseCoder availability check."""
    # Test when goose is available
    mock_which.return_value = '/usr/local/bin/goose'
    assert GooseCoder.is_available() is True
    mock_which.assert_called_with('goose')
    
    # Test when goose is not available
    mock_which.return_value = None
    assert GooseCoder.is_available() is False


@patch('shutil.which')
def test_claude_availability_check(mock_which):
    """Test ClaudeCoder availability check."""
    # Test when claude is available
    mock_which.return_value = '/usr/local/bin/claude'
    assert ClaudeCoder.is_available() is True
    mock_which.assert_called_with('claude')
    
    # Test when claude is not available
    mock_which.return_value = None
    assert ClaudeCoder.is_available() is False


@patch('shutil.which')
def test_codex_availability_check(mock_which):
    """Test CodexCoder availability check."""
    # Test when codex is available
    mock_which.return_value = '/usr/local/bin/codex'
    assert CodexCoder.is_available() is True
    mock_which.assert_called_with('codex')
    
    # Test when codex is not available
    mock_which.return_value = None
    assert CodexCoder.is_available() is False


def test_all_coders_have_availability_method():
    """Test that all coder classes have is_available method."""
    from metacoder.metacoder import AVAILABLE_CODERS
    
    for coder_name, coder_class in AVAILABLE_CODERS.items():
        assert hasattr(coder_class, 'is_available'), f"{coder_name} missing is_available method"
        assert callable(coder_class.is_available), f"{coder_name}.is_available is not callable"


@patch('shutil.which')
def test_gemini_availability_check(mock_which):
    """Test GeminiCoder availability check."""
    # Test when gemini is available
    mock_which.return_value = '/usr/local/bin/gemini'
    assert GeminiCoder.is_available() is True
    mock_which.assert_called_with('gemini')
    
    # Test when gemini is not available
    mock_which.return_value = None
    assert GeminiCoder.is_available() is False


@patch('shutil.which')
def test_qwen_availability_check(mock_which):
    """Test QwenCoder availability check."""
    # Test when qwen is available
    mock_which.return_value = '/usr/local/bin/qwen'
    assert QwenCoder.is_available() is True
    mock_which.assert_called_with('qwen')
    
    # Test when qwen is not available
    mock_which.return_value = None
    assert QwenCoder.is_available() is False


def test_actual_availability():
    """Test actual availability of coders on this system."""
    print("\nActual coder availability on this system:")
    print(f"  DummyCoder: {DummyCoder.is_available()}")
    print(f"  GooseCoder: {GooseCoder.is_available()}")
    print(f"  ClaudeCoder: {ClaudeCoder.is_available()}")
    print(f"  CodexCoder: {CodexCoder.is_available()}")
    print(f"  GeminiCoder: {GeminiCoder.is_available()}")
    print(f"  QwenCoder: {QwenCoder.is_available()}")
    
    # At least dummy should always be available
    assert DummyCoder.is_available() is True