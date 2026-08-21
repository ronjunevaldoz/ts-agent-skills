---
name: ts-audit
description: >
  Code-smell and architecture audit for a React/Next.js/TypeScript project
  scaffolded by this collection. Produces findings, risk levels, and a fix
  order — not implementation code. Every detector traces back to either an
  anti-pattern already documented in one of this collection's 20 skills
  (cited by name) or a pattern verified directly against Next.js/React's own
  docs (cited by URL). Deliberately deferred past v1 launch to avoid shipping
  a thin, noisy detector set — this is the systematized version of
  `ts-review-changes`'s Step 3 checklist, going deeper across the full
  detector catalog instead of just the 10 highest-signal checks.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-22'
  keywords:
    - audit
    - code review
    - architecture review
    - code smell
    - review this project
    - check for issues
    - tech debt
    - static analysis
    - anti-pattern
    - findings
    - risk level
    - fix sequence
    - project health
    - readiness review
    - what is wrong with this project
    - inspect this repo
    - React anti-patterns
    - Next.js anti-patterns
    - waterfall fetching
    - derived state
---

## When to Use This Skill

Use this skill when you need to:
- Review an existing React/Next.js/TypeScript repo for code smells or drift from
  this collection's recommended patterns
- Get findings, severity, and a fix order before touching code — not a rewrite
- Check whether a specific file (a route, a form, a query hook) has a known
  anti-pattern before or after making a change
- Decide which of the other 20 skills owns the fix for a given finding
- Get a prioritized adoption order for a brownfield project with little or none
  of this collection's conventions yet — see Adoption Roadmap Mode below

**Trigger keywords:** audit, code review, architecture review, code smell, review
this project, check for issues, tech debt, static analysis, what is wrong with
this project, inspect this repo, project health, readiness review, findings,
risk level, ts-audit, adoption roadmap, where do I start, incremental adoption,
brownfield project.

**Freshness rule:** the detector catalog cross-references every other skill's own
Common Anti-Patterns section plus 5 patterns verified against react.dev and
nextjs.org directly — recheck both when a skill's anti-pattern list changes or a
detector's source doc gets a version bump. Run
`python3 skills/ts-expert/scripts/validate_keyword_routing.py --repo-root .`
after editing this skill's trigger keywords.

---

## Recommendation First

**No bundled analyzer script exists for this skill** — every other skill in this
collection is prose-based, and a real TypeScript AST-parsing detector (ts-morph or
the TS compiler API) is a bigger undertaking than this collection's current
maturity. `scripts/scan_skill_issues.py` validates this repo's own `SKILL.md`
files, not a consumer's application code — there is nothing to run against a
target project. This skill *is* the review: grep for each detector's code shape
below, read the surrounding context, then judge.

Why grep first, then read:
- most of these detectors have a mechanical, greppable shape (`useState.*useEffect`
  pairs, `.map(` without a `key`, `localStorage.setItem` near a token variable) —
  find candidates fast, then read each one to confirm it's a real instance and not
  a false positive
- reading every file cold, with no shape to search for, is slower and misses
  instances a grep would have caught
- a finding without a file:line citation isn't actionable — always confirm before
  reporting

---

## Audit Flow

1. Read the project's own docs first — `README.md`, `AGENTS.md`, any
   architecture notes — before reporting findings.
2. Identify which of the 20 skills apply, using `ts-review-changes`'s path
   table as a starting map.
3. Grep for each applicable detector's code shape from the catalog below.
4. Read each match in context — confirm it's a real instance, not a false
   positive, before reporting it.
5. Assign severity per the catalog, order findings HIGH → MEDIUM → LOW.
6. Report findings, evidence, and a recommended fix order — do not
   implement fixes without being asked.

---

## Adoption Roadmap Mode

Full content: `references/adoption-roadmap.md`.

---

## Detector Catalog

Each entry cites either the skill that already documents it in full (read that
skill's Common Anti-Patterns section for the complete why/fix) or an external
doc for the 7 new detectors. This catalog is deliberately terser than each
skill's own prose — it exists to be scanned during an audit, not read start to
finish.

### Next.js App Router & Rendering — `ts-nextjs-app-router`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Page-level `"use client"` | MEDIUM | Whole page directive for one interactive child → push `"use client"` to the leaf |
| `useEffect` fetch a Server Component could do | MEDIUM | Client fetch-on-mount with a loading spinner → fetch in the Server Component instead |
| Non-serializable Server→Client prop | HIGH | A function/class instance/Map/Set crossing the boundary → pass plain data only |
| Server Action called from `useEffect` | MEDIUM | Background-polling a `"use server"` function → use a route handler + `fetch` instead |
| Uncached-opt-out on per-user data | HIGH | A cached route/`fetch` returning session-specific data → `{ cache: 'no-store' }` or read `cookies()`/`headers()` |

### Data Fetching Waterfalls & Request Memoization — new, verified against Next.js docs

Not yet owned by any existing skill — a real gap in what `ts-nextjs-app-router`
and `ts-data-fetching` cover (both stop at the client-fetching layer; this is
server-side fetch sequencing).

**Sequential `await`s that could run in parallel (HIGH).** Verified against
[nextjs.org/docs/app/getting-started/fetching-data](https://nextjs.org/docs/app/getting-started/fetching-data),
"Parallel data fetching": two independent `await`s placed one after another
block the second on the first even though neither depends on the other's result.

```tsx
// ❌ sequential — getAlbums blocked until getArtist resolves, no dependency between them
const artist = await getArtist(username);
const albums = await getAlbums(username);

// ✓ parallel — both requests start immediately
const artistData = getArtist(username);
const albumsData = getAlbums(username);
const [artist, albums] = await Promise.all([artistData, albumsData]);
```

**Missing `React.cache()` on a shared ORM/DB read (MEDIUM).** Verified same
page, "Reusing data with React.cache": `fetch` calls are deduplicated
automatically within a request, but a non-`fetch` data source (an ORM/DB client
call) is not — the same query fired by two Server Components in one render
hits the database twice. Wrap the function: `export const getUser =
cache(async () => { ... })`.

### API & Validation Boundary — `ts-api-layer`, `ts-validation-schema`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Public API built in tRPC | MEDIUM | Non-TS consumer told to call a tRPC procedure with curl → REST + OpenAPI |
| REST route skips server validation | HIGH | "Frontend already validates it" reasoning on a route handler → validate server-side regardless |
| N+1 inside a tRPC procedure | MEDIUM | Per-item `db.query` loop inside a procedure body → batch/`include` |
| `200` with `{ error }` body | MEDIUM | Breaks `fetch`/axios default error handling → use the real status code |
| One router file, every procedure | LOW | Split by domain, merge in `_app.ts` |
| Hand-written `interface` beside a Zod schema | LOW | Two sources of truth that drift → `z.infer<typeof Schema>` |
| `.parse()` with no try/catch in a handler | MEDIUM | Invalid body → unhandled 500 → `.safeParse()` at every request boundary |
| Client Zod treated as the security boundary | HIGH | `zodResolver` alone stops nothing against direct `fetch`/curl → re-validate server-side with the same schema |
| Hand-rolled `if (!body.email)` duplicated across files | LOW | Drifts silently → one schema import |
| `UpdateUserSchema` redeclared from scratch | LOW | Derive with `.partial().extend(...)` from a shared base |

### Auth & Security — `ts-auth`

| Smell | Sev | Signal → Fix |
|---|---|---|
| JWT in `localStorage` | HIGH | Any XSS reads it → httpOnly cookie |
| Auth check only in middleware/UI | HIGH | Server Action/route handler itself has no check → add it there too |
| Hand-rolled password hashing | HIGH | `md5`/homemade salt → bcrypt/argon2 or the auth library's own hashing |
| Trusting a client-sent user ID | HIGH | Hidden field/body claims identity → re-derive from the server session |
| No ownership check in the query | HIGH | Logged-in check but no row-owner check → `where: { authorId: session.user.id }` |

### Database & ORM — `ts-orm-database`, `ts-mongodb`

| Smell | Sev | Signal → Fix |
|---|---|---|
| N+1 queries | HIGH | Per-row query inside a loop → `include`/`with`/join |
| Migration against prod with no review | HIGH | `migrate dev` (interactive) pointed at prod `DATABASE_URL` → reviewed SQL diff in CI |
| No connection pooling in serverless | HIGH | `new PrismaClient()` per request → singleton client |
| No unique constraint on a logically-unique field | MEDIUM | App-level-only uniqueness check → `@unique`/`.unique()` in schema |
| Committed generated client | LOW | `.prisma/client` output in git → `.gitignore` + regenerate in CI |
| Raw SQL mixed with ORM builder, no reason | LOW | Drop to `$queryRaw` only when the builder genuinely can't express it |
| `ObjectId`/Mongo document leaks past data layer | MEDIUM | Raw document passed into a component/service → map to a plain type at the repo boundary |
| Unindexed query on a large collection | MEDIUM | Full `COLLSCAN` → run `explain()`, add the index |
| Mongoose schema validation + separate Zod schema | LOW | Two validation sources for one shape → pick one |
| Mongo reached for by default | LOW | Relational data with real joins → Postgres/Prisma per `ts-orm-database` |

### Background Jobs & Resilience — `ts-background-jobs`, `ts-resilience`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Long task inline in a request handler | MEDIUM | Works in dev, exceeds `maxDuration` in prod → trigger + return |
| No idempotency handling on a job | HIGH | Retried/redelivered job double-sends/double-charges → idempotency key |
| Cron route with no auth check | HIGH | Anyone who finds the path re-triggers it → check `CRON_SECRET` |
| Fixed-delay retry, no jitter | MEDIUM | Thundering herd on recovery → add jitter |
| Retrying a mutation with no idempotency key | HIGH | Retry-safety lives in the operation, not the retry logic |
| No timeout on an external call | HIGH | Hung request holds resources indefinitely → add a timeout |
| `findUnique` then conditional `update` for limited stock | HIGH | Race window is the two round-trips, not fixable by retry alone |
| Retrying past an open circuit breaker | MEDIUM | Retry policy layered outside the breaker defeats it |

### Client State & Data Fetching — `ts-state-management`, `ts-data-fetching`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Server-derived data in Zustand/Redux/Context | MEDIUM | Hand-rolled loading/error/refetch → TanStack Query |
| One giant global store | LOW | Cart, UI state, flags all in one store → split by concern |
| Single Context value object | MEDIUM | Any field change re-renders every consumer → split into per-concern Contexts |
| `useEffect` syncing query data into `useState` | MEDIUM | Second copy of the same data can go stale → read `data` at render time |
| No error boundary around a query that can fail | MEDIUM | Only `data`/`isLoading` checked → check `error` or `throwOnError` + boundary |
| Skipped `onMutate` cancel + snapshot | MEDIUM | In-flight refetch overwrites optimistic value → `cancelQueries` + snapshot |
| Offset pagination on a large/write-heavy table | MEDIUM | `OFFSET` skips/duplicates under concurrent writes → cursor-based |

### React Key & Derived-State Smells — new, verified against react.dev

Not owned by any existing skill — general React hygiene, not Next.js- or
data-layer-specific, so it doesn't fit `ts-nextjs-app-router` or
`ts-state-management`'s scope.

**Array index as `key` in a reorderable list (MEDIUM).** Verified against
[react.dev/learn/rendering-lists](https://react.dev/learn/rendering-lists):
"the order in which you render items will change over time if an item is
inserted, deleted, or if the array gets reordered. Index as a key often leads
to subtle and confusing bugs." Use a stable ID from the data, not the loop
index — an index key is only acceptable for a genuinely static list that can
never reorder or grow.

**Derived state synced via `useEffect` + `setState` (MEDIUM).** Verified
against
[react.dev/learn/you-might-not-need-an-effect](https://react.dev/learn/you-might-not-need-an-effect):
"When something can be calculated from the existing props or state, don't put
it in state. Instead, calculate it during rendering."

```tsx
// ❌ redundant state + unnecessary Effect — extra render pass, can go stale
const [fullName, setFullName] = useState('');
useEffect(() => { setFullName(firstName + ' ' + lastName); }, [firstName, lastName]);

// ✓ calculated during render
const fullName = firstName + ' ' + lastName;
```

### Forms — `ts-forms`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Trusting client-side validation alone | HIGH | Server Action skips re-validation → `Schema.safeParse` on raw `FormData` server-side |
| Not disabling submit during submission | MEDIUM | Slow network + impatient click fires twice → `disabled={isSubmitting}` |
| Separate hand-written validator beside the Zod schema | LOW | Two sources drift → express it in the schema |
| Controlled inputs when `register` suffices | LOW | Re-render per keystroke RHF was chosen to avoid |
| Hand re-derived TS type instead of `z.infer` | LOW | Field added to schema, interface silently stale |

### UI System — `ts-shadcn-ui`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Hardcoded colors (`bg-slate-900`) | MEDIUM | Doesn't respond to `.dark` class → token classes (`bg-background`) |
| Mixing Radix-based and Base UI-based components | MEDIUM | Two focus/portal implementations → pick one primitive layer at init |
| Treating shadcn/ui as an unmodifiable package | LOW | `components/ui/*` never customized → it's yours, edit it |
| `cn()` reimplemented as plain `clsx()` | LOW | No `tailwind-merge` → conflicting utility classes both land in the DOM |
| Primitive dependency added manually, not via CLI | LOW | Skips the version pin `components.json` tracks → `npx shadcn add` |

### Accessibility — `ts-accessibility`

| Smell | Sev | Signal → Fix |
|---|---|---|
| `<div onClick={...}>` instead of `<button>` | HIGH | No keyboard activation, no focusability, announced as nothing to a screen reader → real `<button>`/`<a href>` |
| Icon-only button with no `aria-label` | MEDIUM | `<Button size="icon"><X /></Button>` announces as bare "button" → add `aria-label` or visually-hidden text |
| Custom modal built from a styled `<div>` | MEDIUM | Silently drops focus trapping, Esc-to-close, focus restoration → Base UI's Dialog primitive |
| Missing or generic `alt` on a content `next/image` | MEDIUM | `alt=""` on a real content image, or `alt="image"` → a real description; `alt=""` only for decorative images |
| Unconditional `animate-*`/CSS transition | LOW | No `motion-safe:`/`motion-reduce:` gating → users with `prefers-reduced-motion: reduce` still get it |
| Assuming a dark-mode token swap keeps contrast | MEDIUM | `--primary`/`--primary-foreground` flip is a color swap, not a contrast guarantee → check both themes independently |

### Missing `next/image` for Content Images — new, verified against Next.js docs

Not owned by any existing skill. Verified against
[nextjs.org/docs/app/getting-started/images](https://nextjs.org/docs/app/getting-started/images):
a raw `<img>` for a real content image (not a tiny decorative icon) forfeits
three things `next/image` provides automatically — "**Visual stability:**
Preventing layout shift... when images are loading," "**Faster page loads:**
Only loading images when they enter the viewport," and "**Size optimization:**
Automatically serving correctly sized images... using modern image formats
like WebP." Severity: LOW for a small icon, MEDIUM for a hero/content image
where CLS and unoptimized payload size are real user-facing costs.

### Dependency Staleness & Vulnerabilities — new, verified against pnpm docs

Not owned by any existing skill. Two separate, real checks — don't conflate them:

**Known-vulnerable dependency (severity from the advisory itself).** Run `pnpm audit`
— verified against [pnpm.io/cli/audit](https://pnpm.io/cli/audit): checks installed
packages against the registry's security-advisory database, reporting `low`/
`moderate`/`high`/`critical`. `--audit-level <severity>` (or `audit.level` in
`pnpm-workspace.yaml`) filters to advisories at or above a threshold — the flag CI
should use so a `low` advisory doesn't block every build.

**Outdated package with no upgrade plan (LOW, unless the advisory check above also
flags it).** Run `pnpm outdated` — verified against
[pnpm.io/cli/outdated](https://pnpm.io/cli/outdated): lists packages behind their
latest published version. Being outdated alone is LOW severity — the real finding is
a major-version gap on a package the project actively depends on, left with no
tracked upgrade plan, not the mere existence of a newer version.

### Project Foundation, CI & Deploy — `ts-project-foundation`, `ts-ci-github-actions`, `ts-deploy-vercel`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Phantom pnpm dependency | MEDIUM | Import relies on hoisting, not its own `package.json` → declare it |
| Circular package dependency | MEDIUM | `packages/ui` ↔ `packages/db` → extract the shared piece to a third package |
| One giant `packages/shared` | LOW | Everything dumped in one catch-all → split by what changes together |
| `pnpm install` without `--frozen-lockfile` in CI | MEDIUM | Silently regenerates a drifted lockfile → add the flag |
| `fetch-depth: 1` with `--filter=...[origin/main]` | MEDIUM | Shallow checkout breaks Turborepo's git diff → fetch full history |
| Edge runtime + Node-only DB driver | HIGH | `runtime = "edge"` importing `pg`/default Prisma engine → default to Node.js |
| `.env` with real secrets committed | HIGH | Even in a private repo → Vercel env store + gitignored `.env.local` |
| No Root Directory set in a monorepo | MEDIUM | Builds the wrong `package.json` or every app on every commit → set per Vercel Project |
| Preview env vars assumed to match Production | MEDIUM | Different scoping unnoticed in dashboard → check each var's environment scope |

### Layout System — `ts-layout-system`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Real shadcn/ui components in a wireframe | LOW | Looks polished too early, gets styling feedback instead of layout feedback |
| Missing production guard on a wireframe route | MEDIUM | Dead UI reachable by real users → gate it |
| Private folder (`_wireframes`) instead of route group | MEDIUM | Excluded from routing entirely → nobody can open the URL |
| `_components.md` drifted from real implementation | LOW | Update as real components replace placeholders |

### Testing — `ts-testing-vitest`, `ts-testing-playwright`

| Smell | Sev | Signal → Fix |
|---|---|---|
| Not awaiting `userEvent` calls | MEDIUM | Assertion runs before the interaction lands → flaky test → always `await` |
| Mocking the thing under test | MEDIUM | Passes even when the real integration is broken → mock the boundary, not the subject |
| `getByTestId` as first choice | LOW | Skips the accessibility signal `getByRole` gives free |
| Snapshot-testing everything | LOW | Breaks on trivial markup change, reviewers stop reading |
| CSS selectors instead of role/label locators | LOW | Breaks on class rename → `getByRole`/`getByLabelText` |
| `page.waitForTimeout()` instead of auto-wait assertion | LOW | Too slow or too fast → `expect(locator).toBeVisible()` |
| e2e run against the dev server in CI | MEDIUM | Skips prod bundling/SSR behavior → build + start |

---

## Output Format

```
PROJECT:  <name/path>
SKILLS TOUCHED: <list>

FINDINGS: <count>  (HIGH: n, MEDIUM: n, LOW: n)

[HIGH] <file>:<line> — <smell name> — <owning skill>
  <one-line evidence>
  Fix: <one line>

[MEDIUM] ...
[LOW] ...

RECOMMENDED FIX ORDER: <numbered list, HIGH first>
SKILLS TO USE NEXT: <list>
```

Findings first, ordered by severity. Evidence with file:line for every finding —
a finding without a citation isn't actionable. Keep the fix line short; the
owning skill has the full explanation and code example, don't repeat it here.

---

## Common Anti-Patterns

Mistakes in how the audit itself is run, not in the code being audited:

- **Reporting findings before reading the project's own docs** — misses
  project-specific constraints a generic checklist can't know about.
- **Flagging a detector match without reading the surrounding context** — a
  grep hit is a candidate, not a finding; confirm it before reporting.
- **Producing implementation code during an audit instead of findings + fix
  order** — audit and implement are separate steps, same as `kmp-audit`'s rule.
- **Treating every finding as HIGH** — inflated severity trains the reader to
  stop trusting the report; use the catalog's severities as the default and
  only escalate with a specific reason.
- **Inventing a detector with no citation** — every entry in this catalog
  traces to either an owning skill or a verified external doc; a new finding
  that can't cite either is a hunch, not a finding — say so and leave it out.

---

## Related Skills

Every detector above is owned by one of these — load the specific skill for
the full anti-pattern explanation and fix:

- `ts-nextjs-app-router` — Server/Client boundary, caching, Server Actions
- `ts-api-layer` — tRPC/REST contract smells
- `ts-validation-schema` — Zod schema duplication and boundary gaps
- `ts-auth` — session, JWT, and ownership-check findings
- `ts-orm-database` / `ts-mongodb` — query and migration findings
- `ts-background-jobs` / `ts-resilience` — retry, idempotency, timeout findings
- `ts-state-management` / `ts-data-fetching` — client state and query findings
- `ts-forms` — client/server validation split findings
- `ts-shadcn-ui` — design-token and component-source findings
- `ts-accessibility` — keyboard/focus/contrast/motion findings
- `ts-project-foundation` / `ts-ci-github-actions` / `ts-deploy-vercel` —
  monorepo, CI, and deployment findings
- `ts-layout-system` — wireframe-route findings
- `ts-testing-vitest` / `ts-testing-playwright` — test-quality findings
- `ts-expert` — routes a confirmed finding to the right skill for the fix
- `ts-review-changes` — the lighter, diff-scoped command this skill's catalog
  goes deeper than; use that for a quick pre-commit pass, this for a full audit

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-22 | Added Adoption Roadmap Mode (`references/adoption-roadmap.md`) — direct analog to `kmp-audit`'s `--roadmap` mode, missing from the existing-project flow: findings mode answers "what's wrong," nothing answered "what order should I adopt these conventions in" for a brownfield project with none of them yet. 9-row adoption plan (condition/priority/skill/reason/action) plus a state-signal checklist and output template. First `references/` split in this collection — `scan_skill_issues.py` already supported the pattern, just never exercised. |
| 2026-08-22 | Added Accessibility detector section (`ts-accessibility`, 6 rows) — real coverage gap: the skill existed but the audit never checked whether a project follows it. Added Dependency Staleness & Vulnerabilities (new, 2 detectors verified against pnpm's own `audit`/`outdated` docs) — no existing check for known-vulnerable or majorly-outdated packages. Fixed stale skill-count mentions (19/18 → 20) left over from before `ts-accessibility` and this skill itself were added to the roster. |
| 2026-08-10 | Initial version. |
