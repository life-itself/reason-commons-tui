"""The development method is only useful to an agent while what it cites is real.

These checks keep the agent entry points wired to the method documents, and keep
every repository path and relative link they mention pointing at something that
exists. They check references, not prose.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [ROOT / "AGENTS.md", *sorted((ROOT / "docs/development").glob("*.md"))]
EXPECTED = {"README.md", "architecture-principles.md", "testing-strategy.md", "workflow.md", "recipes.md"}


def exists(reference):
    # Documents cite source files relative to the package as well as the repository.
    return any((base / reference).exists() for base in (ROOT, ROOT / "src/reason_commons"))


def test_the_method_documents_exist():
    assert EXPECTED <= {path.name for path in (ROOT / "docs/development").glob("*.md")}


def test_agent_entry_points_lead_to_the_method():
    agents = (ROOT / "AGENTS.md").read_text()
    assert "docs/development/README.md" in agents
    claude = (ROOT / "CLAUDE.md").read_text()
    assert "@AGENTS.md" in claude, "Claude Code reads CLAUDE.md; it must import AGENTS.md"
    overview = (ROOT / "docs/development/README.md").read_text()
    for name in EXPECTED - {"README.md"}:
        assert name in overview, f"The overview does not link {name}"


def test_cited_repository_paths_exist():
    missing = []
    for document in DOCUMENTS:
        for token in re.findall(r"`([^`\s]+)`", document.read_text()):
            if "/" not in token or re.search(r"[*<>${}=:|]", token) or token.startswith(("-", "http", "/")):
                continue
            if not exists(token.rstrip("/")):
                missing.append(f"{document.relative_to(ROOT)}: {token}")
    assert not missing, "Documents cite paths that do not exist:\n" + "\n".join(missing)


def test_relative_links_resolve():
    broken = []
    for document in DOCUMENTS:
        for target in re.findall(r"\]\(([^)\s]+)\)", document.read_text()):
            if target.startswith(("http", "#", "mailto:")):
                continue
            path = target.split("#")[0]
            if path and not (document.parent / path).exists():
                broken.append(f"{document.relative_to(ROOT)}: {target}")
    assert not broken, "Broken links:\n" + "\n".join(broken)


def test_the_workflow_manifest_owns_the_method_and_conversation_scenarios():
    import json
    ownership = json.loads((ROOT / ".workflow.json").read_text())["ownership"]
    assert "tests/conversation/features/**" in ownership["conversation_acceptance"]
    assert "docs/development/**" in ownership["development_method"]
