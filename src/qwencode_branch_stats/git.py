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
    repository_name: str
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
    toplevel = _git(["rev-parse", "--show-toplevel"], cwd)
    repository = normalize_repository(toplevel)
    branch = _git(["branch", "--show-current"], cwd)
    if not branch:
        raise GitError("detached HEAD is not associated with a branch")
    return GitContext(
        repository=repository,
        repository_name=Path(toplevel).name or Path(repository).root,
        branch=branch,
    )

