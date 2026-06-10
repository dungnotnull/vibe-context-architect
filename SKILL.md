---
name: vibe-context-architect
description: >
  AI memory layer for vibe coders — analyzes your codebase and builds a living context
  system that makes every future AI session instantly understand your project.
  
  USE THIS SKILL whenever a developer mentions: "AI keeps forgetting my project",
  "have to re-explain every session", "context window fills up", "AI suggested
  something that doesn't match my stack", "need to document my project for AI",
  "build context files", "CONTEXT.md", "AI memory", "project conventions",
  "make AI understand my codebase", "vibe coding getting messy", "AI keeps making
  the same mistakes", "project is getting too big for AI to understand".
  
  Also trigger for: "analyze my project structure", "extract my coding patterns",
  "document my tech decisions", "set up AI context", "onboard AI to my project",
  "make claude understand my project better", "project is growing and AI is losing track".
  
  This skill runs a 5-phase harness: SCAN → EXTRACT → SYNTHESIZE → GENERATE → INSTALL.
  Output is a complete `.ai-context/` folder with CONTEXT.md, DECISIONS.md,
  PATTERNS.md, STYLE.md, and smart session-starter prompts the developer can
  paste at the start of any new AI chat.
---

# Vibe Context Architect

Turns a messy, fast-grown vibe-coded project into a project with a permanent
AI memory layer — so every new chat session starts with full context, not blank slate.

```
Your codebase (any size, any stack)
            │
            ▼
┌───────────────────────────────────────────────┐
│         5-Phase Context Harness               │
│                                               │
│  1. SCAN      — Map project topology          │
│  2. EXTRACT   — Mine decisions & patterns     │
│  3. SYNTHESIZE — Infer conventions & rules    │
│  4. GENERATE  — Write the context layer       │
│  5. INSTALL   — Wire it into your workflow    │
└───────────────────────────────────────────────┘
            │
            ▼
    .ai-context/
    ├── CONTEXT.md        ← "Who are you" for any AI
    ├── DECISIONS.md      ← Why things are built this way
    ├── PATTERNS.md       ← How things are built here
    ├── STYLE.md          ← Code style + naming rules
    ├── SESSION-STARTER.md ← Paste this to start any AI chat
    └── ANTI-PATTERNS.md  ← What NOT to do (AI guardrails)
```

---

## Quick Decision Tree

```
Has codebase files to scan?
├── YES → [PHASE 1: SCAN]
├── NO, starting new project → [PHASE 1: SCAN] (empty project mode)
└── Only wants to update existing .ai-context/ → [PHASE 2: EXTRACT] (update mode)

Already has .ai-context/ folder?
├── YES → Ask: full rebuild OR incremental update?
│         ├── Full rebuild → [PHASE 1]
│         └── Incremental → [PHASE 2] with --update flag
└── NO → [PHASE 1]
```

---

## PHASE 1 — SCAN: Map Project Topology

**Goal:** Build a complete map of the project — structure, stack, entry points, dependencies.

**Read before executing:** `references/scan-patterns.md`

### Step 1.1 — Run the project scanner

```bash
python scripts/scan_project.py --root <project_root> --output /tmp/vca/scan_result.json
```

This produces a topology map: file tree (depth-limited), detected frameworks,
entry points, dependency files, config files, test files, and estimated project size.

### Step 1.2 — Print topology summary

After scan, print a summary table:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROJECT TOPOLOGY SCAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Project name:    <detected or dirname>
  Stack:           <React + TypeScript + Node.js + PostgreSQL>
  Total files:     247  (42 skipped: node_modules, .git, dist)
  Source files:    89
  Config files:    14
  Test files:      23
  Entry points:    src/index.ts, src/app.ts
  Package manager: pnpm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask user to confirm or correct before proceeding.

### Step 1.3 — Prioritize files for deep analysis

Not all files are equal. Rank by signal value:
1. `README.md`, `CONTRIBUTING.md`, any existing docs
2. Root config files (`package.json`, `tsconfig.json`, `vite.config.ts`, etc.)
3. Entry points and main router/app files
4. Database schema files (`schema.prisma`, `*.sql`, `migrations/`)
5. Shared utilities and hooks (`lib/`, `utils/`, `hooks/`)
6. Sample feature files (pick 2-3 representative feature folders)
7. Test files (reveal intent and expected behavior)
8. CI/CD config (`.github/workflows/`, `Dockerfile`)

Save prioritized file list to `/tmp/vca/priority_files.json`.

---

## PHASE 2 — EXTRACT: Mine Decisions & Patterns

**Goal:** Read high-signal files and extract explicit + implicit decisions.

**Read before executing:** `references/extraction-rules.md`

### Step 2.1 — Extract from config files

Run config extractor on all detected config files:

```bash
python scripts/extract_configs.py --scan /tmp/vca/scan_result.json --output /tmp/vca/config_facts.json
```

Extracts: Node version, TypeScript strictness, linting rules, test framework,
build tool, CSS approach, environment variable patterns, deployment target.

### Step 2.2 — Extract from source files (LLM-powered)

For each priority source file, use the **Pattern Miner** sub-agent (see `agents/pattern-miner.md`):

```
For each file in priority_files:
  → Read file content
  → Ask pattern miner to extract:
      - Naming conventions (components, functions, files, variables)
      - State management patterns
      - Error handling approach
      - API call patterns
      - Import style (barrel exports? relative? absolute?)
      - Component/module structure
      - TypeScript usage patterns
      - Comment style and documentation habits
```

Aggregate into `/tmp/vca/pattern_raw.json`.

### Step 2.3 — Extract from git history (if available)

```bash
python scripts/extract_git_signals.py --root <project_root> --output /tmp/vca/git_signals.json
```

Mines: Recent commit message patterns (reveals naming habits), most-changed files
(reveals what's being iterated), branch naming convention, contributors.

### Step 2.4 — Extract anti-patterns (from TODO/FIXME/HACK comments)

```bash
python scripts/extract_annotations.py --root <project_root> --output /tmp/vca/annotations.json
```

Mines: `TODO`, `FIXME`, `HACK`, `NOTE`, `TEMP` comments — these reveal known debt
and what the developer knows is wrong but hasn't fixed. Critical for AI guardrails.

---

## PHASE 3 — SYNTHESIZE: Infer Conventions & Rules

**Goal:** Turn raw extracted data into coherent, consistent conventions.

**Read before executing:** `references/synthesis-rules.md`

### Step 3.1 — Resolve conflicts

Raw extraction often produces contradictions (e.g., some files use `camelCase` 
components, some use `PascalCase`). Run conflict resolver:

```bash
python scripts/resolve_conflicts.py \
  --patterns /tmp/vca/pattern_raw.json \
  --configs /tmp/vca/config_facts.json \
  --output /tmp/vca/conventions.json
```

For unresolvable conflicts, flag them for the user to decide (see Step 3.3).

### Step 3.2 — Infer implicit rules

Some rules are never written but always followed. The LLM should infer:

```
Looking at the codebase patterns, what rules does this developer
ALWAYS follow that they never wrote down? Examples:
- "Always co-locate tests next to source files"
- "Never use default exports"
- "Always use early returns over nested if blocks"
- "API responses are always wrapped in { data, error, meta }"
```

Add inferred rules to `/tmp/vca/conventions.json` with `"inferred": true` flag.

### Step 3.3 — Surface decisions for user confirmation

Print a numbered list of any conflicts or ambiguities found:

```
⚠️  DECISIONS NEEDED — 3 conflicts found:

[1] Component naming: Found both PascalCase (67%) and kebab-case (33%)
    → Which is your convention? (a) PascalCase  (b) kebab-case

[2] State management: Found useState (local) + Zustand (global) + some Context API
    → Is this intentional? Describe when to use which, or should we flag Context as anti-pattern?

[3] API calls: Found both axios and fetch used
    → Which should AI use? (a) axios  (b) fetch  (c) both are fine
```

Wait for user answers. Update `conventions.json` with resolved values.

---

## PHASE 4 — GENERATE: Write the Context Layer

**Goal:** Produce all `.ai-context/` files from synthesized data.

**Read before executing:** `references/output-templates.md`

Run the generator:

```bash
python scripts/generate_context.py \
  --conventions /tmp/vca/conventions.json \
  --scan /tmp/vca/scan_result.json \
  --configs /tmp/vca/config_facts.json \
  --annotations /tmp/vca/annotations.json \
  --output /tmp/vca/output/
```

This produces 6 files. Each is described below.

### 4A — CONTEXT.md ("Who am I")

The single-file project briefing. Any AI reading this instantly knows:
- What the project does (1-2 sentences)
- The exact tech stack with versions
- Project structure map (key directories + their purpose)
- How to run the project locally
- Key domain concepts and vocabulary
- Current project state / maturity

**Format:** See `references/output-templates.md#context-template`
**Target length:** 150-300 lines (scannable in one read)

### 4B — DECISIONS.md ("Why it's built this way")

Architecture decision log. For each major technical choice:
```markdown
## ADR-001: [Decision Title]
**Decision:** [What was chosen]
**Why:** [Reasoning — inferred from code patterns if not documented]
**Alternatives considered:** [What wasn't chosen]
**Consequences:** [What this means for future development]
**Status:** Active | Superseded | Deprecated
```

Focus on decisions that would surprise an AI: unusual patterns, deliberate constraints,
non-obvious choices.

### 4C — PATTERNS.md ("How things are built here")

Living pattern library with real code examples extracted from the codebase:

```markdown
## Pattern: API Route Handler

**When to use:** Every new API endpoint
**Template:**
\`\`\`typescript
// Always follow this structure:
export async function GET(req: Request) {
  try {
    // ... handler logic
    return Response.json({ data: result })
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 })
  }
}
\`\`\`
**Real example from codebase:** `src/app/api/users/route.ts`
```

### 4D — STYLE.md ("How code looks here")

Naming rules, formatting conventions, import patterns — the micro-decisions:
- File naming convention
- Component/function/variable naming rules
- Import ordering rules
- Export style (default vs named)
- TypeScript patterns (interfaces vs types, generics, etc.)
- Comment style (when to comment, what format)
- Folder structure rules

### 4E — SESSION-STARTER.md ("The magic paste")

The most important file. A pre-written context prompt the developer pastes at the
start of ANY new AI chat session:

```markdown
# [Project Name] — AI Context

You are working on [Project Name]. Here's everything you need to know:

## Stack
[Exact stack summary]

## Current Task
[Leave blank — user fills this in]

## Key Conventions
[Top 10 most important conventions, ultra-condensed]

## Files Map
[Key directories and what lives there]

## Anti-Patterns — Never Do These
[Top 5 things AI commonly gets wrong for this project]

## Decision Log Summary
[1-line summary of each major architectural decision]

---
Full context: Read .ai-context/CONTEXT.md for complete project context.
```

**Target length:** Exactly fits in ~800 tokens (tested against Claude context window).

### 4F — ANTI-PATTERNS.md ("AI guardrails")

The AI trap-door list. Things AI assistants commonly suggest that are WRONG for this project:

```markdown
## ❌ Anti-Pattern: Using `any` type in TypeScript

**Why it's wrong here:** This project uses `strict: true` and `noImplicitAny`.
The codebase has 0 `any` types as policy.
**Instead:** Use proper typing or `unknown` with type guards.
**AI often suggests this when:** Solving complex generic type problems.

## ❌ Anti-Pattern: Direct database queries in route handlers

**Why it's wrong here:** All DB access goes through the service layer in `src/services/`.
**Instead:** Create/use a service function in `src/services/`.
**AI often suggests this when:** Adding quick one-off data fetches.
```

Sources for anti-patterns: TODO/FIXME comments, `// don't` / `// never` / `// avoid`
comments, linting rules that are explicitly set to "error".

---

## PHASE 5 — INSTALL: Wire Into Your Workflow

**Goal:** Make the context layer actually get used, not just exist.

### Step 5.1 — Write files to project

```bash
python scripts/install_context.py \
  --source /tmp/vca/output/ \
  --target <project_root>/.ai-context/
```

Creates `.ai-context/` folder. Respects existing files (asks before overwriting).

### Step 5.2 — Add to .gitignore or track in git

Ask the user:
```
📁 Should .ai-context/ be committed to git?

(a) YES — commit it → team members and future sessions benefit
(b) NO — add to .gitignore → personal AI workflow only
(c) PARTIAL — commit CONTEXT.md and DECISIONS.md, ignore SESSION-STARTER.md
```

### Step 5.3 — Create update hook (optional)

```bash
python scripts/create_update_hook.py --root <project_root> --mode <git-hook|npm-script|manual>
```

Installs a hook that re-runs the scan + extract phases when major changes happen,
then prompts the developer to review and update context files.

### Step 5.4 — Print final summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ VIBE CONTEXT ARCHITECT — CONTEXT LAYER INSTALLED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Project:         <project_name>
  Stack detected:  <stack>
  Files analyzed:  <N>
  Patterns mined:  <N>
  Decisions doc'd: <N>
  Anti-patterns:   <N>

  Generated:
    .ai-context/CONTEXT.md          (<N> lines)
    .ai-context/DECISIONS.md        (<N> decisions)
    .ai-context/PATTERNS.md         (<N> patterns)
    .ai-context/STYLE.md            (<N> rules)
    .ai-context/SESSION-STARTER.md  (~800 tokens)
    .ai-context/ANTI-PATTERNS.md    (<N> guardrails)

  🚀 HOW TO USE:
     1. Copy SESSION-STARTER.md content
     2. Paste at start of any new Claude chat
     3. Done — Claude now knows your full project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Update Mode (Incremental)

When `.ai-context/` already exists and developer wants to update after adding features:

```bash
python scripts/update_context.py \
  --root <project_root> \
  --since <git_ref_or_date> \
  --existing .ai-context/ \
  --output .ai-context/
```

- Only scans files changed since `--since`
- Merges new patterns with existing ones
- Flags conflicts with existing conventions
- Updates SESSION-STARTER.md with any new anti-patterns
- Appends new ADRs to DECISIONS.md

---

## Special Modes

### `--new-project` Mode

Project has no code yet. Generate a template context layer based on the stated stack:

```
User: "I'm starting a SaaS app with Next.js 14, Supabase, Stripe, and Tailwind"
→ Generate opinionated starter context layer with:
   - Best practice conventions for that exact stack
   - Common patterns for SaaS projects
   - Anti-patterns specific to that stack combo
   - Decision log with the "why" for common Next.js + Supabase patterns
```

Read `references/stack-presets.md` for opinionated stack-specific conventions.

### `--diff` Mode

Show what changed between old and new context:

```bash
python scripts/diff_context.py --old .ai-context/ --new /tmp/vca/output/
```

Shows a human-readable diff before installing updates.

### `--export` Mode

Export context as a single portable file for sharing:

```bash
python scripts/export_context.py --input .ai-context/ --output project-context.md
```

Useful for: onboarding new team members, sharing with contractors,
uploading to AI chat interfaces that accept single document upload.

---

## Error Handling

- **No files to analyze** → Switch to `--new-project` mode, ask for stack
- **Too large (>10,000 files)** → Auto-limit scan to `src/` + config root
- **Binary/minified files** → Skip automatically
- **No git history** → Skip git signals phase, continue with file analysis
- **Existing `.ai-context/` detected** → Ask: update or full rebuild
- **No package.json / unclear stack** → Ask user to describe stack manually

---

## Agent Behavior Rules

- Always print phase headers: `[PHASE N/5] — <Name>`
- NEVER skip the user confirmation in Phase 3.3 — ambiguities must be resolved
- Generated files should use the REAL project name, not placeholders
- Code examples in PATTERNS.md must be extracted from actual project files, not invented
- SESSION-STARTER.md must be tested to fit under 800 tokens — trim if needed
- Anti-patterns must be SPECIFIC to this project, not generic best practices

---

## Sub-Skills Reference

| Sub-Skill | File | Phase |
|---|---|---|
| File scan patterns & ignore rules | `references/scan-patterns.md` | 1 |
| Extraction rules by file type | `references/extraction-rules.md` | 2 |
| Conflict resolution & synthesis | `references/synthesis-rules.md` | 3 |
| Output file templates | `references/output-templates.md` | 4 |
| Stack-specific presets | `references/stack-presets.md` | 1, 4 |
| Pattern miner sub-agent | `agents/pattern-miner.md` | 2 |
| Script reference | `scripts/README.md` | All |
