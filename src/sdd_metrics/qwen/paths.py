from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QwenPaths:
    root: Path

    @classmethod
    def discover(cls, override: Path | None = None) -> "QwenPaths":
        configured = override or os.environ.get("SDD_METRICS_QWEN_HOME") or os.environ.get("QWEN_HOME")
        return cls(Path(configured).expanduser() if configured else Path.home() / ".qwen")

    @property
    def usage(self) -> Path:
        return self.root / "usage"

    @property
    def projects(self) -> Path:
        return self.root / "projects"

    @property
    def settings(self) -> Path:
        return self.root / "settings.json"

    def usage_files(self) -> list[Path]:
        return sorted(self.usage.glob("token-usage-*.jsonl")) if self.usage.exists() else []

    def find_transcript(self, session_id: str) -> Path | None:
        if not self.projects.exists():
            return None
        matches = sorted(self.projects.glob(f"*/chats/{session_id}.jsonl"))
        if not matches:
            matches = sorted(self.projects.glob(f"**/chats/{session_id}.jsonl"))
        return matches[-1] if matches else None

    def subagent_directory(self, transcript: Path) -> Path:
        return transcript.parent.parent / "subagents" / transcript.stem

