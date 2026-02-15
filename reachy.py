import json
import os
import re
from typing import Any

import cv2
from mcp.server.fastmcp import Context, FastMCP, Image
from mcp.server.fastmcp.prompts.base import AssistantMessage, UserMessage
from mcp.types import ToolAnnotations

try:
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose
except Exception as exc:  # pragma: no cover
    _reachy_mini_import_error = exc

    class ReachyMini:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "reachy-mini is not installed. Install with `uv sync --extra reachy` "
                "(or `pip install 'reachy-mini-mcp[reachy]'`)."
            ) from _reachy_mini_import_error

    def create_head_pose(*args, **kwargs):  # type: ignore[no-redef]
        raise RuntimeError(
            "reachy-mini is not installed. Install with `uv sync --extra reachy` "
            "(or `pip install 'reachy-mini-mcp[reachy]'`)."
        ) from _reachy_mini_import_error


from reachy_elevenlabs import elevenlabs_tts_to_temp_audio_file, load_elevenlabs_config

# Initialize FastMCP server
mcp = FastMCP("reachy-mini-mcp")

# ---------------------------------------------------------------------------
# Tool annotation presets
# ---------------------------------------------------------------------------
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
MOVEMENT = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)
EXTERNAL = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMOTIONS = {
    "😊": "happy",
    "😕": "confused",
    "😤": "impatient",
    "😴": "sleepy",
    "👋": "greeting",
    "🤔": "thinking",
    "😮": "surprised",
    "😢": "sad",
    "🎉": "celebrate",
    "😐": "neutral",
}

SOUNDS = ["wake_up", "go_sleep", "confused1", "impatient1", "dance1", "count"]

# ---------------------------------------------------------------------------
# MCP Resources — discoverable robot metadata
# ---------------------------------------------------------------------------


@mcp.resource("reachy://emotions")
def get_emotions() -> str:
    """Supported emoji-to-emotion mappings for express_emotion tool."""
    return json.dumps(EMOTIONS, ensure_ascii=False)


@mcp.resource("reachy://sounds")
def get_sounds() -> str:
    """Available built-in sounds for play_sound tool."""
    return json.dumps(SOUNDS)


@mcp.resource("reachy://limits")
def get_limits() -> str:
    """Physical limits and ranges for the robot's actuators."""
    return json.dumps(
        {
            "antennas": {"min_radians": -3.14, "max_radians": 3.14},
            "head_position": {"unit": "mm", "axes": ["x", "y", "z"]},
            "head_rotation": {"unit": "degrees", "axes": ["roll", "pitch", "yaw"]},
            "camera": {"resolution": "1280x720", "format": "BGR"},
        }
    )


@mcp.resource("reachy://capabilities")
def get_capabilities() -> str:
    """Summary of robot capabilities grouped by category."""
    return json.dumps(
        {
            "vision": ["capture_image", "scan_surroundings", "track_face"],
            "movement": [
                "move_head",
                "move_antennas",
                "look_at_point",
                "nod",
                "shake_head",
            ],
            "expression": ["express_emotion", "do_barrel_roll"],
            "audio": ["play_sound", "speak_text", "detect_sound_direction"],
            "lifecycle": ["wake_up", "go_to_sleep", "reset_position"],
        }
    )


# ---------------------------------------------------------------------------
# MCP Prompts — reusable interaction templates
# ---------------------------------------------------------------------------


@mcp.prompt()
def greet_user(user_name: str = "friend") -> list:
    """Greet a user with Reachy Mini — wake up, look around, and say hello."""
    safe_name = re.sub(r"[^a-zA-Z0-9 ]", "", user_name)
    safe_name = " ".join(safe_name.split())[:50]
    if not safe_name:
        safe_name = "friend"

    return [
        UserMessage(f"Please greet {safe_name} using the robot."),
        AssistantMessage(
            "I'll wake up Reachy, express happiness, and nod to greet "
            f"{safe_name}. Let me use wake_up, then express_emotion with 😊, "
            "and finally nod."
        ),
    ]


@mcp.prompt()
def explore_room() -> list:
    """Scan the surroundings and describe what Reachy Mini sees."""
    return [
        UserMessage(
            "Use the robot's camera to look around the room and describe "
            "what you see in detail."
        ),
        AssistantMessage(
            "I'll scan the surroundings by panning the camera across multiple "
            "angles, then describe each view. Let me call scan_surroundings."
        ),
    ]


@mcp.prompt()
def react_to_conversation() -> list:
    """Guide Reachy to physically react during conversation with gestures."""
    return [
        UserMessage(
            "As we chat, use the robot to physically react to what I say. "
            "Nod when you agree, shake your head when you disagree, and use "
            "emoji emotions to express how you feel about the topic."
        ),
        AssistantMessage(
            "I'll use Reachy's gestures throughout our conversation: nod for "
            "agreement, shake_head for disagreement, and express_emotion with "
            "appropriate emojis. I'm ready — what would you like to talk about?"
        ),
    ]


@mcp.prompt()
def find_person() -> list:
    """Use camera and face tracking to find and follow a person."""
    return [
        UserMessage(
            "Find a person in the room using the camera and turn to face them."
        ),
        AssistantMessage(
            "I'll use capture_image to look for a person, then track_face to "
            "orient the robot toward them. If no one is visible, I'll use "
            "scan_surroundings to search the room. Let me start."
        ),
    ]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool(annotations=MOVEMENT)
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


@mcp.tool(annotations=MOVEMENT)
async def play_sound(sound_name: str) -> str:
    """Play a built-in sound on Reachy Mini.

    Available sounds: wake_up, go_sleep, confused1, impatient1, dance1, count

    Args:
        sound_name: Name of the sound to play (without .wav extension)
    """
    with ReachyMini() as mini:
        mini.media.play_sound(f"{sound_name}.wav")
    return f"Reachy played: {sound_name}"


@mcp.tool(annotations=EXTERNAL)
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
    - ELEVENLABS_VOICE_ID (optional; defaults to a premade voice)
    - ELEVENLABS_MODEL_ID (optional, default: eleven_multilingual_v2)
    - ELEVENLABS_OUTPUT_FORMAT (optional, default: mp3_44100_128; you can use wav_44100 if your plan allows it)

    Args:
        text: Text to read aloud.
        voice_id: ElevenLabs voice id override (optional).
        model_id: ElevenLabs model id override (optional).
        stability: Voice stability (0..1, optional).
        similarity_boost: Similarity boost (0..1, optional).
        style: Style exaggeration (0..1, optional).
        use_speaker_boost: Whether to enable speaker boost (default: True).
        output_format: ElevenLabs output format override (default: mp3_44100_128).
    """
    # Note: load_elevenlabs_config supports both ELEVENLABS_* and REACHY_ELEVENLABS_* env vars.
    config = load_elevenlabs_config(
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

    audio_path = await elevenlabs_tts_to_temp_audio_file(
        text=text,
        config=config,
        voice_settings=voice_settings,
    )

    try:
        with ReachyMini() as mini:
            mini.media.play_sound(audio_path)
    finally:
        try:
            os.remove(audio_path)
        except FileNotFoundError:
            pass

    return "Reachy spoke the provided text via ElevenLabs."


@mcp.tool(annotations=MOVEMENT)
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


@mcp.tool(annotations=MOVEMENT)
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


@mcp.tool(annotations=MOVEMENT)
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


@mcp.tool(annotations=MOVEMENT)
async def reset_position(duration: float = 1.5) -> str:
    """Reset Reachy Mini to neutral rest position.

    Returns the robot's head and antennas to the default resting pose.

    Args:
        duration: Movement duration in seconds (default: 1.5)
    """
    with ReachyMini() as mini:
        mini.goto_target(head=create_head_pose(), antennas=[0, 0], duration=duration)
    return "Reachy reset to neutral position"


@mcp.tool(annotations=MOVEMENT)
async def wake_up() -> str:
    """Wake up Reachy Mini with the built-in wake up animation and sound.

    This is a greeting behavior that can be used when starting interaction.
    """
    with ReachyMini() as mini:
        mini.wake_up()
    return "Reachy woke up!"


@mcp.tool(annotations=MOVEMENT)
async def go_to_sleep() -> str:
    """Put Reachy Mini to sleep with the built-in sleep animation and sound.

    This is a farewell behavior that can be used when ending interaction.
    """
    with ReachyMini() as mini:
        mini.goto_sleep()
    return "Reachy went to sleep"


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=MOVEMENT)
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


@mcp.tool(annotations=READ_ONLY)
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


@mcp.tool(annotations=MOVEMENT)
async def scan_surroundings(
    steps: int = 5,
    yaw_range: float = 120.0,
    quality: int = 80,
    ctx: Context | None = None,
) -> list:
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

    if ctx:
        await ctx.info(f"Starting scan: {steps} positions across {yaw_range:.0f}°")

    result: list = []
    with ReachyMini() as mini:
        for i, yaw in enumerate(yaw_positions, 1):
            if ctx:
                await ctx.report_progress(progress=i, total=steps + 1)

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

        if ctx:
            await ctx.report_progress(progress=steps + 1, total=steps + 1)

    result.append(
        f"Scan complete: {steps} positions across {yaw_range:.0f}° "
        f"(from {yaw_positions[0]:+.0f}° to {yaw_positions[-1]:+.0f}°)"
    )
    return result


@mcp.tool(annotations=MOVEMENT)
async def nod(cycles: int = 2, speed: float = 0.3) -> str:
    """Nod Reachy Mini's head up and down to indicate "yes" or agreement.

    Use this when the AI wants to physically agree, confirm, or acknowledge
    something the user said.

    Args:
        cycles: Number of nod repetitions (default: 2, range: 1-5)
        speed: Duration of each half-nod in seconds (default: 0.3, range: 0.1-1.0)
    """
    cycles = max(1, min(5, cycles))
    speed = max(0.1, min(1.0, speed))

    with ReachyMini() as mini:
        for _ in range(cycles):
            mini.goto_target(
                head=create_head_pose(pitch=15, mm=True, degrees=True),
                duration=speed,
            )
            mini.goto_target(
                head=create_head_pose(pitch=-10, mm=True, degrees=True),
                duration=speed,
            )
        # Return to neutral
        mini.goto_target(
            head=create_head_pose(mm=True, degrees=True),
            duration=speed,
        )
    return f"Reachy nodded ({cycles}x)"


@mcp.tool(annotations=MOVEMENT)
async def shake_head(cycles: int = 2, speed: float = 0.3) -> str:
    """Shake Reachy Mini's head left and right to indicate "no" or disagreement.

    Use this when the AI wants to physically disagree, deny, or express
    disapproval.

    Args:
        cycles: Number of shake repetitions (default: 2, range: 1-5)
        speed: Duration of each half-shake in seconds (default: 0.3, range: 0.1-1.0)
    """
    cycles = max(1, min(5, cycles))
    speed = max(0.1, min(1.0, speed))

    with ReachyMini() as mini:
        for _ in range(cycles):
            mini.goto_target(
                head=create_head_pose(yaw=-20, mm=True, degrees=True),
                duration=speed,
            )
            mini.goto_target(
                head=create_head_pose(yaw=20, mm=True, degrees=True),
                duration=speed,
            )
        # Return to neutral
        mini.goto_target(
            head=create_head_pose(mm=True, degrees=True),
            duration=speed,
        )
    return f"Reachy shook head ({cycles}x)"


_face_cascade = None


def _get_face_cascade():
    """Lazily load the Haar cascade classifier for face detection."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        if _face_cascade.empty():
            raise RuntimeError(f"Failed to load face cascade from {cascade_path}")
    return _face_cascade


# Camera field-of-view estimates for Reachy Mini's wide-angle HD camera
_HORIZONTAL_FOV = 65.0  # degrees
_VERTICAL_FOV = 40.0  # degrees


@mcp.tool(annotations=MOVEMENT)
async def track_face(duration: float = 0.4, ctx: Context | None = None) -> str:
    """Detect a face using the camera and turn the robot's head toward it.

    Captures a frame, runs face detection, and moves the head so the
    detected face is centered in the camera view. If multiple faces are
    found, tracks the largest one.

    Note: computes an absolute head pose from neutral. For best results,
    call reset_position first or use from a near-neutral head position.

    Args:
        duration: Head movement duration in seconds (default: 0.4)
    """
    face_cascade = _get_face_cascade()

    with ReachyMini() as mini:
        frame = mini.media.get_frame()
        if frame is None:
            return "Camera not available"

        img_h, img_w = frame.shape[:2]

        # Downscale for faster detection
        scale = 0.25
        small = cv2.resize(frame, None, fx=scale, fy=scale)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(15, 15)
        )

        if len(faces) == 0:
            if ctx:
                await ctx.info("No face detected in frame")
            return "No face detected"

        # Pick the largest face by area and scale coords back
        largest = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = [v / scale for v in largest]

        face_center_x = x + w / 2
        face_center_y = y + h / 2

        # Pixel offset from image center
        offset_x = face_center_x - img_w / 2
        offset_y = face_center_y - img_h / 2

        # Convert to degrees
        yaw = -(offset_x / img_w) * _HORIZONTAL_FOV
        pitch = (offset_y / img_h) * _VERTICAL_FOV

        if ctx:
            await ctx.info(
                f"Face found at ({face_center_x:.0f}, {face_center_y:.0f})px, "
                f"moving yaw={yaw:+.1f}° pitch={pitch:+.1f}°"
            )

        mini.goto_target(
            head=create_head_pose(yaw=yaw, pitch=pitch, mm=True, degrees=True),
            duration=duration,
        )

    return (
        f"Face detected at ({face_center_x:.0f}, {face_center_y:.0f})px, "
        f"moved head yaw={yaw:+.1f}° pitch={pitch:+.1f}°"
    )


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
