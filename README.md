# reachy-mini-mcp

![CI](https://github.com/ArturSkowronski/reachy-mini-mcp/actions/workflows/ci.yml/badge.svg)

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
