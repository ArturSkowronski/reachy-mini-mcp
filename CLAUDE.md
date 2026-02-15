# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server that exposes Reachy Mini robot control as tools via FastMCP. AI assistants connect over stdio transport and control head movement, antennas, emotions, and audio.

Single-module project: all 12 MCP tools live in `reachy.py`. Tests in `tests/test_reachy.py`.

## Workflow

- Always create a feature branch before making changes. Never commit directly to `main`.

## Commands

```bash
# Install (with dev dependencies)
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests verbose
pytest -v

# Run a single test
pytest tests/test_reachy.py::test_express_emotion_happy

# Run tests matching a pattern
pytest -k "move_antennas"

# Pre-commit hooks (runs pytest before each commit)
pre-commit install
pre-commit run --all-files
```

## Architecture

```
MCP Client (stdio) → FastMCP Server (reachy.py) → ReachyMini SDK → Robot/Simulator
```

- **`reachy.py`**: All tool definitions. Each `@mcp.tool()` async function creates its own `ReachyMini()` context manager, performs robot operations, and returns a descriptive string.
- **`reachy_debug.py`**: Standalone script for direct robot interaction without MCP.
- **ReachyMini SDK** (`reachy_mini` package): Provides `goto_target()`, `look_at_world()`, `wake_up()`, `goto_sleep()`, media playback, and audio direction-of-arrival detection.

Key SDK helper: `create_head_pose(x, y, z, roll, pitch, yaw, mm=True, degrees=True)` — always pass `mm=True` and `degrees=True` when calling from this project.

## Tool Patterns

All tools follow the same structure:
1. Open `with ReachyMini() as mini:` context
2. Call SDK methods (`goto_target`, `look_at_world`, `media.play_sound`, etc.)
3. Return a human-readable status string

Antenna values are in radians, clamped to [-3.14, 3.14]. Head position is in mm, rotation in degrees.

`express_emotion()` maps 10 emoji characters to choreographed head/antenna movements + sounds.

## Testing

- pytest with `pytest-asyncio` (asyncio_mode = auto)
- All tests mock `ReachyMini` via `unittest.mock.patch("reachy.ReachyMini", ...)` — no real robot needed
- Mock pattern: create `MagicMock` with `__enter__`/`__exit__` for context manager protocol
- Test naming: `test_<tool_name>_<scenario>()`

## Dependencies

- `mcp[cli]` — FastMCP framework
- `reachy-mini` — Robot SDK
- `httpx` — HTTP client (imported, available for future use)
- Python 3.13+
