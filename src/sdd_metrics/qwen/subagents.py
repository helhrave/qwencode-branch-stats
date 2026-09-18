from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import SubagentRun, ToolCall, WarningMessage
from .tools import read_tool_calls


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def read_subagents(
    directory: Path, session_id: str
) -> tuple[list[SubagentRun], list[ToolCall], list[WarningMessage]]:
    runs: list[SubagentRun] = []
    calls: list[ToolCall] = []
    warnings: list[WarningMessage] = []
    if not directory.exists():
        return runs, calls, warnings
    for path in sorted(directory.glob("*.meta.json")):
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                raw = json.load(handle)
            if not isinstance(raw, dict):
                raise ValueError("metadata is not an object")
            agent_id = str(raw.get("agentId") or path.name.removesuffix(".meta.json"))
            created = raw.get("createdAt")
            updated = raw.get("lastUpdatedAt")
            start, end = _parse_time(created), _parse_time(updated)
            duration = max(int((end - start).total_seconds() * 1000), 0) if start and end else 0
            runs.append(SubagentRun(
                agent_id=agent_id,
                agent_type=str(raw["agentType"]) if raw.get("agentType") is not None else None,
                parent_session_id=str(raw["parentSessionId"]) if raw.get("parentSessionId") else None,
                parent_agent_id=str(raw["parentAgentId"]) if raw.get("parentAgentId") else None,
                created_at=str(created) if created else None,
                last_updated_at=str(updated) if updated else None,
                status=str(raw["status"]) if raw.get("status") is not None else None,
                name=str(raw.get("subagentName") or raw.get("agentType") or "unknown"),
                resume_count=_integer(raw.get("resumeCount")),
                depth=_integer(raw.get("depth")),
                duration_ms=duration,
            ))
            transcript = directory / f"{path.name.removesuffix('.meta.json')}.jsonl"
            if not transcript.exists() and agent_id:
                transcript = directory / f"{agent_id}.jsonl"
            if transcript.exists():
                found, found_warnings = read_tool_calls(transcript, session_id)
                calls.extend(found)
                warnings.extend(found_warnings)
        except (OSError, ValueError, TypeError) as exc:
            warnings.append(WarningMessage(
                "subagent_metadata_missing", f"Cannot read subagent metadata {path.name}: {exc}", session_id
            ))
    runs.sort(key=lambda item: (item.created_at or "", item.agent_id))
    return runs, calls, warnings
