#!/usr/bin/env python3
"""
extract_git_signals.py — Mine git history for patterns.
extract_annotations.py — Mine TODO/FIXME/HACK comments.

Both utilities in one file — run with --mode git OR --mode annotations
"""
import argparse, sys, os, re, subprocess
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from utils import save_json, now_iso, SKIP_DIRS, should_skip_dir


# ── Git Signals ──────────────────────────────────────────────────────────────

def extract_git_signals(root):
    """Extract patterns from git history."""
    result = {"available": False, "root": root}

    # Check git available
    git_dir = Path(root) / ".git"
    if not git_dir.exists():
        result["reason"] = "No .git directory found"
        return result

    def git(cmd):
        try:
            r = subprocess.run(
                ["git"] + cmd, cwd=root,
                capture_output=True, text=True, timeout=10
            )
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""

    result["available"] = True

    # Recent commit messages (last 50)
    log = git(["log", "--oneline", "-50", "--no-merges"])
    messages = [line.split(" ", 1)[1] if " " in line else line for line in log.splitlines() if line]

    # Detect commit format
    conventional = sum(1 for m in messages if re.match(r"^(feat|fix|chore|docs|refactor|style|test|ci|build|perf|revert)(\(.+\))?:", m))
    ticket_prefix = sum(1 for m in messages if re.match(r"^\[?[A-Z]+-\d+\]?", m))
    imperative = sum(1 for m in messages if re.match(r"^(Add|Update|Fix|Remove|Refactor|Move|Rename|Improve|Change|Delete|Create|Implement)", m))

    if conventional > len(messages) * 0.6:
        result["commit_format"] = "Conventional Commits (feat:, fix:, chore:, etc.)"
    elif ticket_prefix > len(messages) * 0.4:
        result["commit_format"] = f"Ticket-prefixed (e.g., {messages[0][:20] if messages else 'PROJ-123'})"
    elif imperative > len(messages) * 0.5:
        result["commit_format"] = "Imperative verb (Add, Fix, Update, etc.)"
    else:
        result["commit_format"] = "Freestyle prose"

    result["sample_commits"] = messages[:5]

    # Branch naming
    branches = git(["branch", "-r"]).splitlines()
    branches = [b.strip().replace("origin/", "") for b in branches if "->" not in b]
    feature_branches = [b for b in branches if "/" in b]
    if feature_branches:
        sample = feature_branches[0]
        if sample.startswith("feature/") or sample.startswith("feat/"):
            result["branch_format"] = "feature/short-description"
        elif sample.startswith("fix/") or sample.startswith("bugfix/"):
            result["branch_format"] = "fix/short-description"
        else:
            result["branch_format"] = sample.split("/")[0] + "/..."
    else:
        result["branch_format"] = "direct branch names (no prefix)"

    # Main branch
    main = git(["symbolic-ref", "--short", "HEAD"])
    result["main_branch"] = main or "main"

    # Most changed files (last 30 days)
    changed = git(["log", "--since=30 days ago", "--name-only", "--format=", "--no-merges"])
    file_counts = Counter(f for f in changed.splitlines() if f and not f.endswith(".lock"))
    result["hot_files"] = [{"file": k, "changes": v} for k, v in file_counts.most_common(10)]

    # Contributors
    contributors = git(["shortlog", "-sn", "--no-merges", "-30"])
    result["contributor_count"] = len([l for l in contributors.splitlines() if l.strip()])

    # Project age
    first_commit_date = git(["log", "--reverse", "--format=%ar", "--max-count=1"])
    result["project_age"] = first_commit_date or "unknown"

    return result


# ── Annotation Miner ─────────────────────────────────────────────────────────

ANNOTATION_PATTERN = re.compile(
    r'(?://|#)\s*(TODO|FIXME|HACK|NOTE|TEMP|XXX|BUG|OPTIMIZE|DEPRECATED)[\s:]+(.+)',
    re.IGNORECASE
)
EXPLICIT_RULE_PATTERN = re.compile(
    r'(?://|#)\s*(don\'t|never|always|do not|avoid|must|warning|important)[\s:]+(.+)',
    re.IGNORECASE
)

SOURCE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".svelte", ".vue", ".py", ".go"}


def extract_annotations(root):
    """Mine annotation comments from source files."""
    annotations = []
    explicit_rules = []
    root_path = Path(root)

    file_count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            file_count += 1
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                rel = str(fpath.relative_to(root_path))
                for i, line in enumerate(content.splitlines(), 1):
                    # Annotations
                    m = ANNOTATION_PATTERN.search(line)
                    if m:
                        annotations.append({
                            "type": m.group(1).upper(),
                            "text": m.group(2).strip()[:200],
                            "file": rel,
                            "line": i,
                        })
                    # Explicit rules
                    m2 = EXPLICIT_RULE_PATTERN.search(line)
                    if m2:
                        rule_type = m2.group(1).lower()
                        rule_text = m2.group(2).strip()[:200]
                        if len(rule_text) > 10:  # filter noise
                            explicit_rules.append({
                                "type": rule_type,
                                "text": rule_text,
                                "file": rel,
                                "line": i,
                            })
            except Exception:
                continue

    # Classify annotations by type
    by_type = {}
    for a in annotations:
        by_type.setdefault(a["type"], []).append(a)

    # Identify anti-patterns from FIXMEs and HACKs
    anti_pattern_candidates = []
    for a in annotations:
        if a["type"] in ("FIXME", "HACK", "TEMP", "BUG"):
            anti_pattern_candidates.append({
                "source": a["type"],
                "description": a["text"],
                "file": a["file"],
                "line": a["line"],
            })

    # Identify explicit prohibitions
    prohibitions = [r for r in explicit_rules if r["type"] in ("don't", "never", "do not", "avoid")]
    requirements = [r for r in explicit_rules if r["type"] in ("always", "must")]

    return {
        "extracted_at": now_iso(),
        "files_scanned": file_count,
        "total_annotations": len(annotations),
        "by_type": {k: v[:10] for k, v in by_type.items()},  # limit per type
        "anti_pattern_candidates": anti_pattern_candidates[:20],
        "prohibitions": prohibitions[:15],
        "requirements": requirements[:15],
        "all_annotations": annotations[:50],
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract git signals OR annotations")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["git", "annotations"], default="git")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())

    if args.mode == "git":
        print("Extracting git signals...", file=sys.stderr)
        result = extract_git_signals(root)
        print(f"  Commit format: {result.get('commit_format', 'unknown')}", file=sys.stderr)
        print(f"  Hot files: {len(result.get('hot_files', []))}", file=sys.stderr)
    else:
        print("Mining annotation comments...", file=sys.stderr)
        result = extract_annotations(root)
        print(f"  Annotations found: {result['total_annotations']}", file=sys.stderr)
        print(f"  Anti-pattern candidates: {len(result['anti_pattern_candidates'])}", file=sys.stderr)
        print(f"  Explicit prohibitions: {len(result['prohibitions'])}", file=sys.stderr)

    save_json(result, args.output)


if __name__ == "__main__":
    main()
