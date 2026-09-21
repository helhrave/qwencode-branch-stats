from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from .models import (
    ModelPricing,
    SessionInfo,
    SubagentRun,
    TokenMetrics,
    ToolCall,
    ToolMetrics,
    UsageRecord,
    WarningMessage,
)
from .qwen.tools import parse_mcp_name


@dataclass
class UsageAccumulator:
    requests: int = 0
    tokens: TokenMetrics = field(default_factory=TokenMetrics)
    api_duration_ms: int = 0
    cost: Decimal = Decimal("0")
    cost_known: bool = True

    def add(self, record: UsageRecord, request_cost: Decimal | None) -> None:
        self.requests += 1
        self.tokens.add(record.tokens)
        self.api_duration_ms += record.api_duration_ms
        if request_cost is None:
            self.cost_known = False
        else:
            self.cost += request_cost


def request_cost(record: UsageRecord, pricing: ModelPricing | None) -> Decimal | None:
    if pricing is None:
        return None
    million = Decimal(1_000_000)
    cached = min(record.tokens.cached_input, record.tokens.input)
    cache_price = pricing.cache_read_per_million
    if cache_price is None:
        cache_price = pricing.input_per_million
    return (
        Decimal(record.tokens.input - cached) / million * pricing.input_per_million
        + Decimal(cached) / million * cache_price
        + Decimal(record.tokens.output) / million * pricing.output_per_million
    )


def _cost(value: UsageAccumulator) -> float | None:
    if not value.cost_known:
        return None
    return float(value.cost.quantize(Decimal("0.000001")))


def _usage_dict(value: UsageAccumulator) -> dict[str, Any]:
    return {
        "requests": value.requests,
        "tokens": value.tokens.as_dict(),
        "cost": _cost(value),
        "api_duration_ms": value.api_duration_ms,
    }


def _aggregate_calls(calls: Iterable[ToolCall]) -> tuple[dict[str, ToolMetrics], dict[tuple[str, str], ToolMetrics]]:
    tools: dict[str, ToolMetrics] = defaultdict(ToolMetrics)
    mcp: dict[tuple[str, str], ToolMetrics] = defaultdict(ToolMetrics)
    seen: set[str] = set()
    for call in calls:
        if call.call_id and call.call_id in seen:
            continue
        if call.call_id:
            seen.add(call.call_id)
        tools[call.name].add_call(call.success, call.duration_ms)
        parsed = parse_mcp_name(call.name, call.tool_type)
        if parsed:
            mcp[parsed].add_call(call.success, call.duration_ms)
    return dict(tools), dict(mcp)


def _merge_tools(target: dict[Any, ToolMetrics], source: dict[Any, ToolMetrics]) -> None:
    for name, metrics in source.items():
        target.setdefault(name, ToolMetrics()).add(metrics)


def _tools_object(tools: dict[str, ToolMetrics]) -> dict[str, dict[str, int]]:
    return {name: tools[name].as_dict() for name in sorted(tools)}


def _mcp_object(mcp: dict[tuple[str, str], ToolMetrics]) -> dict[str, dict[str, dict[str, int]]]:
    result: dict[str, dict[str, dict[str, int]]] = {}
    for server, tool in sorted(mcp):
        result.setdefault(server, {})[tool] = mcp[(server, tool)].as_dict()
    return result


def build_task_metrics(
    repository_name: str,
    branch: str,
    session_infos: dict[str, SessionInfo],
    usage: list[UsageRecord],
    pricing: dict[str, ModelPricing],
    session_calls: dict[str, list[ToolCall]],
    session_subagents: dict[str, list[SubagentRun]],
    warnings: list[WarningMessage],
) -> dict[str, Any]:
    report_warnings = list(warnings)
    missing_models = sorted({item.model for item in usage if item.model not in pricing})
    for model in missing_models:
        report_warnings.append(WarningMessage(
            "pricing_missing", f"Pricing is missing for model {model}"
        ))

    all_usage = UsageAccumulator()
    by_model: dict[str, UsageAccumulator] = defaultdict(UsageAccumulator)
    by_agent: dict[str, UsageAccumulator] = defaultdict(UsageAccumulator)
    by_agent_model: dict[tuple[str, str], UsageAccumulator] = defaultdict(UsageAccumulator)
    by_session: dict[str, UsageAccumulator] = defaultdict(UsageAccumulator)
    by_session_model: dict[tuple[str, str], UsageAccumulator] = defaultdict(UsageAccumulator)
    by_session_agent: dict[tuple[str, str], UsageAccumulator] = defaultdict(UsageAccumulator)
    by_session_agent_model: dict[tuple[str, str, str], UsageAccumulator] = defaultdict(UsageAccumulator)

    usage_timestamps: dict[str, list[str]] = defaultdict(list)
    for record in usage:
        calculated = request_cost(record, pricing.get(record.model))
        all_usage.add(record, calculated)
        by_model[record.model].add(record, calculated)
        by_agent[record.source].add(record, calculated)
        by_agent_model[(record.source, record.model)].add(record, calculated)
        by_session[record.session_id].add(record, calculated)
        by_session_model[(record.session_id, record.model)].add(record, calculated)
        by_session_agent[(record.session_id, record.source)].add(record, calculated)
        by_session_agent_model[(record.session_id, record.source, record.model)].add(record, calculated)
        if record.timestamp:
            usage_timestamps[record.session_id].append(record.timestamp)

    agent_runs: dict[str, int] = defaultdict(int)
    all_subagents: list[SubagentRun] = []
    for runs in session_subagents.values():
        for run in runs:
            agent_runs[run.name] += 1
            all_subagents.append(run)

    global_tools: dict[str, ToolMetrics] = {}
    global_mcp: dict[tuple[str, str], ToolMetrics] = {}
    sessions: list[dict[str, Any]] = []
    observation_starts: list[str] = []
    observation_ends: list[str] = []

    for session_id, info in sorted(
        session_infos.items(), key=lambda item: (item[1].started_at or "", item[0])
    ):
        timestamps = sorted(usage_timestamps.get(session_id, []))
        started_at = info.started_at or (timestamps[0] if timestamps else None)
        ended_at = info.ended_at or (timestamps[-1] if timestamps else None)
        if started_at:
            observation_starts.append(started_at)
        if ended_at:
            observation_ends.append(ended_at)

        tools, mcp = _aggregate_calls(session_calls.get(session_id, []))
        _merge_tools(global_tools, tools)
        _merge_tools(global_mcp, mcp)
        runs = session_subagents.get(session_id, [])
        agent_names = sorted(
            {agent for sid, agent in by_session_agent if sid == session_id}
            | {run.name for run in runs}
        )
        models = []
        for sid, model in sorted(by_session_model):
            if sid != session_id:
                continue
            model_item = {"name": model, **_usage_dict(by_session_model[(sid, model)])}
            models.append(model_item)
        agents = []
        for agent in agent_names:
            accumulator = by_session_agent[(session_id, agent)]
            agent_models = []
            for sid, source, model in sorted(by_session_agent_model):
                if sid == session_id and source == agent:
                    agent_models.append({
                        "name": model,
                        **_usage_dict(by_session_agent_model[(sid, source, model)]),
                    })
            agents.append({
                "name": agent,
                "runs": None if agent == "main" else sum(1 for run in runs if run.name == agent),
                **_usage_dict(accumulator),
                "models": agent_models,
            })
        session_usage = by_session[session_id]
        sessions.append({
            "id": session_id,
            "title": info.title,
            "started_at": started_at,
            "ended_at": ended_at,
            **_usage_dict(session_usage),
            "models": models,
            "agents": agents,
            "tools": _tools_object(tools),
            "mcp": _mcp_object(mcp),
            "subagents": [run.as_dict() for run in runs],
            "tool_calls": sum(item.calls for item in tools.values()),
            "mcp_calls": sum(item.calls for item in mcp.values()),
            "subagent_runs": len(runs),
            "subagent_duration_ms": sum(run.duration_ms for run in runs),
        })

    models = [
        {"name": model, **_usage_dict(by_model[model])}
        for model in sorted(by_model)
    ]
    agents = []
    for agent in sorted(set(by_agent) | set(agent_runs)):
        models_for_agent = [
            {"name": model, **_usage_dict(by_agent_model[(agent, model)])}
            for source, model in sorted(by_agent_model)
            if source == agent
        ]
        agents.append({
            "name": agent,
            "runs": None if agent == "main" else agent_runs.get(agent, 0),
            **_usage_dict(by_agent[agent]),
            "models": models_for_agent,
        })

    tool_calls = sum(item.calls for item in global_tools.values())
    mcp_calls = sum(item.calls for item in global_mcp.values())
    unique_warnings: list[WarningMessage] = []
    seen_warnings: set[tuple[str, str, str | None]] = set()
    for warning in report_warnings:
        key = (warning.code, warning.message, warning.session_id)
        if key not in seen_warnings:
            seen_warnings.add(key)
            unique_warnings.append(warning)

    return {
        "task": {
            "repository": repository_name,
            "branch": branch,
            "session_count": len(session_infos),
            "observation_started_at": min(observation_starts) if observation_starts else None,
            "observation_ended_at": max(observation_ends) if observation_ends else None,
        },
        "totals": {
            **_usage_dict(all_usage),
            "tool_calls": tool_calls,
            "mcp_calls": mcp_calls,
            "subagent_runs": len(all_subagents),
            "tool_duration_ms": sum(item.duration_ms for item in global_tools.values()),
            "subagent_duration_ms": sum(run.duration_ms for run in all_subagents),
        },
        "models": models,
        "agents": agents,
        "tools": [
            {"name": name, **global_tools[name].as_dict()} for name in sorted(global_tools)
        ],
        "mcp": [
            {"server": server, "tool": tool, **global_mcp[(server, tool)].as_dict()}
            for server, tool in sorted(global_mcp)
        ],
        "sessions": sessions,
        "warnings": [warning.as_dict() for warning in unique_warnings],
    }

