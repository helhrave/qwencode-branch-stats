from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sdd_metrics.git import current_context
from sdd_metrics.hooks.session_end import session_end
from sdd_metrics.mappings import MappingStore
from sdd_metrics.qwen.paths import QwenPaths
from sdd_metrics.reports.json_report import write_json_report
from sdd_metrics.reports.markdown_report import write_markdown_report
from sdd_metrics.service import collect_metrics


SESSION_1 = "18697f75-6ead-472a-b700-18afb74ab2a2"
SESSION_2 = "a1b2c3d4-0000-4000-8000-000000000000"
SECRETS = [
    "SECRET_PROMPT_123",
    "SECRET_RESPONSE_123",
    "SECRET_REASONING_123",
    "SECRET_TOOL_ARGUMENT_123",
    "SECRET_TOOL_RESULT_123",
    "SECRET_API_KEY_123",
]


def write_jsonl(path: Path, rows: list[object], malformed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        if malformed:
            handle.write("{not-json\n")


class SddMetricsIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "репозиторий"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "feature/test"], cwd=self.repo, check=True)
        self.qwen_root = self.root / "qwen"
        self.data_root = self.root / "data"
        self.output = self.root / "output"
        self.project = self.qwen_root / "projects" / "project-unicode"
        self.store = MappingStore(self.data_root)

        (self.qwen_root / "settings.json").parent.mkdir(parents=True, exist_ok=True)
        (self.qwen_root / "settings.json").write_text(json.dumps({
            "modelPricing": {
                "model-a": {"inputPerMillionTokens": 2, "outputPerMillionTokens": 4},
                "model-b": {"inputPerMillionTokens": 10, "outputPerMillionTokens": 20},
            },
            "apiKey": "SECRET_API_KEY_123",
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def capture(self, session_id: str) -> None:
        session_end(session_id, cwd=self.repo, store=self.store)

    def fixture(self) -> None:
        chat_1 = [
            {"timestamp": "2026-09-17T10:00:00Z", "role": "user", "content": "SECRET_PROMPT_123"},
            {"timestamp": "2026-09-17T10:01:00Z", "type": "system", "subtype": "custom_title", "title": "Old title"},
            {"timestamp": "2026-09-17T10:02:00Z", "role": "assistant", "content": "SECRET_RESPONSE_123", "reasoning": "SECRET_REASONING_123"},
            {"timestamp": "2026-09-17T10:03:00Z", "type": "system", "subtype": "custom_title", "title": "SESSION_TITLE_123"},
            {"timestamp": "2026-09-17T10:04:00Z", "event": "qwen-code.tool_call", "data": {
                "call_id": "tool-1", "function_name": "run_shell_command", "duration_ms": 120,
                "status": "success", "arguments": "SECRET_TOOL_ARGUMENT_123", "result": "SECRET_TOOL_RESULT_123",
            }},
            {"timestamp": "2026-09-17T10:05:00Z", "event": "qwen-code.tool_call", "data": {
                "call_id": "mcp-1", "function_name": "mcp__gitlab__get_version", "duration_ms": 20,
                "execution_status": "failed", "tool_type": "mcp",
            }},
        ]
        chat_2 = [
            {"timestamp": "2026-09-18T11:00:00Z", "role": "user", "content": "second"},
            {"timestamp": "2026-09-18T11:01:00Z", "event": "qwen-code.tool_call", "data": {
                "call_id": "tool-2", "function_name": "glob", "duration_ms": 10, "success": True,
            }},
        ]
        write_jsonl(self.project / "chats" / f"{SESSION_1}.jsonl", chat_1)
        write_jsonl(self.project / "chats" / f"{SESSION_2}.jsonl", chat_2, malformed=True)

        subdir = self.project / "subagents" / SESSION_1
        subdir.mkdir(parents=True)
        (subdir / "agent-1.meta.json").write_text(json.dumps({
            "agentId": "agent-1", "agentType": "general-purpose", "subagentName": "general-purpose",
            "parentSessionId": SESSION_1, "parentAgentId": None, "depth": 1, "resumeCount": 0,
            "createdAt": "2026-09-17T10:02:00Z", "lastUpdatedAt": "2026-09-17T10:02:05Z",
            "status": "completed",
        }), encoding="utf-8")
        (subdir / "agent-2.meta.json").write_text(json.dumps({
            "agentId": "agent-2", "agentType": "general-purpose", "subagentName": "general-purpose",
            "parentSessionId": SESSION_1, "parentAgentId": "agent-1", "depth": 2, "resumeCount": 1,
            "createdAt": "2026-09-17T10:02:02Z", "lastUpdatedAt": "2026-09-17T10:02:04Z",
            "status": "completed",
        }), encoding="utf-8")
        write_jsonl(subdir / "agent-1.jsonl", [{
            "type": "tool_call", "call_id": "sub-tool-1", "name": "read_file",
            "status": "success", "duration_ms": 30, "arguments": "SECRET_TOOL_ARGUMENT_123",
        }, {
            "role": "assistant", "tool_calls": [{
                "id": "sub-tool-2", "type": "function", "function": {
                    "name": "write_file", "arguments": "SECRET_TOOL_ARGUMENT_123"
                }
            }]
        }])

        usage = [
            {"id": "u1", "timestamp": "2026-09-17T10:00:10Z", "sessionId": SESSION_1,
             "model": "model-a", "source": "main", "inputTokens": 1_000_000,
             "cachedTokens": 400_000, "outputTokens": 10_000, "thoughtsTokens": 500,
             "totalTokens": 1_010_000, "apiDurationMs": 1000},
            {"id": "u2", "timestamp": "2026-09-17T10:02:10Z", "sessionId": SESSION_1,
             "model": "model-b", "source": "general-purpose", "inputTokens": 100_000,
             "cachedTokens": 10_000, "outputTokens": 2_000, "thoughtsTokens": 200,
             "totalTokens": 102_000, "apiDurationMs": 2000},
            {"id": "u2", "timestamp": "2026-09-17T10:02:10Z", "sessionId": SESSION_1,
             "model": "model-b", "source": "general-purpose", "inputTokens": 100_000,
             "outputTokens": 2_000, "totalTokens": 102_000, "apiDurationMs": 2000},
            {"id": "u3", "timestamp": "2026-09-18T11:00:10Z", "sessionId": SESSION_2,
             "model": "unpriced", "source": "main", "inputTokens": 10,
             "outputTokens": 5, "totalTokens": 15, "apiDurationMs": 50},
        ]
        write_jsonl(self.qwen_root / "usage" / "token-usage-2026-09.jsonl", usage, malformed=True)

    def test_full_report_and_privacy(self) -> None:
        self.fixture()
        self.capture(SESSION_1)
        self.capture(SESSION_2)
        metrics = collect_metrics(current_context(self.repo), QwenPaths(self.qwen_root), self.store)

        self.assertEqual(metrics["task"]["session_count"], 2)
        self.assertEqual(metrics["totals"]["requests"], 3)  # duplicate u2 ignored
        self.assertEqual(metrics["totals"]["tokens"]["cached_input"], 410_000)
        self.assertIsNone(metrics["totals"]["cost"])
        self.assertEqual(metrics["totals"]["tool_calls"], 5)
        self.assertEqual(metrics["totals"]["mcp_calls"], 1)
        self.assertEqual(metrics["totals"]["subagent_runs"], 2)
        self.assertEqual(metrics["totals"]["subagent_duration_ms"], 7_000)

        first = next(item for item in metrics["sessions"] if item["id"] == SESSION_1)
        self.assertEqual(first["title"], "SESSION_TITLE_123")
        self.assertEqual(len(first["models"]), 2)
        self.assertEqual(first["tools"]["run_shell_command"]["success"], 1)
        self.assertEqual(first["mcp"]["gitlab"]["get_version"]["failed"], 1)
        agent = next(item for item in metrics["agents"] if item["name"] == "general-purpose")
        self.assertEqual(agent["runs"], 2)
        self.assertAlmostEqual(agent["cost"], 1.04)
        warning_codes = {item["code"] for item in metrics["warnings"]}
        self.assertIn("pricing_missing", warning_codes)
        self.assertIn("malformed_jsonl", warning_codes)

        write_json_report(metrics, self.output / "report.json")
        write_markdown_report(metrics, self.output / "report.md")
        combined = (self.output / "report.json").read_text(encoding="utf-8")
        combined += (self.output / "report.md").read_text(encoding="utf-8")
        self.assertIn("SESSION_TITLE_123", combined)
        for secret in SECRETS:
            self.assertNotIn(secret, combined)

    def test_atomic_mapping_replaces_same_session(self) -> None:
        self.capture(SESSION_1)
        self.capture(SESSION_1)
        context = current_context(self.repo)
        mappings, errors = self.store.find(context.repository, context.branch)
        self.assertFalse(errors)
        self.assertEqual([item.session_id for item in mappings], [SESSION_1])

    def test_idempotent_totals(self) -> None:
        self.fixture()
        self.capture(SESSION_1)
        context = current_context(self.repo)
        first = collect_metrics(context, QwenPaths(self.qwen_root), self.store)
        second = collect_metrics(context, QwenPaths(self.qwen_root), self.store)
        self.assertEqual(first["totals"], second["totals"])
        self.assertEqual(first["models"], second["models"])

    def test_missing_transcript_is_warning(self) -> None:
        self.capture(SESSION_1)
        metrics = collect_metrics(current_context(self.repo), QwenPaths(self.qwen_root), self.store)
        self.assertEqual(metrics["task"]["session_count"], 1)
        self.assertIn("transcript_missing", {item["code"] for item in metrics["warnings"]})


if __name__ == "__main__":
    unittest.main()
