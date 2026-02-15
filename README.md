# Reachy Mini MCP

Control the [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot (or simulator) from Claude, ChatGPT, or any MCP-compatible client.

[![CI](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Reachy Mini](https://img.shields.io/badge/robot-Reachy%20Mini-orange.svg)](https://www.pollen-robotics.com/reachy-mini/)

<table style="border: none;">
<tr style="border: none;">
<td style="width: 42%; vertical-align: middle; border: none;">
  <img src="media/cover.png" alt="Reachy Mini MCP" />
</td>
<td style="vertical-align: middle; border: none;">
<b>Quickstart</b>
<pre><code>uv sync --extra reachy
uv run reachy.py</code></pre>
<b>Simulator demo</b>
<pre><code>uv sync --extra reachy-sim
uv run python reachy_debug.py</code></pre>
</td>
</tr>
</table>

## Dry run (video)

A short "dry run" of the `reachy_debug.py` sequential demo runner (simulator): step announcements, movements, vision, and artifacts.

<video src="media/dry-run.mp4" controls muted playsinline style="max-width: 100%;"></video>

[Watch the dry run video](media/dry-run.mp4)

## How it works

```
AI Assistant  --stdio-->  MCP Server (reachy.py)  -->  ReachyMini SDK  -->  Robot / Simulator
```

The server exposes 16 tools, 4 prompts, and 4 resources via the [Model Context Protocol](https://modelcontextprotocol.io). An AI assistant calls these tools to see through the robot's camera, move the robot, express emotions, play sounds, or detect audio direction -- no robotics knowledge needed on the AI side.

## Installation

### Prerequisites

- Python 3.13+
- [Reachy Mini robot](https://www.pollen-robotics.com/reachy-mini/) or the Reachy Mini simulator
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install the server

```bash
git clone https://github.com/ArturSkowronski/reachy-mini-mcp.git
cd reachy-mini-mcp
uv sync
```

Or with pip:

```bash
pip install -e .
```

### Configure your MCP client

Add the server to your MCP client configuration. The exact location depends on the client:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "reachy-mini": {
      "command": "uv",
      "args": ["--directory", "/path/to/reachy-mini-mcp", "run", "reachy.py"]
    }
  }
}
```

**Claude Code** (`.mcp.json` in your project root):

```json
{
  "mcpServers": {
    "reachy-mini": {
      "command": "uv",
      "args": ["--directory", "/path/to/reachy-mini-mcp", "run", "reachy.py"]
    }
  }
}
```

**Generic stdio transport:**

```bash
uv run reachy.py
```

### ElevenLabs TTS (optional)

To enable the `speak_text` tool, set these environment variables:

```bash
export ELEVENLABS_API_KEY="your-api-key"
export ELEVENLABS_VOICE_ID="your-voice-id"
#
# Optional override prefix (takes precedence):
# export REACHY_ELEVENLABS_API_KEY="your-api-key"
# export REACHY_ELEVENLABS_VOICE_ID="your-voice-id"
```

Default voice (premade/free-tier friendly): `George` with Voice ID `JBFqnCBsd6RMkjVDRZzb`.

Favorite voice (author preference): `Horatius` with Voice ID `qXpMhyvQqiRxWQs4qSSB`.

Optional overrides: `ELEVENLABS_MODEL_ID` (default: `eleven_multilingual_v2`), `ELEVENLABS_OUTPUT_FORMAT` (default: `mp3_44100_128`).

WAV support: if your ElevenLabs plan allows it, you can set `ELEVENLABS_OUTPUT_FORMAT=wav_44100` to get WAV output instead of MP3.

#### MP3 vs WAV playback note

- Default TTS output is MP3 (`mp3_44100_128`) because it works on lower ElevenLabs tiers.
- Some Reachy audio backends/environments may not have MP3 decoding available. In that case, MP3 playback can fail even though WAV works.
- If you need ElevenLabs to return WAV directly (`wav_44100`), ElevenLabs requires a higher tier (minimum **Pro**).
- To force WAV output (when available), override the output format via environment variables:
  - `REACHY_ELEVENLABS_OUTPUT_FORMAT=wav_44100` (preferred, takes precedence)
  - or `ELEVENLABS_OUTPUT_FORMAT=wav_44100`

## Environment variables

General:
- `NO_COLOR`: disable ANSI colors in `reachy_debug.py` output.

Debug runner (`reachy_debug.py`):
- `REACHY_DEBUG_ANNOUNCE_PAUSE_S` (default: `0.6`): pause after each announcement before running the step.
- `REACHY_DEBUG_TTS_SPEED` (default: `0.8`): ElevenLabs speech speed.

ElevenLabs (used by `speak_text` and `reachy_debug.py` announcements):
- `REACHY_ELEVENLABS_API_KEY` or `ELEVENLABS_API_KEY` (required for TTS): API key. `REACHY_` prefixed value takes precedence.
- `REACHY_ELEVENLABS_VOICE_ID` or `ELEVENLABS_VOICE_ID` (optional): voice id. Defaults to `JBFqnCBsd6RMkjVDRZzb` (George) if not set.
- `REACHY_ELEVENLABS_MODEL_ID` or `ELEVENLABS_MODEL_ID` (optional): model id (default: `eleven_multilingual_v2`).
- `REACHY_ELEVENLABS_OUTPUT_FORMAT` or `ELEVENLABS_OUTPUT_FORMAT` (optional): output format (default: `mp3_44100_128`, optionally `wav_44100` if your plan allows it).

## Available tools

| Tool | Description |
|------|-------------|
| `capture_image` | Capture a JPEG frame from the robot's HD camera |
| `scan_surroundings` | Pan camera across multiple angles and return a panoramic set of images |
| `track_face` | Detect a face via OpenCV and turn head to face it |
| `move_head` | 6-DOF head positioning (x/y/z in mm, roll/pitch/yaw in degrees) |
| `move_antennas` | Independent antenna control (-3.14 to 3.14 radians) |
| `look_at_point` | Orient head toward a 3D point in world coordinates |
| `express_emotion` | Emoji-driven emotion system with synchronized movements and sounds |
| `play_sound` | Play built-in sounds (wake_up, go_sleep, confused1, impatient1, dance1, count) |
| `speak_text` | Text-to-speech via ElevenLabs API, played through robot speaker |
| `detect_sound_direction` | Microphone array direction-of-arrival + speech detection |
| `wake_up` | Built-in greeting animation with sound |
| `go_to_sleep` | Built-in farewell animation with sound |
| `nod` | Nod head up and down to indicate "yes" or agreement |
| `shake_head` | Shake head left and right to indicate "no" or disagreement |
| `reset_position` | Return head and antennas to neutral rest pose |
| `do_barrel_roll` | Choreographed head tilt + antenna wiggle sequence |

### Resources

The server also exposes MCP resources that let AI assistants discover robot capabilities dynamically:

| Resource URI | Description |
|-------------|-------------|
| `reachy://emotions` | Supported emoji-to-emotion mappings |
| `reachy://sounds` | Available built-in sound names |
| `reachy://limits` | Physical limits (antenna range, head DOF, camera specs) |
| `reachy://capabilities` | All tools grouped by category (vision, movement, expression, audio, lifecycle) |

### Vision

`capture_image` grabs a frame from Reachy Mini's wide-angle HD camera and returns it as inline JPEG content through the MCP protocol. The AI assistant receives the image directly in the conversation -- no file paths, no URLs, no extra setup.

`scan_surroundings` takes this further by panning the camera across multiple angles and returning all frames in a single response:

```
User:  "Look around and describe the room"

       Claude calls scan_surroundings(steps=5, yaw_range=120)
       <- Robot pans from -60deg to +60deg in 5 steps
       <- MCP returns 5 labeled JPEG frames + summary text

Claude: "Starting from the left I can see a window with blinds,
         then a whiteboard, your desk with two monitors in the
         center, a bookshelf to the right, and a door at the
         far right."
```

The camera returns a standard BGR numpy frame from OpenCV, which gets JPEG-compressed and delivered as MCP `ImageContent`. Any multimodal AI model that supports image inputs can process it -- Claude, GPT-4o, Gemini, etc.

### Tool annotations

Every tool carries semantic annotations that tell AI clients how to use it safely:

| Annotation | Meaning | Tools |
|-----------|---------|-------|
| `readOnlyHint` | Doesn't change robot state | `capture_image`, `detect_sound_direction` |
| `idempotentHint=true` | Safe to call repeatedly | `capture_image`, `detect_sound_direction` |
| `idempotentHint=false` | Repeated calls repeat actions/costs | All movement/gesture/audio tools, including `speak_text` |
| `destructiveHint=false` | No irreversible actions | All tools |
| `openWorldHint` | Calls external services | `speak_text` (ElevenLabs API) |

### Prompts

Pre-built prompt templates that guide AI assistants through common robot interaction scenarios:

| Prompt | Description |
|--------|-------------|
| `greet_user` | Wake up the robot, express happiness, and greet by name |
| `explore_room` | Scan surroundings with the camera and describe the environment |
| `react_to_conversation` | Use gestures and emotions to physically react during chat |
| `find_person` | Use camera and face tracking to locate and follow a person |

### Emotion system

`express_emotion` maps emoji characters to choreographed movements:

| Emoji | Emotion | Behavior |
|-------|---------|----------|
| `😊` | happy | antennas up, cheerful pose, dance sound |
| `😕` | confused | head tilt, asymmetric antennas, confused sound |
| `😤` | impatient | rapid antenna movements, impatient sound |
| `😴` | sleepy | sleep pose with sound |
| `👋` | greeting | wake up animation |
| `🤔` | thinking | contemplative head tilt, antennas spread |
| `😮` | surprised | antennas high, head back |
| `😢` | sad | antennas and head down |
| `🎉` | celebrate | energetic wiggle, dance sound |
| `😐` | neutral | return to rest position |

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest -v

# Unit tests only
uv run pytest -v -m "not integration"

# Integration tests only (MCP protocol layer)
uv run pytest -v -m integration

# Lint
uv run ruff check . && uv run ruff format --check .

# Set up pre-commit hooks
pre-commit install
```

### Direct robot testing

For a one-click, full sequential debug demo (movement, gestures, audio, vision, tracking) with per-step status checks:

```bash
uv sync --extra reachy
# If you want to auto-spawn the simulator daemon, also install:
uv sync --extra reachy-sim
uv run python reachy_debug.py
```

`reachy_debug.py` now:
- Announces each upcoming test step (voice via ElevenLabs if configured, otherwise console fallback).
- Executes a full demo suite in sequence.
- Saves all captured images and a markdown run summary to `results/run-YYYYMMDD-HHMMSS/`.
- Generates a single report file for the run: `run_report.md`.
