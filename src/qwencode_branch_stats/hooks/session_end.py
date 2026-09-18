from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

from ..git import current_context
from ..mappings import MappingStore
from ..models import SessionMapping


def _nested_session_id(payload: dict[str, Any]) -> str | None:
    for key in ("session_id", "sessionId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    session = payload.get("session")
    if isinstance(session, dict) and isinstance(session.get("id"), str):
        return session["id"]
    return None


def session_end(
    session_id: str | None,
    cwd: Path | None = None,
    stdin: TextIO | None = None,
    store: MappingStore | None = None,
) -> SessionMapping:
    if not session_id:
        stream = stdin if stdin is not None else sys.stdin
        raw = stream.read()
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid SessionEnd JSON payload: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("SessionEnd payload must be a JSON object")
        session_id = _nested_session_id(payload)
    if not session_id:
        raise ValueError("SessionEnd payload does not contain a session ID")
    context = current_context(cwd)
    mapping = SessionMapping(
        session_id=session_id,
        repository=context.repository,
        branch=context.branch,
        captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    (store or MappingStore()).save(mapping)
    return mapping

