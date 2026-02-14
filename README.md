# reachy-mini-mcp

[![CI](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Reachy Mini](https://img.shields.io/badge/robot-Reachy%20Mini-orange.svg)](https://www.pollen-robotics.com/reachy-mini/)

MCP server that lets AI assistants control the [Reachy Mini](https://www.pollen-robotics.com/reachy-mini/) robot. Connect Claude, ChatGPT, or any MCP-compatible client and control head movement, antennas, emotions, and audio through natural language.

## How it works

```
AI Assistant  --stdio-->  MCP Server (reachy.py)  -->  ReachyMini SDK  -->  Robot / Simulator
```

The server exposes 11 tools via the [Model Context Protocol](https://modelcontextprotocol.io). An AI assistant calls these tools to move the robot, express emotions, play sounds, or detect audio direction -- no robotics knowledge needed on the AI side.

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
```

Optional overrides: `ELEVENLABS_MODEL_ID` (default: `eleven_multilingual_v2`), `ELEVENLABS_OUTPUT_FORMAT` (default: `wav_44100`).

## Available tools

| Tool | Description |
|------|-------------|
| `move_head` | 6-DOF head positioning (x/y/z in mm, roll/pitch/yaw in degrees) |
| `move_antennas` | Independent antenna control (-3.14 to 3.14 radians) |
| `look_at_point` | Orient head toward a 3D point in world coordinates |
| `express_emotion` | Emoji-driven emotion system with synchronized movements and sounds |
| `play_sound` | Play built-in sounds (wake_up, go_sleep, confused1, impatient1, dance1, count) |
| `speak_text` | Text-to-speech via ElevenLabs API, played through robot speaker |
| `detect_sound_direction` | Microphone array direction-of-arrival + speech detection |
| `wake_up` | Built-in greeting animation with sound |
| `go_to_sleep` | Built-in farewell animation with sound |
| `reset_position` | Return head and antennas to neutral rest pose |
| `do_barrel_roll` | Choreographed head tilt + antenna wiggle sequence |

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

## Use cases

**Interactive AI companion** -- Connect to Claude or another LLM and have natural conversations where the robot physically reacts to what's being said. The AI can express emotions, nod, look around, and respond with body language.

**Accessible robotics education** -- Students interact with the robot through natural language instead of writing low-level control code. Ask the AI to "make the robot look surprised" or "tilt the head 15 degrees to the right" and it translates to SDK calls.

**Trade show / exhibit demos** -- Set up the robot at a booth with a microphone. It detects sound direction, turns toward speakers, reacts with emotions, and responds with TTS -- all orchestrated by an AI assistant.

**Telepresence and remote interaction** -- Control the robot remotely through an AI-powered chat interface. The emotion system gives remote participants a physical presence that goes beyond a video call.

**Rapid prototyping for HRI research** -- Test human-robot interaction scenarios without writing robot code. Describe behaviors in natural language, iterate quickly on emotion mappings and movement sequences.

**Multimodal AI agent** -- Combine with vision MCP servers to create an agent that sees, hears, speaks, and moves. The robot becomes the physical embodiment of an AI system.

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

For debugging robot movements without the MCP layer:

```bash
uv run python reachy_debug.py
```

## Author

Artur Skowronski (me@arturskowronski.com)
