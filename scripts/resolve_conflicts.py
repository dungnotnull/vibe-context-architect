#!/usr/bin/env python3
"""
resolve_conflicts.py — Merge raw patterns + config facts into unified conventions.

Usage:
    python scripts/resolve_conflicts.py \
        --patterns /tmp/vca/pattern_raw.json \
        --configs /tmp/vca/config_facts.json \
        --output /tmp/vca/conventions.json
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_json, save_json, now_iso


def resolve_naming(patterns, configs):
    """Resolve naming conventions from extracted patterns."""
    naming = {}
    ts_cfg = configs.get("typescript", {})

    # Import aliases → naming
    aliases = ts_cfg.get("import_aliases", {})
    if aliases:
        naming["import_style"] = " + ".join(f"`{k}` → `{v}`" for k, v in list(aliases.items())[:3])

    # Prisma naming
    prisma = configs.get("prisma", {})
    if prisma.get("field_naming"):
        naming["prisma_fields"] = prisma["field_naming"]
    if prisma.get("models"):
        sample = prisma["models"][0] if prisma["models"] else ""
        if sample and sample[0].isupper():
            naming["prisma_models"] = "PascalCase singular (User, Post, Comment)"

    # From raw patterns (if LLM-extracted)
    raw_patterns = patterns.get("patterns_found", []) if patterns else []
    for p in raw_patterns:
        cat = p.get("category", "")
        pattern_key = p.get("pattern", "")
        val = p.get("value", "")
        if cat == "naming" and val and p.get("confidence", 0) >= 0.7:
            naming[pattern_key] = val

    # Defaults if nothing extracted
    if not naming.get("component_files"):
        naming["component_files"] = "PascalCase.tsx"
    if not naming.get("non_component_files"):
        naming["non_component_files"] = "kebab-case.ts"
    if not naming.get("utility_functions"):
        naming["utility_functions"] = "camelCase, verb-first (getUser, createPost)"
    if not naming.get("react_hooks"):
        naming["react_hooks"] = "camelCase with use- prefix (useUser, useAuth)"
    if not naming.get("constants"):
        naming["constants"] = "UPPER_SNAKE_CASE"
    if not naming.get("types"):
        naming["types"] = "PascalCase (User, UserStatus, ApiResponse)"

    return naming


def resolve_code_style(patterns, configs):
    """Resolve code style conventions."""
    style = {}
    linting = configs.get("linting", {})
    ts_cfg = configs.get("typescript", {})

    # Hard linting rules → constraints
    if linting.get("no_any"):
        style["type_strictness"] = "No `any` type — use `unknown` with type guards or proper typing"
    if linting.get("no_console"):
        style["logging"] = "No console.log — use project logger utility"

    # TypeScript strictness
    if ts_cfg.get("strict"):
        style["typescript_mode"] = "Strict mode (noImplicitAny, strictNullChecks, etc.)"

    # From raw patterns
    raw_patterns = patterns.get("patterns_found", []) if patterns else []
    for p in raw_patterns:
        if p.get("category") == "code_style" and p.get("confidence", 0) >= 0.7:
            style[p.get("pattern", "")] = p.get("value", "")

    # Defaults
    if not style.get("async_pattern"):
        style["async_pattern"] = "async/await only — no .then() chains"
    if not style.get("error_handling"):
        style["error_handling"] = "try-catch in async functions, toast for user-facing errors"
    if not style.get("null_handling"):
        style["null_handling"] = "Optional chaining (?.) and nullish coalescing (??) preferred"

    return style


def resolve_structure(patterns, configs):
    """Resolve structural conventions."""
    structure = {}
    ts_cfg = configs.get("typescript", {})

    aliases = ts_cfg.get("import_aliases", {})
    if aliases:
        structure["imports"] = f"Use path aliases: {list(aliases.keys())[0]} for absolute imports"
    else:
        structure["imports"] = "Relative imports from same dir, absolute for cross-feature"

    # From raw patterns
    raw_patterns = patterns.get("patterns_found", []) if patterns else []
    for p in raw_patterns:
        if p.get("category") == "structure" and p.get("confidence", 0) >= 0.7:
            structure[p.get("pattern", "")] = p.get("value", "")

    # Defaults
    if not structure.get("component_exports"):
        structure["component_exports"] = "Named exports (except Next.js page.tsx/layout.tsx)"
    if not structure.get("barrel_exports"):
        structure["barrel_exports"] = "index.ts per feature folder"
    if not structure.get("test_colocation"):
        structure["test_colocation"] = "Co-located *.test.tsx next to component"

    return structure


def resolve_api_patterns(patterns, configs, scan=None):
    """Resolve API and data-fetching patterns."""
    api = {}

    # From raw patterns
    raw_patterns = patterns.get("patterns_found", []) if patterns else []
    for p in raw_patterns:
        if p.get("category") in ("api", "data_fetching") and p.get("confidence", 0) >= 0.6:
            api[p.get("pattern", "")] = p.get("value", "")

    # Defaults
    if not api.get("response_shape"):
        api["response_shape"] = "{ data: T | null, error: string | null }"
    if not api.get("data_fetching"):
        api["data_fetching"] = "TanStack Query for client data, direct in Server Components"

    return api


def build_constraints(configs):
    """Build hard constraint list from config facts."""
    constraints = []
    linting = configs.get("linting", {})
    ts_cfg = configs.get("typescript", {})

    if linting.get("no_any"):
        constraints.append("Never use `any` TypeScript type")
    if linting.get("no_console"):
        constraints.append("Never use console.log in production code")
    if ts_cfg.get("strict"):
        constraints.append("TypeScript strict mode — handle all null/undefined cases")

    # From hard error linting rules
    for rule in linting.get("hard_error_rules", [])[:5]:
        if rule not in ("no-console", "@typescript-eslint/no-explicit-any"):
            constraints.append(f"ESLint error: {rule}")

    return constraints


def extract_anti_patterns(patterns, annotations, configs):
    """Extract anti-patterns from all sources."""
    anti = []

    # From annotation mining
    ann_anti = annotations.get("anti_pattern_candidates", []) if annotations else []
    for a in ann_anti[:8]:
        anti.append({
            "pattern": a.get("description", ""),
            "why": f"Marked as {a.get('source')} in {a.get('file', 'codebase')}",
            "instead": "Fix the underlying issue — do not replicate",
            "source_file": a.get("file", ""),
        })

    # From prohibitions
    prohibitions = annotations.get("prohibitions", []) if annotations else []
    for p in prohibitions[:5]:
        anti.append({
            "pattern": f"Explicit prohibition: {p.get('text', '')}",
            "why": f"Written explicitly in {p.get('file', 'source')} line {p.get('line', '?')}",
            "instead": "Follow the code comment",
            "source_file": p.get("file", ""),
        })

    return anti


def infer_rules(patterns, configs, annotations):
    """Collect inferred implicit rules."""
    inferred = []

    # From raw pattern mining (LLM-extracted)
    raw = patterns.get("inferred_rules", []) if patterns else []
    for r in raw:
        if isinstance(r, str):
            inferred.append({"rule": r, "confidence": 0.8})
        elif isinstance(r, dict):
            inferred.append(r)

    # From requirements annotations
    requirements = annotations.get("requirements", []) if annotations else []
    for req in requirements[:5]:
        inferred.append({"rule": req.get("text", ""), "confidence": 0.9})

    return inferred


def main():
    parser = argparse.ArgumentParser(description="Resolve and synthesize conventions")
    parser.add_argument("--patterns", default=None, help="Raw pattern JSON (optional)")
    parser.add_argument("--configs", required=True, help="Config facts JSON")
    parser.add_argument("--annotations", default=None, help="Annotations JSON (optional)")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    configs = load_json(args.configs)
    patterns = load_json(args.patterns) if args.patterns and Path(args.patterns).exists() else {}
    annotations = load_json(args.annotations) if args.annotations and Path(args.annotations).exists() else {}

    print("Resolving conventions...", file=sys.stderr)

    conventions = {
        "synthesized_at": now_iso(),
        "conventions": {
            "naming":        resolve_naming(patterns, configs),
            "code_style":    resolve_code_style(patterns, configs),
            "structure":     resolve_structure(patterns, configs),
            "api_patterns":  resolve_api_patterns(patterns, configs),
        },
        "constraints_hard": build_constraints(configs),
        "anti_patterns":    extract_anti_patterns(patterns, annotations, configs),
        "inferred_rules":   infer_rules(patterns, configs, annotations),
        "resolution_log":   [],
    }

    # Log any conflicts found
    if patterns.get("conflicts_with_existing"):
        for conflict in patterns["conflicts_with_existing"][:5]:
            conventions["resolution_log"].append({
                "conflict": conflict,
                "resolution": "user_decision_required",
                "note": "Manual review needed"
            })

    save_json(conventions, args.output)

    print(f"  Naming rules:     {len(conventions['conventions']['naming'])}", file=sys.stderr)
    print(f"  Style rules:      {len(conventions['conventions']['code_style'])}", file=sys.stderr)
    print(f"  Hard constraints: {len(conventions['constraints_hard'])}", file=sys.stderr)
    print(f"  Anti-patterns:    {len(conventions['anti_patterns'])}", file=sys.stderr)
    print(f"  Inferred rules:   {len(conventions['inferred_rules'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
