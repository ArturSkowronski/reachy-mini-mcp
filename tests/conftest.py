"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_reachy():
    """Mocked ReachyMini with context manager and all SDK methods.

    Patches ``reachy.ReachyMini`` so that every tool under test receives
    this mock instead of connecting to a real robot.

    Yields the mock instance (the object returned by ``__enter__``).
    """
    mock_mini = MagicMock()
    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)

    mock_reachy_class = MagicMock(return_value=mock_mini)

    with patch("reachy.ReachyMini", mock_reachy_class):
        yield mock_mini


@pytest.fixture
def mock_create_head_pose():
    """Mocked ``create_head_pose`` that returns a fresh MagicMock pose.

    Patches ``reachy.create_head_pose`` and yields the patch object so
    tests can inspect call args via ``mock_create_head_pose.assert_called_*``.
    The return value (``mock_create_head_pose.return_value``) is the pose
    object passed to ``goto_target(head=...)``.
    """
    mock_pose = MagicMock(name="head_pose")
    with patch("reachy.create_head_pose", return_value=mock_pose) as mock_fn:
        yield mock_fn
