# reachy-mini-mcp

A Model Context Protocol (MCP) server for controlling the Reachy Mini robot. This MCP server provides tools to interact with and control Reachy Mini through the MCP interface.

## Description

This project enables AI assistants and other MCP-compatible clients to control a Reachy Mini robot. It uses FastMCP to expose robot control capabilities as MCP tools.

## Available Tools

### `do_barrel_roll`
Performs a barrel roll movement with the Reachy Mini robot by tilting and moving the head.

### `say`
Makes Reachy Mini speak the given text using the robot's speaker.

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

## Author

Artur Skowronski (me@arturskowronski.com)
