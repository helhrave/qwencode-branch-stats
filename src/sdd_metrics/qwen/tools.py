from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import ToolCall, WarningMessage
from .jsonl import read_jsonl, walk_dicts


def _first(raw: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in raw and raw[name] is not None:
            return raw[name]
    return None


def _success(raw: dict[str, Any]) -> bool | None:
    value = _first(raw, ("success", "is_success"))
    if isinstance(value, bool):
        return value
    status = str(_first(raw, ("execution_status", "status")) or "").lower()
    if status in {"success", "succeeded", "completed", "ok"}:
        return True
    if status in {"failed", "error", "cancelled", "canceled"}:
        return False
    return None


def _duration(raw: dict[str, Any]) -> int:
    value = _first(raw, ("duration_ms", "durationMs"))
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def _tool_call(raw: dict[str, Any]) -> ToolCall | None:
    event_name = str(_first(raw, ("event", "event_name", "name")) or "")
    explicit = event_name == "qwen-code.tool_call" or raw.get("type") == "qwen-code.tool_call"
    name = _first(raw, ("function_name", "functionName", "tool_name", "toolName"))
    if not name and raw.get("type") in {"function_call", "tool_call", "tool_use"}:
        name = raw.get("name")
        explicit = True
    if not name and isinstance(raw.get("functionCall"), dict):
        name = raw["functionCall"].get("name")
        explicit = True
    if not name and isinstance(raw.get("function"), dict):
        name = raw["function"].get("name")
        explicit = True
    if name and any(key in raw for key in (
        "call_id", "callId", "tool_call_id", "duration_ms", "durationMs",
        "execution_status", "success", "tool_type", "toolType",
    )):
        explicit = True
    if not explicit or not isinstance(name, str) or not name:
        return None
    call_id = _first(raw, ("call_id", "callId", "tool_call_id", "id"))
    tool_type = _first(raw, ("tool_type", "toolType"))
    return ToolCall(
        call_id=str(call_id) if call_id is not None else None,
        name=name,
        success=_success(raw),
        duration_ms=_duration(raw),
        tool_type=str(tool_type) if tool_type is not None else None,
    )


def read_tool_calls(path: Path, session_id: str) -> tuple[list[ToolCall], list[WarningMessage]]:
    calls: list[ToolCall] = []
    warnings: list[WarningMessage] = []
    seen: set[str] = set()

    def malformed(line: int, detail: str) -> None:
        warnings.append(WarningMessage(
            "malformed_jsonl", f"Malformed tool JSONL in {path.name}:{line}: {detail}", session_id
        ))

    try:
        for event in read_jsonl(path, malformed):
            for nested in walk_dicts(event):
                call = _tool_call(nested)
                if call is None:
                    continue
                if call.call_id and call.call_id in seen:
                    continue
                if call.call_id:
                    seen.add(call.call_id)
                calls.append(call)
    except OSError as exc:
        warnings.append(WarningMessage("transcript_unreadable", f"Cannot read tools: {exc}", session_id))
    return calls, warnings


def parse_mcp_name(name: str, tool_type: str | None) -> tuple[str, str] | None:
    if tool_type != "mcp" and not name.startswith("mcp__"):
        return None
    parts = name.split("__", 2)
    if len(parts) != 3 or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]
