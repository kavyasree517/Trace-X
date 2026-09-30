"""Repository scan to prevent committed private keys, live tokens, or credentials."""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"etherscan(?:_api_key)?\s*=\s*['\"][A-Za-z0-9]{30,}['\"]", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*=\s*['\"][A-Za-z0-9]{32,}['\"]", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9_\-\.]{40,}", re.IGNORECASE),
]

EXCLUDED_FILES = {
    ".env.example",
    "scripts/check_secrets.py",
}


def run_secret_scan() -> int:
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

    violations: list[tuple[str, int, str]] = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        rel_posix = path.relative_to(root_dir).as_posix()
        if rel_posix in EXCLUDED_FILES or rel_posix.startswith(".env"):
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for line_no, line in enumerate(content.splitlines(), start=1):
            for pat in SECRET_PATTERNS:
                if pat.search(line):
                    violations.append((rel_posix, line_no, pat.pattern))

    if violations:
        sys.stderr.write(f"Secret scan failed with {len(violations)} match(es):\n")
        for f, l, p in violations:
            sys.stderr.write(f"  {f}:{l} matched secret pattern '{p}'\n")
        return 1

    sys.stdout.write("Secret scan check passed: no secrets detected.\n")
    return 0


if __name__ == "__main__":
    sys.exit(run_secret_scan())
