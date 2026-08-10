---
name: ts-expert
description: >
  TS Expert Orchestrator — maps every skill in this collection, their dependency
  order, and how to sequence them for a TypeScript/Next.js project. This is a
  meta-routing skill: it does not implement anything itself. Load it first for
  any non-trivial TypeScript/Next.js architecture task to get routed to the
  right skill — the skill map, dependency graph, decision trees, and the
  Skill Invocation Map below all exist to answer "which skill do I use here?"
  before any code gets written.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
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
where do I start, project plan, what do I use here.

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

## The 16 Skills and What They Own

### Foundation & Architecture Contract
| Skill | Owns |
|---|---|
| `ts-project-foundation` | Monorepo layout, tsconfig strict-mode baseline, ESLint flat config, pnpm workspaces + Turborepo, package boundary rules |
| `ts-nextjs-app-router` | Server vs Client Component boundary, layouts and route groups, Server Actions, middleware |
| `ts-ci-github-actions` | CI pipeline — lint, typecheck, test, build, Turborepo remote caching |

### Core Infrastructure
| Skill | Owns |
|---|---|
| `ts-validation-schema` | Zod schemas as the single source of runtime + compile-time type validation |
| `ts-orm-database` | Prisma vs Drizzle decision, schema/migration workflow, typed query client |
| `ts-api-layer` | tRPC vs REST decision, API contract shape, request/response typing |
| `ts-auth` | Auth.js vs Clerk vs Lucia decision, session handling, route protection |
| `ts-deploy-vercel` | Vercel deployment, environment variables, preview deployments, edge vs node runtime |
| `ts-resilience` | Retry/backoff, circuit breaker, timeout, rate limiting, idempotency keys, limited-resource ("last seat") contention |

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
ts-ci-github-actions
        |
ts-validation-schema
        |
ts-orm-database
        |
ts-api-layer
        |
ts-resilience
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
3. `ts-ci-github-actions` — CI pipeline
4. `ts-validation-schema` — Zod schemas
5. `ts-orm-database` — Prisma/Drizzle
6. `ts-api-layer` — tRPC/REST
7. `ts-resilience` — retry, circuit breaker, timeout, rate limiting, idempotency keys
8. `ts-auth` — Auth.js/Clerk/Lucia
9. `ts-state-management` — Redux/Zustand/Context
10. `ts-forms` + `ts-data-fetching` — form submission and client-side fetching
11. `ts-shadcn-ui` — component system
12. `ts-testing-vitest` + `ts-testing-playwright` — unit/component tests and e2e tests
13. `ts-deploy-vercel` — production deployment

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

---

## Skill Invocation Map

| Keyword/Task | Skill |
|---|---|
| "set up a monorepo", "tsconfig", "pnpm workspace", "package boundary" | `ts-project-foundation` |
| "Server Component", "Client Component", "use client", "Server Action", "route group" | `ts-nextjs-app-router` |
| "CI pipeline", "GitHub Actions", "Turborepo caching in CI" | `ts-ci-github-actions` |
| "Redux vs Zustand", "Context state", "client state", "global state" | `ts-state-management` |
| "Zod schema", "runtime validation", "parse input" | `ts-validation-schema` |
| "tRPC vs REST", "API contract", "typed API" | `ts-api-layer` |
| "Prisma vs Drizzle", "database schema", "migration" | `ts-orm-database` |
| "Auth.js", "Clerk", "Lucia", "session", "protect a route" | `ts-auth` |
| "deploy to production", "Vercel", "preview deployment", "env vars" | `ts-deploy-vercel` |
| "retry", "circuit breaker", "rate limiting", "idempotency key", "last seat", "timeout" | `ts-resilience` |
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
