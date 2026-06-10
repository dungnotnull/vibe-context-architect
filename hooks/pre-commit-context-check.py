#!/usr/bin/env python3
"""
hooks/pre-commit-context-check.py

Git pre-commit hook that warns when significant files change
but .ai-context/ hasn't been updated recently.

Install:
    cp hooks/pre-commit-context-check.py .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
"""
import subprocess, sys, os
from pathlib import Path
from datetime import datetime, timezone

YELLOW = "\033[93m"
GREEN  = "\033[92m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

SIGNIFICANT_PATTERNS = [
    ".prisma", "schema.sql", "package.json",
    "tsconfig.json", ".eslintrc", "drizzle.config",
    "tailwind.config", "next.config", "vite.config",
]

CONTEXT_DIR = ".ai-context"
STALE_DAYS = 14  # warn if context not updated in N days


def get_staged_files():
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True
    )
    return r.stdout.strip().splitlines() if r.returncode == 0 else []


def is_significant(filepath):
    return any(pat in filepath for pat in SIGNIFICANT_PATTERNS)


def context_age_days():
    meta = Path(CONTEXT_DIR) / ".vca-meta"
    if not meta.exists():
        return None

    mtime = meta.stat().st_mtime
    age = (datetime.now().timestamp() - mtime) / 86400
    return round(age, 1)


def main():
    staged = get_staged_files()
    if not staged:
        sys.exit(0)

    significant_changed = [f for f in staged if is_significant(f)]
    if not significant_changed:
        sys.exit(0)

    age = context_age_days()

    print(f"\n{BOLD}🧠 Vibe Context Architect{RESET}", file=sys.stderr)

    if not Path(CONTEXT_DIR).exists():
        print(f"{YELLOW}  ⚠ No .ai-context/ found.{RESET}", file=sys.stderr)
        print(f"  Significant files changed: {', '.join(significant_changed[:3])}", file=sys.stderr)
        print(f"  Consider generating your AI context layer.", file=sys.stderr)
    elif age is not None and age > STALE_DAYS:
        print(f"{YELLOW}  ⚠ .ai-context/ is {age} days old.{RESET}", file=sys.stderr)
        print(f"  Changed: {', '.join(significant_changed[:3])}", file=sys.stderr)
        print(f"  Run: {BOLD}npm run context:update{RESET} to refresh.", file=sys.stderr)
    else:
        print(f"{GREEN}  ✓ .ai-context/ is up to date ({age} days old){RESET}", file=sys.stderr)

    print("", file=sys.stderr)
    sys.exit(0)  # Never block the commit — only warn


if __name__ == "__main__":
    main()
