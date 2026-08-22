# ts-agent-skills

[![skills.sh](https://skills.sh/b/ronjunevaldoz/ts-agent-skills)](https://skills.sh/ronjunevaldoz/ts-agent-skills)
[![License](https://img.shields.io/github/license/ronjunevaldoz/ts-agent-skills)](LICENSE)
[![Repo size](https://img.shields.io/github/repo-size/ronjunevaldoz/ts-agent-skills)](https://github.com/ronjunevaldoz/ts-agent-skills)
[![Last commit](https://img.shields.io/github/last-commit/ronjunevaldoz/ts-agent-skills)](https://github.com/ronjunevaldoz/ts-agent-skills)

AI agent skills for **TypeScript** full-stack development — React, Next.js, and
Node.js. Clean architecture boundaries, real decision guidance where the ecosystem is
genuinely contested (state management, ORM, auth), and explicit review loops before
code is generated.

Sibling collection to [`kmp-agent-skills`](https://github.com/ronjunevaldoz/kmp-agent-skills)
(Kotlin Multiplatform) — same toolchain-scoped-skills model, TypeScript is the
unifying toolchain here the way Kotlin+Gradle is there.

---

## Main Use Cases

### Start a new project

Run `/ts-new-project` with a natural language description. The agent asks a short
set of clarifying questions, drafts an MVP + delivery plan and gets it confirmed
before writing any code, then scaffolds the full project — wireframes, database,
API layer, auth, `shadcn/ui`, tests, deploy config.

```
/ts-new-project "A SaaS dashboard with team billing"
```

**Don't just say "use ts-agent-skills to build this"** — that alone doesn't tell the
agent to run the gated command. Invoke `/ts-new-project` explicitly, or ask the agent
to run it. Without it, nothing routes through this collection's architecture
decisions, review gates, or component system — the agent falls back to generic
Next.js knowledge instead. For a structural guarantee instead of a hope, run
`/ts-setup-agents` once after install — it writes a `.claude/AGENTS.md` that makes
this routing automatic every session, not dependent on keyword matching.

1. **First time in a project** → `/ts-setup-agents` (bootstraps routing)
2. **New project** → `/ts-new-project <description>`
3. **Verify a change** → `/ts-verify`
4. **Review a diff** → `/ts-review-changes`
5. **Audit an existing project** → load `ts-audit`
6. **Migrate a specific thing** (Pages→App Router, state library, incremental Zod) → load `ts-migration`

**Start here:** not sure which skill to use? Load `ts-expert` — it routes you to
the smallest relevant skill set.

---

## Why this exists

Built from real production pain, not theory: the same architecture gaps kept costing
time across real projects, so the fix was to research how mature ecosystems actually
solve them — and codify it once, held to the same rigor as production code (tests,
release gates, sources verified against real docs) instead of another prose-only best
practices doc that goes stale.

Built by [Ron June Valdoz](https://github.com/ronjunevaldoz) — full-stack and mobile
software engineer.

---

## Skills

24 skills covering the TypeScript/Next.js/Node stack. Load the smallest set that
answers the request. Start with `ts-expert` to get routed to the right skill.

### Foundation & Architecture Contract
- `ts-project-foundation` — tsconfig, ESLint/Prettier, pnpm workspaces + Turborepo, package boundaries
- `ts-nextjs-app-router` — Server vs Client Component boundary, layouts, Server Actions, middleware
- `ts-vite-spa` — Vite + React SPA alternative when the project doesn't need SSR
- `ts-layout-system` — low-fi screen wireframes (dev-only routes), drafted before real components
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
- `ts-accessibility` — focus management, keyboard nav, ARIA, contrast, reduced motion for the Base UI/shadcn stack
- `ts-specialty-ui` — React Bits, assistant-ui, driver.js, Tailark: four opt-in libraries for animation, AI chat, tours, and marketing blocks

### Testing & Quality
- `ts-testing-vitest` — Vitest + React Testing Library, unit/component tests
- `ts-testing-playwright` — Playwright, e2e tests

### Meta
- `ts-expert` — routing, dependency order, decision trees for the full skill set
- `ts-audit` — post-hoc code-smell/architecture audit: findings, severity, fix order
- `ts-migration` — named migration mechanics: Pages→App Router, state-management migration, incremental Zod adoption

---

## Usage

```
@ts-expert what should I do next?
```

Or trigger a skill directly by keyword — each `SKILL.md`'s **Trigger keywords** line
fires automatically when your prompt matches.

---

## Installation

```bash
npx skills add ronjunevaldoz/ts-agent-skills
```

Or clone and copy the `skills/`, `agents/`, and `commands/` directories into your
project's `.claude/` (or equivalent) directory manually.

---

## Related

- [`kmp-agent-skills`](https://github.com/ronjunevaldoz/kmp-agent-skills) — the sibling Kotlin Multiplatform collection this repo's conventions are ported from
- [`docs/reference/versioning-policy.md`](docs/reference/versioning-policy.md) — commit format, release tiers
- [`PLAN.md`](PLAN.md) — roadmap, deferred v2 skills
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — confirmed agent behavior gaps and workarounds
