#!/usr/bin/env python3
"""
install_context.py — Write generated .ai-context/ files to project directory.

Usage:
    python scripts/install_context.py --source /tmp/vca/output/ --target ./my-project/.ai-context/
"""
import argparse, sys, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import VCA_VERSION


def main():
    parser = argparse.ArgumentParser(description="Install context files to project")
    parser.add_argument("--source", required=True, help="Generated files directory")
    parser.add_argument("--target", required=True, help="Target .ai-context/ directory")
    parser.add_argument("--force", action="store_true", help="Overwrite without asking")
    args = parser.parse_args()

    src = Path(args.source)
    tgt = Path(args.target)

    if not src.exists():
        print(f"ERROR: Source directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    tgt.mkdir(parents=True, exist_ok=True)

    files_written = []
    files_skipped = []

    for f in sorted(src.glob("*.md")):
        dest = tgt / f.name
        if dest.exists() and not args.force:
            answer = input(f"  Overwrite {dest.name}? [y/N] ").strip().lower()
            if answer != "y":
                files_skipped.append(f.name)
                continue
        shutil.copy2(f, dest)
        files_written.append(f.name)
        print(f"  ✓ {f.name}", file=sys.stderr)

    # Write a .vca-meta file to track version
    meta = tgt / ".vca-meta"
    meta.write_text(f"version={VCA_VERSION}\ninstalled=yes\n")

    print(f"\n  Installed {len(files_written)} files to {tgt}", file=sys.stderr)
    if files_skipped:
        print(f"  Skipped: {', '.join(files_skipped)}", file=sys.stderr)


if __name__ == "__main__":
    main()
