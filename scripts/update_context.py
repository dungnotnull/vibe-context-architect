#!/usr/bin/env python3
"""
update_context.py — Incrementally update .ai-context/ based on recent changes.

Usage:
    python scripts/update_context.py \
        --root ./my-project \
        --since "7 days ago" \
        --existing .ai-context/ \
        --output .ai-context/
"""
import argparse, sys, subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_json, save_text, now_date


def get_changed_files(root, since):
    """Get files changed since a git ref or date."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", since, "HEAD"],
            cwd=root, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        pass
    return []


def update_session_starter(existing_path, new_antipatterns=None):
    """Add a timestamp note to SESSION-STARTER indicating it was updated."""
    path = Path(existing_path)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    # Add update notice at top if not already there
    update_line = f"<!-- Updated: {now_date()} -->\n"
    if "<!-- Updated:" not in content:
        content = update_line + content
    else:
        import re
        content = re.sub(r"<!-- Updated: [\d-]+ -->", update_line.strip(), content)
    path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Incrementally update context files")
    parser.add_argument("--root", required=True)
    parser.add_argument("--since", default="7 days ago",
                        help="Git ref or date string, e.g. 'HEAD~10' or '7 days ago'")
    parser.add_argument("--existing", required=True,
                        help="Existing .ai-context/ directory")
    parser.add_argument("--output", required=True,
                        help="Output directory (can be same as --existing)")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())
    existing = Path(args.existing)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    print(f"\n🔄 Incremental context update", file=sys.stderr)
    print(f"   Since: {args.since}", file=sys.stderr)

    changed = get_changed_files(root, args.since)
    print(f"   Changed files: {len(changed)}", file=sys.stderr)

    if not changed:
        print("   No changes detected. Context is up to date.", file=sys.stderr)
        sys.exit(0)

    # Categorize changes
    schema_changes = [f for f in changed if "schema" in f.lower() or f.endswith(".prisma")]
    config_changes = [f for f in changed if any(f.endswith(x) for x in [".json", ".yaml", ".yml", ".toml"])]
    source_changes = [f for f in changed if any(f.endswith(x) for x in [".ts", ".tsx", ".js", ".jsx"])]

    print(f"\n   Schema changes:  {len(schema_changes)}", file=sys.stderr)
    print(f"   Config changes:  {len(config_changes)}", file=sys.stderr)
    print(f"   Source changes:  {len(source_changes)}", file=sys.stderr)

    # Build update summary
    lines = [
        f"# Update Log — {now_date()}",
        "",
        f"Incremental context update (since: {args.since})",
        "",
        f"## Changed Files ({len(changed)} total)",
        "",
    ]
    for f in changed[:20]:
        lines.append(f"- `{f}`")
    if len(changed) > 20:
        lines.append(f"- *(and {len(changed) - 20} more)*")

    lines += [
        "",
        "## Update Actions",
        "",
        "- [ ] Review CONTEXT.md — directory structure may have changed",
        "- [ ] Review PATTERNS.md — new patterns may have emerged",
        "- [ ] Review ANTI-PATTERNS.md — new FIXMEs or HACKs found",
        "- [ ] Review DECISIONS.md — add ADRs for new architectural choices",
        "",
        "## Files That May Need Manual Review",
        "",
    ]

    if schema_changes:
        lines.append(f"- ⚠️ **Schema changed** — update CONTEXT.md data models section")
        for f in schema_changes:
            lines.append(f"  - `{f}`")
    if config_changes:
        lines.append(f"- ⚠️ **Config changed** — update STYLE.md or DECISIONS.md if needed")
    if source_changes:
        lines.append(f"- 💡 **Source changed** — consider updating PATTERNS.md with new patterns")

    update_log = "\n".join(lines)
    save_text(update_log, str(output / "UPDATE-LOG.md"))

    # Update SESSION-STARTER timestamp
    starter_path = existing / "SESSION-STARTER.md"
    if starter_path.exists():
        update_session_starter(str(starter_path))
        print(f"  ✓ Updated SESSION-STARTER.md timestamp", file=sys.stderr)

    print(f"\n  📋 Update log written to: {output}/UPDATE-LOG.md", file=sys.stderr)
    print(f"  Review UPDATE-LOG.md and manually update context files as needed.", file=sys.stderr)


if __name__ == "__main__":
    main()
