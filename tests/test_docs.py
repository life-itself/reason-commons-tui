"""User-facing docs: every relative link and image points at a file in the repository."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *sorted((ROOT / "docs").glob("*.md"))]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")


def test_relative_links_and_images_resolve():
    missing = []
    for page in PAGES:
        text = re.sub(r"```.*?```", "", page.read_text(encoding="utf-8"), flags=re.S)
        for target in LINK.findall(text):
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue
            if not (page.parent / target.split("#")[0]).exists():
                missing.append(f"{page.relative_to(ROOT)} -> {target}")
    assert missing == []


def test_readme_pictures_are_committed():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    pictures = re.findall(r"!\[[^\]]+\]\((docs/images/[^)]+)\)", readme)
    assert len(pictures) >= 4
    assert all((ROOT / picture).stat().st_size > 1000 for picture in pictures)


def test_readme_shows_all_six_trees():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for tree in ("goal-tree", "current-reality-tree", "evaporating-cloud", "future-reality-tree",
                 "prerequisite-tree", "transition-tree"):
        assert f"](docs/images/trees/{tree}.svg)" in readme
