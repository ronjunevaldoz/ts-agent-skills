---
name: ts-vite-spa
description: >
  Vite + React SPA scaffold as an alternative to ts-nextjs-app-router when the
  project doesn't need SSR, Server Components, or file-based routing — a pure
  client-side app, a dashboard behind auth, an embeddable widget, or a static
  site with a light backend. Covers the Vite scaffold, routing-library choice
  (no built-in router), import.meta.env / VITE_ prefix, and static deploy
  output. Does NOT cover shadcn/ui setup on Vite (see ts-shadcn-ui, which
  already documents the Vite template) or Tailwind (folded into ts-shadcn-ui).
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-22'
  keywords:
    - Vite
    - Vite SPA
    - single page application
    - React Router
    - TanStack Router
    - vite.config.ts
    - import.meta.env
    - VITE_ prefix
    - static deploy
    - client-side only
    - no SSR
    - not Next.js
    - dashboard app
    - embeddable widget
    - create vite
---

## When to Use This Skill

Use when:
- The project is a pure client-side app with no SEO/SSR requirement — an
  internal dashboard, an admin panel, an embeddable widget, a Chrome extension
  popup, or a static marketing site with a thin API
- Someone asks for "Vite" or "a Vite app" specifically, not "Next.js"
- An existing Next.js project needs a Vite comparison to justify (or rule out)
  switching

Do NOT use when the project needs SSR, streaming, file-based routing, or
Server Components — that's `ts-nextjs-app-router`, load it instead.

**Trigger keywords:** Vite, Vite SPA, vite.config.ts, create vite, single page
application, React Router, TanStack Router, import.meta.env, VITE_ prefix,
static deploy, client-side only, no SSR, dashboard app, embeddable widget,
not Next.js, why not Next.js.

**Freshness rule:** Vite's plugin API and `@vitejs/plugin-react` version pin
change between major Vite releases — recheck vite.dev's own docs before
upgrading Vite itself.

---

## Recommendation First

Default to **Next.js App Router** (`ts-nextjs-app-router`) unless the project
has a concrete reason not to need SSR/SEO. Vite is the right call when:

- the app sits behind auth for every route (no SEO to serve — a dashboard,
  an admin panel)
- it's an embeddable widget or browser extension, not a full site
- the team wants the smallest possible toolchain and deploys as static files
  to any host, not specifically Vercel

Why this default, not the reverse: Next.js's App Router gives Server
Components, streaming, and file-based routing for free — reimplementing
routing and data-fetching conventions by hand in Vite is real, avoidable work
for a project that would benefit from SSR. Pick Vite because the project
genuinely doesn't need that, not because it's "simpler" in the abstract.

---

## Scaffold

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app
npm install
```

`--template react-ts` is the only template variant this skill covers —
TypeScript is this collection's baseline everywhere else, no reason to diverge
here.

`@vitejs/plugin-react` ships in the template already — it's what wires up Fast
Refresh and JSX; no separate setup step.

---

## Routing — No Built-In Router

Unlike Next.js, Vite ships no router. Pick one before writing more than one
route:

| Library | Pick when |
|---|---|
| **React Router** | Default choice — largest ecosystem, most Stack Overflow/LLM training coverage, works fine for most SPA route trees |
| **TanStack Router** | Type-safe route params/search params matter (a dashboard with heavy query-string filtering) — its file-based route generation is closer to what App Router users are used to |

```bash
npm install react-router
```

```tsx
// src/main.tsx
import { BrowserRouter, Routes, Route } from "react-router";

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  </BrowserRouter>,
);
```

No `app/` directory convention — routes are declared, not inferred from the
filesystem, unless TanStack Router's file-based generator is opted into
separately.

---

## Environment Variables — `VITE_` Prefix

Vite only exposes env vars prefixed `VITE_` to client code, via
`import.meta.env`, not `process.env`:

```bash
# .env
VITE_API_URL=https://api.example.com
```

```ts
const apiUrl = import.meta.env.VITE_API_URL;
```

This is the direct equivalent of Next.js's `NEXT_PUBLIC_` prefix — same
reasoning (anything without the prefix stays server/build-time only, never
bundled into client JS), different prefix string. Don't reuse `NEXT_PUBLIC_`
vars from a migrated Next.js project without renaming them; Vite won't expose
them.

---

## Deploy Output — Static Files, Not SSR

```bash
npm run build   # outputs dist/ — static HTML/JS/CSS
```

`dist/` is a static bundle — deploy it to any static host (Vercel, Netlify,
Cloudflare Pages, S3+CloudFront, GitHub Pages). There is no server runtime to
select (no Edge vs Node decision like `ts-deploy-vercel` covers for Next.js)
because there's no server — every route resolves client-side. Configure the
host to rewrite all paths to `index.html` (SPA fallback) so client-side
routing handles deep links instead of 404ing.

---

## What Still Applies From Other Skills

Vite replaces only the Next.js framework layer — everything above and below
it is unchanged:

- `ts-shadcn-ui` — install with `-t vite`; the shadcn CLI already covers the
  Vite template (path aliases in `tsconfig.json`/`tsconfig.app.json`/
  `vite.config.ts`, `components.json` without `rsc: true`)
- `ts-validation-schema`, `ts-state-management`, `ts-forms`,
  `ts-data-fetching` — none of these depend on Next.js; use them as-is
- `ts-testing-vitest` — Vitest is already Vite-native, no extra config beyond
  what a Next.js project needs
- `ts-orm-database` / `ts-api-layer` — a Vite SPA still needs a real backend
  for these; it just isn't the same process serving the frontend

---

## Common Anti-Patterns

- reaching for Vite because Next.js "feels heavy" without checking whether
  the project actually needs SSR/SEO first — see Recommendation First
- reading `process.env.VITE_*` instead of `import.meta.env.VITE_*` — Vite
  doesn't polyfill `process.env` by default, this silently returns `undefined`
- forgetting the SPA-fallback rewrite on the static host — deep links 404 on
  refresh because the host looks for a matching file, not a client route
- copying `NEXT_PUBLIC_`-prefixed env vars over unchanged during a migration —
  Vite won't expose them; rename to `VITE_`

---

## Related Skills

- `ts-nextjs-app-router` — the SSR/App-Router alternative this skill assumes
  you've ruled out; see its own scope for when to prefer it instead
- `ts-shadcn-ui` — component system, already covers the `-t vite` template
- `ts-testing-vitest` — Vitest, Vite-native already
- `ts-migration` — mechanics for moving an existing Pages/App Router project;
  this skill is a fresh scaffold, not a migration path
- `ts-expert` — routing and build order for the full skill set

---

## Output Style

When asked to scaffold a Vite SPA, respond in this order:
1. confirm SSR/SEO genuinely isn't needed (Recommendation First)
2. the `npm create vite@latest` scaffold command
3. routing library choice with a one-line reason
4. env var setup (`VITE_` prefix) if the project reads config at runtime
5. deploy shape (static `dist/`, host rewrite rule)

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-22 | Initial release. Real gap found researching Vite/Next.js/Tailwind/shadcn coverage: every "vite" keyword hit in the repo was actually a "Vitest" substring match — zero real Vite-the-framework coverage existed. Verified against vite.dev's own docs and shadcn/ui's own Vite install guide before writing. Scoped to framework-level concerns only (scaffold, routing, env vars, deploy shape) since `ts-shadcn-ui` already covers the Vite template's `components.json` differences and every other skill (state, forms, data-fetching, validation, testing) already applies unchanged. |
