from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]

SAFE_TOOLS: Final[frozenset[str]] = frozenset({"create_vps", "resize_vps", "start_vps", "stop_vps", "restart_vps", "delete_vps", "get_vps_stats", "get_vps_logs", "install_sshx"})
DESTRUCTIVE_TOOLS: Final[frozenset[str]] = frozenset({"delete_vps", "resize_vps"})

def validate_tool_call(call: ToolCall) -> ToolCall:
    if call.name not in SAFE_TOOLS:
        raise ValueError(f"unknown tool: {call.name}")
    if call.name in DESTRUCTIVE_TOOLS and call.arguments.get("confirmed") is not True:
        raise ValueError(f"confirmation required for {call.name}")
    if call.name != "create_vps" and "vps_id" not in call.arguments:
        raise ValueError("vps_id is required")
    if call.name == "create_vps" and "owner_id" not in call.arguments:
        raise ValueError("owner_id is required")
    return call

def tool_definitions() -> list[dict[str, Any]]:
    return [{"name": n, "description": d} for n, d in (
        ("create_vps", "Create a VPS using validated resource limits."),
        ("resize_vps", "Resize CPU/RAM of an existing VPS."),
        ("start_vps", "Start a VPS."), ("stop_vps", "Stop a VPS."),
        ("restart_vps", "Restart a VPS."), ("delete_vps", "Permanently delete a VPS after confirmation."),
        ("get_vps_stats", "Read resource statistics."), ("get_vps_logs", "Read recent logs."),
        ("install_sshx", "Prepare a short-lived SSH access session."),
    )]
