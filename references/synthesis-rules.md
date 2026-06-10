# Synthesis Rules & Conflict Resolution

## Conflict Resolution Algorithm

When the same convention appears inconsistently across the codebase,
apply the following resolution strategy:

### 1. Majority Rule (>70% threshold)
If one pattern appears in >70% of cases, it wins.
```
Components: PascalCase (67/78 files = 86%) → Convention: PascalCase ✅
```

### 2. Recency Bias (60-70% threshold)
If split 60/40 but newer files consistently use one pattern, the newer pattern wins.
Convention note: "Transitioning from X to Y — use Y for new files."

### 3. User Decision (40-60% split or semantic conflict)
Genuine ambiguity — must ask the user. Do NOT guess.

### 4. Config File Authority
If `.eslintrc` or `tsconfig.json` explicitly defines a rule,
that overrides all observed patterns.
```
.eslintrc: { "@typescript-eslint/no-explicit-any": "error" }
→ Convention: never use `any` (regardless of how many `any` appear in old code)
Note: "Legacy code violates this — do not replicate."
```

---

## Inferring Implicit Rules

### High-Confidence Inferences (state as facts)

| Observation | Inferred Rule |
|---|---|
| All async code uses `async/await`, zero `.then()` | "Use async/await, never .then() chains" |
| Every component has co-located `*.test.tsx` | "Every component gets a test file" |
| All API handlers return `{ data, error }` shape | "API responses always use `{ data, error }` envelope" |
| No `console.log` anywhere in production code | "Use logger utility, not console.log" |
| All `useEffect` have cleanup functions | "Always clean up useEffect subscriptions" |
| All colors use CSS variables, no hardcoded hex | "Colors from design tokens only" |
| All DB queries behind service layer | "Never query DB directly in route/component" |

### Medium-Confidence Inferences (state with caveat)

| Observation | Inferred Rule | Caveat |
|---|---|---|
| Most exports are named, ~10% are default | "Prefer named exports" | "exceptions for page components (Next.js requires default)" |
| Most files < 150 lines | "Keep files small, extract when > 150 lines" | "service layer files are an exception" |

### Requiring User Confirmation

Ambiguous patterns that AI should NOT infer without asking:
- Mix of `interface` and `type` for objects
- Mix of `function` declaration and arrow function components
- Mix of `export const X = () =>` and `export function X()`
- Multiple state management approaches with unclear separation
- Multiple ways to do the same thing (2+ fetch utilities)

---

## Convention Output Schema

`conventions.json`:
```json
{
  "synthesized_at": "ISO8601",
  "resolution_log": [
    {
      "convention": "component_naming",
      "winner": "PascalCase",
      "resolution_method": "majority_rule",
      "confidence": 0.86,
      "note": null
    },
    {
      "convention": "export_style",
      "winner": "named_exports",
      "resolution_method": "user_decision",
      "user_answer": "named exports, except page.tsx files which must default export",
      "confidence": 1.0
    }
  ],

  "conventions": {
    "naming": {
      "component_files": "PascalCase.tsx",
      "non_component_files": "kebab-case.ts",
      "component_functions": "PascalCase",
      "utility_functions": "camelCase, verb-first (getUser, createPost, formatDate)",
      "react_hooks": "camelCase, use-prefix required (useUser, useAuth)",
      "constants": "UPPER_SNAKE_CASE in constants files, camelCase if local",
      "types": "PascalCase, no I-prefix, Type suffix for unions (UserStatus)",
      "prisma_models": "PascalCase singular (User, not Users)",
      "api_routes": "kebab-case (/api/user-sessions, not /api/userSessions)",
      "env_variables": "UPPER_SNAKE_CASE (NEXT_PUBLIC_ prefix for browser-exposed)"
    },

    "structure": {
      "component_exports": "named export only (except app/*/page.tsx, layout.tsx)",
      "imports": "@/ alias for src/, relative only within same folder",
      "barrel_exports": "yes — each feature folder has index.ts",
      "props_interface": "defined above component, named ComponentNameProps",
      "test_colocation": "co-located *.test.tsx next to every component"
    },

    "code_style": {
      "async_pattern": "async/await only, no .then() chains",
      "error_handling": "try-catch in async functions, toast for user-facing errors",
      "type_strictness": "no `any` type — use `unknown` with type guards",
      "null_handling": "optional chaining (?.) over null checks",
      "state_updates": "Zustand actions for global, useState for component-local"
    },

    "api_patterns": {
      "data_fetching": "TanStack Query for all server data, no raw fetch in components",
      "mutations": "useMutation hook with onSuccess/onError callbacks",
      "response_shape": "{ data: T | null, error: string | null }",
      "auth_check": "middleware.ts + useSession hook, never manual in components"
    },

    "database": {
      "access_layer": "service functions in src/services/ only",
      "id_format": "CUID2 (createId from @paralleldrive/cuid2)",
      "soft_delete": "yes — deletedAt: DateTime? on most models",
      "audit_fields": "createdAt and updatedAt on all models"
    },

    "git": {
      "commit_format": "Conventional Commits (feat: fix: chore: docs: refactor:)",
      "branch_format": "feature/short-description or fix/short-description"
    }
  },

  "constraints_hard": [
    "Never use `any` TypeScript type",
    "Never console.log in production (use logger)",
    "Never query database outside service layer",
    "Never skip error handling in async functions"
  ],

  "inferred_rules": [
    { "rule": "Always use async/await, never .then() chains", "confidence": 0.97 },
    { "rule": "Every new component gets a co-located test file", "confidence": 0.89 }
  ],

  "anti_patterns": [
    {
      "pattern": "Direct Prisma queries in route handlers",
      "why": "Violates service layer architecture — found in 2 legacy files only",
      "instead": "Create a function in src/services/ and call that",
      "legacy_files": ["src/app/api/admin/users/route.ts (line 34)"]
    }
  ]
}
```

---

## Scoring Conventions for SESSION-STARTER.md Compression

The SESSION-STARTER.md must be ~800 tokens. Priority order for what to include:

1. **Must include** (always): Stack versions, project name/purpose, folder map
2. **Must include** (always): Top 5 anti-patterns (what AI gets wrong most)
3. **High value**: Component naming + file naming conventions
4. **High value**: API response shape + data fetching approach
5. **Medium value**: Import/export patterns
6. **Low value** (summarize only): Git commit format, test colocation
7. **Omit** (link to PATTERNS.md): Full code examples, detailed ADRs

Compression rules:
- Replace code examples with one-line descriptions
- Collapse similar rules into one rule
- Use bullet points, never prose paragraphs
- Cut any rule that's already enforced by linting (redundant)
