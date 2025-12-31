# reachy-mini-mcp

![CI](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml/badge.svg)

A Model Context Protocol (MCP) server for controlling the Reachy Mini robot. This MCP server provides tools to interact with and control Reachy Mini through the MCP interface.

## Description

This project enables AI assistants and other MCP-compatible clients to control a Reachy Mini robot. It uses FastMCP to expose robot control capabilities as MCP tools.

The server provides comprehensive control over the robot's movements, including:
- **Head control**: Precise 6-DOF head positioning and orientation
- **Antenna control**: Independent control of both antennas for expressive gestures
- **Emotion expression**: Emoji-based emotion system with synchronized movements and sounds
- **Audio capabilities**: Sound playback and sound direction detection
- **Predefined behaviors**: Wake up, sleep, and barrel roll animations

## Available Tools

### `do_barrel_roll`
Performs a barrel roll movement with the Reachy Mini robot by tilting and moving the head.

### `play_sound`
Play a built-in sound on Reachy Mini. Available sounds: `wake_up`, `go_sleep`, `confused1`, `impatient1`, `dance1`, `count`.

### `express_emotion`
Make Reachy Mini express an emotion based on an emoji character. The robot will move its head and antennas to reflect the emotion, and play corresponding sounds.

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

### `look_at_point`
Make Reachy Mini look at a specific point in 3D space. The robot will orient its head to look at the specified coordinates in the world frame.

Parameters:
- `x`, `y`, `z`: Coordinates in meters (forward/backward, left/right, up/down)
- `duration`: Movement duration in seconds (default: 1.0)

### `move_antennas`
Move Reachy Mini's antennas to specific positions. The antennas can be used to express emotions or indicate direction.

Parameters:
- `right`: Right antenna position in radians (range: -3.14 to 3.14)
- `left`: Left antenna position in radians (range: -3.14 to 3.14)
- `duration`: Movement duration in seconds (default: 0.5)

### `move_head`
Move Reachy Mini's head to a specific pose with 6 degrees of freedom.

Parameters:
- `x`, `y`, `z`: Position offset in millimeters (forward/backward, left/right, up/down)
- `roll`, `pitch`, `yaw`: Rotation in degrees
- `duration`: Movement duration in seconds (default: 1.0)

### `reset_position`
Reset Reachy Mini to neutral rest position. Returns the robot's head and antennas to the default resting pose.

Parameters:
- `duration`: Movement duration in seconds (default: 1.5)

### `wake_up`
Wake up Reachy Mini with the built-in wake up animation and sound. This is a greeting behavior that can be used when starting interaction.

### `go_to_sleep`
Put Reachy Mini to sleep with the built-in sleep animation and sound. This is a farewell behavior that can be used when ending interaction.

### `detect_sound_direction`
Detect the direction of a sound source using Reachy's microphone array. Returns the angle in radians where sound is coming from and whether speech was detected.

## Development

For debugging and testing robot movements directly, use the `reachy_debug.py` script:
```bash
python reachy_debug.py
```

## Testing

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

## Pre-commit Hooks

This project uses pre-commit hooks to run tests automatically on commit. To set up:

1. Install pre-commit (included in dev dependencies):
```bash
pip install -e ".[dev]"
```

2. Install the git hooks:
```bash
pre-commit install
```

Now tests will run automatically before each commit. If tests fail, the commit will be blocked.

To run hooks manually:
```bash
pre-commit run --all-files
```

## Author

Artur Skowronski (me@arturskowronski.com)
