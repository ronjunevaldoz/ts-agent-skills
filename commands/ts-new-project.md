# /ts-new-project $ARGUMENTS

**TS Agent Skills** — scaffold a complete TypeScript/Next.js project from a natural
language description.

`$ARGUMENTS` is optional:
- Omitted: the command asks what the app does before proceeding
- Plain description: `build a SaaS dashboard with team billing`
- A path to a sample spec file

This is a single self-contained command — there is no phase-split reference tree to
delegate to yet (this is a 15-skill v1 collection, not a large one that needs
splitting). Load `ts-expert`'s SKILL.md once at the start for the skill map and Build
Order, then work straight through the steps below.

For every clarifying question below, use the `AskUserQuestion` tool to present
options — not a printed block the user replies to in free text.

---

## Step 1 — Intake

Read `$ARGUMENTS`. If empty, ask what the app does before proceeding.

From the description, infer what's obvious (e.g. "dashboard with billing" implies a
database and auth) but ask `AskUserQuestion` for anything genuinely undetermined:

- **Does it need a database?** (most apps do — skip only for a static/marketing site)
- **Does it need auth?** If yes: Auth.js, Clerk, or Lucia — `ts-auth` owns this
  decision table, ask again there if the answer is "not sure"
- **tRPC or REST?** REST if the API needs non-TS consumers (mobile app, public API,
  webhooks); tRPC if client and server are both TypeScript in the same repo
- **Prisma or Drizzle?** — only if a database is needed; `ts-orm-database` owns the
  full decision table
- **Redux, Zustand, or plain Context for client state?** — remind the user this is
  for genuine client-only state, not server data (that's `ts-data-fetching`, always
  included)

Print the inferred assumptions before moving on, so the user can correct anything
before scaffolding starts.

**Inference examples** (state these explicitly, don't silently assume):

| Description contains | Infer |
|---|---|
| "SaaS", "dashboard", "team", "billing", "workspace" | database + auth needed |
| "internal tool", "admin panel" | auth needed, database likely needed |
| "landing page", "marketing site", "blog" (no CMS mentioned) | no database, no auth — skip both |
| "mobile app calls this", "public API", "webhook" | REST, not tRPC |
| "just me and the frontend", "same repo", no external consumer named | tRPC is the default |

If the description is ambiguous (e.g. "build a todo app" — could be single-user
local-only or multi-user with accounts), ask rather than guessing either direction.

---

## Step 2 — Build in dependency order

Apply skills in `ts-expert`'s Build Order — each step assumes the one before it is
settled. Skip a step only when Step 1 determined the project doesn't need it (e.g. no
auth → skip `ts-auth`; no database → skip `ts-orm-database` and narrow `ts-api-layer`
to a schema-validation-only contract).

1. **`ts-project-foundation`** — monorepo layout (or single-package, if the project
   doesn't need a monorepo), `tsconfig.json` strict mode, ESLint flat config, pnpm
   workspaces + Turborepo if multi-package.
2. **`ts-nextjs-app-router`** — app directory, route groups, layouts, the Server vs
   Client Component boundary. Default every new component to a Server Component;
   only add `"use client"` at the actual interactive leaf.
3. **`ts-ci-github-actions`** — CI pipeline: lint, typecheck, test, build, Turborepo
   remote caching wired with `--frozen-lockfile`.
4. **`ts-validation-schema`** — Zod schemas for every shape that crosses a trust
   boundary (form input, API request body, env vars). This is the source every later
   step (`ts-orm-database`, `ts-api-layer`, `ts-forms`) derives types from — settle it
   before anything downstream needs a shape to validate against.
5. **`ts-orm-database`** — only if Step 1 said yes. Prisma or Drizzle per its decision
   table, schema + first migration, typed query client.
6. **`ts-api-layer`** — tRPC or REST per Step 1's answer. Procedures/routes validate
   every input with the Step 4 schemas; server-side validation always runs regardless
   of what the client already checked.
7. **`ts-auth`** — only if Step 1 said yes. Auth.js/Clerk/Lucia per its decision table,
   session handling, route protection, and the auth check inside the mutation itself
   (not just middleware).
8. **`ts-state-management`** — only for genuine client-only state (UI toggles, cart,
   multi-step wizard progress). Server-derived data goes through `ts-data-fetching`
   instead, never here.
9. **`ts-forms` + `ts-data-fetching`** — React Hook Form + the Step 4 Zod schemas for
   every form; TanStack Query for every client-side fetch, keyed for granular
   invalidation.
10. **`ts-shadcn-ui`** — component system. Pick Base UI or Radix once at init, use
    token classes (`bg-background`, not `bg-slate-900`) so dark mode isn't hardcoded
    away.
11. **`ts-testing-vitest` + `ts-testing-playwright`** — unit/component coverage for
    forms, hooks, and utilities; e2e coverage for the critical user flows only
    (login, checkout, whatever the app's core loop is). Wire Playwright's
    `webServer.command` to a production build, not `next dev`.
12. **`ts-deploy-vercel`** — Root Directory set for monorepos, env vars scoped
    correctly per environment (Preview vs Production), `turbo-ignore` wired so
    unrelated app changes don't trigger a rebuild.

Work through these in order. Don't jump to `ts-api-layer` before `ts-validation-schema`
and (if needed) `ts-orm-database` are settled — the API contract has nothing stable to
validate against or query yet.

---

## Step 3 — Verify

Run `/ts-verify` against the scaffolded project once every step above is done. Fix
anything it flags before declaring the project ready.

---

## Step 4 — Summary

Print what was scaffolded:

```
SCAFFOLDED: <project name>

  Foundation:       ts-project-foundation, ts-nextjs-app-router, ts-ci-github-actions
  Data:             ts-validation-schema, ts-orm-database (<Prisma|Drizzle|skipped>)
  API:              ts-api-layer (<tRPC|REST>)
  Auth:             ts-auth (<Auth.js|Clerk|Lucia|skipped>)
  State:            ts-state-management (<Redux|Zustand|Context|skipped>), ts-data-fetching
  Forms:            ts-forms
  UI:               ts-shadcn-ui
  Testing:          ts-testing-vitest, ts-testing-playwright
  Deploy:           ts-deploy-vercel

NEXT STEPS:
  - <anything the user still needs to do manually — e.g. set real env vars,
    connect a real database, run the first migration>
  - Run /ts-verify before the first PR
```

---

## Notes

- Server Component by default, Client Component only at the interactive leaf — this
  is the single most common mistake `ts-review-changes` checks for later, so get it
  right at scaffold time.
- Every schema lives once, in `ts-validation-schema`'s layer, and every other skill
  (`ts-forms`, `ts-api-layer`, `ts-orm-database`) derives from it with `z.infer` — never
  hand-write a parallel TS `interface` for the same shape.
- If the user's description doesn't clearly need a database or auth, ask rather than
  defaulting to "yes" — a static/marketing site scaffolded with a full auth+DB stack
  is unrequested weight.
- Don't scaffold both tRPC and REST "just in case" — Step 1's answer picks one.
  `ts-api-layer` covers switching later if the requirement genuinely changes (e.g. a
  mobile client gets added to a tRPC-only project), but that's a deliberate migration,
  not a default to hedge against up front.
- If Step 1 skipped `ts-auth` and `ts-orm-database`, still scaffold `ts-testing-vitest`
  and `ts-testing-playwright` — test coverage isn't conditional on which optional
  skills were needed, every project gets it.
