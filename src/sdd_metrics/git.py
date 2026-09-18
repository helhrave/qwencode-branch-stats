from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitContext:
    repository: str
    branch: str


def _git(args: list[str], cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise GitError(detail.strip()) from exc
    return completed.stdout.strip()


def normalize_repository(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def current_context(cwd: Path | None = None) -> GitContext:
    repository = normalize_repository(_git(["rev-parse", "--show-toplevel"], cwd))
    branch = _git(["branch", "--show-current"], cwd)
    if not branch:
        raise GitError("detached HEAD is not associated with a branch")
    return GitContext(repository=repository, branch=branch)

