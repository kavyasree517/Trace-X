"""Repository scan to reject non-ASCII characters, emojis, and decorative symbols."""

from __future__ import annotations

import sys
import unicodedata
from pathlib import Path


def is_prohibited_char(char: str) -> bool:
    """Return True if character is non-ASCII or belongs to emoji/symbol category."""
    codepoint = ord(char)
    # Require pure ASCII (codepoint < 128)
    if codepoint >= 128:
        return True
    category = unicodedata.category(char)
    # Prohibit control characters except standard whitespace
    if category.startswith("C") and char not in "\n\r\t":
        return True
    return False


def run_character_scan() -> int:
    root_dir = Path(__file__).resolve().parent.parent
    ignored_dirs = {
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "dist",
        ".pytest_cache",
        "pgdata",
        "__pycache__",
        "venv",
        ".venv"
    }

    target_extensions = {
        ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md",
        ".toml", ".ini", ".yml", ".yaml", ".txt", ".html", ".css", ".mako"
    }

    violations: list[tuple[str, int, int, str, int]] = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.suffix.lower() not in target_extensions:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            violations.append((path.relative_to(root_dir).as_posix(), 0, 0, "binary/non-utf8", 0))
            continue
        except OSError:
            continue

        lines = content.splitlines()
        for line_no, line in enumerate(lines, start=1):
            for col_no, char in enumerate(line, start=1):
                if is_prohibited_char(char):
                    rel_path = path.relative_to(root_dir).as_posix()
                    violations.append((rel_path, line_no, col_no, char, ord(char)))

    if violations:
        sys.stderr.write(
            f"Character scan failed with {len(violations)} non-ASCII or prohibited symbol(s):\n"
        )
        for rel_path, line_no, col_no, char, code in violations[:50]:
            sys.stderr.write(
                f"  {rel_path}:{line_no}:{col_no} -> character U+{code:04X} ('{char}')\n"
            )
        if len(violations) > 50:
            sys.stderr.write(f"  ... and {len(violations) - 50} more\n")
        return 1

    sys.stdout.write("Character scan check passed: all tracked files are pure ASCII.\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_character_scan())
