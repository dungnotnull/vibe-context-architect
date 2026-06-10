# Extraction Rules by File Type

## What to Extract From Each File Type

### `package.json`
- Exact dependency versions (especially major framework versions)
- Script names and what they do (reveals dev workflow)
- Engine requirements (`engines.node`)
- Workspace config (monorepo detection)
- Custom scripts → reveal project-specific CLI commands

Key signals:
```json
"scripts": {
  "dev": "next dev --turbo",         → uses Turbopack
  "db:push": "prisma db push",       → Prisma workflow
  "db:studio": "prisma studio",      → has DB GUI
  "lint": "eslint . --fix",          → auto-fix linting
  "typecheck": "tsc --noEmit"        → separate typecheck step
}
```

### `tsconfig.json`
Extract:
- `strict: true/false` → TypeScript strictness culture
- `baseUrl` + `paths` → import alias patterns (e.g., `@/` maps to `src/`)
- `target` + `lib` → browser/Node target
- `noImplicitAny` → any-type tolerance
- `exactOptionalPropertyTypes` → strict optional handling

### `.eslintrc` / `biome.json`
Extract:
- Rules set to `"error"` → hard constraints (these become anti-patterns)
- Rules set to `"warn"` → soft conventions
- `no-console` → whether console.log is banned
- `import/order` → import ordering rules
- `@typescript-eslint/no-explicit-any` → any-type policy

### `tailwind.config.ts`
Extract:
- Custom color palette (reveals brand colors to use)
- Custom font families
- Custom breakpoints
- Plugin list (`typography`, `forms`, `animate`, etc.)
- `darkMode` strategy

### `schema.prisma` / `*.sql`
Extract:
- Model naming convention (singular/plural, PascalCase/snake_case)
- Field naming convention (camelCase vs snake_case)
- Relationship patterns (1:N, M:N approach)
- Soft delete pattern (is `deletedAt` used?)
- Audit fields pattern (`createdAt`, `updatedAt` — always present?)
- ID strategy (UUID, CUID, autoincrement)
- Enum usage patterns

### Source Files (`*.ts`, `*.tsx`)
Extract these patterns using LLM analysis:

#### Naming Conventions
```
Components:   PascalCase | kebab-case | SCREAMING_CASE?
Functions:    camelCase | verb-first (getUser) | noun-first (userGet)?
Files:        kebab-case | camelCase | PascalCase?
Constants:    UPPER_SNAKE | camelCase?
Types/Interfaces: PascalCase (I-prefix?) | just PascalCase?
Hooks:        use-prefix always? (useUser, useFetch)
```

#### Error Handling Patterns
```
Try-catch everywhere?
Custom error classes?
Error boundary usage?
Toast notifications for errors? (look for toast() calls)
Sentry/error tracking? (look for Sentry.captureException)
```

#### API / Data Fetching Patterns
```
All in useQuery hooks?
Custom useFetch wrapper?
Direct fetch() calls?
Axios with interceptors?
Server actions (Next.js)?
tRPC procedures?
REST vs RPC style?
```

#### Component Structure Pattern
```
Props interface defined above component?
Default export or named export?
Component size preference? (small, composable vs larger, self-contained)
Co-located CSS module?
Co-located test file?
```

#### Import Patterns
```
Barrel exports (index.ts per folder)?
Path aliases (@/components/..)?
Relative imports (../../) or always absolute?
Import ordering? (external → internal → relative)
```

---

## Git History Signal Extraction

### Commit Message Patterns
From recent 50 commits, detect:
- Format: `feat:`, `fix:`, `chore:` (Conventional Commits)
- Format: `[TICKET-123]` (ticket-prefixed)
- Format: `Add ...`, `Update ...` (imperative verbs)
- Format: freestyle prose
- Average commit size (reveals whether dev commits often or in chunks)

### Branch Naming Patterns
- `feature/ticket-name` vs `feat/ticket-name` vs `123-ticket-name`
- `main` vs `master` vs `dev` as primary branch

### File Change Frequency
Files changed most → currently active areas of codebase
Files never changed → stable, well-established patterns

---

## Annotation Mining (`TODO`, `FIXME`, `HACK`)

### Classification Rules
| Annotation | Meaning | Use In |
|---|---|---|
| `TODO:` | Planned work | DECISIONS.md (planned) |
| `FIXME:` | Known bug/problem | ANTI-PATTERNS.md |
| `HACK:` | Intentional workaround | DECISIONS.md (ADR with status: Temporary) |
| `NOTE:` | Important explanation | PATTERNS.md context |
| `TEMP:` | Temporary code | ANTI-PATTERNS.md |
| `// don't` or `// never` | Explicit prohibition | ANTI-PATTERNS.md |
| `// always` | Explicit rule | PATTERNS.md |
| `// @deprecated` | Deprecated pattern | ANTI-PATTERNS.md |

### Anti-Pattern Mining from Comments
Look for inline warnings like:
```typescript
// Don't use this directly — always go through userService
// Never mutate state here — use the store action
// TODO: Replace with proper auth check before production
// HACK: Supabase real-time doesn't support this natively, workaround below
```

Each of these becomes an entry in ANTI-PATTERNS.md.

---

## Extraction Output Schema

`pattern_raw.json`:
```json
{
  "extracted_at": "ISO8601",
  "source_files_analyzed": 23,
  
  "naming": {
    "components": { "convention": "PascalCase", "confidence": 0.95, "examples": ["UserCard.tsx", "AuthModal.tsx"] },
    "files": { "convention": "kebab-case", "confidence": 0.88, "examples": ["user-service.ts", "auth-utils.ts"] },
    "functions": { "convention": "camelCase-verb-first", "confidence": 0.92, "examples": ["getUser", "createPost"] },
    "constants": { "convention": "UPPER_SNAKE", "confidence": 0.7, "examples": ["MAX_RETRY", "API_BASE_URL"] },
    "types": { "convention": "PascalCase-no-prefix", "confidence": 0.9, "examples": ["User", "PostPayload"] }
  },
  
  "patterns": {
    "error_handling": "try-catch with toast notification",
    "api_calls": "TanStack Query with custom fetcher",
    "state": "Zustand for global, useState for local",
    "component_structure": "named export, props interface above, co-located test",
    "imports": "barrel exports + @/ alias"
  },
  
  "constraints": {
    "no_any_type": true,
    "no_console_log": true,
    "conventional_commits": true
  },
  
  "annotations": [
    {
      "type": "HACK",
      "text": "Supabase doesn't support row-level filtering in real-time, polling instead",
      "file": "src/hooks/useMessages.ts",
      "line": 45
    }
  ],
  
  "inferred_rules": [
    "All async functions use async/await (no .then() chains)",
    "Server components never have 'use client' directive",
    "Every Prisma query wrapped in service layer function"
  ]
}
```
