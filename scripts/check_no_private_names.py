#!/usr/bin/env python3
"""Leak guard for the public Scry repo.

Fails (non-zero exit) if any private/internal component or product name appears in
the tracked files. This is the public, source-available mirror; private component
names must never leak into it. Run locally (`python scripts/check_no_private_names.py`)
and in CI before every push.

Notes:
- "Diwata" (the owner/Licensor) and the GitHub org "Diwata-Domains" are allowed.
- Matching is case-insensitive and word-boundary aware, so "Diwa" does NOT flag
  "Diwata" / "Diwata-Domains".
- This file and the CI workflow are skipped (they necessarily contain the terms).
"""

from __future__ import annotations

import re
import subprocess
import sys

# Private/internal component + product names that must not appear publicly.
DENY = [
    "DAEMON", "Conclave", "Grimoire", "Chronicle",
    "Lore", "Vault", "Grain", "Pulse", "Apex",
    "Ironvale", "Aether", "Sanctum",
    "Diwa",            # word-boundary: matches "Diwa"/"Diwa Domains", not "Diwata"
    "Limitless", "WARDRIVE",
]

# Files that legitimately contain the terms (skip to avoid self-flagging).
SKIP = {
    "scripts/check_no_private_names.py",
    ".github/workflows/leak-guard.yml",
    # The BSL Additional Use Grant must name the products it exempts; "Diwa Domains"
    # there is intentional (a public brand, diwa.domains), not an internal-component leak.
    "LICENSE",
}

PATTERNS = [
    (term, re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", re.IGNORECASE))
    for term in DENY
]


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if f and f not in SKIP]


def main() -> int:
    violations: list[tuple[str, int, str, str]] = []
    for path in tracked_files():
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except (OSError, UnicodeError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for term, pat in PATTERNS:
                if pat.search(line):
                    violations.append((path, i, term, line.strip()[:120]))

    if violations:
        print("❌ Leak guard FAILED — private/internal names found in the public repo:\n")
        for path, i, term, line in violations:
            print(f"  {path}:{i}  [{term}]  {line}")
        print(f"\n{len(violations)} occurrence(s). Remove the private names before publishing.")
        return 1

    print("✅ Leak guard passed — no private/internal names in the public repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
