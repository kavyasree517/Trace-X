"""Copy lint script to detect prohibited phrases across the repository."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


def run_copy_lint() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "scripts" / "copy_lint_config.toml"

    if not config_path.exists():
        sys.stderr.write("Configuration file copy_lint_config.toml not found\n")
        return 1

    with config_path.open("rb") as f:
        config = tomllib.load(f)

    prohibited = [p.lower() for p in config.get("prohibited_phrases", {}).get("phrases", [])]
    excluded_paths = [Path(p) for p in config.get("exclusions", {}).get("paths", [])]

    # Normalize exclusions relative to root
    excluded_set = {str((root_dir / p).resolve()).lower() for p in excluded_paths}

    violations: list[tuple[str, int, str]] = []

    target_extensions = {".py", ".ts", ".tsx", ".html", ".md", ".json", ".txt"}
    ignored_dirs = {".git", ".mypy_cache", ".ruff_cache", "node_modules", "dist", ".pytest_cache", "pgdata"}

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

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            lower_line = line.lower()
            for phrase in prohibited:
                if phrase in lower_line:
                    rel_path = path.relative_to(root_dir).as_posix()
                    violations.append((rel_path, idx, phrase))

    if violations:
        sys.stderr.write(f"Copy lint failed with {len(violations)} prohibited phrase occurrence(s):\n")
        for file_path, line_no, phrase in violations:
            sys.stderr.write(f"  {file_path}:{line_no} -> prohibited phrase '{phrase}'\n")
        return 1

    sys.stdout.write("Copy lint check passed with zero prohibited phrases found.\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_copy_lint())
