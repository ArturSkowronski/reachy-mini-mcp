import os
from typing import Any

import cv2
from mcp.server.fastmcp import FastMCP, Image
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

from reachy_elevenlabs import elevenlabs_tts_to_temp_wav, load_elevenlabs_config

# Initialize FastMCP server
mcp = FastMCP("reachy-mini-mcp")


@mcp.tool()
async def do_barrel_roll() -> str:
    """Do the barrel roll with Reachy."""

    with ReachyMini() as mini:
        print("Connected to simulation!")

        # Look up and tilt head
        print("Moving head...")
        mini.goto_target(
            head=create_head_pose(z=20, roll=10, mm=True, degrees=True), duration=1.0
        )

        # Wiggle antennas
        print("Wiggling antennas...")
        mini.goto_target(antennas=[0.6, -0.6], duration=0.3)
        mini.goto_target(antennas=[-0.6, 0.6], duration=0.3)

        # Reset to rest position
        mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=1.0)
    return "Did the barrel roll!"


@mcp.tool()
async def play_sound(sound_name: str) -> str:
    """Play a built-in sound on Reachy Mini.

    Available sounds: wake_up, go_sleep, confused1, impatient1, dance1, count

    Args:
        sound_name: Name of the sound to play (without .wav extension)
    """
    with ReachyMini() as mini:
        mini.media.play_sound(f"{sound_name}.wav")
    return f"Reachy played: {sound_name}"


@mcp.tool()
async def speak_text(
    text: str,
    voice_id: str | None = None,
    model_id: str | None = None,
    stability: float | None = None,
    similarity_boost: float | None = None,
    style: float | None = None,
    use_speaker_boost: bool = True,
    output_format: str | None = None,
) -> str:
    """Speak the provided text using ElevenLabs TTS and play it on Reachy Mini.

    Configuration via environment variables:
    - ELEVENLABS_API_KEY (required)
    - ELEVENLABS_VOICE_ID (required unless passed as voice_id)
    - ELEVENLABS_MODEL_ID (optional, default: eleven_multilingual_v2)
    - ELEVENLABS_OUTPUT_FORMAT (optional, default: wav_44100)

    Args:
        text: Text to read aloud.
        voice_id: ElevenLabs voice id override (optional).
        model_id: ElevenLabs model id override (optional).
        stability: Voice stability (0..1, optional).
        similarity_boost: Similarity boost (0..1, optional).
        style: Style exaggeration (0..1, optional).
        use_speaker_boost: Whether to enable speaker boost (default: True).
        output_format: ElevenLabs output format override (default: wav_44100).
    """
    config = load_elevenlabs_config(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id=voice_id,
        model_id=model_id,
        output_format=output_format,
    )

    voice_settings: dict[str, Any] = {"use_speaker_boost": use_speaker_boost}
    if stability is not None:
        voice_settings["stability"] = stability
    if similarity_boost is not None:
        voice_settings["similarity_boost"] = similarity_boost
    if style is not None:
        voice_settings["style"] = style

    wav_path = await elevenlabs_tts_to_temp_wav(
        text=text,
        config=config,
        voice_settings=voice_settings,
    )

    try:
        with ReachyMini() as mini:
            mini.media.play_sound(wav_path)
    finally:
        try:
            os.remove(wav_path)
        except FileNotFoundError:
            pass

    return "Reachy spoke the provided text via ElevenLabs."


@mcp.tool()
async def express_emotion(emoji: str) -> str:
    """Make Reachy Mini express an emotion based on an emoji character.

    The robot will move its head and antennas to reflect the emotion,
    and play corresponding sounds. This can be used to make the robot
    react to chat messages in real-time.

    Supported emojis:
    - 😊 happy: antennas up, cheerful pose, dance sound
    - 😕 confused: head tilt, asymmetric antennas, confused sound
    - 😤 impatient: rapid antenna movements, impatient sound
    - 😴 sleepy: sleep pose with sound
    - 👋 wave: greeting animation with wake up sound
    - 🤔 thinking: contemplative head tilt, antennas spread
    - 😮 surprised: antennas high, head back
    - 😢 sad: antennas and head down
    - 🎉 celebrate: energetic wiggle, dance sound
    - 😐 neutral: return to rest position

    Args:
        emoji: The emoji character representing the emotion
    """
    with ReachyMini() as mini:
        # Emotion mappings
        if emoji == "😊":  # Happy
            mini.goto_target(
                head=create_head_pose(z=15, roll=5, pitch=-10, mm=True, degrees=True),
                antennas=[0.8, 0.8],
                duration=0.8,
            )
            mini.media.play_sound("dance1.wav")
            emotion = "happy"

        elif emoji == "😕":  # Confused
            mini.goto_target(
                head=create_head_pose(z=10, roll=15, pitch=5, mm=True, degrees=True),
                antennas=[0.5, -0.3],
                duration=0.6,
            )
            mini.media.play_sound("confused1.wav")
            emotion = "confused"

        elif emoji == "😤":  # Impatient
            # Rapid antenna movements
            mini.goto_target(antennas=[0.7, -0.7], duration=0.2)
            mini.goto_target(antennas=[-0.7, 0.7], duration=0.2)
            mini.goto_target(antennas=[0.7, -0.7], duration=0.2)
            mini.media.play_sound("impatient1.wav")
            emotion = "impatient"

        elif emoji == "😴":  # Sleepy
            mini.goto_sleep()
            emotion = "sleepy"

        elif emoji == "👋":  # Wave/Greeting
            mini.wake_up()
            emotion = "greeting"

        elif emoji == "🤔":  # Thinking
            mini.goto_target(
                head=create_head_pose(z=10, roll=-10, pitch=10, mm=True, degrees=True),
                antennas=[0.6, -0.6],
                duration=1.0,
            )
            emotion = "thinking"

        elif emoji == "😮":  # Surprised
            mini.goto_target(
                head=create_head_pose(z=5, pitch=-15, mm=True, degrees=True),
                antennas=[1.2, 1.2],
                duration=0.4,
            )
            emotion = "surprised"

        elif emoji == "😢":  # Sad
            mini.goto_target(
                head=create_head_pose(z=20, pitch=15, mm=True, degrees=True),
                antennas=[-0.5, -0.5],
                duration=1.2,
            )
            emotion = "sad"

        elif emoji == "🎉":  # Celebrate
            # Wiggle celebration
            mini.goto_target(
                head=create_head_pose(z=10, roll=10, mm=True, degrees=True),
                antennas=[0.8, -0.8],
                duration=0.3,
            )
            mini.goto_target(
                head=create_head_pose(z=10, roll=-10, mm=True, degrees=True),
                antennas=[-0.8, 0.8],
                duration=0.3,
            )
            mini.media.play_sound("dance1.wav")
            emotion = "celebrate"

        elif emoji == "😐":  # Neutral
            mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=0.8)
            emotion = "neutral"

        else:
            return (
                f"Unsupported emoji: {emoji}. Please use one of the supported emojis."
            )

    return f"Reachy expressed: {emotion} ({emoji})"


@mcp.tool()
async def look_at_point(x: float, y: float, z: float, duration: float = 1.0) -> str:
    """Make Reachy Mini look at a specific point in 3D space.

    The robot will orient its head to look at the specified coordinates
    in the world frame (robot's base coordinate system).

    Args:
        x: X coordinate in meters (forward/backward)
        y: Y coordinate in meters (left/right)
        z: Z coordinate in meters (up/down)
        duration: Movement duration in seconds (default: 1.0)
    """
    with ReachyMini() as mini:
        mini.look_at_world(x, y, z, duration=duration)
    return f"Reachy looking at point ({x}, {y}, {z})"


@mcp.tool()
async def move_antennas(right: float, left: float, duration: float = 0.5) -> str:
    """Move Reachy Mini's antennas to specific positions.

    The antennas can be used to express emotions or indicate direction.
    Range: -3.14 to 3.14 radians for each antenna.

    Args:
        right: Right antenna position in radians
        left: Left antenna position in radians
        duration: Movement duration in seconds (default: 0.5)
    """
    # Clamp values to valid range
    right = max(-3.14, min(3.14, right))
    left = max(-3.14, min(3.14, left))

    with ReachyMini() as mini:
        mini.goto_target(antennas=[right, left], duration=duration)
    return f"Moved antennas to right={right:.2f}, left={left:.2f}"


@mcp.tool()
async def reset_position(duration: float = 1.5) -> str:
    """Reset Reachy Mini to neutral rest position.

    Returns the robot's head and antennas to the default resting pose.

    Args:
        duration: Movement duration in seconds (default: 1.5)
    """
    with ReachyMini() as mini:
        mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=duration)
    return "Reachy reset to neutral position"


@mcp.tool()
async def wake_up() -> str:
    """Wake up Reachy Mini with the built-in wake up animation and sound.

    This is a greeting behavior that can be used when starting interaction.
    """
    with ReachyMini() as mini:
        mini.wake_up()
    return "Reachy woke up!"


@mcp.tool()
async def go_to_sleep() -> str:
    """Put Reachy Mini to sleep with the built-in sleep animation and sound.

    This is a farewell behavior that can be used when ending interaction.
    """
    with ReachyMini() as mini:
        mini.goto_sleep()
    return "Reachy went to sleep"


@mcp.tool()
async def detect_sound_direction() -> str:
    """Detect the direction of a sound source using Reachy's microphone array.

    Returns the angle in radians where sound is coming from and whether
    speech was detected.
    - Angle: 0 = left, π/2 = front/back, π = right
    """
    with ReachyMini() as mini:
        angle, speech_detected = mini.media.audio.get_DoA()

    # Convert to degrees for easier understanding
    angle_degrees = angle * 180 / 3.14159

    speech_status = "speech detected" if speech_detected else "no speech detected"
    return f"Sound from {angle:.2f} radians ({angle_degrees:.1f}°), {speech_status}"


@mcp.tool()
async def move_head(
    x: float = 0,
    y: float = 0,
    z: float = 0,
    roll: float = 0,
    pitch: float = 0,
    yaw: float = 0,
    duration: float = 1.0,
) -> str:
    """Move Reachy Mini's head to a specific pose.

    Control the head position and orientation with 6 degrees of freedom.

    Args:
        x: Forward/backward offset in millimeters (default: 0)
        y: Left/right offset in millimeters (default: 0)
        z: Up/down offset in millimeters (default: 0)
        roll: Roll rotation in degrees (default: 0)
        pitch: Pitch rotation in degrees (default: 0)
        yaw: Yaw rotation in degrees (default: 0)
        duration: Movement duration in seconds (default: 1.0)
    """
    with ReachyMini() as mini:
        pose = create_head_pose(
            x=x, y=y, z=z, roll=roll, pitch=pitch, yaw=yaw, mm=True, degrees=True
        )
        mini.goto_target(head=pose, duration=duration)

    return f"Moved head to pos({x}, {y}, {z})mm, rot({roll}, {pitch}, {yaw})°"


@mcp.tool()
async def capture_image(quality: int = 90) -> Image:
    """Capture an image from Reachy Mini's built-in camera.

    Returns the current camera frame as a JPEG image. Use this to see what
    the robot sees, identify objects, read text, or observe the environment.

    Args:
        quality: JPEG compression quality 1-100 (default: 90)
    """
    quality = max(1, min(100, quality))
    with ReachyMini() as mini:
        frame = mini.media.get_frame()
    if frame is None:
        raise RuntimeError("Camera not available or failed to capture frame")
    success, jpeg_bytes = cv2.imencode(
        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality]
    )
    if not success:
        raise RuntimeError("Failed to encode frame to JPEG")
    return Image(data=jpeg_bytes.tobytes(), format="jpeg")


@mcp.tool()
async def scan_surroundings(
    steps: int = 5,
    yaw_range: float = 120.0,
    quality: int = 80,
) -> list[str | Image]:
    """Scan the robot's surroundings by panning the camera across multiple angles.

    Captures images at evenly spaced yaw positions across the specified range,
    then returns to center. The AI receives all frames in a single response
    for a panoramic understanding of the environment.

    Args:
        steps: Number of positions to capture (default: 5, range: 2-9)
        yaw_range: Total horizontal sweep in degrees (default: 120, range: 30-180)
        quality: JPEG compression quality 1-100 (default: 80)
    """
    steps = max(2, min(9, steps))
    yaw_range = max(30.0, min(180.0, yaw_range))
    quality = max(1, min(100, quality))

    half = yaw_range / 2
    yaw_positions = [-half + i * yaw_range / (steps - 1) for i in range(steps)]

    result: list = []
    with ReachyMini() as mini:
        for i, yaw in enumerate(yaw_positions, 1):
            mini.goto_target(
                head=create_head_pose(yaw=yaw, mm=True, degrees=True),
                duration=0.6,
            )
            frame = mini.media.get_frame()
            if frame is None:
                result.append(
                    f"Position {i}/{steps} (yaw {yaw:+.0f}°): frame capture failed"
                )
                continue
            success, jpeg_bytes = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality]
            )
            if not success:
                result.append(
                    f"Position {i}/{steps} (yaw {yaw:+.0f}°): JPEG encoding failed"
                )
                continue
            result.append(f"Position {i}/{steps} (yaw {yaw:+.0f}°):")
            result.append(Image(data=jpeg_bytes.tobytes(), format="jpeg"))

        # Return to center
        mini.goto_target(
            head=create_head_pose(mm=True, degrees=True),
            duration=0.6,
        )

    result.append(
        f"Scan complete: {steps} positions across {yaw_range:.0f}° "
        f"(from {yaw_positions[0]:+.0f}° to {yaw_positions[-1]:+.0f}°)"
    )
    return result


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
