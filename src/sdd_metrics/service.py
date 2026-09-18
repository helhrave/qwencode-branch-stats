from __future__ import annotations

from pathlib import Path
from typing import Any

from .aggregation import build_task_metrics
from .git import GitContext
from .mappings import MappingStore
from .models import SessionInfo, WarningMessage
from .qwen.paths import QwenPaths
from .qwen.sessions import read_session
from .qwen.settings import read_pricing
from .qwen.subagents import read_subagents
from .qwen.tools import read_tool_calls
from .qwen.usage import read_usage


def collect_metrics(
    context: GitContext,
    qwen: QwenPaths,
    store: MappingStore,
) -> dict[str, Any]:
    mappings, mapping_errors = store.find(context.repository, context.branch)
    warnings = [WarningMessage("mapping_unreadable", message) for message in mapping_errors]
    if not mappings:
        warnings.append(WarningMessage(
            "session_mapping_missing",
            "No completed Qwen sessions are mapped to this repository and branch",
        ))
    session_ids = {item.session_id for item in mappings}
    pricing, pricing_warnings = read_pricing(qwen.settings)
    warnings.extend(pricing_warnings)
    usage, usage_warnings = read_usage(qwen.usage_files(), session_ids)
    warnings.extend(usage_warnings)

    infos: dict[str, SessionInfo] = {}
    calls: dict[str, list] = {}
    subagents: dict[str, list] = {}
    for mapping in mappings:
        session_id = mapping.session_id
        transcript = qwen.find_transcript(session_id)
        if transcript is None:
            infos[session_id] = SessionInfo(id=session_id)
            warnings.append(WarningMessage(
                "transcript_missing", "Qwen session transcript was not found", session_id
            ))
            calls[session_id] = []
            subagents[session_id] = []
            continue
        info, info_warnings = read_session(session_id, transcript)
        infos[session_id] = info
        warnings.extend(info_warnings)
        main_calls, tool_warnings = read_tool_calls(transcript, session_id)
        warnings.extend(tool_warnings)
        runs, subagent_calls, subagent_warnings = read_subagents(
            qwen.subagent_directory(transcript), session_id
        )
        warnings.extend(subagent_warnings)
        calls[session_id] = main_calls + subagent_calls
        subagents[session_id] = runs

    return build_task_metrics(
        repository=context.repository,
        branch=context.branch,
        session_infos=infos,
        usage=usage,
        pricing=pricing,
        session_calls=calls,
        session_subagents=subagents,
        warnings=warnings,
    )

