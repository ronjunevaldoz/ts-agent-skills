# /ts-review-changes

**TS Agent Skills** — review everything in the current working tree against the 15
skills' documented anti-patterns before considering the work done.

---

## Step 1 — Find changed files

```bash
git diff --name-only HEAD
git diff --name-only --cached
```

## Step 2 — Load only the skills that apply

| Path pattern | Skill |
|---|---|
| `app/**/page.tsx`, `app/**/layout.tsx`, `middleware.ts` | `ts-nextjs-app-router` |
| `app/**/route.ts`, `server/api/**`, `**/trpc/**` | `ts-api-layer` |
| `prisma/schema.prisma`, `drizzle/**`, `db/**` | `ts-orm-database` |
| `**/*.schema.ts`, `lib/validations/**` | `ts-validation-schema` |
| `lib/auth/**`, `auth.ts` | `ts-auth` |
| `store/**`, `**/*.store.ts` | `ts-state-management` |
| `**/*Form*.tsx`, `app/**/actions.ts` | `ts-forms` |
| `**/use*Query*.ts`, `**/use*Mutation*.ts`, hooks calling `useQuery`/`useMutation` | `ts-data-fetching` |
| `components/ui/**` | `ts-shadcn-ui` |
| `.github/**` | `ts-ci-github-actions` |
| `vercel.json`, `turbo.json` | `ts-deploy-vercel` |
| `**/*.test.ts(x)` | `ts-testing-vitest` |
| `**/*.spec.ts`, `e2e/**` | `ts-testing-playwright` |
| `package.json`, `pnpm-workspace.yaml`, `tsconfig*.json` | `ts-project-foundation` |

No architecture-audit script exists yet for a scaffolded consumer project (only
`scripts/scan_skill_issues.py`, which validates this collection's own `SKILL.md`
files, not application code) — the checklist below is the review, not a script gate.

---

## Step 3 — Review against each loaded skill's anti-patterns

Pull each applicable skill's **Common Anti-Patterns** section and check the diff
against it. The highest-signal checks, regardless of which skills loaded:

- **`"use client"` on a whole page** instead of pushed down to the interactive leaf
  (`ts-nextjs-app-router`)
- **Server-derived data stored in Zustand/Redux/Context** instead of TanStack Query —
  hand-rolled cache invalidation instead of the real thing (`ts-state-management`,
  `ts-data-fetching`)
- **N+1 queries** — a loop issuing one DB/procedure call per item instead of a single
  `include`/`with`/join (`ts-orm-database`, `ts-api-layer`)
- **Server-side re-validation skipped on a form submit** — trusting the client-side
  Zod/RHF check alone instead of re-running `.safeParse` on the raw `FormData`
  server-side (`ts-forms`, `ts-validation-schema`)
- **Phantom pnpm dependency** — a package imports something it never lists in its own
  `package.json`, relying on hoisting (`ts-project-foundation`)
- **Auth check only in middleware/UI**, missing from the Server Action or route
  handler itself (`ts-auth`)
- **JWT in `localStorage`** instead of an httpOnly cookie (`ts-auth`)
- **Hardcoded Tailwind colors** (`bg-slate-900`) instead of token classes
  (`bg-background`) — breaks dark mode silently (`ts-shadcn-ui`)
- **Edge runtime on a route needing a Node-only driver** (raw `pg`, default Prisma
  engine) (`ts-deploy-vercel`)
- **CSS-selector locators in a new Playwright test** instead of `getByRole`/
  `getByLabelText` (`ts-testing-playwright`)

---

## Step 4 — Output

```
CHANGED:  <N> files across <skills touched>
SKILLS:   <list loaded>

BLOCKERS: <count>
WARNINGS: <count>
VERDICT:  APPROVE | NEEDS_FIXES

<finding: file:line — anti-pattern — which skill's rule — fix>
```

If `NEEDS_FIXES`, list the exact required change per finding. Do not apply fixes
automatically — present them to the user first.
