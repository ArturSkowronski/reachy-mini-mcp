"""Unit tests for reachy.py MCP tools."""

from unittest.mock import MagicMock

import pytest

from reachy import (
    capture_image,
    detect_sound_direction,
    express_emotion,
    go_to_sleep,
    look_at_point,
    move_antennas,
    move_head,
    play_sound,
    reset_position,
    scan_surroundings,
    speak_text,
    wake_up,
)


# ---------------------------------------------------------------------------
# wake_up
# ---------------------------------------------------------------------------


async def test_wake_up(mock_reachy):
    """Test that wake_up calls the robot's wake_up method."""
    result = await wake_up()

    assert result == "Reachy woke up!"
    mock_reachy.wake_up.assert_called_once()
    mock_reachy.__enter__.assert_called_once()
    mock_reachy.__exit__.assert_called_once()


# ---------------------------------------------------------------------------
# go_to_sleep
# ---------------------------------------------------------------------------


async def test_go_to_sleep(mock_reachy):
    """Test that go_to_sleep calls goto_sleep."""
    result = await go_to_sleep()

    assert result == "Reachy went to sleep"
    mock_reachy.goto_sleep.assert_called_once()
    mock_reachy.__enter__.assert_called_once()
    mock_reachy.__exit__.assert_called_once()


# ---------------------------------------------------------------------------
# play_sound
# ---------------------------------------------------------------------------


async def test_play_sound(mock_reachy):
    """Test play_sound calls media.play_sound with correct filename."""
    result = await play_sound("dance1")

    assert result == "Reachy played: dance1"
    mock_reachy.media.play_sound.assert_called_once_with("dance1.wav")


async def test_play_sound_appends_wav(mock_reachy):
    """Test that .wav extension is appended to the sound name."""
    await play_sound("confused1")

    mock_reachy.media.play_sound.assert_called_once_with("confused1.wav")


# ---------------------------------------------------------------------------
# look_at_point
# ---------------------------------------------------------------------------


async def test_look_at_point(mock_reachy):
    """Test look_at_point calls look_at_world with correct args."""
    result = await look_at_point(x=1.0, y=0.5, z=0.3, duration=2.0)

    assert result == "Reachy looking at point (1.0, 0.5, 0.3)"
    mock_reachy.look_at_world.assert_called_once_with(1.0, 0.5, 0.3, duration=2.0)


async def test_look_at_point_default_duration(mock_reachy):
    """Test look_at_point uses default duration of 1.0."""
    await look_at_point(x=0.0, y=0.0, z=1.0)

    mock_reachy.look_at_world.assert_called_once_with(0.0, 0.0, 1.0, duration=1.0)


# ---------------------------------------------------------------------------
# reset_position
# ---------------------------------------------------------------------------


async def test_reset_position(mock_reachy, mock_create_head_pose):
    """Test reset_position sends default pose and zeroed antennas."""
    result = await reset_position()

    assert result == "Reachy reset to neutral position"
    mock_create_head_pose.assert_called_once_with()
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0, 0],
        duration=1.5,
    )


async def test_reset_position_custom_duration(mock_reachy, mock_create_head_pose):
    """Test reset_position respects custom duration."""
    await reset_position(duration=3.0)

    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0, 0],
        duration=3.0,
    )


# ---------------------------------------------------------------------------
# detect_sound_direction
# ---------------------------------------------------------------------------


async def test_detect_sound_direction_with_speech(mock_reachy):
    """Test detect_sound_direction when speech is detected."""
    mock_reachy.media.audio.get_DoA.return_value = (1.57, True)

    result = await detect_sound_direction()

    assert "1.57" in result
    assert "speech detected" in result
    mock_reachy.media.audio.get_DoA.assert_called_once()


async def test_detect_sound_direction_no_speech(mock_reachy):
    """Test detect_sound_direction when no speech is detected."""
    mock_reachy.media.audio.get_DoA.return_value = (0.0, False)

    result = await detect_sound_direction()

    assert "0.00" in result
    assert "no speech detected" in result


async def test_detect_sound_direction_left_side(mock_reachy):
    """Test detect_sound_direction for sound from the left (0 radians)."""
    mock_reachy.media.audio.get_DoA.return_value = (0.0, True)

    result = await detect_sound_direction()

    assert "0.00" in result
    assert "speech detected" in result
    assert "0.0°" in result


# ---------------------------------------------------------------------------
# move_antennas
# ---------------------------------------------------------------------------


async def test_move_antennas_basic(mock_reachy):
    """Test move_antennas with basic values."""
    result = await move_antennas(right=1.0, left=-1.0)

    assert "right=1.00" in result
    assert "left=-1.00" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[1.0, -1.0],
        duration=0.5,
    )


async def test_move_antennas_with_duration(mock_reachy):
    """Test move_antennas with custom duration."""
    result = await move_antennas(right=0.5, left=0.5, duration=1.0)

    assert "right=0.50" in result
    assert "left=0.50" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[0.5, 0.5],
        duration=1.0,
    )


async def test_move_antennas_clamp_upper_bound(mock_reachy):
    """Test that values above 3.14 are clamped."""
    result = await move_antennas(right=5.0, left=4.0)

    assert "right=3.14" in result
    assert "left=3.14" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[3.14, 3.14],
        duration=0.5,
    )


async def test_move_antennas_clamp_lower_bound(mock_reachy):
    """Test that values below -3.14 are clamped."""
    result = await move_antennas(right=-5.0, left=-4.0)

    assert "right=-3.14" in result
    assert "left=-3.14" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[-3.14, -3.14],
        duration=0.5,
    )


async def test_move_antennas_zero_position(mock_reachy):
    """Test move_antennas with zero positions."""
    result = await move_antennas(right=0.0, left=0.0)

    assert "right=0.00" in result
    assert "left=0.00" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[0.0, 0.0],
        duration=0.5,
    )


async def test_move_antennas_exact_boundary(mock_reachy):
    """Test that exact boundary values +-3.14 are not clamped."""
    result = await move_antennas(right=3.14, left=-3.14)

    assert "right=3.14" in result
    assert "left=-3.14" in result
    mock_reachy.goto_target.assert_called_once_with(
        antennas=[3.14, -3.14],
        duration=0.5,
    )


# ---------------------------------------------------------------------------
# move_head
# ---------------------------------------------------------------------------


async def test_move_head_basic(mock_reachy, mock_create_head_pose):
    """Test move_head with all parameters."""
    result = await move_head(
        x=10,
        y=5,
        z=15,
        roll=10,
        pitch=-5,
        yaw=20,
        duration=1.5,
    )

    assert "pos(10, 5, 15)mm" in result
    assert "rot(10, -5, 20)°" in result
    mock_create_head_pose.assert_called_once_with(
        x=10,
        y=5,
        z=15,
        roll=10,
        pitch=-5,
        yaw=20,
        mm=True,
        degrees=True,
    )
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        duration=1.5,
    )


async def test_move_head_defaults(mock_reachy, mock_create_head_pose):
    """Test move_head with default values."""
    result = await move_head()

    assert "pos(0, 0, 0)mm" in result
    assert "rot(0, 0, 0)°" in result
    mock_create_head_pose.assert_called_once_with(
        x=0,
        y=0,
        z=0,
        roll=0,
        pitch=0,
        yaw=0,
        mm=True,
        degrees=True,
    )
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        duration=1.0,
    )


async def test_move_head_position_only(mock_reachy, mock_create_head_pose):
    """Test move_head with only position parameters."""
    result = await move_head(x=20, y=10, z=30)

    assert "pos(20, 10, 30)mm" in result
    assert "rot(0, 0, 0)°" in result
    mock_create_head_pose.assert_called_once_with(
        x=20,
        y=10,
        z=30,
        roll=0,
        pitch=0,
        yaw=0,
        mm=True,
        degrees=True,
    )
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        duration=1.0,
    )


async def test_move_head_rotation_only(mock_reachy, mock_create_head_pose):
    """Test move_head with only rotation parameters."""
    result = await move_head(roll=15, pitch=-10, yaw=30, duration=0.8)

    assert "pos(0, 0, 0)mm" in result
    assert "rot(15, -10, 30)°" in result
    mock_create_head_pose.assert_called_once_with(
        x=0,
        y=0,
        z=0,
        roll=15,
        pitch=-10,
        yaw=30,
        mm=True,
        degrees=True,
    )
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        duration=0.8,
    )


async def test_move_head_negative_values(mock_reachy, mock_create_head_pose):
    """Test move_head with negative position and rotation values."""
    result = await move_head(x=-10, y=-5, z=-15, roll=-10, pitch=-20, yaw=-30)

    assert "pos(-10, -5, -15)mm" in result
    assert "rot(-10, -20, -30)°" in result
    mock_create_head_pose.assert_called_once_with(
        x=-10,
        y=-5,
        z=-15,
        roll=-10,
        pitch=-20,
        yaw=-30,
        mm=True,
        degrees=True,
    )
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        duration=1.0,
    )


# ---------------------------------------------------------------------------
# express_emotion
# ---------------------------------------------------------------------------


async def test_express_emotion_happy(mock_reachy, mock_create_head_pose):
    """Test express_emotion with happy emoji."""
    result = await express_emotion("😊")

    assert result == "Reachy expressed: happy (😊)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0.8, 0.8],
        duration=0.8,
    )
    mock_reachy.media.play_sound.assert_called_once_with("dance1.wav")


async def test_express_emotion_confused(mock_reachy, mock_create_head_pose):
    """Test express_emotion with confused emoji."""
    result = await express_emotion("😕")

    assert result == "Reachy expressed: confused (😕)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0.5, -0.3],
        duration=0.6,
    )
    mock_reachy.media.play_sound.assert_called_once_with("confused1.wav")


async def test_express_emotion_impatient(mock_reachy):
    """Test express_emotion with impatient emoji — 3 rapid antenna moves."""
    result = await express_emotion("😤")

    assert result == "Reachy expressed: impatient (😤)"
    assert mock_reachy.goto_target.call_count == 3
    mock_reachy.goto_target.assert_any_call(antennas=[0.7, -0.7], duration=0.2)
    mock_reachy.goto_target.assert_any_call(antennas=[-0.7, 0.7], duration=0.2)
    mock_reachy.media.play_sound.assert_called_once_with("impatient1.wav")


async def test_express_emotion_sleepy(mock_reachy):
    """Test express_emotion with sleepy emoji calls goto_sleep."""
    result = await express_emotion("😴")

    assert result == "Reachy expressed: sleepy (😴)"
    mock_reachy.goto_sleep.assert_called_once()


async def test_express_emotion_wave(mock_reachy):
    """Test express_emotion with wave emoji calls wake_up."""
    result = await express_emotion("👋")

    assert result == "Reachy expressed: greeting (👋)"
    mock_reachy.wake_up.assert_called_once()


async def test_express_emotion_thinking(mock_reachy, mock_create_head_pose):
    """Test express_emotion with thinking emoji."""
    result = await express_emotion("🤔")

    assert result == "Reachy expressed: thinking (🤔)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0.6, -0.6],
        duration=1.0,
    )


async def test_express_emotion_surprised(mock_reachy, mock_create_head_pose):
    """Test express_emotion with surprised emoji."""
    result = await express_emotion("😮")

    assert result == "Reachy expressed: surprised (😮)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[1.2, 1.2],
        duration=0.4,
    )


async def test_express_emotion_sad(mock_reachy, mock_create_head_pose):
    """Test express_emotion with sad emoji."""
    result = await express_emotion("😢")

    assert result == "Reachy expressed: sad (😢)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[-0.5, -0.5],
        duration=1.2,
    )


async def test_express_emotion_celebrate(mock_reachy, mock_create_head_pose):
    """Test express_emotion with celebrate emoji — wiggle + sound."""
    result = await express_emotion("🎉")

    assert result == "Reachy expressed: celebrate (🎉)"
    assert mock_reachy.goto_target.call_count == 2
    mock_reachy.media.play_sound.assert_called_once_with("dance1.wav")


async def test_express_emotion_neutral(mock_reachy, mock_create_head_pose):
    """Test express_emotion with neutral emoji resets to rest."""
    result = await express_emotion("😐")

    assert result == "Reachy expressed: neutral (😐)"
    mock_reachy.goto_target.assert_called_once_with(
        head=mock_create_head_pose.return_value,
        antennas=[0, 0],
        duration=0.8,
    )


async def test_express_emotion_unsupported(mock_reachy):
    """Test express_emotion with unsupported emoji."""
    result = await express_emotion("🔥")

    assert "Unsupported emoji: 🔥" in result
    assert "Please use one of the supported emojis" in result


@pytest.mark.parametrize("emoji", ["💀", "🤖", "🦄"])
async def test_express_emotion_multiple_unsupported(mock_reachy, emoji):
    """Test that various unsupported emojis all return the error message."""
    result = await express_emotion(emoji)

    assert f"Unsupported emoji: {emoji}" in result


# ---------------------------------------------------------------------------
# speak_text
# ---------------------------------------------------------------------------


async def test_speak_text_plays_audio_and_cleans_temp_file(mock_reachy, tmp_path):
    """Test speak_text generates audio and plays it via Reachy media."""
    from unittest.mock import AsyncMock, patch

    temp_wav = tmp_path / "out.wav"
    temp_wav.write_bytes(b"not-a-real-wav")

    with (
        patch("reachy.load_elevenlabs_config", return_value=MagicMock()),
        patch(
            "reachy.elevenlabs_tts_to_temp_wav",
            new=AsyncMock(return_value=str(temp_wav)),
        ),
    ):
        result = await speak_text("Hello!")

    assert result == "Reachy spoke the provided text via ElevenLabs."
    mock_reachy.media.play_sound.assert_called_once_with(str(temp_wav))
    assert not temp_wav.exists()


# ---------------------------------------------------------------------------
# capture_image
# ---------------------------------------------------------------------------


async def test_capture_image(mock_reachy_with_frame):
    """Test capture_image returns an Image with JPEG data."""
    from mcp.server.fastmcp import Image

    result = await capture_image()

    assert isinstance(result, Image)
    mock_reachy_with_frame.media.get_frame.assert_called_once()


async def test_capture_image_camera_unavailable(mock_reachy):
    """Test capture_image raises when camera returns None."""
    mock_reachy.media.get_frame.return_value = None

    with pytest.raises(RuntimeError, match="Camera not available"):
        await capture_image()


async def test_capture_image_custom_quality(mock_reachy_with_frame):
    """Test capture_image clamps quality to valid range."""
    from unittest.mock import patch

    with patch("reachy.cv2.imencode", wraps=__import__("cv2").imencode) as mock_enc:
        await capture_image(quality=150)
        # Quality should be clamped to 100
        call_args = mock_enc.call_args
        assert call_args[0][0] == ".jpg"
        quality_param = call_args[0][2]
        assert quality_param[1] == 100


# ---------------------------------------------------------------------------
# scan_surroundings
# ---------------------------------------------------------------------------


async def test_scan_surroundings_default(mock_reachy_with_frame, mock_create_head_pose):
    """Test scan_surroundings captures 5 frames across 120° and returns to center."""
    from mcp.server.fastmcp import Image

    result = await scan_surroundings()

    # 5 text labels + 5 images + 1 summary = 11 items
    assert len(result) == 11
    # Check interleaved text/image pattern
    for i in range(5):
        assert isinstance(result[i * 2], str)
        assert isinstance(result[i * 2 + 1], Image)
    # Summary is last
    assert "Scan complete: 5 positions across 120°" in result[-1]
    # 5 captures + 1 return-to-center = 6 goto_target calls
    assert mock_reachy_with_frame.goto_target.call_count == 6
    assert mock_reachy_with_frame.media.get_frame.call_count == 5


async def test_scan_surroundings_custom_steps(
    mock_reachy_with_frame, mock_create_head_pose
):
    """Test scan_surroundings with 3 steps across 90°."""
    result = await scan_surroundings(steps=3, yaw_range=90.0)

    # 3 text labels + 3 images + 1 summary = 7 items
    assert len(result) == 7
    assert "3 positions across 90°" in result[-1]
    assert "from -45° to +45°" in result[-1]
    # 3 captures + 1 return = 4 goto_target calls
    assert mock_reachy_with_frame.goto_target.call_count == 4


async def test_scan_surroundings_clamps_params(
    mock_reachy_with_frame, mock_create_head_pose
):
    """Test that steps and yaw_range are clamped to valid bounds."""
    result = await scan_surroundings(steps=100, yaw_range=500.0)

    # Steps clamped to 9, yaw_range clamped to 180
    assert "9 positions across 180°" in result[-1]


async def test_scan_surroundings_frame_failure(mock_reachy, mock_create_head_pose):
    """Test scan_surroundings handles frame capture failures gracefully."""
    mock_reachy.media.get_frame.return_value = None

    result = await scan_surroundings(steps=2)

    # 2 failure messages + 1 summary = 3 items (no images)
    assert len(result) == 3
    assert "frame capture failed" in result[0]
    assert "frame capture failed" in result[1]
    assert "Scan complete" in result[2]


async def test_scan_surroundings_yaw_positions(
    mock_reachy_with_frame, mock_create_head_pose
):
    """Test that yaw positions are evenly distributed across the range."""
    await scan_surroundings(steps=3, yaw_range=60.0)

    # Expected yaw positions: -30, 0, +30
    create_calls = mock_create_head_pose.call_args_list
    # First 3 calls are for scan positions, 4th is return-to-center
    yaws = [call.kwargs["yaw"] for call in create_calls[:3]]
    assert yaws == pytest.approx([-30.0, 0.0, 30.0])


# ---------------------------------------------------------------------------
# Connection error tests
# ---------------------------------------------------------------------------


async def test_wake_up_connection_error():
    """Test that connection errors propagate from wake_up."""
    from unittest.mock import MagicMock, patch

    mock_class = MagicMock(side_effect=ConnectionError("Robot not found"))
    with patch("reachy.ReachyMini", mock_class):
        with pytest.raises(ConnectionError, match="Robot not found"):
            await wake_up()


async def test_move_head_connection_error():
    """Test that connection errors propagate from move_head."""
    from unittest.mock import MagicMock, patch

    mock_class = MagicMock(side_effect=ConnectionError("Timeout"))
    with patch("reachy.ReachyMini", mock_class):
        with pytest.raises(ConnectionError, match="Timeout"):
            await move_head()


async def test_detect_sound_connection_error():
    """Test that connection errors propagate from detect_sound_direction."""
    from unittest.mock import MagicMock, patch

    mock_class = MagicMock(side_effect=OSError("Network unreachable"))
    with patch("reachy.ReachyMini", mock_class):
        with pytest.raises(OSError, match="Network unreachable"):
            await detect_sound_direction()
