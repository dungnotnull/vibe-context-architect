#!/usr/bin/env python3
"""
scan_project.py — Scan project topology and detect tech stack.

Usage:
    python scripts/scan_project.py --root ./my-project --output /tmp/vca/scan_result.json
"""
import argparse, json, os, sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import save_json, now_iso, VCA_VERSION, SKIP_DIRS, SKIP_EXTENSIONS, should_skip_dir, should_skip_file


# ── Stack Detection ────────────────────────────────────────────────────────────

STACK_SIGNALS = {
    "frontend": [
        (["next"], ["app", "pages"], "Next.js"),
        (["nuxt"], [], "Nuxt.js"),
        (["@remix-run/react"], [], "Remix"),
        (["astro"], [], "Astro"),
        (["svelte", "@sveltejs/kit"], [], "SvelteKit"),
        (["react-native"], [], "React Native"),
        (["expo"], [], "Expo"),
        (["react"], [], "React + Vite"),
        (["vue"], [], "Vue.js"),
        (["angular"], [], "Angular"),
        (["solid-js"], [], "SolidJS"),
        (["qwik"], [], "Qwik"),
    ],
    "backend": [
        (["elysia"], [], "ElysiaJS (Bun)"),
        (["hono"], [], "Hono"),
        (["fastify"], [], "Fastify"),
        (["@nestjs/core"], [], "NestJS"),
        (["express"], [], "Express.js"),
        (["koa"], [], "Koa"),
    ],
    "database": [
        (["@prisma/client"], [], "Prisma"),
        (["drizzle-orm"], [], "Drizzle ORM"),
        (["typeorm"], [], "TypeORM"),
        (["mongoose"], [], "MongoDB + Mongoose"),
        (["@supabase/supabase-js"], [], "Supabase"),
        (["pg", "@vercel/postgres"], [], "PostgreSQL"),
        (["better-sqlite3"], [], "SQLite"),
        (["@planetscale/database"], [], "PlanetScale"),
        (["@neon-database/serverless"], [], "Neon"),
    ],
    "auth": [
        (["next-auth", "@auth/core"], [], "Auth.js / NextAuth"),
        (["@clerk/nextjs", "@clerk/clerk-sdk-node"], [], "Clerk"),
        (["lucia-auth", "lucia"], [], "Lucia"),
        (["@kinde-oss/kinde-auth-nextjs"], [], "Kinde"),
        (["@supabase/auth-helpers-nextjs"], [], "Supabase Auth"),
        (["better-auth"], [], "Better Auth"),
    ],
    "styling": [
        (["tailwindcss"], [], "Tailwind CSS"),
        (["@emotion/react"], [], "Emotion"),
        (["styled-components"], [], "Styled Components"),
        (["@vanilla-extract/css"], [], "Vanilla Extract"),
        (["unocss"], [], "UnoCSS"),
    ],
    "ui_library": [
        (["@radix-ui/react-dialog"], [], "Radix UI / shadcn"),
        (["@mui/material"], [], "Material UI"),
        (["@chakra-ui/react"], [], "Chakra UI"),
        (["@mantine/core"], [], "Mantine"),
        (["antd"], [], "Ant Design"),
    ],
    "state": [
        (["zustand"], [], "Zustand"),
        (["jotai"], [], "Jotai"),
        (["@reduxjs/toolkit"], [], "Redux Toolkit"),
        (["recoil"], [], "Recoil"),
        (["valtio"], [], "Valtio"),
        (["pinia"], [], "Pinia"),
    ],
    "data_fetching": [
        (["@tanstack/react-query"], [], "TanStack Query"),
        (["swr"], [], "SWR"),
        (["@trpc/client", "@trpc/server"], [], "tRPC"),
        (["axios"], [], "Axios"),
        (["ky"], [], "Ky"),
    ],
    "testing": [
        (["vitest"], [], "Vitest"),
        (["jest"], [], "Jest"),
        (["@playwright/test"], [], "Playwright"),
        (["cypress"], [], "Cypress"),
        (["@testing-library/react"], [], "+ Testing Library"),
        (["msw"], [], "+ MSW"),
    ],
    "deployment": [],  # detected from files
}

DEPLOYMENT_SIGNALS = {
    "vercel.json": "Vercel",
    ".vercel": "Vercel",
    "netlify.toml": "Netlify",
    "fly.toml": "Fly.io",
    "railway.json": "Railway",
    "render.yaml": "Render",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "kubernetes": "Kubernetes",
    ".github/workflows": "GitHub Actions (CI/CD)",
    "wrangler.toml": "Cloudflare Workers",
}

PKG_MANAGER_SIGNALS = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lockb": "bun",
    "package-lock.json": "npm",
}


def detect_stack(root, pkg_data, dirs, files_flat):
    """Detect tech stack from package.json + file system."""
    all_deps = {}
    if pkg_data:
        all_deps.update(pkg_data.get("dependencies", {}))
        all_deps.update(pkg_data.get("devDependencies", {}))

    stack = {}
    dep_names = list(all_deps.keys())

    for category, signals in STACK_SIGNALS.items():
        if not signals:
            continue
        for dep_list, dir_hints, name in signals:
            if any(d in dep_names for d in dep_list):
                # Check Next.js version
                if name == "Next.js" and "next" in all_deps:
                    v = all_deps["next"]
                    major = re.search(r"(\d+)", v)
                    if major and int(major.group(1)) >= 14:
                        name = "Next.js 14+ (App Router)"
                stack.setdefault(category, []).append(name)
                break

    # Detect deployment
    for fname, deploy in DEPLOYMENT_SIGNALS.items():
        if any(f.endswith(fname) or fname in str(f) for f in files_flat):
            stack["deployment"] = deploy
            break

    # Detect package manager
    for fname, pm in PKG_MANAGER_SIGNALS.items():
        if (Path(root) / fname).exists():
            stack["package_manager"] = pm
            break
    else:
        stack["package_manager"] = "npm"

    # Language
    ts_files = sum(1 for f in files_flat if str(f).endswith((".ts", ".tsx")))
    js_files = sum(1 for f in files_flat if str(f).endswith((".js", ".jsx")))
    if ts_files > js_files:
        stack["language"] = "TypeScript"
        # Get version
        ts_ver = all_deps.get("typescript", all_deps.get("@types/node", ""))
        if ts_ver:
            m = re.search(r"(\d+\.\d+)", ts_ver)
            stack["language"] += f" {m.group(1)}" if m else ""
    else:
        stack["language"] = "JavaScript"

    # Flatten single-item lists
    result = {}
    for k, v in stack.items():
        result[k] = v[0] if isinstance(v, list) and len(v) == 1 else v if isinstance(v, list) else v

    return result


def build_directory_map(root, max_depth=3):
    """Build a condensed directory map."""
    root_path = Path(root)
    result = {}

    for item in sorted(root_path.iterdir()):
        if item.is_dir() and not should_skip_dir(item.name):
            sub_items = []
            if max_depth > 1:
                try:
                    for sub in sorted(item.iterdir()):
                        if sub.is_dir() and not should_skip_dir(sub.name):
                            sub_items.append(sub.name + "/")
                        elif sub.is_file() and not should_skip_file(str(sub)):
                            sub_items.append(sub.name)
                except PermissionError:
                    pass
            result[item.name + "/"] = sub_items[:12]  # limit
        elif item.is_file() and not should_skip_file(str(item)):
            result[item.name] = []

    return result


def prioritize_files(all_files, pkg_data, stack):
    """Score and rank files for deep analysis."""
    priority = []

    HIGH_NAMES = {
        "README.md": 95, "schema.prisma": 92, "package.json": 90,
        "tsconfig.json": 87, "tsconfig.base.json": 80,
        ".eslintrc.js": 75, ".eslintrc.json": 75, ".eslintrc.cjs": 75,
        "biome.json": 74, ".prettierrc": 70, ".prettierrc.js": 70,
        "tailwind.config.ts": 75, "tailwind.config.js": 73,
        "vite.config.ts": 72, "next.config.ts": 72, "next.config.mjs": 72,
        "drizzle.config.ts": 70, ".env.example": 68, ".env.template": 68,
        "Dockerfile": 60, "docker-compose.yml": 58,
        "middleware.ts": 80,  # Next.js
        "CONTRIBUTING.md": 60, "ARCHITECTURE.md": 65,
    }

    HIGH_PATHS = {
        "src/index.ts": 85, "src/main.ts": 85, "src/app.ts": 82,
        "src/app/layout.tsx": 82, "src/app/page.tsx": 78,
        "src/app/globals.css": 65,
        "app/layout.tsx": 82, "app/page.tsx": 78,
        "src/lib/db.ts": 80, "src/lib/prisma.ts": 80,
        "src/lib/utils.ts": 72, "src/lib/auth.ts": 78,
        "src/store/index.ts": 72, "src/stores/index.ts": 72,
        "src/types/index.ts": 70,
        "src/server/router.ts": 78,
    }

    scored = []
    for f in all_files:
        path = Path(f)
        name = path.name
        rel = str(f)

        score = 0

        # Exact name match
        if name in HIGH_NAMES:
            score = HIGH_NAMES[name]
        elif rel in HIGH_PATHS:
            score = HIGH_PATHS[rel]
        # Pattern scoring
        elif "schema" in rel.lower():
            score = 78
        elif "/services/" in rel or "/service/" in rel:
            score = 65
        elif "/hooks/" in rel:
            score = 58
        elif "/lib/" in rel or "/utils/" in rel:
            score = 55
        elif "/components/" in rel and not "/ui/" in rel:
            score = 52
        elif "/api/" in rel:
            score = 60
        elif "/store" in rel or "/stores" in rel:
            score = 55
        elif "/middleware" in rel:
            score = 65
        elif "/types/" in rel:
            score = 50
        elif ".test." in rel or ".spec." in rel:
            score = 35
        else:
            score = 20

        # Boost config files
        if path.suffix in (".json", ".yaml", ".yml", ".toml") and score < 60:
            score = max(score, 45)

        if score > 0:
            scored.append({"path": str(f), "score": score, "reason": _score_reason(rel, name, score)})

    return sorted(scored, key=lambda x: -x["score"])


def _score_reason(rel, name, score):
    if score >= 85: return "Entry point / critical config"
    if score >= 70: return "Core configuration"
    if score >= 55: return "Business logic"
    if score >= 40: return "Supporting code"
    return "Standard source file"


def walk_project(root):
    """Walk project, skip ignored dirs, return all files."""
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(root)
            if not should_skip_file(str(rel)):
                all_files.append(str(rel))
    return all_files


def classify_files(all_files):
    """Classify files by type."""
    source_files = [f for f in all_files if Path(f).suffix in
                    {".ts", ".tsx", ".js", ".jsx", ".svelte", ".vue", ".py", ".go", ".rs"}]
    config_files = [f for f in all_files if Path(f).suffix in
                    {".json", ".yaml", ".yml", ".toml", ".env"} or
                    Path(f).name in {".eslintrc.js", ".prettierrc", "biome.json"}]
    test_files = [f for f in source_files if ".test." in f or ".spec." in f]
    source_files = [f for f in source_files if f not in test_files]

    return {
        "source": source_files,
        "config": config_files,
        "test": test_files,
        "total": all_files,
    }


def detect_project_name(root, pkg_data):
    if pkg_data and pkg_data.get("name"):
        return pkg_data["name"]
    return Path(root).resolve().name


def classify_size(source_count):
    if source_count < 50: return "Tiny"
    if source_count < 200: return "Small"
    if source_count < 500: return "Medium"
    if source_count < 1000: return "Large"
    return "XL"


def detect_scripts(pkg_data):
    scripts = pkg_data.get("scripts", {}) if pkg_data else {}
    return {k: v for k, v in scripts.items() if k not in ("test", "build", "start")}


def main():
    parser = argparse.ArgumentParser(description="Scan project topology")
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: Root not found: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning project: {root}", file=sys.stderr)

    # Load package.json
    pkg_data = None
    pkg_path = root / "package.json"
    if pkg_path.exists():
        try:
            pkg_data = json.loads(pkg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Walk files
    all_files = walk_project(root)
    classified = classify_files(all_files)

    # Detect stack
    dirs = [d for d in os.listdir(root) if (root / d).is_dir() and not should_skip_dir(d)]
    stack = detect_stack(root, pkg_data, dirs, all_files)

    # Build structure map
    directory_map = build_directory_map(root)

    # Prioritize files
    priority_files = prioritize_files(all_files, pkg_data, stack)

    # Entry points
    entry_hints = ["src/index.ts", "src/main.ts", "src/app.ts",
                   "src/app/layout.tsx", "app/layout.tsx", "index.ts", "main.ts"]
    entry_points = [h for h in entry_hints if h in all_files]

    size = classify_size(len(classified["source"]))
    max_files = {"Tiny": 50, "Small": 40, "Medium": 30, "Large": 20, "XL": 15}[size]

    result = {
        "vca_version": VCA_VERSION,
        "scanned_at": now_iso(),
        "root": str(root),

        "project_name": detect_project_name(root, pkg_data),
        "project_version": pkg_data.get("version", "unknown") if pkg_data else "unknown",
        "classification": size,

        "stack": stack,

        "counts": {
            "total_files": len(all_files),
            "source_files": len(classified["source"]),
            "config_files": len(classified["config"]),
            "test_files": len(classified["test"]),
        },

        "entry_points": entry_points,
        "directory_map": directory_map,

        "priority_files": priority_files[:max_files],
        "all_config_files": classified["config"][:30],

        "scripts": detect_scripts(pkg_data),
        "engines": pkg_data.get("engines", {}) if pkg_data else {},
    }

    save_json(result, args.output)

    # Print summary
    print(f"\n{'━' * 45}", file=sys.stderr)
    print(f"  PROJECT TOPOLOGY SCAN", file=sys.stderr)
    print(f"{'━' * 45}", file=sys.stderr)
    print(f"  Name:        {result['project_name']}", file=sys.stderr)
    for cat, val in stack.items():
        if isinstance(val, list):
            val = ", ".join(val)
        print(f"  {cat.title():<13}{val}", file=sys.stderr)
    print(f"{'━' * 45}", file=sys.stderr)
    print(f"  Total files: {result['counts']['total_files']}", file=sys.stderr)
    print(f"  Source:      {result['counts']['source_files']}", file=sys.stderr)
    print(f"  Config:      {result['counts']['config_files']}", file=sys.stderr)
    print(f"  Tests:       {result['counts']['test_files']}", file=sys.stderr)
    print(f"  Priority:    Top {len(result['priority_files'])} files queued for analysis", file=sys.stderr)
    print(f"{'━' * 45}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
