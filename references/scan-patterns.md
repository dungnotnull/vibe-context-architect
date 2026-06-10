# Scan Patterns Reference

## File Scanner Rules

### Always Include
```
src/, app/, lib/, utils/, hooks/, components/, pages/, api/,
server/, client/, shared/, common/, core/, features/, modules/,
config/, types/, models/, services/, stores/, contexts/,
*.config.ts, *.config.js, *.config.mjs,
package.json, package-lock.json, pnpm-lock.yaml, yarn.lock,
tsconfig.json, tsconfig.*.json,
.eslintrc*, .prettierrc*, biome.json,
Dockerfile, docker-compose.yml, docker-compose.yaml,
.env.example, .env.template,
*.prisma, schema.sql, *.migration.ts,
README.md, CONTRIBUTING.md, CHANGELOG.md,
*.test.ts, *.spec.ts, *.test.tsx, *.spec.tsx (sample, not all),
.github/workflows/*.yml
```

### Always Skip
```
node_modules/, .git/, dist/, build/, .next/, .nuxt/,
out/, coverage/, .turbo/, .cache/, __pycache__/,
*.min.js, *.min.css, *.bundle.js,
*.jpg, *.png, *.gif, *.svg, *.ico, *.woff*, *.ttf,
*.lock (except for stack detection),
*.generated.ts, *.generated.js,
storybook-static/, .storybook/ (scan config only),
```

### Scan Depth Limits
- Max file tree depth: 4 levels from root
- Max source files to deep-read: 40 (take top by priority score)
- Max file size for full read: 500 lines (read first 200 + last 50 for larger)
- Max total tokens for scan phase: ~60,000

---

## Stack Detection Signals

### Frontend Frameworks
| Signal | Framework |
|---|---|
| `"next"` in package.json deps + `app/` or `pages/` dir | Next.js |
| `"nuxt"` in deps | Nuxt.js |
| `"@remix-run/react"` in deps | Remix |
| `"astro"` in deps | Astro |
| `"svelte"` in deps | SvelteKit |
| `vite.config.*` + `"react"` in deps | Vite + React |
| `"react-native"` in deps | React Native |
| `"expo"` in deps | Expo (React Native) |
| `angular.json` present | Angular |

### Backend Frameworks
| Signal | Framework |
|---|---|
| `"express"` in deps | Express.js |
| `"fastify"` in deps | Fastify |
| `"hono"` in deps | Hono |
| `"@nestjs/core"` in deps | NestJS |
| `"elysia"` in deps | ElysiaJS (Bun) |
| `requirements.txt` + `django` | Django |
| `requirements.txt` + `fastapi` | FastAPI |

### Database / ORM
| Signal | Tool |
|---|---|
| `schema.prisma` present | Prisma ORM |
| `"drizzle-orm"` in deps | Drizzle ORM |
| `"typeorm"` in deps | TypeORM |
| `"mongoose"` in deps | MongoDB + Mongoose |
| `"@supabase/supabase-js"` | Supabase |
| `"@vercel/postgres"` or `"pg"` | PostgreSQL |
| `"better-sqlite3"` or `"bun:sqlite"` | SQLite |

### Auth
| Signal | Tool |
|---|---|
| `"next-auth"` or `"@auth/core"` | NextAuth / Auth.js |
| `"@clerk/nextjs"` or `"@clerk/clerk-sdk-node"` | Clerk |
| `"lucia-auth"` | Lucia |
| `"@kinde-oss/kinde-auth-nextjs"` | Kinde |

### State Management
| Signal | Tool |
|---|---|
| `"zustand"` in deps | Zustand |
| `"jotai"` in deps | Jotai |
| `"@reduxjs/toolkit"` | Redux Toolkit |
| `"@tanstack/react-query"` | TanStack Query |
| `"swr"` | SWR |

### Styling
| Signal | Tool |
|---|---|
| `tailwind.config.*` present | Tailwind CSS |
| `"@emotion/react"` | Emotion (CSS-in-JS) |
| `"styled-components"` | Styled Components |
| `*.module.css` files | CSS Modules |
| `"@shadcn/ui"` or `components/ui/` dir | shadcn/ui |

---

## Priority Scoring Algorithm

Score each file 0-100 for analysis priority:

```python
PRIORITY_SCORES = {
    # Highest priority
    "README.md": 95,
    "schema.prisma": 90,
    "package.json": 90,
    "tsconfig.json": 85,
    
    # High priority — entry points
    "src/index.ts": 85,
    "src/main.ts": 85,
    "src/app.ts": 85,
    "app/layout.tsx": 80,   # Next.js
    "src/routes/index.ts": 80,
    
    # High priority — config
    "*.config.ts": 75,
    ".eslintrc*": 70,
    ".env.example": 70,
    "Dockerfile": 65,
    
    # Medium priority — feature samples
    "src/components/*.tsx": 60,
    "src/app/api/**/*.ts": 65,
    "src/services/**/*.ts": 65,
    "src/lib/**/*.ts": 60,
    "src/hooks/**/*.ts": 60,
    "src/utils/**/*.ts": 55,
    
    # Lower priority — tests (read selectively)
    "*.test.ts": 40,
    "*.spec.ts": 40,
}

# Boost scores for files that have been recently modified
# (from git log --since=30days): +15 points
```

---

## Project Size Classification

| Files | Classification | Strategy |
|---|---|---|
| < 50 source files | Tiny | Read all source files |
| 50-200 source files | Small | Read top 40 by priority |
| 200-500 source files | Medium | Read top 30, sample features |
| 500-1000 source files | Large | Read top 20, focus on config + entry |
| > 1000 source files | XL | Read top 15, ask user to highlight key dirs |

---

## Canonical Scan Output Schema

```json
{
  "project_name": "my-saas-app",
  "root_path": "/home/user/projects/my-saas-app",
  "scanned_at": "ISO8601",
  "classification": "Small",
  
  "stack": {
    "frontend": "Next.js 14 (App Router)",
    "language": "TypeScript 5.3",
    "runtime": "Node.js 20",
    "styling": "Tailwind CSS + shadcn/ui",
    "state": "Zustand + TanStack Query",
    "database": "PostgreSQL + Prisma",
    "auth": "Clerk",
    "deployment": "Vercel",
    "package_manager": "pnpm",
    "test_framework": "Vitest + Testing Library"
  },
  
  "structure": {
    "src/app": "Next.js App Router pages and API routes",
    "src/components": "Shared React components",
    "src/lib": "Utility functions and configs",
    "src/hooks": "Custom React hooks",
    "src/services": "Business logic and data access",
    "src/store": "Zustand state stores",
    "src/types": "TypeScript type definitions",
    "prisma": "Database schema and migrations"
  },
  
  "entry_points": ["src/app/layout.tsx", "src/app/page.tsx"],
  "config_files": ["tsconfig.json", "tailwind.config.ts", "..."],
  "test_files_count": 23,
  "total_source_files": 89,
  
  "priority_files": [
    { "path": "schema.prisma", "score": 90, "reason": "Database schema" },
    { "path": "src/app/layout.tsx", "score": 80, "reason": "App entry point" }
  ]
}
```
