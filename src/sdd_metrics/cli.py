from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .git import GitError, current_context
from .hooks.session_end import session_end
from .mappings import MappingStore
from .qwen.paths import QwenPaths
from .reports.json_report import write_json_report
from .reports.markdown_report import write_markdown_report
from .service import collect_metrics


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="sdd-metrics")
    root.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = root.add_subparsers(dest="command", required=True)

    report = commands.add_parser("report", help="generate report.json and report.md")
    report.add_argument("--output-dir", type=Path, default=Path.cwd())
    report.add_argument("--qwen-home", type=Path)
    report.add_argument("--data-dir", type=Path)
    report.add_argument("--cwd", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)

    hook = commands.add_parser("hook", help="commands intended for Qwen hooks")
    hook_commands = hook.add_subparsers(dest="hook_command", required=True)
    session = hook_commands.add_parser("session-end", help="capture session Git context")
    session.add_argument("--session-id")
    session.add_argument("--data-dir", type=Path)
    session.add_argument("--cwd", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)

    doctor = commands.add_parser("doctor", help="diagnose local data availability")
    doctor.add_argument("--qwen-home", type=Path)
    doctor.add_argument("--data-dir", type=Path)
    doctor.add_argument("--cwd", type=Path, default=Path.cwd(), help=argparse.SUPPRESS)
    doctor.add_argument("--json", action="store_true", dest="as_json")
    return root


def _doctor(args: argparse.Namespace) -> int:
    qwen = QwenPaths.discover(args.qwen_home)
    store = MappingStore(args.data_dir)
    checks: dict[str, object] = {
        "qwen_home": str(qwen.root),
        "qwen_home_exists": qwen.root.exists(),
        "settings_exists": qwen.settings.exists(),
        "usage_files": len(qwen.usage_files()),
        "mapping_store": str(store.root),
    }
    try:
        context = current_context(args.cwd)
        mappings, errors = store.find(context.repository, context.branch)
        checks.update({
            "repository": context.repository,
            "branch": context.branch,
            "mapped_sessions": len(mappings),
            "mapping_errors": errors,
            "git_ok": True,
        })
    except GitError as exc:
        checks.update({"git_ok": False, "git_error": str(exc)})
    if args.as_json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
    else:
        for key, value in checks.items():
            print(f"{key}: {value}")
    healthy = bool(checks.get("git_ok")) and bool(checks["qwen_home_exists"])
    return 0 if healthy else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "hook" and args.hook_command == "session-end":
            mapping = session_end(
                args.session_id, cwd=args.cwd, store=MappingStore(args.data_dir)
            )
            print(json.dumps({
                "session_id": mapping.session_id,
                "repository": mapping.repository,
                "branch": mapping.branch,
                "captured_at": mapping.captured_at,
            }, ensure_ascii=False))
            return 0
        if args.command == "doctor":
            return _doctor(args)
        if args.command == "report":
            context = current_context(args.cwd)
            metrics = collect_metrics(
                context,
                QwenPaths.discover(args.qwen_home),
                MappingStore(args.data_dir),
            )
            output = args.output_dir.resolve()
            write_json_report(metrics, output / "report.json")
            write_markdown_report(metrics, output / "report.md")
            print(f"Wrote {output / 'report.json'}")
            print(f"Wrote {output / 'report.md'}")
            return 0
    except (GitError, OSError, ValueError) as exc:
        print(f"sdd-metrics: error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
