# CLAUDE.md — Vibe Context Architect

This file governs how Claude and any AI agent should work within this project.
Read before making any changes.

---

## Project Identity

**Name:** `vibe-context-architect`
**Type:** Claude Skill — 5-phase AI agent harness
**Domain:** Developer productivity — AI memory layer for vibe-coded projects
**Target user:** Vibe coders who use AI heavily and need persistent project context

---

## Core Purpose

This skill solves the "blank slate" problem: every new AI chat session knows
nothing about the project. The skill builds a permanent `.ai-context/` folder
that makes any AI session instantly understand the project.

**This is not:** a documentation generator, a linter, a code analyzer.
**This is:** an AI memory layer — context that helps AI help you better.

---

## Repository Layout

```
vibe-context-architect/
├── SKILL.md                              ← PRIMARY: 5-phase harness
├── CLAUDE.md                             ← This file
├── README.md                             ← Public-facing docs
├── PROJECT-detail.md                     ← Architecture & design
├── PROJECT-DEVELOPMENT-PHASE-TRACKING.md ← Sprint tracker
│
├── references/                           ← Sub-skill docs (read per phase)
│   ├── scan-patterns.md                  ← Phase 1: File scanning rules
│   ├── extraction-rules.md               ← Phase 2: Extraction by file type
│   ├── synthesis-rules.md                ← Phase 3: Conflict resolution
│   ├── output-templates.md               ← Phase 4: Output file templates
│   └── stack-presets.md                  ← Presets for common stacks
│
├── scripts/                              ← Python pipeline scripts
│   ├── README.md
│   ├── utils.py                          ← Shared utilities
│   ├── scan_project.py                   ← Phase 1: Topology scan
│   ├── extract_configs.py                ← Phase 2: Config extraction
│   ├── extract_signals.py                ← Phase 2: Git + annotations
│   ├── resolve_conflicts.py              ← Phase 3: Convention synthesis
│   ├── generate_context.py               ← Phase 4: Generate all 6 files
│   ├── install_context.py                ← Phase 5: Write to project
│   ├── create_update_hook.py             ← Phase 5: Install hooks
│   ├── update_context.py                 ← Update mode
│   └── diff_context.py                   ← Diff old vs new
│
├── hooks/
│   └── pre-commit-context-check.py       ← Git pre-commit staleness warning
│
├── templates/                            ← Markdown file templates
│   ├── SESSION-STARTER.template.md
│   └── CONTEXT.template.md
│
├── agents/
│   └── pattern-miner.md                  ← Sub-agent for source file analysis
│
├── assets/
│   └── vscode-snippets.json              ← VSCode snippet helpers
│
└── evals/
    └── evals.json                        ← 4 eval scenarios
```

---

## Development Rules

### 1. The 6 Output Files Are Fixed

The skill always produces exactly these files in `.ai-context/`:
- `CONTEXT.md` — project briefing
- `DECISIONS.md` — architecture decision log
- `PATTERNS.md` — code patterns with examples
- `STYLE.md` — naming and style rules
- `SESSION-STARTER.md` — the paste-at-top-of-chat file
- `ANTI-PATTERNS.md` — AI guardrails

Do not add new output files without updating SKILL.md Phase 4 and `generate_context.py`.

### 2. SESSION-STARTER.md Has a Hard Token Budget

SESSION-STARTER.md MUST fit within ~800 tokens. This is non-negotiable — it
needs to fit at the top of a chat context without consuming too much space.

The `count_tokens_approx()` function in `utils.py` estimates token count.
`generate_context.py` trims automatically. Do not remove this trimming logic.

### 3. Never Invent Patterns — Extract or Ask

Code examples in PATTERNS.md MUST come from the actual project codebase.
Do NOT generate plausible-looking code that isn't actually in the project.

If no real example exists, use the stack preset templates from
`references/stack-presets.md`, clearly marked as "recommended pattern (not yet implemented)".

### 4. Conflicts Must Surface to User — Never Silently Resolve

When Phase 3 detects a conflict (e.g. 50% named exports, 50% default exports),
the agent MUST ask the user to decide. Do NOT pick the majority and silently proceed.

The exception: if a linting config explicitly sets a rule to "error",
that config wins over observed patterns without asking.

### 5. Deterministic Scripts, AI for Prose

Scripts handle: file walking, JSON parsing, token counting, file writing.
AI handles: writing DECISIONS.md prose, explaining WHY patterns exist,
generating migration guide text, inferring implicit rules.

### 6. Anti-Patterns Must Be Project-Specific

ANTI-PATTERNS.md is useless if it's just generic best practices.
Every entry should either:
- Come from an annotation in the codebase (FIXME, HACK, "don't...")
- Come from a hard linting rule
- Come from explicit information given by the user
- Come from a stack-specific known footgun (in `stack-presets.md`)

Generic "avoid global variables" entries pollute the guardrails.

---

## Adding a New Stack Preset

1. Add preset to `references/stack-presets.md`
2. Add detection signals to `scripts/scan_project.py` STACK_SIGNALS if not covered
3. Add framework-specific pattern generation to `scripts/generate_context.py`
4. Add at least one eval case in `evals/evals.json` for the new stack
5. Document in README.md supported stacks list

## Workspace Convention

Intermediate files: `/tmp/vca/`
```
/tmp/vca/
├── scan_result.json
├── config_facts.json
├── git_signals.json
├── annotations.json
├── pattern_raw.json       ← from LLM pattern miner
├── conventions.json
└── output/
    ├── CONTEXT.md
    ├── DECISIONS.md
    ├── PATTERNS.md
    ├── STYLE.md
    ├── SESSION-STARTER.md
    └── ANTI-PATTERNS.md
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VCA_WORKSPACE` | `/tmp/vca` | Intermediate workspace |
| `VCA_MAX_FILES` | `40` | Max files for deep analysis |
| `VCA_MAX_FILE_LINES` | `500` | Max lines per file |
| `VCA_AUTO` | `false` | Skip confirmations |

## Python Requirements

```
python >= 3.11
pyyaml >= 6.0    # optional, for YAML configs
```

No external dependencies required for core pipeline.

## Coding Style

- Type hints on all functions
- `sys.stderr` for progress, `sys.stdout` only for data
- `save_text()` / `save_json()` from `utils.py` for all writes
- Exit codes: 0 = success, 1 = logical error, 2 = script/parse error
