"""Each guarded change names its tree update, and method arguments stay well formed.

The trailer check links a commit to an argument; it does not judge the argument.
"""
from pathlib import Path
import subprocess

import pytest

from scripts.check_tree_updates import check_branch, guarded, problem, proposal_ids
from scripts.feature_arguments import load_argument, validate_argument

ROOT = Path(__file__).resolve().parents[1]
ARGUMENTS = sorted((ROOT / "docs/development/arguments").glob("*.feature"))
IDS = {"contribution-feedback"}


def test_method_arguments_are_complete_and_declare_their_proposal():
    assert ARGUMENTS
    for path in ARGUMENTS:
        text = path.read_text()
        argument = load_argument(text)
        assert validate_argument(argument, text) == [], path.name
        assert path.stem == argument["proposal_id"], "One file per proposal, named by its identity"


def test_the_repository_declares_each_argued_proposal():
    assert {"contribution-feedback", "repo-tree-discipline"} <= proposal_ids(ROOT)


def test_only_behavior_and_method_paths_are_guarded():
    assert guarded(["src/reason_commons/adapters/tui.py", "AGENTS.md", "docs/development/workflow.md",
                    "reason-commons-spec/features/15_contribution_feedback.feature"]) == [
        "src/reason_commons/adapters/tui.py", "AGENTS.md", "docs/development/workflow.md",
        "reason-commons-spec/features/15_contribution_feedback.feature"]
    assert guarded(["docs/images/home.png", "docs/tui.md", "README.md", "tests/test_tui.py"]) == []


@pytest.mark.parametrize("message", [
    "Show a receipt\n\nTree-update: contribution-feedback\n",
    "Bump textual\n\nTree-update: upkeep - dependency maintenance\n",
    "Regenerate\n\nTree-update: upkeep: screenshots after the theme fix\n",
])
def test_a_linked_or_declared_upkeep_commit_passes(message):
    assert problem(message, ["src/reason_commons/application/service.py"], IDS) is None


@pytest.mark.parametrize("message, reason", [
    ("Add a feature\n", "needs exactly one"),
    ("Add a feature\n\nTree-update: some-new-idea\n", "no argument block"),
    ("Add a feature\n\nTree-update: upkeep\n", "upkeep needs a reason"),
    ("Two links\n\nTree-update: contribution-feedback\nTree-update: upkeep - also\n", "needs exactly one"),
    ("Commented out\n\n# Tree-update: contribution-feedback\n", "needs exactly one"),
])
def test_an_unlinked_guarded_commit_is_rejected(message, reason):
    assert reason in problem(message, ["src/reason_commons/application/service.py"], IDS)


def test_unguarded_changes_need_no_trailer():
    assert problem("Fix a typo in the tutorial\n", ["docs/tutorial.md"], IDS) is None


def test_the_branch_check_reads_each_commit_after_the_base(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (tmp_path / "README.md").write_text("start\n")
    git("add", ".")
    git("commit", "-q", "-m", "Start")
    git("checkout", "-q", "-b", "work")
    argument = (ROOT / "docs/development/arguments/repo-tree-discipline.feature").read_text()
    (tmp_path / "docs/development/arguments").mkdir(parents=True)
    (tmp_path / "docs/development/arguments/repo-tree-discipline.feature").write_text(argument)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("x = 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "Argued\n\nTree-update: repo-tree-discipline")
    assert check_branch("main", root=tmp_path) == []
    (tmp_path / "src/a.py").write_text("x = 2\n")
    git("commit", "-q", "-am", "Unargued feature")
    issues = check_branch("main", root=tmp_path)
    assert len(issues) == 1 and "Unargued feature" in issues[0]
