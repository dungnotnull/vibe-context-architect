# Stack Presets — Opinionated Conventions for Common Stacks

Use these when generating context for a new project (no existing code to analyze),
or to supplement analysis of an early-stage project with best-practice defaults.

---

## Preset: Next.js 14+ App Router + TypeScript + Tailwind + Prisma

### Opinionated Conventions
```
Component naming:       PascalCase.tsx
Page files:             page.tsx (Next.js default export required)
Layout files:           layout.tsx
API routes:             route.ts (named exports: GET, POST, etc.)
Utility files:          kebab-case.ts
Hook files:             use-hook-name.ts (camelCase with use- prefix)
Service files:          user.service.ts OR user-service.ts

Import alias:           @/ maps to src/
State management:       Zustand (global) + useState (local)
Data fetching:          TanStack Query for client, direct in Server Components
API response:           { data: T | null, error: string | null }
Auth check:             middleware.ts + useSession, never in components
DB access:              src/services/ or src/lib/db.ts only
```

### ADRs to Pre-generate
1. App Router over Pages Router — performance, streaming, server components
2. Prisma over raw SQL — type safety, migrations, DX
3. Tailwind over CSS modules — utility-first, no context switching
4. Server Components by default — client components only when needed
5. Zustand over Redux — simpler, less boilerplate for most apps

### Common Anti-Patterns for This Stack
- Using `useEffect` for data fetching (use TanStack Query or Server Components)
- `"use client"` at top of every component (only where needed)
- Direct Prisma calls in `page.tsx` (use service layer)
- Mixing `fetch` and TanStack Query in the same project
- JWT in localStorage (use httpOnly cookies via Next-Auth)

---

## Preset: React + Vite + TypeScript + TanStack Router

### Opinionated Conventions
```
Router:                 TanStack Router (file-based routes in src/routes/)
Component pattern:      Named export, props interface above, default at bottom
State:                  Zustand global + TanStack Query server state
API:                    Axios with instance in src/lib/axios.ts
Error handling:         React Error Boundary + toast notifications
Testing:                Vitest + Testing Library + MSW for mocking
```

### Common Anti-Patterns
- React Router v5 patterns (if migrated from CRA)
- Prop drilling past 2 levels (use Zustand or Context)
- Global CSS over CSS Modules or Tailwind
- Direct API calls in components (use TanStack Query)

---

## Preset: Node.js + Express/Fastify + TypeScript + PostgreSQL

### Opinionated Conventions
```
Route structure:        src/routes/{resource}.routes.ts
Controller pattern:     src/controllers/{resource}.controller.ts
Service pattern:        src/services/{resource}.service.ts
Middleware:             src/middleware/{name}.middleware.ts
Validation:             Zod schemas co-located with routes
Error handling:         Custom AppError class + global error middleware
Auth:                   JWT + refresh tokens, middleware-based
Response shape:         { success: bool, data: T | null, error: string | null, meta?: {} }
```

### ADRs to Pre-generate
1. Layered architecture (routes → controllers → services → DB)
2. Zod for runtime validation — type safety at boundary
3. Custom error classes — consistent error handling
4. Repository pattern — DB logic isolated

---

## Preset: SvelteKit + TypeScript + Drizzle + Tailwind

### Opinionated Conventions
```
Pages:                  +page.svelte (SvelteKit convention)
Layouts:                +layout.svelte
Endpoints:              +server.ts
Store:                  Svelte stores ($store syntax)
Database:               Drizzle ORM with src/lib/db.ts
Schema:                 src/lib/schema.ts
```

---

## Preset: Nuxt 3 + TypeScript + Pinia + Prisma

### Opinionated Conventions
```
Pages:                  Auto-imported from pages/
Composables:            src/composables/use*.ts
Stores:                 src/stores/*.ts (Pinia)
API:                    server/api/**/*.ts
Middleware:             server/middleware/*.ts
Utils:                  Auto-imported from utils/
```

---

## Preset: Bun + ElysiaJS + TypeScript + Drizzle

### Opinionated Conventions
```
Router:                 Elysia route chaining
Validation:             Elysia's built-in schema (based on TypeBox)
Database:               Drizzle with Bun's SQLite or PostgreSQL
Auth:                   Elysia JWT plugin
Testing:                Bun's built-in test runner
```

---

## Generic Anti-Patterns (All Stacks)

These apply regardless of stack and should appear in every project's ANTI-PATTERNS.md:

```markdown
## ❌ Hardcoded secrets / credentials
Use environment variables. Never commit .env files.

## ❌ Catching errors silently
Every catch block must either log or re-throw. Silent catches hide bugs.

## ❌ N+1 database queries
Always check whether a loop makes individual DB calls. Use eager loading.

## ❌ Missing loading/error states in UI
Every async operation needs loading and error UI states.

## ❌ Untyped `response.json()` calls
Always type API responses: `const data = await res.json() as UserResponse`
```
