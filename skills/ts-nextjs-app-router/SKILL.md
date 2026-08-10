---
name: ts-nextjs-app-router
description: >
  Next.js App Router architecture contract — Server vs Client Component boundary,
  layouts and route groups, Server Actions, and middleware. The single most
  consequential architecture decision in a Next.js app: get the server/client
  boundary wrong and every feature built on top inherits the mistake.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Next.js
    - App Router
    - Server Components
    - Client Components
    - Server Actions
    - middleware
    - use client
    - use server
    - RSC
    - route groups
    - layouts
---

## When to Use This Skill

Use when you need to:
- Decide whether a component should be a Server or Client Component
- Structure routes, layouts, and route groups
- Mutate data from a form without a separate API route
- Explain a "Text content did not match" hydration error or a `useState` used in a
  Server Component error

**Trigger keywords:** Server Component, Client Component, use client, use server,
Server Action, App Router, route group, layout.tsx, page.tsx, hydration mismatch,
Next.js middleware, streaming, Suspense boundary.

**Freshness rule:** App Router's caching semantics (`fetch` defaults, `revalidatePath`/
`revalidateTag`) have changed across Next.js major versions — recheck the current
Next.js docs before relying on a specific caching default.

---

## Recommendation First

**Server Components by default. Add `"use client"` only at the leaf that actually
needs interactivity** (state, effects, event handlers, browser APIs) — not at the top
of a page.

Why: a Server Component never ships its JavaScript to the browser. Marking a whole
page `"use client"` because one button needs `onClick` ships the entire subtree's JS
for nothing.

```tsx
// ✓ Server Component (default, no directive needed) — fetches data, renders static markup
export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await db.product.findUnique({ where: { id: params.id } });
  return (
    <div>
      <ProductInfo product={product} />
      <AddToCartButton productId={product.id} />   {/* only this needs interactivity */}
    </div>
  );
}

// ✓ Client Component — pushed to the leaf, not the whole page
"use client";
export function AddToCartButton({ productId }: { productId: string }) {
  const [pending, setPending] = useState(false);
  return <button onClick={() => addToCart(productId)} disabled={pending}>Add to cart</button>;
}
```

---

## The Server/Client Boundary Is One-Directional

A Server Component can render a Client Component. A Client Component **cannot**
import and render a Server Component directly — once you cross into client code,
everything below it in that subtree is client code too, unless passed in as `children`
from a Server Component parent.

```tsx
// ❌ Wrong — ServerOnlyWidget can't be imported into client code
"use client";
import { ServerOnlyWidget } from "./server-only-widget"; // fails or silently becomes client-bundled

// ✓ Correct — pass the server-rendered content down as children
// (Server Component)
<ClientShell>
  <ServerOnlyWidget />
</ClientShell>
```

---

## Server Actions — Mutating Without a Separate API Route

```tsx
// app/actions.ts
"use server";
import { z } from "zod";

const AddCommentSchema = z.object({ postId: z.string(), body: z.string().min(1) });

export async function addComment(formData: FormData) {
  const parsed = AddCommentSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { error: parsed.error.flatten() };
  await db.comment.create({ data: parsed.data });
  revalidatePath(`/posts/${parsed.data.postId}`);
}
```

```tsx
// Server Component — <form action={addComment}> works with no client JS at all
<form action={addComment}>
  <input name="postId" value={postId} type="hidden" />
  <textarea name="body" />
  <button type="submit">Comment</button>
</form>
```

A Server Action is not the same as an API route (`app/api/*/route.ts`) — use a Server
Action for a form mutation triggered from within the app; use a route handler for a
webhook, a third-party callback, or anything that needs a stable public URL contract.

---

## Layouts and Route Groups

```
app/
├── (marketing)/            # route group — doesn't affect the URL
│   ├── layout.tsx           # marketing-only layout (nav, footer)
│   └── page.tsx              # "/"
├── (app)/
│   ├── layout.tsx           # app-shell layout (sidebar, auth check)
│   └── dashboard/
│       └── page.tsx          # "/dashboard"
└── layout.tsx               # root layout — <html>/<body>, shared across both groups
```

A `layout.tsx` persists across navigations within its scope — it does not remount when
a child `page.tsx` changes, which is why data fetched in a layout (e.g. the current
user session) doesn't refetch on every navigation.

---

## Caching Layers — Fetch Cache, Full Route Cache, and ISR

Three distinct caches — don't conflate them:

- **Fetch cache** — Next.js caches `fetch()` calls made in Server Components. Control
  per-call with `{ cache: 'force-cache' | 'no-store' }` or `{ next: { revalidate: N } }`.
- **Full route cache** — the rendered HTML/RSC payload for a route with no dynamic data,
  computed once at build/deploy and served statically on every request.
- **ISR (Incremental Static Regeneration)** — a route stays statically served but
  regenerates in the background once its `revalidate` window elapses, so users get a
  fast (if slightly stale) response while the next version builds.

```tsx
// Revalidate every hour — content that changes occasionally (blog post, product listing)
const res = await fetch('https://api.example.com/posts', { next: { revalidate: 3600 } });

// Always fresh — required for user-specific/authenticated data
const res = await fetch('https://api.example.com/me', { cache: 'no-store' });

// No options — default cached behavior for a fetch in a Server Component
const res = await fetch('https://api.example.com/posts');
```

`revalidatePath`/`revalidateTag` (see the `addComment` Server Action above) are the
on-demand escape hatch — they invalidate the fetch cache and full route cache for a
path/tag immediately, instead of waiting for a `revalidate` window to expire.

**Why this is the scalability lever:** deployed to Vercel, a statically-rendered or
ISR'd route is served from Vercel's CDN at the edge. Most traffic never reaches your
server or database at all — origin is only hit on a cache miss or background
regeneration, not per-request.

**The gotcha:** a Server Component that reads per-user data (the logged-in user's name,
a cart) still inherits the *route's* cache under default caching — render it that way
and Next.js can serve user A's data to user B. Fetch that data with `{ cache: 'no-store' }`,
or read `cookies()`/`headers()`, which Next.js recognizes as dynamic and automatically
opts the route out of static caching.

---

## Common Anti-Patterns

- **`"use client"` on a page component** because one child needs interactivity — push
  the directive down to the actual interactive leaf instead.
- **`useEffect` fetching data a Server Component could fetch directly** — a Client
  Component `useEffect` fetch means: ship the JS, wait for hydration, then fetch,
  causing a loading-spinner flash the server could have avoided entirely.
- **Passing a non-serializable prop from Server to Client Component** (a function, a
  class instance, a `Date` isn't the issue but a Map/Set is) — Server→Client props
  cross a serialization boundary; only plain data survives.
- **Calling a Server Action directly from a `useEffect`** instead of a form/button
  interaction — Server Actions are designed around explicit user-triggered mutations,
  not background polling; use a route handler + `fetch` for that instead.
- **Caching a route or `fetch` call that returns per-user or authenticated data**
  without opting out — the default cached behavior leaks one user's data to another;
  use `{ cache: 'no-store' }` or read `cookies()`/`headers()` to force it dynamic.

---

## Related Skills

- `ts-project-foundation` — the package layout this app architecture sits inside
- `ts-forms` — React Hook Form + Zod, often paired with a Server Action for the submit
- `ts-auth` — session checks in middleware and layouts
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
