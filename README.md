# ts-agent-skills

AI agent skills for **TypeScript** full-stack development — React, Next.js, and
Node.js — clean architecture boundaries, real decision guidance where the ecosystem
is genuinely contested (state management, ORM, auth), and explicit review loops
before code is generated.

Sibling collection to [`kmp-agent-skills`](https://github.com/ronjunevaldoz/kmp-agent-skills)
(Kotlin Multiplatform), applying the same toolchain-scoped-skills model — TypeScript
is the unifying toolchain here the way Kotlin+Gradle is there.

---

## Skills

18 skills covering the TypeScript/Next.js/Node stack. Load the smallest set that
answers the request. Start with `ts-expert` to get routed to the right skill.

### Foundation & Architecture Contract
- `ts-project-foundation` — tsconfig, ESLint/Prettier, pnpm workspaces + Turborepo, package boundaries
- `ts-nextjs-app-router` — Server vs Client Component boundary, layouts, Server Actions, middleware
- `ts-ci-github-actions` — CI pipeline: lint, typecheck, test, build, Turborepo caching
- `ts-state-management` — Redux Toolkit vs Zustand vs Context decision
- `ts-validation-schema` — Zod as the shared runtime-validation backbone

### Core Infrastructure
- `ts-api-layer` — tRPC vs REST route handlers decision
- `ts-orm-database` — SQL default, Prisma vs Drizzle decision
- `ts-mongodb` — document-database alternative to `ts-orm-database`
- `ts-auth` — Auth.js vs Clerk vs Lucia decision
- `ts-deploy-vercel` — Vercel deployment, env vars, Edge vs Node runtime
- `ts-resilience` — retry/backoff, circuit breaker, timeout, rate limiting, idempotency keys, "last seat" contention
- `ts-background-jobs` — Vercel Cron, QStash, BullMQ/Inngest decision for work that can't run inline

### Feature Building Blocks
- `ts-forms` — React Hook Form + Zod
- `ts-data-fetching` — TanStack Query, the server-state counterpart to `ts-state-management`, cursor-based pagination

### UI System
- `ts-shadcn-ui` — shadcn/ui component system (Base UI default as of July 2026, Radix still supported)

### Testing & Quality
- `ts-testing-vitest` — Vitest + React Testing Library, unit/component tests
- `ts-testing-playwright` — Playwright, e2e tests

### Meta
- `ts-expert` — routing, dependency order, decision trees for the full skill set

---

## Usage

```
@ts-expert what should I do next?
```

Or trigger a skill directly by keyword — each `SKILL.md`'s **Trigger keywords** line
fires automatically when your prompt matches.

---

## Related

- [`kmp-agent-skills`](https://github.com/ronjunevaldoz/kmp-agent-skills) — the sibling Kotlin Multiplatform collection this repo's conventions are ported from
- [`docs/reference/versioning-policy.md`](docs/reference/versioning-policy.md) — commit format, release tiers
- [`PLAN.md`](PLAN.md) — roadmap, deferred v2 skills
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — confirmed agent behavior gaps and workarounds
