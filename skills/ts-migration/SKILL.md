---
name: ts-migration
description: >
  Incremental adoption guide for teams moving an existing React/Next.js project
  toward this collection's conventions. Covers named migration paths — Pages
  Router to App Router, prop-drilling/Context to a real state-management
  library, an untyped API to incremental Zod validation — and how to migrate
  without breaking a live app. Does NOT cover which order to adopt conventions
  in for a project with none yet — see ts-audit's Adoption Roadmap Mode for
  that; this skill is migration mechanics for a specific named transition.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-22'
  keywords:
    - migration
    - incremental adoption
    - existing project
    - Pages Router to App Router
    - pages to app directory
    - Context to Zustand
    - Redux to Zustand
    - incremental Zod adoption
    - legacy migration
    - refactor architecture
    - retrofit existing project
    - how to start
    - where to begin
    - old project adoption
    - brownfield
    - migrate without breaking
---

## When to Use This Skill

Use when:
- An existing Next.js project is migrating from the Pages Router to the App Router
- A team is moving off prop-drilling/Context to a real state-management library, or
  between two state-management libraries
- An API has no validation at all and needs Zod added incrementally, not in one
  big-bang rewrite
- You need the *mechanics* of one specific named migration — not a priority order
  for adopting conventions on a project with none yet (that's `ts-audit`'s Adoption
  Roadmap Mode)

**Trigger keywords:** migration, incremental adoption, existing project, Pages Router
to App Router, pages to app directory, migrate off Context, Context to Zustand,
Redux to Zustand, incremental Zod, add validation to existing API, legacy migration,
retrofit existing project, migrate without breaking, brownfield.

**Freshness rule:** Path A is verified against
[nextjs.org/docs/app/guides/migrating/app-router-migration](https://nextjs.org/docs/app/guides/migrating/app-router-migration)
— recheck before relying on it if Next.js has shipped a major version since.

---

## Recommendation First

**One migration path, one step at a time — never combine two migrations in one PR.**
Migrating routing *and* state management together doubles what a broken build could be
blamed on. Finish one path (or one step within a path) before starting the next.

If you don't yet know *which* conventions to adopt in what order for a project with
none of them, that's `ts-audit`'s Adoption Roadmap Mode, not this skill — this skill
starts once you already know the specific migration you're doing.

---

## Path A — Pages Router to App Router

Verified against Next.js's own migration guide. The `app/` and `pages/` directories
**coexist intentionally** — this is designed to be page-by-page, not a cutover.

### Step 1 — Create the root layout, keep `_app`/`_document`

Create `app/layout.tsx`. Copy global styles/providers from `_app`/`_document` into it,
but **keep the originals** until every page is migrated — deleting them early breaks
every `pages/*` route still in flight.

```tsx
// app/layout.tsx — new, coexists with pages/_app.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

React Context providers still in `_app.tsx` need to move into a Client Component
(`'use client'`) before a layout can use them — layouts are Server Components by
default.

### Step 2 — Migrate one page at a time

Two-step move per page, not a rewrite: extract the existing page component into a
Client Component file unchanged, then create the `app/` `page.tsx` as a thin Server
Component wrapper that fetches data and passes it down.

```tsx
// app/dashboard/dashboard-client.tsx — the old page component, moved as-is
'use client'
export default function DashboardClient({ projects }: { projects: Project[] }) {
  return <ul>{projects.map((p) => <li key={p.id}>{p.name}</li>)}</ul>
}

// app/dashboard/page.tsx — new, replaces getServerSideProps/getStaticProps
import DashboardClient from './dashboard-client'

async function getProjects() {
  const res = await fetch('https://...', { cache: 'no-store' }) // matches getServerSideProps
  return res.json()
}

export default async function Page() {
  const projects = await getProjects()
  return <DashboardClient projects={projects} />
}
```

`{ cache: 'no-store' }` matches `getServerSideProps`'s always-fresh behavior;
`{ cache: 'force-cache' }` (the `fetch` default) matches `getStaticProps`;
`{ next: { revalidate: N } }` matches `getStaticProps` with a `revalidate` option.
`getStaticPaths` becomes `generateStaticParams`.

### Step 3 — Migrate routing hooks on each page you touch

`useRouter` from `next/navigation` (App Router) is a different hook than
`next/router` (Pages Router) — no `pathname`, no `query`. Use `usePathname()`,
`useSearchParams()`, and `useParams()` instead, and only inside Client Components.

```tsx
// ❌ Pages Router hook — does not exist in app/
import { useRouter } from 'next/router'
const { pathname, query } = useRouter()

// ✓ App Router — three focused hooks instead of one wide one
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
const pathname = usePathname()
const searchParams = useSearchParams()
```

**Known cost during the transition**: navigating between a `pages/*` route and an
`app/*` route is a hard navigation — `next/link` prefetching doesn't cross routers.
This is a real, temporary cost of the coexistence period, not a bug to fix mid-migration.

Delete `_app.tsx`/`_document.tsx` only after every page has moved to `app/`.

---

## Path B — State Management Migration

See `ts-state-management`'s Migration Cost table for which transition is Low/Medium/
High cost — this section is the *mechanics*, not the cost comparison.

**Add the new store alongside the old mechanism, migrate one slice at a time:**

```tsx
// Step 1 — new Zustand store lives beside existing Context, not replacing it yet
const useCartStore = create<CartState>((set) => ({
  items: [],
  addItem: (item) => set((s) => ({ items: [...s.items, item] })),
}))

// Step 2 — migrate one consumer at a time from useContext(CartContext) to useCartStore()
// Step 3 — once zero components read CartContext, delete the provider and the context file
```

Never run both the old and new mechanisms as the *source of truth* for the same piece
of state at once — one direction only (old → new), or the two silently drift.

---

## Path C — Incremental Zod Adoption on an Untyped API

Start at the highest-traffic or highest-risk boundary, not every route at once —
a schema added to one route handler doesn't require touching the other nine.

```ts
// Before — no validation at all
export async function POST(req: Request) {
  const body = await req.json()
  return createUser(body.email, body.name) // trusts the shape blindly
}

// After — this one route validated, the rest of the API untouched for now
const CreateUserSchema = z.object({ email: z.string().email(), name: z.string().min(1) })

export async function POST(req: Request) {
  const parsed = CreateUserSchema.safeParse(await req.json())
  if (!parsed.success) return Response.json({ error: parsed.error.flatten() }, { status: 400 })
  return createUser(parsed.data.email, parsed.data.name)
}
```

Expand outward from there — each newly-validated route is done, no partial-validation
state to track across the codebase.

---

## Common Anti-Patterns During Migration

- Migrating routing and state management in the same PR — doubles what a broken
  build could be blamed on
- Deleting `_app`/`_document` before every page has moved to `app/`
- Running Context and a new store as dual sources of truth for the same state
- Rewriting every API route's validation in one PR instead of expanding outward
  from the highest-risk boundary
- Treating `useRouter` from `next/router` and `next/navigation` as interchangeable
  — they have different return shapes

---

## Testing During Migration

Write a test against the *existing* behavior before migrating it — the test is the
safety net that proves the migration didn't change behavior.

```tsx
// Write this first, against the Pages Router version
test('dashboard shows project names', async () => {
  render(<DashboardPage projects={[{ id: '1', name: 'Alpha' }]} />)
  expect(screen.getByText('Alpha')).toBeInTheDocument()
})

// Then migrate to the App Router version — the test must still pass unchanged
```

---

## Related Skills

- `ts-audit` — run Adoption Roadmap Mode first for *which* conventions to adopt in
  what order; this skill is the mechanics once a specific migration is chosen
- `ts-nextjs-app-router` — the target architecture Path A migrates toward
- `ts-state-management` — the cost table Path B's mechanics build on
- `ts-validation-schema` — the target pattern Path C migrates toward
- `ts-testing-vitest` — write the safety-net test before migrating each piece

---

## Output Style

When helping with a migration:
1. State which path applies (A, B, C, or a different named migration)
2. Propose the next single step only — not the full path at once
3. After each step: verify build passes, tests pass, then propose the next step

Never propose more than one migration step at a time — migration stalls when the
scope is too large to finish and verify in a single session.

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-22 | Initial version. Real gap found reviewing the existing-project flow: `kmp-migration` had no analog here — `ts-audit`'s Adoption Roadmap Mode gives adoption *order*, nothing gave migration *mechanics* for a specific named transition. Path A (Pages→App Router) verified against Next.js's own migration guide; Path B builds on `ts-state-management`'s existing cost table rather than duplicating it; Path C is the incremental-Zod pattern `ts-validation-schema` never covered. |
