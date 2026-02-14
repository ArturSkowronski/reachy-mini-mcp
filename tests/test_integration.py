"""Integration tests — exercise tools through the full MCP protocol stack.

Uses ``create_connected_server_and_client_session`` to create an in-memory
MCP client/server pair so that every call goes through JSON-RPC
serialization, schema validation, and the FastMCP dispatcher.
"""

from unittest.mock import MagicMock, patch

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from reachy import mcp as server

pytestmark = pytest.mark.integration

EXPECTED_TOOLS = {
    "capture_image",
    "do_barrel_roll",
    "play_sound",
    "express_emotion",
    "look_at_point",
    "move_antennas",
    "nod",
    "reset_position",
    "scan_surroundings",
    "shake_head",
    "track_face",
    "wake_up",
    "go_to_sleep",
    "detect_sound_direction",
    "move_head",
    "speak_text",
}


def _make_mock_mini():
    """Create a MagicMock that behaves like a ReachyMini context manager."""
    mock_mini = MagicMock()
    mock_mini.__enter__ = MagicMock(return_value=mock_mini)
    mock_mini.__exit__ = MagicMock(return_value=False)
    return mock_mini


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------


async def test_all_tools_registered():
    """All 10 tools should be discoverable via list_tools."""
    async with create_connected_server_and_client_session(server) as session:
        result = await session.list_tools()
        tool_names = {t.name for t in result.tools}

    assert tool_names == EXPECTED_TOOLS


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


async def test_move_head_schema():
    """move_head should expose x, y, z, roll, pitch, yaw, duration params."""
    async with create_connected_server_and_client_session(server) as session:
        result = await session.list_tools()
        move_head_tool = next(t for t in result.tools if t.name == "move_head")

    props = move_head_tool.inputSchema["properties"]
    assert set(props.keys()) == {"x", "y", "z", "roll", "pitch", "yaw", "duration"}


async def test_move_antennas_schema():
    """move_antennas should expose right, left, duration params."""
    async with create_connected_server_and_client_session(server) as session:
        result = await session.list_tools()
        tool = next(t for t in result.tools if t.name == "move_antennas")

    props = tool.inputSchema["properties"]
    assert set(props.keys()) == {"right", "left", "duration"}


async def test_express_emotion_schema():
    """express_emotion should expose a single emoji param."""
    async with create_connected_server_and_client_session(server) as session:
        result = await session.list_tools()
        tool = next(t for t in result.tools if t.name == "express_emotion")

    props = tool.inputSchema["properties"]
    assert set(props.keys()) == {"emoji"}


# ---------------------------------------------------------------------------
# Tool calls through MCP
# ---------------------------------------------------------------------------


async def test_call_wake_up_via_mcp():
    """Call wake_up through the MCP protocol and verify the result text."""
    mock_mini = _make_mock_mini()
    mock_class = MagicMock(return_value=mock_mini)

    with patch("reachy.ReachyMini", mock_class):
        async with create_connected_server_and_client_session(server) as session:
            result = await session.call_tool("wake_up", {})

    assert result.content[0].text == "Reachy woke up!"
    mock_mini.wake_up.assert_called_once()


async def test_call_move_head_via_mcp():
    """Call move_head with arguments through MCP and verify SDK received them."""
    mock_mini = _make_mock_mini()
    mock_class = MagicMock(return_value=mock_mini)
    mock_pose = MagicMock()

    with (
        patch("reachy.ReachyMini", mock_class),
        patch("reachy.create_head_pose", return_value=mock_pose) as mock_create,
    ):
        async with create_connected_server_and_client_session(server) as session:
            result = await session.call_tool(
                "move_head",
                {
                    "x": 10,
                    "y": 5,
                    "z": 15,
                    "roll": 10,
                    "pitch": -5,
                    "yaw": 20,
                    "duration": 1.5,
                },
            )

    # MCP JSON-RPC deserializes integers as floats
    assert "pos(10.0, 5.0, 15.0)mm" in result.content[0].text
    mock_create.assert_called_once_with(
        x=10.0,
        y=5.0,
        z=15.0,
        roll=10.0,
        pitch=-5.0,
        yaw=20.0,
        mm=True,
        degrees=True,
    )
    mock_mini.goto_target.assert_called_once_with(head=mock_pose, duration=1.5)


async def test_call_express_emotion_via_mcp():
    """Call express_emotion with emoji argument through MCP."""
    mock_mini = _make_mock_mini()
    mock_class = MagicMock(return_value=mock_mini)
    mock_pose = MagicMock()

    with (
        patch("reachy.ReachyMini", mock_class),
        patch("reachy.create_head_pose", return_value=mock_pose),
    ):
        async with create_connected_server_and_client_session(server) as session:
            result = await session.call_tool("express_emotion", {"emoji": "😊"})

    assert result.content[0].text == "Reachy expressed: happy (😊)"


async def test_call_tool_unsupported_emoji_via_mcp():
    """Unsupported emoji should return an error message, not crash."""
    mock_mini = _make_mock_mini()
    mock_class = MagicMock(return_value=mock_mini)

    with patch("reachy.ReachyMini", mock_class):
        async with create_connected_server_and_client_session(server) as session:
            result = await session.call_tool("express_emotion", {"emoji": "🔥"})

    assert "Unsupported emoji" in result.content[0].text


# ---------------------------------------------------------------------------
# Resources through MCP
# ---------------------------------------------------------------------------

EXPECTED_RESOURCES = {
    "reachy://emotions",
    "reachy://sounds",
    "reachy://limits",
    "reachy://capabilities",
}


async def test_all_resources_registered():
    """All 4 resources should be discoverable via list_resources."""
    async with create_connected_server_and_client_session(server) as session:
        result = await session.list_resources()
        resource_uris = {str(r.uri) for r in result.resources}

    assert resource_uris == EXPECTED_RESOURCES


async def test_read_emotions_resource():
    """Reading reachy://emotions should return JSON with emoji mappings."""
    import json

    async with create_connected_server_and_client_session(server) as session:
        result = await session.read_resource("reachy://emotions")

    data = json.loads(result.contents[0].text)
    assert data["😊"] == "happy"
    assert data["😢"] == "sad"
    assert len(data) == 10


async def test_read_sounds_resource():
    """Reading reachy://sounds should return JSON list of sound names."""
    import json

    async with create_connected_server_and_client_session(server) as session:
        result = await session.read_resource("reachy://sounds")

    data = json.loads(result.contents[0].text)
    assert "dance1" in data
    assert "wake_up" in data


async def test_read_capabilities_resource():
    """Reading reachy://capabilities should return categorized tool lists."""
    import json

    async with create_connected_server_and_client_session(server) as session:
        result = await session.read_resource("reachy://capabilities")

    data = json.loads(result.contents[0].text)
    assert "vision" in data
    assert "track_face" in data["vision"]
    assert "movement" in data
    assert "nod" in data["movement"]
