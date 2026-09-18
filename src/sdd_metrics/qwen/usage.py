from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ..models import TokenMetrics, UsageRecord, WarningMessage
from .jsonl import read_jsonl


def _integer(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(int(value or 0), 0)
    except (TypeError, ValueError):
        return 0


def read_usage(
    paths: Iterable[Path], session_ids: set[str]
) -> tuple[list[UsageRecord], list[WarningMessage]]:
    records: list[UsageRecord] = []
    warnings: list[WarningMessage] = []
    seen: set[str] = set()

    for path in paths:
        def malformed(line: int, detail: str) -> None:
            warnings.append(WarningMessage(
                "malformed_jsonl", f"Malformed usage JSONL in {path.name}:{line}: {detail}"
            ))

        try:
            for raw in read_jsonl(path, malformed):
                session_id = str(raw.get("sessionId") or raw.get("session_id") or "")
                if session_id not in session_ids:
                    continue
                usage_id = str(raw.get("id") or "")
                if not usage_id:
                    warnings.append(WarningMessage(
                        "unknown_qwen_schema", f"Usage record in {path.name} has no id", session_id
                    ))
                    continue
                if usage_id in seen:
                    continue
                seen.add(usage_id)
                model = str(raw.get("model") or "unknown")
                source = str(raw.get("source") or "main")
                input_tokens = _integer(raw.get("inputTokens"))
                output_tokens = _integer(raw.get("outputTokens"))
                total_tokens = _integer(raw.get("totalTokens"))
                if raw.get("totalTokens") is None:
                    total_tokens = input_tokens + output_tokens
                records.append(UsageRecord(
                    id=usage_id,
                    timestamp=str(raw["timestamp"]) if raw.get("timestamp") else None,
                    session_id=session_id,
                    model=model,
                    source=source,
                    tokens=TokenMetrics(
                        input=input_tokens,
                        cached_input=_integer(raw.get("cachedTokens")),
                        output=output_tokens,
                        reasoning=_integer(raw.get("thoughtsTokens")),
                        total=total_tokens,
                    ),
                    api_duration_ms=_integer(raw.get("apiDurationMs")),
                ))
        except OSError as exc:
            warnings.append(WarningMessage("usage_unreadable", f"Cannot read {path}: {exc}"))
    records.sort(key=lambda item: (item.timestamp or "", item.id))
    return records, warnings
