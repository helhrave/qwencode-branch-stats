from __future__ import annotations

from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _number(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _cost(value: float | None) -> str:
    return "unknown" if value is None else f"{value:,.6f}".rstrip("0").rstrip(".")


def _duration(value: int) -> str:
    seconds = value / 1000
    return f"{seconds:,.3f} s"


def _usage_row(name: str, item: dict[str, Any], runs: Any = ...) -> str:
    tokens = item["tokens"]
    cells = [_text(name)]
    if runs is not ...:
        cells.append(_text(runs))
    cells.extend([
        _number(item["requests"]), _number(tokens["input"]),
        _number(tokens["cached_input"]), _number(tokens["output"]),
        _number(tokens["reasoning"]), _cost(item["cost"]),
    ])
    return "| " + " | ".join(cells) + " |"


def render_markdown(metrics: dict[str, Any]) -> str:
    task, totals = metrics["task"], metrics["totals"]
    lines = [
        f"# {_text(task['branch'])}", "",
        f"Repository: {_text(task['repository'])}  ",
        f"Branch: {_text(task['branch'])}  ",
        f"Sessions: {task['session_count']}  ",
        f"Observation span: {_text(task['observation_started_at'])} — {_text(task['observation_ended_at'])}", "",
        "## Cost by model", "",
        "| Model | Requests | Input | Cached | Output | Reasoning | Cost |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(_usage_row(item["name"], item) for item in metrics["models"])
    if not metrics["models"]:
        lines.append("| — | 0 | 0 | 0 | 0 | 0 | 0 |")
    lines.extend(["", f"Total cost: {_cost(totals['cost'])}", "", "## Cost by agent", "",
        "| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    lines.extend(_usage_row(item["name"], item, item["runs"]) for item in metrics["agents"])
    if not metrics["agents"]:
        lines.append("| — | — | 0 | 0 | 0 | 0 | 0 | 0 |")

    lines.extend(["", "## Sessions", "",
        "| Session | Title | Models | Requests | Input | Cached | Output | Reasoning | Cost |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for session in metrics["sessions"]:
        tokens = session["tokens"]
        model_names = ", ".join(item["name"] for item in session["models"]) or "—"
        lines.append("| " + " | ".join([
            _text(session["id"][:8] + "…"), _text(session["title"]), _text(model_names),
            _number(session["requests"]), _number(tokens["input"]), _number(tokens["cached_input"]),
            _number(tokens["output"]), _number(tokens["reasoning"]), _cost(session["cost"]),
        ]) + " |")

    tokens = totals["tokens"]
    lines.extend(["", "## Overall usage", "",
        f"Requests: {_number(totals['requests'])}  ",
        f"Input tokens: {_number(tokens['input'])}  ",
        f"Cached input tokens: {_number(tokens['cached_input'])}  ",
        f"Output tokens: {_number(tokens['output'])}  ",
        f"Reasoning tokens: {_number(tokens['reasoning'])}  ",
        f"Total tokens: {_number(tokens['total'])}  ",
        f"API duration: {_duration(totals['api_duration_ms'])}  ",
        f"Tool calls: {_number(totals['tool_calls'])}  ",
        f"MCP calls: {_number(totals['mcp_calls'])}  ",
        f"Subagent runs: {_number(totals['subagent_runs'])}  ",
        f"Tool duration: {_duration(totals['tool_duration_ms'])}  ",
        f"Subagent duration: {_duration(totals['subagent_duration_ms'])}",
    ])

    lines.extend(["", "## Session details", ""])
    for session in metrics["sessions"]:
        lines.extend([
            f"### {_text(session['title'] or session['id'])}", "",
            f"Session: {_text(session['id'])}  ",
            f"Started: {_text(session['started_at'])}  ",
            f"Ended: {_text(session['ended_at'])}  ",
            f"Cost: {_cost(session['cost'])}  ",
            "Models: " + (_text(", ".join(item["name"] for item in session["models"])) or "—") + "  ",
            "Agents: " + (_text(", ".join(item["name"] for item in session["agents"])) or "—") + "  ",
            f"Tool calls: {session['tool_calls']}  ",
            f"MCP calls: {session['mcp_calls']}  ",
            f"Subagent runs: {session['subagent_runs']}", "",
        ])

    lines.extend(["## Tools", "", "| Tool | Calls | Success | Failed | Duration |",
                  "|---|---:|---:|---:|---:|"])
    for item in metrics["tools"]:
        lines.append(f"| {_text(item['name'])} | {item['calls']} | {item['success']} | {item['failed']} | {_duration(item['duration_ms'])} |")
    if not metrics["tools"]:
        lines.append("| — | 0 | 0 | 0 | 0 s |")

    lines.extend(["", "## MCP", "", "| Server | Tool | Calls | Success | Failed | Duration |",
                  "|---|---|---:|---:|---:|---:|"])
    for item in metrics["mcp"]:
        lines.append(f"| {_text(item['server'])} | {_text(item['tool'])} | {item['calls']} | {item['success']} | {item['failed']} | {_duration(item['duration_ms'])} |")
    if not metrics["mcp"]:
        lines.append("| — | — | 0 | 0 | 0 | 0 s |")

    lines.extend(["", "## Subagents", "",
        "| Agent | Runs | Requests | Input | Cached | Output | Reasoning | Cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    subagents = [item for item in metrics["agents"] if item["name"] != "main"]
    lines.extend(_usage_row(item["name"], item, item["runs"]) for item in subagents)
    if not subagents:
        lines.append("| — | 0 | 0 | 0 | 0 | 0 | 0 | 0 |")

    lines.extend(["", "## Data quality / warnings", ""])
    if metrics["warnings"]:
        for warning in metrics["warnings"]:
            suffix = f" (session: {warning['session_id']})" if warning.get("session_id") else ""
            lines.append(f"- `{_text(warning['code'])}`: {_text(warning['message'])}{_text(suffix)}")
    else:
        lines.append("No warnings.")
    return "\n".join(lines) + "\n"


def write_markdown_report(metrics: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(metrics))
