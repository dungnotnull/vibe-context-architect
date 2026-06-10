# 🧠 Vibe Context Architect

> **Stop re-explaining your project to AI every single session.**
> Build a permanent AI memory layer that makes any new chat instantly understand
> your codebase, conventions, and architectural decisions.

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)](https://claude.ai)
[![For Vibe Coders](https://img.shields.io/badge/For-Vibe%20Coders-purple)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## The Problem

You're a vibe coder. You build fast with AI. But after a few weeks:

- Claude keeps suggesting patterns that don't match your stack
- Every new session starts with 10 minutes of "here's what my project does..."
- AI adds `use client` to every component (you use Next.js Server Components)
- AI writes database queries directly in route handlers (you have a service layer)
- AI uses `.then()` chains (you use async/await exclusively)
- Your codebase is getting inconsistent because AI doesn't know your conventions

**The root cause:** AI has no memory. Every session starts blank.

**The solution:** A structured `.ai-context/` folder that gives AI everything
it needs to know in the first ~800 tokens of any session.

---

## What It Builds

```
your-project/
└── .ai-context/
    ├── SESSION-STARTER.md    ← Paste at start of any AI chat (~800 tokens)
    ├── CONTEXT.md            ← Full project briefing (stack, structure, models)
    ├── DECISIONS.md          ← Why things are built this way (ADR log)
    ├── PATTERNS.md           ← How to add new things (with real code examples)
    ├── STYLE.md              ← Naming rules and code style conventions
    └── ANTI-PATTERNS.md      ← What NOT to do (AI-specific guardrails)
```

**SESSION-STARTER.md is the key file.** Copy its contents. Paste at the top
of any new AI chat. Done — Claude now knows your full project in seconds.

---

## How to Use It

### Option A — Tell Claude (Recommended)

Just describe your problem:

```
"My Next.js project is getting big and AI keeps forgetting my conventions.
I use TypeScript strict mode, Prisma for DB with a service layer, 
Zustand for state, and TanStack Query for data fetching. 
Build my AI context layer."
```

Claude will automatically run the Vibe Context Architect skill and guide you
through all 5 phases.

### Option B — Use the Scripts

```bash
git clone https://github.com/your-org/vibe-context-architect
pip install pyyaml  # optional, for YAML support

# Scan your project
python scripts/scan_project.py --root ./my-project --output /tmp/vca/scan_result.json

# Extract config facts
python scripts/extract_configs.py --scan /tmp/vca/scan_result.json --output /tmp/vca/config_facts.json

# Mine git + annotations
python scripts/extract_signals.py --root ./my-project --output /tmp/vca/git_signals.json --mode git
python scripts/extract_signals.py --root ./my-project --output /tmp/vca/annotations.json --mode annotations

# Synthesize conventions
python scripts/resolve_conflicts.py --configs /tmp/vca/config_facts.json --annotations /tmp/vca/annotations.json --output /tmp/vca/conventions.json

# Generate context files
python scripts/generate_context.py --scan /tmp/vca/scan_result.json --configs /tmp/vca/config_facts.json --annotations /tmp/vca/annotations.json --conventions /tmp/vca/conventions.json --output /tmp/vca/output/

# Install to your project
python scripts/install_context.py --source /tmp/vca/output/ --target ./my-project/.ai-context/
```

### Option C — Keep It Fresh (Update Mode)

```bash
# After making major changes
python scripts/update_context.py \
  --root ./my-project \
  --since "7 days ago" \
  --existing .ai-context/ \
  --output .ai-context/
```

Or install the git hook to get a reminder:

```bash
python scripts/create_update_hook.py --root ./my-project --mode git-hook
```

---

## The 5-Phase Process

```
Phase 1: SCAN       Map project topology, detect stack, rank files
    │
Phase 2: EXTRACT    Mine configs, git history, annotation comments
    │
Phase 3: SYNTHESIZE Resolve conflicts, infer implicit rules, ask user
    │
Phase 4: GENERATE   Write all 6 context files from synthesized data
    │
Phase 5: INSTALL    Place in .ai-context/, set up update hooks
```

---

## Output Example

### SESSION-STARTER.md (what you paste into every chat)

```markdown
# my-saas-app — AI Context Starter

You are working on **my-saas-app**: a B2B SaaS platform for team task management.

## Stack
Next.js 14 (App Router) · TypeScript Strict · Tailwind + shadcn/ui · 
Prisma + PostgreSQL · Clerk Auth · Zustand · TanStack Query · Vercel

## Project Structure
  src/app/           Next.js App Router pages + API routes
  src/components/    Shared React components (PascalCase named exports)
  src/services/      ALL database queries live here — never elsewhere
  src/store/         Zustand stores
  src/hooks/         Custom React hooks (use- prefix)
  src/lib/           Utility functions + configs

## Key Conventions
- Component naming: PascalCase.tsx, named exports only
- DB access: ONLY through src/services/ — never direct Prisma in routes/components
- Async: async/await everywhere — no .then() chains
- Imports: @/ alias for src/, barrel exports per folder
- State: Zustand (global) + useState (local only)
- API response: { data: T | null, error: string | null }

## ❌ Never Do These
- ❌ Direct Prisma/DB calls in route handlers — use service layer
- ❌ Adding 'use client' to components that don't need it
- ❌ console.log in production (eslint no-console: error)
- ❌ TypeScript `any` type (eslint no-explicit-any: error)
- ❌ .then() chains — use async/await

## Current Task
[Describe what you're building here]
```

---

## What Gets Detected Automatically

### Stack Detection
| Category | Detected From |
|---|---|
| Frontend framework | `package.json` deps + directory structure |
| Database / ORM | `package.json` + `schema.prisma` existence |
| Auth provider | `package.json` deps |
| State management | `package.json` deps |
| Styling approach | `tailwind.config.*`, `package.json` |
| Test framework | `package.json` devDeps |
| Deployment | `vercel.json`, `fly.toml`, `Dockerfile`, etc. |

### Convention Mining
| Convention | Extracted From |
|---|---|
| TypeScript strictness | `tsconfig.json` |
| Linting hard rules → anti-patterns | `.eslintrc` / `biome.json` |
| No console.log rule | ESLint `no-console: error` |
| No `any` type rule | ESLint `no-explicit-any: error` |
| Import aliases | `tsconfig.json` paths |
| DB conventions | `schema.prisma` field naming, ID strategy |
| Anti-patterns | `FIXME`, `HACK`, `// don't`, `// never` comments |
| Commit format | Git log analysis |

---

## Supported Stacks

**Fully supported (presets + detection):**
- Next.js 14+ (App Router)
- Next.js (Pages Router)
- React + Vite
- SvelteKit
- Nuxt 3
- Remix
- Node.js + Express/Fastify/Hono
- Bun + ElysiaJS

**Partially supported (detection, no preset):**
- Angular, Vue, Solid
- Python (FastAPI, Django) — roadmap v1.1
- Go — roadmap v1.1

---

## Keeping Context Fresh

Context goes stale as your project evolves. Three ways to keep it updated:

**1. Git hook (automatic reminder):**
```bash
python scripts/create_update_hook.py --root . --mode git-hook
# Now warns you when significant files change
```

**2. npm script:**
```bash
npm run context:update  # added by create_update_hook.py
```

**3. Manual on schedule:**
Run the update command after any sprint where you:
- Added new Prisma models
- Changed state management approach
- Added new route patterns
- Changed linting rules
- Made significant architectural decisions

---

## For Teams

Commit `.ai-context/` to git so everyone (and every AI session) benefits:

```bash
git add .ai-context/
git commit -m "chore: initialize AI context layer"
```

Now every team member's AI sessions share the same conventions.
New team members get instant project context.
AI-assisted code reviews use the same guardrails.

---

## Project Structure

```
vibe-context-architect/
├── SKILL.md                              ← Claude agent 5-phase workflow
├── CLAUDE.md                             ← AI agent behavior instructions
├── README.md                             ← This file
├── PROJECT-detail.md                     ← Architecture & design decisions
├── PROJECT-DEVELOPMENT-PHASE-TRACKING.md ← Sprint & milestone tracker
│
├── references/                           ← Sub-skill reference docs
│   ├── scan-patterns.md                  ← File scanning rules + stack signals
│   ├── extraction-rules.md               ← What to extract from each file type
│   ├── synthesis-rules.md                ← Conflict resolution algorithm
│   ├── output-templates.md               ← Output file templates
│   └── stack-presets.md                  ← Opinionated conventions per stack
│
├── scripts/                              ← Python pipeline (deterministic core)
│   ├── README.md                         ← Script index + usage
│   ├── utils.py                          ← Shared utilities
│   ├── scan_project.py                   ← Phase 1
│   ├── extract_configs.py                ← Phase 2
│   ├── extract_signals.py                ← Phase 2 (git + annotations)
│   ├── resolve_conflicts.py              ← Phase 3
│   ├── generate_context.py               ← Phase 4 (all 6 files)
│   ├── install_context.py                ← Phase 5
│   ├── create_update_hook.py             ← Phase 5
│   ├── update_context.py                 ← Update mode
│   └── diff_context.py                   ← Preview changes before install
│
├── hooks/
│   └── pre-commit-context-check.py       ← Staleness reminder hook
│
├── templates/                            ← Markdown starting templates
│   ├── SESSION-STARTER.template.md
│   └── CONTEXT.template.md
│
├── agents/
│   └── pattern-miner.md                  ← LLM sub-agent for source analysis
│
├── assets/
│   └── vscode-snippets.json              ← VSCode snippet helpers
│
└── evals/
    └── evals.json                        ← 4 evaluation scenarios
```

---

## Requirements

- Python 3.11+
- `pyyaml` (optional, for YAML config files): `pip install pyyaml`
- `git` (for git signals extraction)

---

## License

MIT — see LICENSE file.

---

*Built as a Claude Skill for the vibe coding generation.*
*The AI memory layer your project deserves.*
