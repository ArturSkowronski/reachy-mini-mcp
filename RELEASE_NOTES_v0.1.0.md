## Reachy Mini MCP v0.1.0

First public release.

### Highlights
- MCP server with tools for Reachy Mini: movement, expressions, audio, and vision.
- ElevenLabs TTS integration (`speak_text`) with `REACHY_ELEVENLABS_*` env var overrides.
- `reachy_debug.py` sequential "Debug Run" demo runner with preflight checks, colored output, step announcements, and run artifacts.
- Test suite (unit, smoke, integration) + CI via GitHub Actions.

### Notable tools
- Vision: `capture_image`, `scan_surroundings`, `track_face`
- Movement: `move_head`, `move_antennas`, `look_at_point`, `nod`, `shake_head`, `do_barrel_roll`
- Audio: `play_sound`, `speak_text`, `detect_sound_direction`
- Lifecycle: `wake_up`, `go_to_sleep`, `reset_position`

### Installation
- Dev: `uv sync --extra dev`
- With robot SDK: `uv sync --extra reachy`

### Configuration
See README for the full list of environment variables.
