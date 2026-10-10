"""Official SDK client/server handshake and real stdio contribution/recovery."""

import asyncio
from datetime import timedelta
import sys

import pytest

pytest.importorskip("mcp", reason="Optional MCP SDK requires Python 3.10+ and the mcp extra")
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from reason_commons.bootstrap import open_case
from tests.support import ROOT
from tests.test_invocation import skill_server


def test_real_stdio_tools_retention_failure_retry_and_restart(skill_server, tmp_path):
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "reason_commons", "mcp",
        "--commons-root", str(tmp_path), "--model", "fixture-model", "--base-url", skill_server.url],
        cwd=str(ROOT))

    async def run():
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=15)) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert next(t for t in tools if t.name == "inspect").annotations.readOnlyHint
                assert next(t for t in tools if t.name == "workspace").annotations.readOnlyHint
                assert not next(t for t in tools if t.name == "retain_input").annotations.readOnlyHint
                created = await session.call_tool("new_case", {"case": "payments", "name": "Payments"})
                assert not created.isError and created.structuredContent["case"]["revision"] == 0
                opened = await session.call_tool("workspace", {"case": "payments"})
                assert opened.structuredContent["workspace"]["question"] is None
                assert skill_server.consult_calls == 0
                invalid = await session.call_tool("retain_input", {"case": "payments", "text": "literal", "speaker": "Sam",
                    "base_revision": 0})
                assert invalid.isError
                retained = await session.call_tool("retain_input", {"case": "payments", "text": "5\n:options\n", "speaker": "Sam",
                    "base_revision": 0, "response_target": None})
                request_id = retained.structuredContent["request_id"]
                skill_server.fail_consult = True
                failed = await session.call_tool("consult", {"case": "payments", "request_id": request_id})
                assert failed.isError and failed.structuredContent["status"] == "unavailable"
                assert failed.structuredContent["workspace"]["pending_requests"][0]["status"] == "unavailable"
                assert skill_server.consult_calls == 1
        # Reconnect from a fresh server process; recovery has no hidden host state.
        skill_server.fail_consult = False
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                saved = await session.call_tool("retry", {"case": "payments", "request_id": request_id})
                assert not saved.isError and saved.structuredContent["status"] == "saved"
                assert saved.structuredContent["workspace"]["question"]["ref"] == "I1@1"
                assert "What should we observe next?" in saved.structuredContent["rendered"]["markdown"]
                explained = await session.call_tool("workspace", {"case": "payments", "view": "explain"})
                assert "Keep the next move bounded." in explained.structuredContent["rendered"]["text"]
                again = await session.call_tool("retry", {"case": "payments", "request_id": request_id})
                assert again.structuredContent["already_applied"] and skill_server.consult_calls == 2
                rejected = await session.call_tool("new_case", {"case": "../outside", "name": "No"})
                assert rejected.isError
                with open_case(tmp_path / "payments") as app:
                    assert app.sources()["sources"][request_id]["text"] == "5\n:options\n"
                    assert app.inspect()["case"]["revision"] == 1
    asyncio.run(run())
