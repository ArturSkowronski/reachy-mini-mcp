"""Tests for reachy.py MCP tools."""

import pytest
from unittest.mock import MagicMock, patch

from reachy import do_barrel_roll, say

@pytest.mark.asyncio
async def test_say():
    """Test that say makes Reachy speak the given text."""
    test_text = "Hello, World!"
    mock_mini = MagicMock()
    mock_speaker = MagicMock()
    mock_mini.speaker = mock_speaker

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await say(test_text)
    
    assert result == f"Reachy said: {test_text}"
    
    mock_speaker.say.assert_called_once_with(test_text)
    
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_say_empty_string():
    """Test that say handles empty strings."""
    test_text = ""
    mock_mini = MagicMock()
    mock_speaker = MagicMock()
    mock_mini.speaker = mock_speaker

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await say(test_text)
    
    assert result == "Reachy said: "
    mock_speaker.say.assert_called_once_with("")


@pytest.mark.asyncio
async def test_say_long_text():
    """Test that say handles longer text strings."""
    test_text = "This is a longer text string that Reachy should be able to speak without any issues."
    mock_mini = MagicMock()
    mock_speaker = MagicMock()
    mock_mini.speaker = mock_speaker

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await say(test_text)
    
    assert result == f"Reachy said: {test_text}"
    mock_speaker.say.assert_called_once_with(test_text)

