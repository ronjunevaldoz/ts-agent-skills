---
name: ts-expert
description: >
  TS Expert Orchestrator — maps every skill in this collection, their dependency
  order, and how to sequence them for a TypeScript/Next.js project. This is a
  meta-routing skill: it does not implement anything itself. Load it first for
  any non-trivial TypeScript/Next.js architecture task to get routed to the
  right skill — the skill map, dependency graph, decision trees, and the
  Skill Invocation Map below all exist to answer "which skill do I use here?"
  before any code gets written. Critically: a request to create, build, or
  scaffold a new TypeScript/Next.js project (including a take-home exam, a
  spec from an external doc, or a generic "use ts-agent-skills to build this")
  must be routed to the /ts-new-project command, never implemented ad hoc —
  that command owns the plan-confirmation gate, wireframe step, and full
  build order this collection exists to provide.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-10'
  keywords:
    - routing
    - expert
    - skill map
    - decision tree
    - TypeScript architecture
    - Next.js architecture
    - orchestrator
    - meta-skill
    - dependency graph
    - build order
    - which skill
    - skill sequencing
    - new project
    - create a project
    - scaffold a project
    - build this app
    - take-home
    - ts-agent-skills
---

## When to Use This Skill

Use when you need to:
- Start a new TypeScript/Next.js project and don't know which skills to invoke or in
  what order
- Add a feature that spans multiple layers (data + API + form + UI) and need the right
  skill for each layer
- Decide which skill answers a specific question ("where do I put this?", "which
  pattern fits?")
- Get a high-level roadmap before diving into implementation

**Trigger keywords:** which skill, ts-expert, skill order, TypeScript architecture
decision, Next.js architecture decision, skill map, build order, dependency graph,
where do I start, project plan, what do I use here, new project, create a project,
scaffold a project, build this app, take-home, use ts-agent-skills.

**A request to build a new project is a command dispatch, not an implementation task.**
"Use ts-agent-skills to create this project," "build this from the spec in this doc,"
or any other from-scratch project request means: read this skill for context, then
run `/ts-new-project <description>` — do not start writing Next.js code directly.
Skipping the command is the confirmed, real failure mode: it skips the plan-confirmation
gate (so nothing gets analyzed/summarized before code is written, even when explicitly
asked for), and skips every downstream skill (`ts-shadcn-ui`, `ts-layout-system`,
`ts-orm-database`, etc.) in favor of generic, un-routed Next.js knowledge.

**Freshness rule:** recheck the skill count, the layer tables, and the Skill
Invocation Map whenever a skill is added or removed from `skills/` — the routing
table must stay in sync with the actual directories. Run
`python3 skills/ts-expert/scripts/validate_skill_map.py --repo-root .` and
`python3 skills/ts-expert/scripts/validate_keyword_routing.py --repo-root .` after any
skill addition.

---

## Recommendation First

Load this skill first for any non-trivial task. Do not implement here — route to the
specific skill that owns the layer in question, then hand off.

Why:
- the skill collection grows; a recommendation based on a stale skill list misroutes work
- the dependency graph below defines the correct build order — skipping foundation
  skills causes downstream failures (e.g. building an API layer before the ORM contract
  is settled)
- routing to the wrong skill wastes a context window on the wrong patterns

---

## The 19 Skills and What They Own

### Foundation & Architecture Contract
| Skill | Owns |
|---|---|
| `ts-project-foundation` | Monorepo layout, tsconfig strict-mode baseline, ESLint flat config, pnpm workspaces + Turborepo, package boundary rules |
| `ts-nextjs-app-router` | Server vs Client Component boundary, layouts and route groups, Server Actions, middleware |
| `ts-layout-system` | Low-fidelity screen wireframes (dev-only routes), drafted before real components |
| `ts-ci-github-actions` | CI pipeline — lint, typecheck, test, build, Turborepo remote caching |

### Core Infrastructure
| Skill | Owns |
|---|---|
| `ts-validation-schema` | Zod schemas as the single source of runtime + compile-time type validation |
| `ts-orm-database` | SQL default, Prisma vs Drizzle decision, schema/migration workflow, connection pooling |
| `ts-mongodb` | Document-database alternative to `ts-orm-database` — Mongoose vs native driver, change streams, indexing |
| `ts-api-layer` | tRPC vs REST decision, API contract shape, request/response typing |
| `ts-auth` | Auth.js vs Clerk vs Lucia decision, session handling, route protection |
| `ts-deploy-vercel` | Vercel deployment, environment variables, preview deployments, edge vs node runtime |
| `ts-resilience` | Retry/backoff, circuit breaker, timeout, rate limiting, idempotency keys, limited-resource ("last seat") contention |
| `ts-background-jobs` | Work that can't run inline in a request — Vercel Cron, QStash, BullMQ/Inngest decision |

### Feature Building Blocks
| Skill | Owns |
|---|---|
| `ts-state-management` | Redux vs Zustand vs Context decision for client-side state |
| `ts-forms` | React Hook Form + Zod integration, form state, submit handling |
| `ts-data-fetching` | TanStack Query — client-side fetching, caching, mutation, invalidation |

### UI System
| Skill | Owns |
|---|---|
| `ts-shadcn-ui` | shadcn/ui component system — install, theme, compose components |

### Testing & Quality
| Skill | Owns |
|---|---|
| `ts-testing-vitest` | Unit and component tests with Vitest |
| `ts-testing-playwright` | End-to-end tests with Playwright |

### Meta
| Skill | Owns |
|---|---|
| `ts-expert` | This skill — routing, dependency graph, decision trees, build order |

---

## Dependency Graph

Build order runs foundation before app architecture before infrastructure before
features before UI before testing/deploy:

```
ts-project-foundation
        |
ts-nextjs-app-router
        |
ts-layout-system
        |
ts-ci-github-actions
        |
ts-validation-schema
        |
ts-orm-database (or ts-mongodb)
        |
ts-api-layer
        |
   +----+----+
ts-resilience   ts-background-jobs
        |
ts-auth
        |
ts-state-management
        |
   +----+----+
ts-forms   ts-data-fetching
        |
ts-shadcn-ui
        |
   +----+----+
ts-testing-vitest   ts-testing-playwright
        |
ts-deploy-vercel
```

Each layer assumes the one above it is already decided. Skipping straight to
`ts-api-layer` before `ts-validation-schema` and `ts-orm-database` are settled means the
API contract has nothing stable to validate against or query.

## Build Order for a New Project

1. `ts-project-foundation` — monorepo layout, tsconfig, ESLint
2. `ts-nextjs-app-router` — Server/Client Component boundary, routes
3. `ts-layout-system` — low-fi wireframes per MVP screen, before real components
4. `ts-ci-github-actions` — CI pipeline
5. `ts-validation-schema` — Zod schemas
6. `ts-orm-database` (or `ts-mongodb` — see its Decision Trees entry below) — schema and queries
7. `ts-api-layer` — tRPC/REST
8. `ts-resilience` + `ts-background-jobs` — retry/circuit-breaker/rate-limiting, and offloading long-running work
9. `ts-auth` — Auth.js/Clerk/Lucia
10. `ts-state-management` — Redux/Zustand/Context
11. `ts-forms` + `ts-data-fetching` — form submission and client-side fetching
12. `ts-shadcn-ui` — component system
13. `ts-testing-vitest` + `ts-testing-playwright` — unit/component tests and e2e tests
14. `ts-deploy-vercel` — production deployment

---

## Decision Trees

This skill routes, it doesn't duplicate the full decision logic — each destination
skill owns its own decision table in full.

**Which state management?**
Server-derived data that's cached/refetched → that's `ts-data-fetching` (TanStack
Query), not state management at all. For genuine client-only state, load
`ts-state-management` and use its own decision table (Context vs Zustand vs Redux by
update frequency and cross-tree sharing).

**Which API layer?**
Client and server both TypeScript, same repo → load `ts-api-layer` and use its own
decision table (tRPC is the default there). A public API consumed by non-TS clients,
or a webhook/third-party callback → same skill, REST branch of its table.

**SQL or MongoDB?**
Default to `ts-orm-database` (SQL/Prisma-Drizzle) — real relationships, transactions,
joins cover most apps. Only load `ts-mongodb` instead for genuinely document-shaped or
variable-structure data, or an append-heavy/rarely-joined access pattern (event logs,
time-series) — check `ts-orm-database`'s own note on `JSONB` columns first, since that
often covers the flexibility need without a second database technology at all.

**Does this work need to run in the background?**
Anything that can exceed a serverless function's execution limit (sending a batch of
emails, processing an upload, a slow third-party call) → load `ts-background-jobs` and
use its own decision table (Vercel Cron for scheduled, QStash for one-off event-triggered,
BullMQ/Inngest for complex orchestration). Its retry/idempotency handling is
`ts-resilience`'s job, not duplicated there.

---

## Skill Invocation Map

| Keyword/Task | Skill |
|---|---|
| "set up a monorepo", "tsconfig", "pnpm workspace", "package boundary" | `ts-project-foundation` |
| "Server Component", "Client Component", "use client", "Server Action", "route group" | `ts-nextjs-app-router` |
| "wireframe", "mock UI", "low-fi mockup", "screen layout", "sketch a screen" | `ts-layout-system` |
| "CI pipeline", "GitHub Actions", "Turborepo caching in CI" | `ts-ci-github-actions` |
| "Redux vs Zustand", "Context state", "client state", "global state" | `ts-state-management` |
| "Zod schema", "runtime validation", "parse input" | `ts-validation-schema` |
| "tRPC vs REST", "API contract", "typed API" | `ts-api-layer` |
| "Prisma vs Drizzle", "database schema", "migration" | `ts-orm-database` |
| "MongoDB", "Mongoose", "document database", "change streams" | `ts-mongodb` |
| "Auth.js", "Clerk", "Lucia", "session", "protect a route" | `ts-auth` |
| "deploy to production", "Vercel", "preview deployment", "env vars" | `ts-deploy-vercel` |
| "retry", "circuit breaker", "rate limiting", "idempotency key", "last seat", "timeout" | `ts-resilience` |
| "background job", "queue", "BullMQ", "Inngest", "QStash", "Vercel Cron" | `ts-background-jobs` |
| "add a form", "React Hook Form", "form validation UI" | `ts-forms` |
| "fetch data on the client", "TanStack Query", "cache invalidation" | `ts-data-fetching` |
| "shadcn/ui", "component library", "theme components" | `ts-shadcn-ui` |
| "unit test", "component test", "Vitest" | `ts-testing-vitest` |
| "e2e test", "end-to-end test", "Playwright", "browser test" | `ts-testing-playwright` |
| "which skill", "project plan", "build order", "skill map" | `ts-expert` |

---

## Related Skills

N/A — this skill is the meta-router for the collection. It has no peer skill; every
other skill in `skills/` is a routing destination, not a related skill.

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
| 2026-08-10 | Added `ts-layout-system` (19th skill) — low-fi wireframes, slotted into the Build Order right after `ts-nextjs-app-router`. |
| 2026-08-10 | Confirmed real bug: a generic "use ts-agent-skills to create this project" request never routed to `/ts-new-project` — the agent implemented ad hoc from scratch (skipped `ts-shadcn-ui`, skipped the plan-confirmation gate even when explicitly asked to analyze first). Added explicit routing instruction + new-project trigger keywords to this skill's description and body. |
