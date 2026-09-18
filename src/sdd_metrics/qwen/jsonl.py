from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Callable


def read_jsonl(
    path: Path,
    on_error: Callable[[int, str], None] | None = None,
) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                if on_error:
                    on_error(line_number, str(exc))
                continue
            if isinstance(value, dict):
                yield value
            elif on_error:
                on_error(line_number, "JSON value is not an object")


def walk_dicts(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_dicts(child)

