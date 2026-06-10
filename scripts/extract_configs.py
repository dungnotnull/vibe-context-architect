#!/usr/bin/env python3
"""
extract_configs.py — Extract facts from config files (tsconfig, eslint, tailwind, etc.)

Usage:
    python scripts/extract_configs.py --scan scan_result.json --output config_facts.json
"""
import argparse, json, sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import load_json, save_json, read_file_safe, now_iso


def parse_tsconfig(root, path):
    content = read_file_safe(Path(root) / path)
    if not content:
        return {}
    # Strip comments before JSON parse
    cleaned = re.sub(r"//.*", "", content)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
    try:
        data = json.loads(cleaned)
    except Exception:
        return {}
    opts = data.get("compilerOptions", {})
    paths = opts.get("paths", {})
    aliases = {}
    for alias, targets in paths.items():
        key = alias.rstrip("/*")
        val = targets[0].rstrip("/*") if targets else ""
        aliases[key] = val

    return {
        "strict": opts.get("strict", False),
        "no_implicit_any": opts.get("noImplicitAny", opts.get("strict", False)),
        "exact_optional": opts.get("exactOptionalPropertyTypes", False),
        "target": opts.get("target", "unknown"),
        "module": opts.get("module", "unknown"),
        "base_url": opts.get("baseUrl"),
        "import_aliases": aliases,
        "jsx": opts.get("jsx"),
    }


def parse_eslint(root, path):
    content = read_file_safe(Path(root) / path)
    if not content:
        return {}
    rules = {}
    try:
        cleaned = re.sub(r"//.*", "", content)
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        if "module.exports" in cleaned:
            # JS config — extract rules section roughly
            m = re.search(r'"rules"\s*:\s*\{([^}]+)\}', cleaned, re.DOTALL)
            if m:
                rule_text = m.group(1)
                for match in re.finditer(r'"([\w/@-]+)"\s*:\s*"(\w+)"', rule_text):
                    rules[match.group(1)] = match.group(2)
        else:
            data = json.loads(cleaned)
            rules = data.get("rules", {})
    except Exception:
        pass

    hard_errors = [k for k, v in rules.items()
                   if v == "error" or (isinstance(v, list) and v[0] == "error")]
    warnings = [k for k, v in rules.items()
                if v == "warn" or (isinstance(v, list) and v[0] == "warn")]

    return {
        "hard_error_rules": hard_errors[:20],
        "warning_rules": warnings[:10],
        "no_console": "no-console" in hard_errors or "no-console" in warnings,
        "no_any": "@typescript-eslint/no-explicit-any" in hard_errors,
        "import_order": "import/order" in hard_errors or "import/order" in warnings,
    }


def parse_package_json(root):
    path = Path(root) / "package.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    scripts = data.get("scripts", {})
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

    # Interesting script patterns
    script_insights = []
    for k, v in scripts.items():
        if "prisma" in v: script_insights.append(f"Prisma workflow: `{k}: {v}`")
        if "drizzle" in v: script_insights.append(f"Drizzle workflow: `{k}: {v}`")
        if "turbo" in v: script_insights.append(f"Uses Turborepo: `{k}: {v}`")
        if "typecheck" in k or "tsc --noEmit" in v: script_insights.append("Separate typecheck step")
        if "lint:fix" in k or "--fix" in v: script_insights.append("Auto-fix linting on demand")

    return {
        "node_version": data.get("engines", {}).get("node", "unspecified"),
        "project_type": "monorepo" if "workspaces" in data else "single",
        "script_insights": script_insights[:8],
        "has_postinstall": "postinstall" in scripts,
        "test_command": scripts.get("test", ""),
        "dev_command": scripts.get("dev", ""),
        "build_command": scripts.get("build", ""),
    }


def parse_prisma_schema(root):
    schema_path = Path(root) / "prisma" / "schema.prisma"
    alt_path = Path(root) / "schema.prisma"
    path = schema_path if schema_path.exists() else (alt_path if alt_path.exists() else None)
    if not path:
        return {}

    content = path.read_text(encoding="utf-8")
    models = re.findall(r"^model\s+(\w+)\s*\{", content, re.MULTILINE)
    enums = re.findall(r"^enum\s+(\w+)\s*\{", content, re.MULTILINE)

    # Detect ID strategy
    id_strategy = "unknown"
    if "@default(cuid())" in content: id_strategy = "CUID"
    elif "@default(cuid2())" in content or "createId()" in content: id_strategy = "CUID2"
    elif "@default(uuid())" in content: id_strategy = "UUID"
    elif "@default(autoincrement())" in content: id_strategy = "Auto-increment"

    # Soft delete pattern
    has_soft_delete = "deletedAt" in content or "deleted_at" in content

    # Audit fields
    has_audit = "createdAt" in content and "updatedAt" in content

    # Field naming
    camel_fields = len(re.findall(r'[a-z][A-Z]', content))
    snake_fields = len(re.findall(r'[a-z]_[a-z]', content))
    field_naming = "camelCase" if camel_fields > snake_fields else "snake_case"

    return {
        "models": models,
        "model_count": len(models),
        "enums": enums,
        "id_strategy": id_strategy,
        "soft_delete": has_soft_delete,
        "audit_fields": has_audit,
        "field_naming": field_naming,
        "db_url_env": "DATABASE_URL" if "DATABASE_URL" in content else "unknown",
    }


def parse_env_example(root):
    for fname in [".env.example", ".env.template", ".env.sample"]:
        path = Path(root) / fname
        if path.exists():
            content = path.read_text(encoding="utf-8")
            vars_found = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key = line.split("=")[0].strip()
                    vars_found.append(key)
            return {"env_vars": vars_found, "source_file": fname}
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    scan = load_json(args.scan)
    root = scan["root"]

    print("Extracting config facts...", file=sys.stderr)

    result = {
        "extracted_at": now_iso(),
        "root": root,
    }

    # package.json
    result["package"] = parse_package_json(root)

    # TypeScript
    ts_configs = [f for f in scan.get("all_config_files", []) if "tsconfig" in f]
    if ts_configs:
        result["typescript"] = parse_tsconfig(root, ts_configs[0])

    # ESLint
    eslint_configs = [f for f in scan.get("all_config_files", [])
                      if ".eslintrc" in f or "eslint.config" in f or "biome.json" in f]
    if eslint_configs:
        result["linting"] = parse_eslint(root, eslint_configs[0])

    # Prisma
    result["prisma"] = parse_prisma_schema(root)

    # Env vars
    result["env"] = parse_env_example(root)

    save_json(result, args.output)
    print(f"  Config extraction complete", file=sys.stderr)


if __name__ == "__main__":
    main()
