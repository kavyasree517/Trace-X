"""Tests for the copy lint script.

The copy lint is a repository guard rather than application logic, so these
tests check both the scan of the real repository and the behaviour of the
inline allow marker against a temporary tree.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lint_copy import ALLOW_MARKER, find_violations, run_copy_lint  # noqa: E402

MINIMAL_CONFIG = """\
[prohibited_phrases]
phrases = ["criminal exchange", "guilty"]

[exclusions]
paths = ["config/allowed.md"]
"""


def _build_tree(root: Path) -> None:
    """Create a minimal repository tree with a valid lint config."""
    (root / "scripts").mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "scripts" / "copy_lint_config.toml").write_text(MINIMAL_CONFIG, encoding="utf-8")
    (root / "config" / "allowed.md").write_text("A criminal exchange.\n", encoding="utf-8")


def test_the_real_repository_contains_no_prohibited_phrases() -> None:
    assert find_violations(REPO_ROOT) == []


def test_the_repository_lint_run_succeeds() -> None:
    assert run_copy_lint() == 0


def test_a_prohibited_phrase_in_a_scanned_file_is_reported(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    (tmp_path / "README.md").write_text(
        "Neutral text.\nThis names a criminal exchange.\n", encoding="utf-8"
    )

    violations = find_violations(tmp_path)

    assert violations == [("README.md", 2, "criminal exchange")]


def test_a_file_listed_in_the_exclusions_is_not_scanned(tmp_path: Path) -> None:
    _build_tree(tmp_path)

    assert find_violations(tmp_path) == []


def test_the_allow_marker_exempts_only_the_marked_line(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    (tmp_path / "README.md").write_text(
        f"1. Never call a service guilty. <!-- {ALLOW_MARKER} -->\n"
        f"2. Also never say guilty. <!-- {ALLOW_MARKER} -->\n"
        "3. And this line is guilty.\n",
        encoding="utf-8",
    )

    violations = find_violations(tmp_path)

    assert violations == [("README.md", 3, "guilty")]


def test_ignored_directories_are_not_scanned(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    for ignored in (".venv", "venv", "node_modules", "dist", "site-packages"):
        target = tmp_path / ignored / "lib"
        target.mkdir(parents=True)
        (target / "notes.md").write_text("guilty criminal exchange\n", encoding="utf-8")

    assert find_violations(tmp_path) == []


def test_files_without_a_scanned_extension_are_ignored(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    (tmp_path / "diagram.png").write_bytes(b"criminal exchange")
    (tmp_path / "data.bin").write_text("guilty", encoding="utf-8")

    assert find_violations(tmp_path) == []


def test_a_missing_configuration_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        find_violations(tmp_path)


def test_the_match_is_case_insensitive(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    (tmp_path / "page.md").write_text("A CRIMINAL Exchange here.\n", encoding="utf-8")

    violations = find_violations(tmp_path)

    assert violations == [("page.md", 1, "criminal exchange")]
