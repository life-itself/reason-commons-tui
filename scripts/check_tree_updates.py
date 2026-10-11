#!/usr/bin/env python3
"""Check that each commit touching guarded paths names its tree update.

A guarded commit ends with `Tree-update: <proposal-id>`, naming an argument block
in the repository, or `Tree-update: upkeep - <reason>`. This checks that the link
is declared and resolves; it does not judge the argument. See
docs/development/tree-updates.md.
"""
import argparse
from fnmatch import fnmatch
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# Paths whose change alters behavior, scope or the development method.
GUARDED = ("src/*", "skills/*", "reason-commons-spec/*", "tests/conversation/features/*", "scripts/*",
           "AGENTS.md", "CLAUDE.md", "docs/development/*", ".workflow.json", ".githooks/*", "pyproject.toml")
ARGUMENT_ROOTS = ("reason-commons-spec/features", "tests/conversation/features", "docs/development/arguments")
TRAILER = re.compile(r"^Tree-update:[ \t]*(.*?)[ \t]*$", re.M)
UPKEEP = re.compile(r"upkeep\s*[-:—]\s*\S")
PROPOSAL = re.compile(r"^# (?:rc-argument: schema 1 \| proposal |proposal_id: )([a-z][a-z0-9_-]*)", re.M)


def guarded(paths):
    return [path for path in paths if any(fnmatch(path, pattern) for pattern in GUARDED)]


def proposal_ids(root=ROOT):
    """Proposal identities declared by argument blocks; the gate validates their content."""
    ids = set()
    for folder in ARGUMENT_ROOTS:
        for path in sorted((Path(root) / folder).glob("*.feature")):
            text = path.read_text()
            if "# RC-ARGUMENT-BEGIN" in text:
                ids.update(PROPOSAL.findall(text))
    return ids


def problem(message, paths, ids):
    """Why this commit's tree link is missing or unresolved, or None."""
    touched = guarded(paths)
    if not touched:
        return None
    trailers = TRAILER.findall("\n".join(line for line in message.splitlines() if not line.startswith("#")))
    if len(trailers) != 1:
        return (f"touches {', '.join(touched[:3])}{' ...' if len(touched) > 3 else ''} and needs exactly one "
                "'Tree-update: <proposal-id>' or 'Tree-update: upkeep - <reason>' trailer")
    value = trailers[0]
    if value.startswith("upkeep"):
        return None if UPKEEP.match(value) else "upkeep needs a reason: 'Tree-update: upkeep - <reason>'"
    if value not in ids:
        return f"Tree-update names '{value}', which no argument block in the repository declares"
    return None


def git(*args, root=ROOT):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def check_message(path, root=ROOT):
    """commit-msg hook: the staged change and the message being written."""
    if subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=root, capture_output=True).returncode == 0:
        return []
    paths = git("diff", "--cached", "--name-only", root=root).split()
    issue = problem(Path(path).read_text(), paths, proposal_ids(root))
    return [issue] if issue else []


def check_branch(base, root=ROOT):
    """Every non-merge commit after the base."""
    issues = []
    for sha in git("rev-list", "--no-merges", "--reverse", f"{base}..HEAD", root=root).split():
        paths = git("diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha, root=root).split()
        issue = problem(git("log", "-1", "--format=%B", sha, root=root), paths, proposal_ids(root))
        if issue:
            issues.append(f"{sha[:9]} {git('log', '-1', '--format=%s', sha, root=root).strip()}: {issue}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="main", help="check commits after this ref (default: main)")
    parser.add_argument("--commit-msg", metavar="FILE", help="check a commit being made (the commit-msg hook)")
    options = parser.parse_args()
    if options.commit_msg:
        issues = check_message(options.commit_msg)
    else:
        base = options.base
        if subprocess.run(["git", "rev-parse", "-q", "--verify", base], cwd=ROOT, capture_output=True).returncode:
            base = f"origin/{base}"
        issues = check_branch(base)
    for issue in issues:
        print(f"FAIL: {issue}", file=sys.stderr)
    if issues:
        print("Every guarded change names its tree update; see docs/development/tree-updates.md.", file=sys.stderr)
        return 1
    if not options.commit_msg:
        print(f"PASS: every guarded commit after {base} names a tree update")
    return 0


if __name__ == "__main__":
    sys.exit(main())
