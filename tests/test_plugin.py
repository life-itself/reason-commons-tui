"""The Claude Code plugin installs the one packaged skill and the MCP server with the host consultant."""

import json
import shlex
from pathlib import Path

from tests.support import ROOT

PLUGIN = ROOT / "plugins" / "reason-commons"


def test_the_marketplace_offers_the_plugin_from_this_repository():
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entry, = marketplace["plugins"]
    assert entry["source"] == "./plugins/reason-commons" and (ROOT / entry["source"]).resolve() == PLUGIN.resolve()
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert entry["name"] == manifest["name"] == "reason-commons"


def test_the_plugin_skill_is_the_packaged_skill_not_a_copy():
    link = PLUGIN / "skills" / "reason-commons-contribute"
    assert link.is_symlink()
    packaged = ROOT / "src" / "reason_commons" / "adapters" / "contribution_skill"
    assert link.resolve() == packaged.resolve()
    assert (link / "SKILL.md").read_text().startswith("---\nname: reason-commons-contribute\n")


def test_the_plugin_server_uses_the_host_consultant_in_the_workspace_folder():
    server = json.loads((PLUGIN / ".mcp.json").read_text())["mcpServers"]["reason-commons"]
    assert server["command"] == "sh" and server["args"][0] == "-c"
    script = server["args"][1]
    # Claude Code expands ${VAR} in a plugin's arguments itself; the script leaves every variable to sh.
    assert "${" not in script
    assert '"$HOME/.local/bin' in script and 'root="$REASON_COMMONS_HOME"' in script and 'root="$HOME/ReasonCommons"' in script
    command = shlex.split(script.split("exec ", 1)[1])
    assert command[:3] == ["uvx", "--from", "reason-commons[mcp] @ git+https://github.com/life-itself/reason-commons-tui"]
    assert command[3:] == ["reason-commons", "mcp", "--commons-root", "$root", "--provider", "host"]
