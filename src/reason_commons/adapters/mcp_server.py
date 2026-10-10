"""Local stdio MCP projection of application capabilities.

Each call opens/closes one session, so an idle client holds no writer lock.
Commons names select direct children of a configured root, never arbitrary paths.
The optional official SDK owns transport/lifecycle/schema validation.
"""

import asyncio
import base64
from copy import deepcopy
from importlib.resources import files
import json
from pathlib import Path
import re

from reason_commons.adapters.invocation import procedure_text
from reason_commons.adapters.skill_agent import TOOLS as CONTRIBUTION_TOOLS
from reason_commons.adapters.rendering import workspace_output
from reason_commons.adapters.usage import session_notice
from reason_commons.bootstrap import configured_consultant, create_case, open_case, usage_session
from reason_commons.domain.model import CONSULT_INTENTS


READS = {"inspect", "workspace", "history", "sources", "receipts", "storage_help", "context"}
STRING = {"type": "string"}
CASE = {"type": "string", "description": "Existing commons folder name under the configured root; no path."}


def tool(name, description, properties=None, required=(), case=True):
    properties = deepcopy(properties or {})
    if case:
        properties["case"] = deepcopy(CASE)
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": properties,
        "required": (["case"] if case else []) + list(required), "additionalProperties": False}}


TOOLS = [tool(t["function"]["name"], t["function"]["description"],
              t["function"]["parameters"]["properties"], t["function"]["parameters"]["required"])
         for t in CONTRIBUTION_TOOLS]
# MCP clients execute the procedure themselves; all semantic application use
# cases are available independently, with explicit base/target on submission.
retain = next(t for t in TOOLS if t["name"] == "retain_input")
retain["inputSchema"]["properties"]["request_id"] = {"type": ["string", "null"]}
retain["inputSchema"]["properties"]["intent"]["enum"] = sorted({"answer"} | CONSULT_INTENTS)
submit_schema = deepcopy(retain["inputSchema"])
TOOLS += [
    {"name": "submit", "description": "Deliberately retain and consult once, with an explicit revision and target.",
     "inputSchema": submit_schema},
    tool("history", "Read published commons history offline."),
    tool("sources", "Read attributed inputs and supplied sources offline."),
    tool("receipts", "Read attempt receipts for an original retained request.", {"request_id": STRING}, ("request_id",)),
    tool("storage_help", "Read application storage guarantees offline."),
    tool("add_source", "Attach participant-supplied content. Do not invent content or attribution.",
         {"name": STRING, "content_base64": STRING, "speaker": STRING}, ("name", "content_base64", "speaker")),
    tool("export", "Export a new portable bundle under the commons root's exports folder.",
         {"bundle": {"type": "string", "description": "New filename ending .reasoncase; no path."}}, ("bundle",)),
    tool("new_case", "Create a named commons only when the participant requests creation.",
         {"name": STRING}, ("name",)),
    tool("context", "Read the owning domain glossary, capability contract and contribution procedure.", case=False),
]
# The operator's decisions about proposals. Each acts only on the participant's explicit choice;
# a "confirm" result lists what else the decision would take and changes nothing until confirmed.
REFS = {"type": "array", "items": STRING, "description": "Exact record refs the participant chose, such as C3@1."}
DECISION = {"refs": REFS, "speaker": STRING, "base_revision": {"type": "integer", "minimum": 0},
            "confirmed": {"type": "boolean"}}
TOOLS += [
    tool("accept", "Admit the participant's chosen proposals into the model, with the waiting proposals they need.",
         DECISION, ("refs", "speaker", "base_revision")),
    tool("reject", "Reject the participant's chosen proposals, with the waiting proposals that need them.",
         DECISION, ("refs", "speaker", "base_revision")),
    tool("undo", "Undo accepted records the participant chose; final. Always confirm first.",
         DECISION, ("refs", "speaker", "base_revision")),
    tool("still_holds", "Record that the participant says a flagged record still holds.",
         {"ref": STRING, "speaker": STRING, "base_revision": {"type": "integer", "minimum": 0}},
         ("ref", "speaker", "base_revision")),
    tool("set_acceptance", "Change how later proposals enter the model. Refused unless the operator started "
         "this server with --allow-acceptance-setting.",
         {"mode": {"type": "string", "enum": ["review", "automatic"]}, "speaker": STRING,
          "base_revision": {"type": "integer", "minimum": 0}}, ("mode", "speaker", "base_revision")),
]


class CaseToolBridge:
    def __init__(self, case_root, consultant, allow_acceptance_setting=False, usage=None):
        self.root = Path(case_root).resolve(strict=True)
        # The usage log session of a paid consultant: from 80% of the monthly budget, consulting results carry a
        # usage_notice for the person. It says; it never blocks, and nothing is written to stdout, the transport.
        self.usage = usage
        if not self.root.is_dir():
            raise ValueError("Commons root must be an existing directory")
        self.consultant = consultant
        # Automatic acceptance delegates the operator's decision; an agent gets it only when granted.
        self.allow_acceptance_setting = allow_acceptance_setting

    def _case(self, name):
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", name):
            raise ValueError("Use a commons folder name of letters, digits, underscores or hyphens")
        if name == "exports":
            raise ValueError("The exports folder is reserved for portable bundles")
        path = self.root / name
        if path.is_symlink() or path.resolve().parent != self.root:
            raise ValueError("Commons must be a direct folder under the configured root")
        return path

    def invoke(self, name, arguments):
        if name == "context":
            return {"domain": files("reason_commons.domain").joinpath("CONTEXT.md").read_text(encoding="utf-8"),
                    "capabilities": files("reason_commons.application").joinpath("ports.py").read_text(encoding="utf-8"),
                    "procedure": procedure_text()}
        args = deepcopy(arguments)
        path = self._case(args.pop("case"))
        if name == "new_case":
            with create_case(path, args["name"]) as app:
                return app.inspect()
        if name not in {t["name"] for t in TOOLS}:
            raise ValueError("Unknown commons capability")
        if name == "set_acceptance" and not self.allow_acceptance_setting:
            return {"status": "rejected", "message": "Only the operator changes how proposals are accepted; "
                    "this server was not granted that capability"}
        with open_case(path, consultant=self.consultant, writable=name not in READS) as app:
            if name == "export":
                bundle = args["bundle"]
                if not isinstance(bundle, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.reasoncase", bundle):
                    raise ValueError("Use a new .reasoncase filename without a path")
                exports = self.root / "exports"
                if exports.is_symlink():
                    raise ValueError("Exports directory must stay within the commons root")
                exports.mkdir(exist_ok=True)
                destination = exports / bundle
                app.export(str(destination))
                return {"status": "exported", "bundle": str(destination)}
            if name == "add_source":
                content = base64.b64decode(args.pop("content_base64"), validate=True)
                return {"source_ref": app.add_source(content=content, **args)}
            result = getattr(app, name)(**args)
            if name == "workspace":
                return workspace_output(result)
            if name in {"consult", "submit", "retry"}:
                notice = session_notice(self.usage) if self.usage is not None else None
                return {**result, **workspace_output(app.workspace(), result=result),
                        **({"usage_notice": notice} if notice else {})}
            return result


def build_server(bridge):
    try:
        import mcp.types as types
        from mcp.server.lowlevel import Server
        from jsonschema import validate
    except ImportError:
        raise RuntimeError("The MCP adapter requires Python 3.10+ and pip install '.[mcp]'") from None
    server = Server("reason-commons")

    @server.list_tools()
    async def list_tools():
        return [types.Tool(**item, annotations=types.ToolAnnotations(
                    readOnlyHint=item["name"] in READS, destructiveHint=False,
                    idempotentHint=item["name"] in READS, openWorldHint=False))
                for item in TOOLS]

    @server.call_tool(validate_input=False)
    async def call_tool(name, arguments):
        try:
            spec = next(item for item in TOOLS if item["name"] == name)
            validate(arguments, spec["inputSchema"])
            # One blocking adapter call per tool in a worker. Cancelling the
            # client doesn't start another request; retained input remains queryable.
            result = await asyncio.to_thread(bridge.invoke, name, arguments)
            failed = isinstance(result, dict) and result.get("status") in {
                "not_saved", "unavailable", "rejected", "stale"}
            structured = result if isinstance(result, dict) else {"result": result}
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(structured, ensure_ascii=False))],
                                        structuredContent=structured, isError=failed)
        except Exception as exc:
            # Do not echo exception text, which may contain paths, input or credentials.
            result = {"status": "tool_error", "failure_category": type(exc).__name__}
            return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(result))],
                                        structuredContent=result, isError=True)

    return server


def serve(case_root, model=None, base_url=None, provider=None, allow_acceptance_setting=False):
    from reason_commons.adapters.anthropic import AnthropicConsultant
    usage = usage_session("mcp")
    consultant = configured_consultant(provider=provider, model=model, base_url=base_url, usage=usage.record)
    bridge = CaseToolBridge(case_root, consultant, allow_acceptance_setting,
                            usage=usage if isinstance(consultant, AnthropicConsultant) else None)
    server = build_server(bridge)
    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())

    asyncio.run(run())
