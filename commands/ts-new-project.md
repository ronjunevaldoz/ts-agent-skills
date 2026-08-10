# /ts-new-project $ARGUMENTS

**TS Agent Skills** — scaffold a complete TypeScript/Next.js project from a natural
language description.

`$ARGUMENTS` is optional:
- Omitted: the command asks what the app does before proceeding
- Plain description: `build a SaaS dashboard with team billing`
- A path to a sample spec file

This is a single self-contained command — there is no phase-split reference tree to
delegate to yet (this is a 19-skill v1 collection, not a large one that needs
splitting). Load `ts-expert`'s SKILL.md once at the start for the skill map and Build
Order, then work straight through the steps below.

For every clarifying question below, use the `AskUserQuestion` tool to present
options — not a printed block the user replies to in free text.

---

## Step 1 — Intake

Read `$ARGUMENTS`. If empty, ask what the app does before proceeding.

Print, before any question is asked:

```
PROJECT: <description summary, one line>
TARGET:  <current working directory>
```

From the description, infer what's obvious (e.g. "dashboard with billing" implies a
database and auth) but ask `AskUserQuestion` for anything genuinely undetermined:

- **Does it need a database?** (most apps do — skip only for a static/marketing site)
- **SQL or MongoDB?** — only if a database is needed. Default to SQL; MongoDB only for
  genuinely document-shaped/variable-structure data or an append-heavy, rarely-joined
  pattern (event logs, time-series) — `ts-orm-database`'s Recommendation First and
  `ts-expert`'s Decision Trees own this in full
- **Prisma or Drizzle?** (if SQL) / native driver or Mongoose (if MongoDB) — only if a
  database is needed; `ts-orm-database`/`ts-mongodb` own the full decision tables
- **Does it need auth?** If yes: Auth.js, Clerk, or Lucia — `ts-auth` owns this
  decision table, ask again there if the answer is "not sure"
- **tRPC or REST?** REST if the API needs non-TS consumers (mobile app, public API,
  webhooks); tRPC if client and server are both TypeScript in the same repo
- **Does any call need real resilience?** (payments, a flaky third-party API, anything
  where a silent failure has a real cost) → `ts-resilience`. Skip for a simple internal
  tool with no external dependency worth protecting against
- **Does anything need to run outside the request cycle?** (emails, webhooks, scheduled
  reports, anything that could exceed a serverless function's time limit) →
  `ts-background-jobs`. Skip if every operation genuinely completes inline
- **Redux, Zustand, or plain Context for client state?** — remind the user this is
  for genuine client-only state, not server data (that's `ts-data-fetching`, always
  included)
- **Base color for `ts-shadcn-ui`?** — Neutral (recommended default), Slate, Zinc,
  Stone, or Gray. Always pre-select Neutral as the recommended option — purely
  visual, cheap to change later (`components.json`'s `baseColor` field, re-run
  `shadcn init` to change it), so don't spend more than one question on it.

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
| "payment", "billing", "checkout", "third-party API", "flaky", "external service" | include `ts-resilience` |
| "email", "report", "export", "webhook", "scheduled", "notification" | include `ts-background-jobs` |
| "activity feed", "logs", "events", "analytics", "time-series", CMS with varied content shapes | MongoDB, not SQL — confirm, don't assume |

If the description is ambiguous (e.g. "build a todo app" — could be single-user
local-only or multi-user with accounts), ask rather than guessing either direction.

### Persist the requirements analysis

Once every question above is answered, write `docs/requirements-analysis.md` at the
project root — this is the durable record of what was actually asked for. A printed
summary alone doesn't survive a session stopping here, and "analyze and summarize"
requests specifically (a linked spec doc, a take-home exam, a pasted requirements
doc) need something on disk to hand off or come back to, not just a chat message.

```markdown
# <PROJECT_NAME> — Requirements Analysis

## Source
<"Plain description" | "Spec file: <path>" | "External doc: <link, if the user
pasted content from one>">

## Requirements (as given)

<Restate the actual requirements, summarized but complete — every explicit
requirement from the source, not a one-line gloss. If the source was long
(a multi-page spec), this is the place to compress it faithfully — don't drop a
requirement because it seemed minor.>

## Assumptions made

<Only the ambiguities Step 1 actually resolved — inferred or asked. Skip anything
the source stated explicitly; this section is for gaps the source left open.>

See `PLAN.md`'s Architecture decisions section for the resulting technical choices
and reasoning — not duplicated here.
```

This file is written unconditionally, before Step 2's plan-confirmation gate — it's a
record of the input, not a decision that could still change during 2c's review.

---

## Step 2 — Plan: MVP, delivery slices, tasks

The gate before any code is written. Produce one **compact drafted plan** with
recommendations pre-selected — never a blank template. The user should only need to
say "looks good" or tweak one item. ⛔ No code is written during this step; the first
line of code is written only after the user confirms in 2c.

### 2a — Draft the MVP scope

- Every MVP needs: a working route + at least one data-bearing page
- Auth is MVP only if the app cannot work anonymously — otherwise post-MVP
- Nice-to-haves (settings, profile, onboarding, notifications) → post-MVP by default
- `ts-resilience` and `ts-background-jobs` are hardening, not core functionality —
  post-MVP by default unless Step 1 found a real reason (payments, a scheduled job the
  app can't function without)

```
## Draft: MVP scope

MVP:
  1. <feature> — <why it's core> (recommended)
  2. <feature> — <why it's core> (recommended)
  3. <feature> — included because auth is required to function

Post-MVP (after first release):
  4. <feature> — nice-to-have, not blocking
  5. <feature> — can ship without it
```

### 2b — Draft the delivery slices

Concrete slice names from the app type, not placeholders ("Alpha — browse products",
not "Milestone 1").

```
## Draft: delivery plan

Slice 1 — Foundation (~1 week)
  Outcome: clean build, CI green, first route renders
  Tasks: ts-project-foundation, ts-nextjs-app-router, ts-ci-github-actions,
         ts-validation-schema wired

Slice 2 — <First MVP feature> (~1 week)
  Outcome: <feature> works end-to-end (data layer through UI)

Slice N — Polish + QA (~1 week)
  Outcome: ready for a first deploy
  Tasks: Playwright e2e for the core flow, CI pipeline green (lint, typecheck,
         test, build), Vercel preview deploy

Estimated MVP: <N> weeks
```

### 2c — Confirm the plan

Print 2a and 2b's drafts together and **end the turn there** — do not call
`AskUserQuestion` in the same response. The confirmation popup renders on top of the
draft; calling both together gives the user no real chance to read the plan before
being asked to approve it. Ask for confirmation via `AskUserQuestion` only in the next
message:

- **Looks good** — accept the plan as drafted, proceed to 2d
- **Move a task to a different slice**
- **Add or remove a feature from MVP**
- **Split a slice**

**Do not proceed to 2d until confirmed.** After any change, re-print only the affected
section with the change highlighted, then ask again (same two-turn split) — never
re-print the whole plan for a minor edit.

### 2d — Persist the plan to `PLAN.md`

Immediately after confirmation — before any code is written — write `PLAN.md` at the
project root. The printed draft in 2a/2b is not durable; a session that stops after
this point must not lose the plan.

```markdown
# <PROJECT_NAME> — Development Plan

<WHAT_IT_DOES>

## Status key

| Symbol | Meaning |
|---|---|
| [ ] | Not started |
| [x] | Done |

## Architecture decisions

Carried over from Step 1's intake — the *why* behind what gets built, not just the
task list. Only include rows Step 1 actually asked about or inferred; omit anything
that didn't apply (e.g. no row for auth if the app has none).

| Decision | Choice | Why |
|---|---|---|
| Database | <SQL (Prisma\|Drizzle) / MongoDB / none> | <reason from Step 1> |
| Auth | <Auth.js/Clerk/Lucia / none> | <reason> |
| API layer | <tRPC / REST> | <reason> |
| Resilience | <included / skipped> | <reason> |
| Background jobs | <included / skipped> | <reason> |
| State management | <Redux/Zustand/Context> | <reason> |

## MVP scope

- [ ] <feature 1> — <why it's core>
- [ ] <feature 2> — <why it's core>

## Post-MVP

- <feature> — nice-to-have, not blocking

## Delivery plan

### Slice 1 — Foundation (~1 week)
Outcome: clean build, CI green, first route renders
- [ ] <task>

### Slice 2 — <First MVP feature> (~1 week)
Outcome: <feature> works end-to-end
- [ ] <task>

### Slice N — Polish + QA (~1 week)
Outcome: ready for a first deploy
- [ ] Playwright e2e for the core flow
- [ ] CI pipeline green (lint, typecheck, test, build)
- [ ] Vercel preview deploy
```

Step 4 checks off each slice's tasks in this file as they complete — `PLAN.md` is the
live source of truth for what's done, not the chat transcript. This is the *scaffolded
project's* `PLAN.md`, not this collection's own — same filename, different repo,
distinct purpose (a project roadmap here, a pointer to `ts-expert`'s table there).

---

## Step 3 — Draft wireframes

Before real components get built, draft a low-fidelity wireframe for each MVP screen
from Step 2's confirmed plan — see `ts-layout-system`. Gray-box JSX, no real styling,
viewable live via the dev server instead of an ASCII sketch.

For each MVP screen: write `docs/layout-system/<screen>.md` (component table + region
notes) and `app/(dev)/wireframes/<screen>/page.tsx` (the live gray-box JSX, guarded to
never render in production). Write the `/wireframes` index page linking all of them.

Print the list of URLs and end the turn there — this is a visual review, not a
fixed-choice decision, so don't force an `AskUserQuestion` popup here:

```
WIREFRAMES DRAFTED: <N> screens

  Run `pnpm dev`, then visit:
    /wireframes/<screen-1>
    /wireframes/<screen-2>

Review the layout before Step 4 builds the real components. Ask for changes in
plain language, or say "looks good" to proceed.
```

On "looks good" (or equivalent), proceed to Step 4. On requested changes, edit the
wireframe file(s) and re-print the updated URL list.

---

## Step 4 — Build in dependency order

Apply skills in `ts-expert`'s Build Order — each step assumes the one before it is
settled. Skip a step only when Step 1 determined the project doesn't need it (e.g. no
auth → skip `ts-auth`; no database → skip `ts-orm-database` and narrow `ts-api-layer`
to a schema-validation-only contract). Check off each task in Step 2's `PLAN.md` as its
slice completes — the plan is live, not a one-time snapshot.

1. **`ts-project-foundation`** — monorepo layout (or single-package, if the project
   doesn't need a monorepo), `tsconfig.json` strict mode, ESLint flat config, pnpm
   workspaces + Turborepo if multi-package.
2. **`ts-nextjs-app-router`** — app directory, route groups, layouts, the Server vs
   Client Component boundary. Default every new component to a Server Component;
   only add `"use client"` at the actual interactive leaf.
3. **`ts-layout-system`** — already drafted in Step 3 above; this is where the real
   components start replacing each screen's gray-box placeholders.
4. **`ts-ci-github-actions`** — CI pipeline: lint, typecheck, test, build, Turborepo
   remote caching wired with `--frozen-lockfile`.
5. **`ts-validation-schema`** — Zod schemas for every shape that crosses a trust
   boundary (form input, API request body, env vars). This is the source every later
   step (`ts-orm-database`, `ts-api-layer`, `ts-forms`) derives types from — settle it
   before anything downstream needs a shape to validate against.
6. **`ts-orm-database`** (SQL, default) **or `ts-mongodb`** (only if Step 1's
   SQL-vs-MongoDB answer says document/NoSQL) — only if a database is needed at all.
   Schema + first migration, typed query client. Never both — the decision is
   exclusive, not additive.
7. **`ts-api-layer`** — tRPC or REST per Step 1's answer. Procedures/routes validate
   every input with the item 5 schemas; server-side validation always runs regardless
   of what the client already checked.
8. **`ts-resilience`** (only if Step 1 said yes) **+ `ts-background-jobs`** (only if
   Step 1 said yes) — retry/circuit-breaker/rate-limiting wraps calls made through the
   item 7 API layer; background jobs offload anything that could exceed a serverless
   function's execution limit. Independent decisions — a project can need one, both,
   or neither.
9. **`ts-auth`** — only if Step 1 said yes. Auth.js/Clerk/Lucia per its decision table,
   session handling, route protection, and the auth check inside the mutation itself
   (not just middleware).
10. **`ts-state-management`** — only for genuine client-only state (UI toggles, cart,
    multi-step wizard progress). Server-derived data goes through `ts-data-fetching`
    instead, never here.
11. **`ts-forms` + `ts-data-fetching`** — React Hook Form + the item 5 Zod schemas for
    every form; TanStack Query for every client-side fetch, keyed for granular
    invalidation, cursor-based pagination for any list that can grow past a page.
12. **`ts-shadcn-ui`** — component system. Pick Base UI or Radix once at init, pass
    Step 1's base color answer to `shadcn init`, use token classes
    (`bg-background`, not `bg-slate-900`) so dark mode isn't hardcoded away.
13. **`ts-testing-vitest` + `ts-testing-playwright`** — unit/component coverage for
    forms, hooks, and utilities; e2e coverage for the critical user flows only
    (login, checkout, whatever the app's core loop is). Wire Playwright's
    `webServer.command` to a production build, not `next dev`. Record a
    `toHaveScreenshot()` baseline for each core page once its UI is stable, so later
    changes get a visual-regression check for free — see `ts-testing-playwright`'s
    Visual Regression section.
14. **`ts-deploy-vercel`** — Root Directory set for monorepos, env vars scoped
    correctly per environment (Preview vs Production), `turbo-ignore` wired so
    unrelated app changes don't trigger a rebuild.

Work through these in order. Don't jump to `ts-api-layer` before `ts-validation-schema`
and (if needed) `ts-orm-database` are settled — the API contract has nothing stable to
validate against or query yet.

---

## Step 5 — Verify

`/ts-verify` validates this skills collection itself (`skills/`, `commands/`,
`scripts/`) — it does not apply to the scaffolded project. Instead, run the
scaffolded project's own CI pipeline, the one `ts-ci-github-actions` wired in Step 4:

```bash
pnpm turbo run lint typecheck test build
```

This is the same command CI runs, so a clean local run means CI will pass too. Fix
anything it flags before declaring the project ready.

---

## Step 6 — Summary

Print what was scaffolded:

```
SCAFFOLDED: <project name>

  Foundation:       ts-project-foundation, ts-nextjs-app-router, ts-layout-system, ts-ci-github-actions
  Data:             ts-validation-schema, <ts-orm-database (Prisma|Drizzle)|ts-mongodb (Mongoose|native)|skipped>
  API:              ts-api-layer (<tRPC|REST>)
  Resilience:       <ts-resilience|skipped>, <ts-background-jobs|skipped>
  Auth:             ts-auth (<Auth.js|Clerk|Lucia|skipped>)
  State:            ts-state-management (<Redux|Zustand|Context|skipped>), ts-data-fetching
  Forms:            ts-forms
  UI:               ts-shadcn-ui (<base color>, <Base UI|Radix>)
  Testing:          ts-testing-vitest, ts-testing-playwright
  Deploy:           ts-deploy-vercel

NEXT STEPS:
  - <anything the user still needs to do manually — e.g. set real env vars,
    connect a real database, run the first migration>
  - Theme is `new-york`/`neutral` by default — cheap to change, shadcn/ui copies
    component source into the repo, so edit the CSS variable tokens directly or run
    `npx shadcn add` for a different preset. Not a locked-in decision.
  - Run `pnpm turbo run lint typecheck test build` before the first PR
```

---

## Step 7 — Offer the next milestone

`PLAN.md`'s `## MVP scope` is now fully checked off. Before ending the session, draft
the next milestone from `## Post-MVP` — same draft → confirm → persist pattern as
Step 2a-2d, scoped to what ships next instead of the whole MVP.

Pull the `## Post-MVP` list and draft:

```
## Draft: next milestone

Slice <N+1> — <name from the top Post-MVP items> (~1 week)
  Outcome: <what ships>
  Tasks: <features pulled from Post-MVP>

Remaining Post-MVP (not in this milestone): <rest>
```

Print the draft and end the turn there, same two-turn split as Step 2c — do not call
`AskUserQuestion` in the same response. Confirm in the next message (same options as
Step 2c: looks good / move a task / add-remove a feature / split). On confirm, append
the new slice to `PLAN.md`'s
`## Delivery plan` with checkbox tasks, and remove the drafted items from
`## Post-MVP`.

Skip this offer if `## Post-MVP` is empty, or if the user says the project is done.

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
- If Step 1 skipped `ts-auth` and both database options, still scaffold
  `ts-testing-vitest` and `ts-testing-playwright` — test coverage isn't conditional on
  which optional skills were needed, every project gets it.
- `ts-orm-database` and `ts-mongodb` are mutually exclusive — never scaffold both.
  `ts-resilience` and `ts-background-jobs` are independent of each other and of the
  database choice — a project can need any combination of the four, including none.
