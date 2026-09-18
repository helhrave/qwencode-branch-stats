from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .models import SessionMapping


def default_data_dir() -> Path:
    override = os.environ.get("QBS_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "qwencode-branch-stats"
    if sys_platform() == "darwin":
        return Path.home() / "Library" / "Application Support" / "qwencode-branch-stats"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "qwencode-branch-stats"


def sys_platform() -> str:
    import sys

    return sys.platform


class MappingStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or default_data_dir()
        self.directory = self.root / "sessions"

    @staticmethod
    def _filename(session_id: str) -> str:
        digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
        return f"{digest}.json"

    def save(self, mapping: SessionMapping) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        target = self.directory / self._filename(mapping.session_id)
        payload = {
            "schema_version": 1,
            "session_id": mapping.session_id,
            "repo": mapping.repository,
            "branch": mapping.branch,
            "captured_at": mapping.captured_at,
        }
        fd, temporary = tempfile.mkstemp(prefix="mapping-", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def find(self, repository: str, branch: str) -> tuple[list[SessionMapping], list[str]]:
        mappings: list[SessionMapping] = []
        warnings: list[str] = []
        if not self.directory.exists():
            return mappings, warnings
        for path in sorted(self.directory.glob("*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    raw = json.load(handle)
                item = SessionMapping(
                    session_id=str(raw["session_id"]),
                    repository=str(raw["repo"]),
                    branch=str(raw["branch"]),
                    captured_at=str(raw["captured_at"]),
                )
            except (OSError, ValueError, KeyError, TypeError) as exc:
                warnings.append(f"Cannot read mapping {path.name}: {exc}")
                continue
            if item.repository == repository and item.branch == branch:
                mappings.append(item)
        mappings.sort(key=lambda value: (value.captured_at, value.session_id))
        return mappings, warnings

