#!/usr/bin/env python3
"""
create_update_hook.py — Install an update hook to keep context fresh.

Modes:
  git-hook   → post-commit git hook that suggests updating context
  npm-script → adds 'context:update' script to package.json
  manual     → just prints the command to run manually

Usage:
    python scripts/create_update_hook.py --root ./my-project --mode git-hook
"""
import argparse, sys, json, stat, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import VCA_VERSION


HOOK_SCRIPT = """#!/bin/sh
# Vibe Context Architect — post-commit hook
# Reminds you to update .ai-context/ when significant files change

CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || true)

if echo "$CHANGED" | grep -qE '\\.(prisma|sql)$|schema\\.|package\\.json|tsconfig\\.json'; then
  echo ""
  echo "🧠 AI Context Update Suggested"
  echo "   Significant files changed — your .ai-context/ may be out of date."
  echo "   Run: npm run context:update"
  echo ""
fi
"""

NPM_SCRIPT = "python .vca/scripts/update_context.py --root . --since HEAD~10 --existing .ai-context/ --output .ai-context/"


def install_git_hook(root):
    hook_dir = Path(root) / ".git" / "hooks"
    if not hook_dir.exists():
        print("ERROR: No .git directory found. Initialize git first.", file=sys.stderr)
        return False

    hook_path = hook_dir / "post-commit"
    if hook_path.exists():
        answer = input("  post-commit hook exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print("  Skipped.", file=sys.stderr)
            return False

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    print(f"  ✓ Git post-commit hook installed at {hook_path}", file=sys.stderr)
    return True


def install_npm_script(root):
    pkg_path = Path(root) / "package.json"
    if not pkg_path.exists():
        print("  No package.json found. Skipping npm script.", file=sys.stderr)
        return False

    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  Could not read package.json: {e}", file=sys.stderr)
        return False

    scripts = data.setdefault("scripts", {})
    if "context:update" in scripts:
        print("  'context:update' script already exists.", file=sys.stderr)
        return True

    scripts["context:update"] = NPM_SCRIPT
    pkg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  ✓ Added 'context:update' to package.json scripts", file=sys.stderr)
    print(f"    Run: npm run context:update", file=sys.stderr)
    return True


def print_manual_instructions(root):
    print(f"""
  Manual update command:
  
    python scripts/update_context.py \\
        --root {root} \\
        --since "7 days ago" \\
        --existing .ai-context/ \\
        --output .ai-context/
  
  Add this to your workflow whenever you make major changes.
""", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["git-hook", "npm-script", "manual"],
                        default="manual")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())

    print(f"\nInstalling context update hook (mode: {args.mode})...", file=sys.stderr)

    if args.mode == "git-hook":
        install_git_hook(root)
        install_npm_script(root)
    elif args.mode == "npm-script":
        install_npm_script(root)
    else:
        print_manual_instructions(root)


if __name__ == "__main__":
    main()
