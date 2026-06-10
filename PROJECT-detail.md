# PROJECT-detail.md — Vibe Context Architect

## Problem Definition

### The Vibe Coder's AI Memory Problem

Vibe coders — developers who build primarily through AI-assisted sessions —
face a compounding problem as their project grows:

```
Day 1:  Claude knows everything (small project, fits in context)
Day 7:  "Wait, which state management did I decide on again?"
Day 14: "Why does Claude keep suggesting the wrong pattern?"
Day 30: "AI is actively making my code WORSE — it's inconsistent with itself"
```

**Root cause:** AI has no persistent memory between sessions. Every chat starts
at zero. The developer has to re-explain the project, the conventions, the
decisions — every single time.

**Current workarounds (all inadequate):**
- Copy-pasting old chat threads into new sessions (lossy, token-heavy)
- Writing README.md (not AI-optimized, not structured for fast context loading)
- Using Projects/Memory in Claude (helpful but not project-specific enough)
- Just hoping AI figures it out (it doesn't)

**What's missing:** A structured, AI-optimized "brain dump" file system that
captures not just WHAT the project is, but HOW it's built and WHY.

---

## Solution Architecture

### The AI Memory Layer

```
Developer's Project
        │
        ▼
.ai-context/                    ← New directory, committed to git
├── CONTEXT.md                  ← "Here's what this project is"
├── DECISIONS.md                ← "Here's why it's built this way"
├── PATTERNS.md                 ← "Here's how to add new things"
├── STYLE.md                    ← "Here's how code looks here"
├── SESSION-STARTER.md          ← "Paste this at the top of every chat"
└── ANTI-PATTERNS.md            ← "Don't let AI do these things"
```

**The key insight:** SESSION-STARTER.md is the centerpiece. It's a pre-written
context prompt, optimized for ~800 tokens, that the developer pastes at the
start of every new AI session. It instantly gives the AI:
- Full stack context
- Key conventions
- What NOT to do (the most valuable part)
- Enough structure to code correctly immediately

### Why 6 Files Instead of 1?

Each file serves a different AI consumption pattern:

| File | When Used | Token Budget |
|---|---|---|
| SESSION-STARTER.md | Every session — mandatory | ~800 tokens |
| CONTEXT.md | When AI needs deep project understanding | ~1500 tokens |
| PATTERNS.md | When AI is writing new code | Reference as needed |
| STYLE.md | When AI is naming things or styling | Reference as needed |
| DECISIONS.md | When AI needs to understand architectural choices | Reference as needed |
| ANTI-PATTERNS.md | When reviewing AI suggestions | Reference as needed |

---

## What Makes This Unique

### vs README.md

README is for humans onboarding to a project. It explains what to install, how to deploy.
It's not structured for AI consumption. It doesn't cover conventions.
It doesn't have guardrails. It's written once and rarely updated.

The `.ai-context/` layer is structured for AI consumption:
- Conventions in machine-readable format
- Code examples from the actual codebase
- Explicit anti-patterns as negative examples
- Token-budgeted SESSION-STARTER for immediate loading

### vs GitHub Copilot Instructions / Cursor Rules

`.cursorrules` and `.github/copilot-instructions.md` are similar in spirit,
but this skill goes further:
1. **Automated extraction** — we mine the codebase to DISCOVER conventions,
   not require the developer to write them from scratch
2. **Multi-file structure** — different context for different situations
3. **Living document** — update mode keeps it fresh as the project evolves
4. **Anti-patterns sourced from real code** — FIXMEs and HACs in code become guardrails
5. **Decision log** — explains WHY not just WHAT

### vs AI-generated documentation tools

Tools like Mintlify, Swimm generate technical docs. They don't create
AI-consumption-optimized context. They don't extract conventions.
They don't generate anti-patterns. They don't create session-starter prompts.

---

## Data Flow (Complete)

```
Project filesystem
        │
        ▼
[scan_project.py]
  - Walk directory tree
  - Detect stack from package.json / file patterns
  - Score and rank files by analysis value
  - Output: scan_result.json
        │
        ▼
[extract_configs.py]              [extract_signals.py --mode git]
  - Parse tsconfig.json           - Mine git commit messages
  - Parse .eslintrc               - Detect commit format convention
  - Parse schema.prisma           - Find hot (frequently changed) files
  - Parse .env.example            - Get project age, contributors
  - Output: config_facts.json     - Output: git_signals.json
        │                                   │
        ▼                                   ▼
[extract_signals.py --mode annotations]
  - Mine TODO/FIXME/HACK/NOTE comments
  - Find explicit "don't"/"never"/"always" rules
  - Output: annotations.json
        │
        ▼
[SKILL.md Phase 2 — LLM Pattern Mining via agents/pattern-miner.md]
  - Read top-priority source files
  - Extract naming conventions per file
  - Extract error handling patterns
  - Extract component structure
  - Extract import patterns
  - Output: pattern_raw.json (built incrementally)
        │
        ▼
[resolve_conflicts.py]
  - Merge all 4 data sources
  - Apply majority-rule / config-authority resolution
  - Flag genuine conflicts → surface to user
  - Output: conventions.json
        │
  [User resolves conflicts in Phase 3.3]
        │
        ▼
[generate_context.py]
  - Generate CONTEXT.md from scan + stack info
  - Generate DECISIONS.md from stack choices + annotations
  - Generate PATTERNS.md from conventions + stack presets
  - Generate STYLE.md from naming + typescript + linting
  - Generate ANTI-PATTERNS.md from annotations + linting + user info
  - Generate SESSION-STARTER.md (token-budgeted)
  - Output: /tmp/vca/output/*.md
        │
        ▼
[install_context.py]
  - Copy to .ai-context/
  - Respect existing files (ask before overwrite)
  - Write .vca-meta tracking file
        │
        ▼
[create_update_hook.py]
  - Install git post-commit hook
  - Add npm context:update script
  - Output: .git/hooks/post-commit + package.json update
```

---

## Output Quality Standards

### SESSION-STARTER.md Quality Checklist

- [ ] Under 900 tokens (measured by `count_tokens_approx()`)
- [ ] Includes exact stack with versions
- [ ] Has 5+ anti-patterns (most important: AI-specific footguns)
- [ ] Has 6+ key conventions (naming + async + error handling + imports)
- [ ] Has directory map (key dirs only, 6-8 entries)
- [ ] Has "Current Task" placeholder for developer to fill
- [ ] Links to other .ai-context/ files for deeper reference
- [ ] Uses project's actual name, not placeholder

### ANTI-PATTERNS.md Quality Checklist

- [ ] All entries are PROJECT-SPECIFIC (not generic best practices)
- [ ] Each has "why wrong HERE" not just "why wrong in general"
- [ ] Each has "AI often does this when" — the trigger scenario
- [ ] Each has concrete before/after code example where possible
- [ ] Sources: linting rules + annotations + stack-specific footguns + user info

### PATTERNS.md Quality Checklist

- [ ] Code examples are from ACTUAL project files (cited with path)
- [ ] OR from stack presets, clearly marked as "recommended starter"
- [ ] Covers: component structure, API routes, data fetching, state, error handling
- [ ] Language matches the project (TypeScript for TS projects, etc.)

---

## Performance Targets

| Operation | Target | Notes |
|---|---|---|
| Full scan (100 file project) | < 5s | Python file walk |
| Config extraction | < 2s | JSON/YAML parsing |
| Git signals | < 3s | Subprocess calls |
| Annotation mining | < 5s | Regex over source files |
| LLM pattern mining (20 files) | 15-30s | Depends on API latency |
| Document generation | < 3s | String templating |
| Full pipeline (no LLM) | < 15s | Deterministic only |
| Full pipeline (with LLM) | 30-60s | Includes LLM calls |

---

## Known Limitations

1. **LLM pattern mining requires AI** — the pattern-miner sub-agent uses
   Claude API. Scripts alone can extract config facts but not source code patterns.

2. **Monorepos need guidance** — the scanner auto-limits to one package.
   For monorepos, user should specify which package to analyze.

3. **Non-JS/TS projects are partially supported** — Python, Go, Rust projects
   can be scanned but stack detection and pattern extraction are more limited.

4. **Context goes stale** — the update mode helps, but it's pull-based.
   No automatic push notification when context needs updating.

5. **Cannot analyze runtime behavior** — only static code analysis.
   Can't detect which patterns are actually used in production.

---

## Future Roadmap

### v1.1
- [ ] Monorepo support (workspace-aware scanning)
- [ ] Python stack preset (FastAPI, Django)
- [ ] Go stack preset
- [ ] `.cursorrules` export mode (for Cursor IDE)

### v1.2
- [ ] MCP server: expose as `generate_context` tool for Claude Desktop
- [ ] Auto-detect when context is stale via git hook + age check
- [ ] VSCode extension: sidebar showing current context summary

### v2.0
- [ ] Multi-project context: reference conventions from other projects in org
- [ ] Team conventions layer: shared org-wide `.ai-context/` + project-specific
- [ ] LLM-powered conflict resolution (suggest resolution, not just surface)
- [ ] Context quality score: rate how good the context layer is
