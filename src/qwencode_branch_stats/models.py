from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass
class TokenMetrics:
    input: int = 0
    cached_input: int = 0
    output: int = 0
    reasoning: int = 0
    total: int = 0

    def add(self, other: "TokenMetrics") -> None:
        self.input += other.input
        self.cached_input += other.cached_input
        self.output += other.output
        self.reasoning += other.reasoning
        self.total += other.total

    def as_dict(self) -> dict[str, int]:
        return {
            "input": self.input,
            "cached_input": self.cached_input,
            "output": self.output,
            "reasoning": self.reasoning,
            "total": self.total,
        }


@dataclass(frozen=True)
class WarningMessage:
    code: str
    message: str
    session_id: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.session_id is not None:
            result["session_id"] = self.session_id
        return result


@dataclass(frozen=True)
class SessionMapping:
    session_id: str
    repository: str
    branch: str
    captured_at: str


@dataclass
class SessionInfo:
    id: str
    title: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    transcript_path: Optional[str] = None


@dataclass(frozen=True)
class UsageRecord:
    id: str
    timestamp: Optional[str]
    session_id: str
    model: str
    source: str
    tokens: TokenMetrics
    api_duration_ms: int


@dataclass(frozen=True)
class ModelPricing:
    input_per_million: Decimal
    output_per_million: Decimal
    cache_read_per_million: Optional[Decimal] = None


@dataclass
class ToolMetrics:
    calls: int = 0
    success: int = 0
    failed: int = 0
    duration_ms: int = 0

    def add_call(self, successful: Optional[bool], duration_ms: int = 0) -> None:
        self.calls += 1
        if successful is True:
            self.success += 1
        elif successful is False:
            self.failed += 1
        self.duration_ms += max(duration_ms, 0)

    def add(self, other: "ToolMetrics") -> None:
        self.calls += other.calls
        self.success += other.success
        self.failed += other.failed
        self.duration_ms += other.duration_ms

    def as_dict(self) -> dict[str, int]:
        return {
            "calls": self.calls,
            "success": self.success,
            "failed": self.failed,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True)
class ToolCall:
    call_id: Optional[str]
    name: str
    success: Optional[bool]
    duration_ms: int
    tool_type: Optional[str] = None


@dataclass(frozen=True)
class SubagentRun:
    agent_id: str
    agent_type: Optional[str]
    parent_session_id: Optional[str]
    parent_agent_id: Optional[str]
    created_at: Optional[str]
    last_updated_at: Optional[str]
    status: Optional[str]
    name: str
    resume_count: int
    depth: int
    duration_ms: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "parent_session_id": self.parent_session_id,
            "parent_agent_id": self.parent_agent_id,
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
            "status": self.status,
            "name": self.name,
            "resume_count": self.resume_count,
            "depth": self.depth,
            "duration_ms": self.duration_ms,
        }

