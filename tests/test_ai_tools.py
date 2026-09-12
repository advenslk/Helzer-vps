import pytest

from helzer.ai.tools import ToolCall, validate_tool_call


def test_safe_tool_call_allows_create_vps():
    call = ToolCall("create_vps", {"owner_id": 123, "name": "demo", "cpu_cores": 2, "ram_mb": 2048, "disk_gb": 20})
    assert validate_tool_call(call) == call


def test_unknown_tool_is_rejected():
    with pytest.raises(ValueError, match="unknown tool"):
        validate_tool_call(ToolCall("docker_exec", {}))


def test_destructive_tool_requires_confirmation():
    call = ToolCall("delete_vps", {"vps_id": 7})
    with pytest.raises(ValueError, match="confirmation"):
        validate_tool_call(call)


def test_destructive_tool_accepts_confirmation():
    call = ToolCall("delete_vps", {"vps_id": 7, "confirmed": True})
    assert validate_tool_call(call) == call
