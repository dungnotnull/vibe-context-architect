"""utils.py — Shared utilities for Vibe Context Architect scripts"""
import json, sys, os
from pathlib import Path
from datetime import datetime, timezone

VCA_VERSION = "1.0"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path, pretty=True):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2 if pretty else None, default=str)
    print(f"  → Saved: {path}", file=sys.stderr)

def save_text(text, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  → Saved: {path}", file=sys.stderr)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def now_date():
    return datetime.now().strftime("%Y-%m-%d")

def ensure_workspace(workspace=None):
    ws = workspace or os.environ.get("VCA_WORKSPACE", "/tmp/vca")
    Path(ws).mkdir(parents=True, exist_ok=True)
    return ws

def phase_header(n, total, name):
    bar = "━" * 50
    print(f"\n{bar}\n  [PHASE {n}/{total}] — {name}\n{bar}\n")

def count_tokens_approx(text):
    """Rough token count: ~4 chars per token"""
    return len(text) // 4

SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt", "out",
    "coverage", ".turbo", ".cache", "__pycache__", "storybook-static",
    ".svelte-kit", ".output", "vendor", ".venv", "venv", "env",
    "public/build", ".vercel", ".netlify"
}

SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp", ".avif",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mp3", ".wav", ".mov", ".avi",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class",
    ".map",  # source maps
}

def should_skip_file(path):
    p = Path(path)
    if p.suffix.lower() in SKIP_EXTENSIONS:
        return True
    name = p.name
    if name.endswith(".min.js") or name.endswith(".min.css") or name.endswith(".bundle.js"):
        return True
    if name.endswith(".generated.ts") or name.endswith(".generated.js"):
        return True
    if name.endswith("-lock.json") or name == "yarn.lock":
        return False  # keep for stack detection
    return False

def should_skip_dir(name):
    return name in SKIP_DIRS or name.startswith(".")

def read_file_safe(path, max_lines=500):
    """Read file content safely, truncating large files."""
    try:
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        if len(lines) > max_lines:
            return "\n".join(lines[:int(max_lines * 0.8)] +
                             [f"\n... [{len(lines) - max_lines} lines truncated] ...\n"] +
                             lines[-int(max_lines * 0.1):])
        return content
    except Exception:
        return None
