"""Copy lint script to detect prohibited phrases across the repository.

A line may opt out with an inline ``copy-lint: allow`` marker when it has to
quote a prohibited phrase in order to prohibit it, for example inside the
README claims-to-avoid list. The marker is an HTML comment in Markdown so it
does not render.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


ALLOW_MARKER = "copy-lint: allow"


def find_violations(root_dir: Path) -> list[tuple[str, int, str]]:
    """Return every prohibited phrase occurrence under ``root_dir``.

    Each violation is a ``(relative_path, line_number, phrase)`` tuple.
    """
    config_path = root_dir / "scripts" / "copy_lint_config.toml"

    if not config_path.exists():
        raise FileNotFoundError("Configuration file copy_lint_config.toml not found")

    with config_path.open("rb") as f:
        config = tomllib.load(f)

    prohibited = [p.lower() for p in config.get("prohibited_phrases", {}).get("phrases", [])]
    excluded_paths = [Path(p) for p in config.get("exclusions", {}).get("paths", [])]

    excluded_set = {str((root_dir / p).resolve()).lower() for p in excluded_paths}

    violations: list[tuple[str, int, str]] = []

    target_extensions = {".py", ".ts", ".tsx", ".html", ".md", ".json", ".txt"}
    ignored_dirs = {
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "node_modules",
        "dist",
        "build",
        "pgdata",
        ".venv",
        "venv",
        "site-packages",
    }

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.suffix.lower() not in target_extensions:
            continue
        if str(path.resolve()).lower() in excluded_set:
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for idx, line in enumerate(content.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            lower_line = line.lower()
            for phrase in prohibited:
                if phrase in lower_line:
                    violations.append((path.relative_to(root_dir).as_posix(), idx, phrase))

    return violations


def run_copy_lint() -> int:
    """Lint the real repository and report the result."""
    root_dir = Path(__file__).resolve().parent.parent

    try:
        violations = find_violations(root_dir)
    except FileNotFoundError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    if violations:
        sys.stderr.write(f"Copy lint failed with {len(violations)} prohibited phrase occurrence(s):\n")
        for file_path, line_no, phrase in violations:
            sys.stderr.write(f"  {file_path}:{line_no} -> prohibited phrase '{phrase}'\n")
        return 1

    sys.stdout.write("Copy lint check passed with zero prohibited phrases found.\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_copy_lint())
