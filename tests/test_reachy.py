"""Tests for reachy.py MCP tools."""

import pytest
from unittest.mock import MagicMock, patch

from reachy import do_barrel_roll, say, wake_up, detect_sound_direction, move_antennas, move_head, express_emotion

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


@pytest.mark.asyncio
async def test_wake_up():
    """Test that wake_up calls the robot's wake_up method."""
    mock_mini = MagicMock()
    mock_mini.wake_up = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await wake_up()
    
    assert result == "Reachy woke up!"
    mock_mini.wake_up.assert_called_once()
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_detect_sound_direction_with_speech():
    """Test detect_sound_direction when speech is detected."""
    mock_mini = MagicMock()
    mock_audio = MagicMock()
    mock_media = MagicMock()
    mock_media.audio = mock_audio
    
    # Mock get_DoA to return angle and speech_detected=True
    mock_audio.get_DoA = MagicMock(return_value=(1.57, True))  # ~90 degrees, speech detected
    mock_mini.media = mock_media

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await detect_sound_direction()
    
    assert "1.57" in result
    assert "speech detected" in result
    mock_audio.get_DoA.assert_called_once()
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_detect_sound_direction_no_speech():
    """Test detect_sound_direction when no speech is detected."""
    mock_mini = MagicMock()
    mock_audio = MagicMock()
    mock_media = MagicMock()
    mock_media.audio = mock_audio
    
    # Mock get_DoA to return angle and speech_detected=False
    mock_audio.get_DoA = MagicMock(return_value=(0.0, False))  # 0 degrees, no speech
    mock_mini.media = mock_media

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await detect_sound_direction()
    
    assert "0.00" in result
    assert "no speech detected" in result
    mock_audio.get_DoA.assert_called_once()
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_detect_sound_direction_left_side():
    """Test detect_sound_direction for sound coming from the left."""
    mock_mini = MagicMock()
    mock_audio = MagicMock()
    mock_media = MagicMock()
    mock_media.audio = mock_audio
    
    # Mock get_DoA to return angle pointing left (0 radians) with speech
    mock_audio.get_DoA = MagicMock(return_value=(0.0, True))
    mock_mini.media = mock_media

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await detect_sound_direction()
    
    assert "0.00" in result
    assert "speech detected" in result
    assert "0.0°" in result  # Should convert radians to degrees
    mock_audio.get_DoA.assert_called_once()


@pytest.mark.asyncio
async def test_move_antennas_basic():
    """Test move_antennas with basic values."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await move_antennas(right=1.0, left=-1.0)
    
    assert "right=1.00" in result
    assert "left=-1.00" in result
    mock_mini.goto_target.assert_called_once_with(antennas=[1.0, -1.0], duration=0.5)
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_move_antennas_with_duration():
    """Test move_antennas with custom duration."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await move_antennas(right=0.5, left=0.5, duration=1.0)
    
    assert "right=0.50" in result
    assert "left=0.50" in result
    mock_mini.goto_target.assert_called_once_with(antennas=[0.5, 0.5], duration=1.0)


@pytest.mark.asyncio
async def test_move_antennas_clamp_upper_bound():
    """Test that move_antennas clamps values above 3.14."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await move_antennas(right=5.0, left=4.0)
    
    # Values should be clamped to 3.14
    assert "right=3.14" in result
    assert "left=3.14" in result
    mock_mini.goto_target.assert_called_once_with(antennas=[3.14, 3.14], duration=0.5)


@pytest.mark.asyncio
async def test_move_antennas_clamp_lower_bound():
    """Test that move_antennas clamps values below -3.14."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await move_antennas(right=-5.0, left=-4.0)
    
    # Values should be clamped to -3.14
    assert "right=-3.14" in result
    assert "left=-3.14" in result
    mock_mini.goto_target.assert_called_once_with(antennas=[-3.14, -3.14], duration=0.5)


@pytest.mark.asyncio
async def test_move_antennas_zero_position():
    """Test move_antennas with zero positions."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await move_antennas(right=0.0, left=0.0)
    
    assert "right=0.00" in result
    assert "left=0.00" in result
    mock_mini.goto_target.assert_called_once_with(antennas=[0.0, 0.0], duration=0.5)


@pytest.mark.asyncio
async def test_move_head_basic():
    """Test move_head with all parameters."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose) as mock_create_pose:
        result = await move_head(x=10, y=5, z=15, roll=10, pitch=-5, yaw=20, duration=1.5)
    
    assert "pos(10, 5, 15)mm" in result
    assert "rot(10, -5, 20)°" in result
    mock_create_pose.assert_called_once_with(
        x=10, y=5, z=15,
        roll=10, pitch=-5, yaw=20,
        mm=True,
        degrees=True
    )
    mock_mini.goto_target.assert_called_once_with(head=mock_pose, duration=1.5)
    mock_mini.__enter__.assert_called_once()
    mock_mini.__exit__.assert_called_once()


@pytest.mark.asyncio
async def test_move_head_defaults():
    """Test move_head with default values."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose) as mock_create_pose:
        result = await move_head()
    
    assert "pos(0, 0, 0)mm" in result
    assert "rot(0, 0, 0)°" in result
    mock_create_pose.assert_called_once_with(
        x=0, y=0, z=0,
        roll=0, pitch=0, yaw=0,
        mm=True,
        degrees=True
    )
    mock_mini.goto_target.assert_called_once_with(head=mock_pose, duration=1.0)


@pytest.mark.asyncio
async def test_move_head_position_only():
    """Test move_head with only position parameters."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose) as mock_create_pose:
        result = await move_head(x=20, y=10, z=30)
    
    assert "pos(20, 10, 30)mm" in result
    assert "rot(0, 0, 0)°" in result
    mock_create_pose.assert_called_once_with(
        x=20, y=10, z=30,
        roll=0, pitch=0, yaw=0,
        mm=True,
        degrees=True
    )
    mock_mini.goto_target.assert_called_once_with(head=mock_pose, duration=1.0)


@pytest.mark.asyncio
async def test_move_head_rotation_only():
    """Test move_head with only rotation parameters."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose) as mock_create_pose:
        result = await move_head(roll=15, pitch=-10, yaw=30, duration=0.8)
    
    assert "pos(0, 0, 0)mm" in result
    assert "rot(15, -10, 30)°" in result
    mock_create_pose.assert_called_once_with(
        x=0, y=0, z=0,
        roll=15, pitch=-10, yaw=30,
        mm=True,
        degrees=True
    )
    mock_mini.goto_target.assert_called_once_with(head=mock_pose, duration=0.8)


@pytest.mark.asyncio
async def test_express_emotion_happy():
    """Test express_emotion with happy emoji 😊."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_media = MagicMock()
    mock_media.play_sound = MagicMock()
    mock_mini.media = mock_media
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("😊")
    
    assert result == "Reachy expressed: happy (😊)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[0.8, 0.8],
        duration=0.8
    )
    mock_media.play_sound.assert_called_once_with("dance1.wav")


@pytest.mark.asyncio
async def test_express_emotion_confused():
    """Test express_emotion with confused emoji 😕."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_media = MagicMock()
    mock_media.play_sound = MagicMock()
    mock_mini.media = mock_media
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("😕")
    
    assert result == "Reachy expressed: confused (😕)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[0.5, -0.3],
        duration=0.6
    )
    mock_media.play_sound.assert_called_once_with("confused1.wav")


@pytest.mark.asyncio
async def test_express_emotion_impatient():
    """Test express_emotion with impatient emoji 😤."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_media = MagicMock()
    mock_media.play_sound = MagicMock()
    mock_mini.media = mock_media

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await express_emotion("😤")
    
    assert result == "Reachy expressed: impatient (😤)"
    # Should be called 3 times for rapid antenna movements
    assert mock_mini.goto_target.call_count == 3
    mock_mini.goto_target.assert_any_call(antennas=[0.7, -0.7], duration=0.2)
    mock_mini.goto_target.assert_any_call(antennas=[-0.7, 0.7], duration=0.2)
    mock_media.play_sound.assert_called_once_with("impatient1.wav")


@pytest.mark.asyncio
async def test_express_emotion_sleepy():
    """Test express_emotion with sleepy emoji 😴."""
    mock_mini = MagicMock()
    mock_mini.goto_sleep = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await express_emotion("😴")
    
    assert result == "Reachy expressed: sleepy (😴)"
    mock_mini.goto_sleep.assert_called_once()


@pytest.mark.asyncio
async def test_express_emotion_wave():
    """Test express_emotion with wave/greeting emoji 👋."""
    mock_mini = MagicMock()
    mock_mini.wake_up = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await express_emotion("👋")
    
    assert result == "Reachy expressed: greeting (👋)"
    mock_mini.wake_up.assert_called_once()


@pytest.mark.asyncio
async def test_express_emotion_thinking():
    """Test express_emotion with thinking emoji 🤔."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("🤔")
    
    assert result == "Reachy expressed: thinking (🤔)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[0.6, -0.6],
        duration=1.0
    )


@pytest.mark.asyncio
async def test_express_emotion_surprised():
    """Test express_emotion with surprised emoji 😮."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("😮")
    
    assert result == "Reachy expressed: surprised (😮)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[1.2, 1.2],
        duration=0.4
    )


@pytest.mark.asyncio
async def test_express_emotion_sad():
    """Test express_emotion with sad emoji 😢."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("😢")
    
    assert result == "Reachy expressed: sad (😢)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[-0.5, -0.5],
        duration=1.2
    )


@pytest.mark.asyncio
async def test_express_emotion_celebrate():
    """Test express_emotion with celebrate emoji 🎉."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_media = MagicMock()
    mock_media.play_sound = MagicMock()
    mock_mini.media = mock_media
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("🎉")
    
    assert result == "Reachy expressed: celebrate (🎉)"
    # Should be called twice for wiggle celebration
    assert mock_mini.goto_target.call_count == 2
    mock_media.play_sound.assert_called_once_with("dance1.wav")


@pytest.mark.asyncio
async def test_express_emotion_neutral():
    """Test express_emotion with neutral emoji 😐."""
    mock_mini = MagicMock()
    mock_mini.goto_target = MagicMock()
    mock_pose = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class), \
         patch("reachy.create_head_pose", return_value=mock_pose):
        result = await express_emotion("😐")
    
    assert result == "Reachy expressed: neutral (😐)"
    mock_mini.goto_target.assert_called_once_with(
        head=mock_pose,
        antennas=[0, 0],
        duration=0.8
    )


@pytest.mark.asyncio
async def test_express_emotion_unsupported():
    """Test express_emotion with unsupported emoji."""
    mock_mini = MagicMock()

    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    
    mock_reachy_class = MagicMock(return_value=mock_mini)
    
    with patch("reachy.ReachyMini", mock_reachy_class):
        result = await express_emotion("🔥")
    
    assert "Unsupported emoji: 🔥" in result
    assert "Please use one of the supported emojis" in result

