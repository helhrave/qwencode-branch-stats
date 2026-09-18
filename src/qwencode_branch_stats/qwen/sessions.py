from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import SessionInfo, WarningMessage
from .jsonl import read_jsonl, walk_dicts


def _timestamp(raw: dict[str, Any]) -> str | None:
    for key in ("timestamp", "createdAt", "created_at", "time"):
        value = raw.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _custom_title(raw: dict[str, Any]) -> str | None:
    if raw.get("type") == "system" and raw.get("subtype") == "custom_title":
        for key in ("title", "content", "text"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = value.get("title") or value.get("text")
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
    return None


def read_session(session_id: str, path: Path) -> tuple[SessionInfo, list[WarningMessage]]:
    warnings: list[WarningMessage] = []
    timestamps: list[str] = []
    title: str | None = None

    def malformed(line: int, detail: str) -> None:
        warnings.append(WarningMessage(
            "malformed_jsonl", f"Malformed transcript JSONL in {path.name}:{line}: {detail}", session_id
        ))

    try:
        for event in read_jsonl(path, malformed):
            value = _timestamp(event)
            if value:
                timestamps.append(value)
            for nested in walk_dicts(event):
                candidate = _custom_title(nested)
                if candidate is not None:
                    title = candidate
    except OSError as exc:
        warnings.append(WarningMessage("transcript_unreadable", f"Cannot read transcript: {exc}", session_id))
    timestamps.sort()
    return SessionInfo(
        id=session_id,
        title=title,
        started_at=timestamps[0] if timestamps else None,
        ended_at=timestamps[-1] if timestamps else None,
        transcript_path=str(path),
    ), warnings

