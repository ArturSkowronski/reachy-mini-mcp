"""Smoke test for do_barrel_roll — verifies the full choreography sequence."""

from unittest.mock import call

from reachy import do_barrel_roll


async def test_barrel_roll_full_sequence(mock_reachy, mock_create_head_pose):
    """Verify the complete barrel-roll choreography.

    Expected sequence:
    1. goto_target(head=tilted_pose, duration=1.0)   — head tilt
    2. goto_target(antennas=[0.6, -0.6], duration=0.3) — wiggle right
    3. goto_target(antennas=[-0.6, 0.6], duration=0.3) — wiggle left
    4. goto_target(head=default_pose, antennas=[0,0], duration=1.0) — reset
    """
    result = await do_barrel_roll()

    assert result == "Did the barrel roll2!"
    assert mock_reachy.goto_target.call_count == 4

    calls = mock_reachy.goto_target.call_args_list

    # Call 1: head tilt (head pose with z=20, roll=10)
    assert calls[0] == call(
        head=mock_create_head_pose.return_value, duration=1.0,
    )

    # Call 2: antenna wiggle right
    assert calls[1] == call(antennas=[0.6, -0.6], duration=0.3)

    # Call 3: antenna wiggle left
    assert calls[2] == call(antennas=[-0.6, 0.6], duration=0.3)

    # Call 4: reset to rest position
    assert calls[3] == call(
        head=mock_create_head_pose.return_value,
        antennas=[0, 0],
        duration=1.0,
    )


async def test_barrel_roll_head_pose_args(mock_reachy, mock_create_head_pose):
    """Verify create_head_pose is called with correct tilt + reset args."""
    await do_barrel_roll()

    pose_calls = mock_create_head_pose.call_args_list
    # First call: tilted pose
    assert pose_calls[0] == call(z=20, roll=10, mm=True, degrees=True)
    # Second call: default rest pose
    assert pose_calls[1] == call()


async def test_barrel_roll_context_manager(mock_reachy):
    """Verify the context manager lifecycle is followed."""
    await do_barrel_roll()

    mock_reachy.__enter__.assert_called_once()
    mock_reachy.__exit__.assert_called_once()


async def test_barrel_roll_return_string(mock_reachy):
    """Verify the return string format."""
    result = await do_barrel_roll()

    assert isinstance(result, str)
    assert "barrel roll" in result.lower()
