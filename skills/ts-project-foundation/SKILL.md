---
name: ts-project-foundation
description: >
  TypeScript project architecture contract for a Next.js/Node monorepo — tsconfig
  strict-mode baseline, ESLint flat config + Prettier, pnpm workspaces + Turborepo
  layout, and package boundary rules. This is the TS analog of a Gradle module
  graph: TS has no compiler-enforced module boundary, so the workspace layout and
  lint rules together *are* the architecture contract every other skill assumes.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - tsconfig
    - strict mode
    - ESLint
    - Prettier
    - pnpm workspaces
    - Turborepo
    - monorepo
    - package boundaries
    - project references
---

## When to Use This Skill

Use when you need to:
- Set up a new TypeScript monorepo from scratch
- Decide package boundaries between apps and shared libraries
- Enforce that one package can't reach into another's internals
- Explain why a build is slow, or why types don't resolve across packages

**Trigger keywords:** tsconfig, strict mode, ESLint config, Prettier, pnpm workspace,
Turborepo, monorepo setup, package boundary, project references, workspace protocol,
turbo.json, shared config package.

**Freshness rule:** Turborepo and pnpm's workspace protocol both change release to
release — recheck their own docs before setting up a new monorepo.

---

## Recommendation First

**pnpm workspaces + Turborepo**, TypeScript project references for cross-package type
checking, one shared `tsconfig.base.json` every package extends.

Why:
- pnpm's strict node_modules (no phantom dependencies) catches a missing `package.json`
  dependency at install time, not at a random runtime import failure
- Turborepo caches per-package build/lint/test output — a CI run only re-does work for
  packages that actually changed
- TS project references (`"references": [{ "path": "../shared" }]`) make cross-package
  type errors surface in the IDE, not just at build time

Use a single-package repo (no workspaces) only for a standalone library or a small app
with no shared code — don't scaffold monorepo tooling for something that will never
have a second package.

---

## Layout

```
my-app/
├── apps/
│   ├── web/              # Next.js app
│   └── api/               # Nest.js or Express app, if separate from web
├── packages/
│   ├── ui/                 # shared shadcn/ui components
│   ├── db/                 # Prisma/Drizzle schema + client
│   ├── config/             # shared tsconfig.base.json, eslint config
│   └── types/              # shared types with zero runtime dependencies
├── turbo.json
├── pnpm-workspace.yaml
└── package.json
```

`pnpm-workspace.yaml`:
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

Each package depends on another via the `workspace:*` protocol, never a version range:
```json
{
  "dependencies": {
    "@myapp/ui": "workspace:*"
  }
}
```

---

## Organizing Feature Code — Frontend vs Backend

The `apps/`/`packages/` layout above is the workspace-level boundary. Within `apps/web`,
features need their own convention — App Router (`ts-nextjs-app-router`) only defines
routing, not where business logic lives.

### Frontend (`apps/web`) — flat `features/` folders

```
apps/web/
├── app/                    # routing only — see ts-nextjs-app-router
├── features/
│   ├── billing/
│   │   ├── api/             # queries/mutations for this feature
│   │   ├── components/
│   │   ├── hooks/
│   │   └── types.ts
│   └── team-members/
│       └── ...
```

Rule: `shared → features → app`, one-directional. A feature never imports another
feature directly — share through `packages/ui`/`packages/types`, or lift the shared
piece into its own package. Enforce with ESLint, not just convention:

```js
// eslint.config.js
{
  rules: {
    "import/no-restricted-paths": ["error", {
      zones: [
        { target: "./features/billing", from: "./features/team-members" },
      ],
    }],
  },
}
```

This flat convention (bulletproof-react) is the right weight for most apps. If the app
accumulates enough shared business-domain objects (a `user`/`product`/`order` reused
across many features) that flat `features/` starts tangling, escalate to Feature-Sliced
Design's full layer stack (`app → pages → widgets → features → entities → shared`) —
don't adopt FSD's seven layers up front for an app that doesn't need them yet.

### Backend (`apps/api`) — framework decides, not convention

- **Nest.js** — feature boundaries are framework-enforced, not a convention to
  remember. Each feature is a `@Module` (`nest g module billing`) whose
  `controllers`/`providers` are private unless explicitly listed in `exports` — an
  unexported service literally cannot be injected into another module. `nest generate`
  colocates `billing.module.ts`, `billing.controller.ts`, `billing.service.ts` in one
  folder by default.
- **Express** — has no module system, so nothing enforces this. Mirror the same shape
  by hand (`routes/billing/{router,controller,service}.ts` per feature) and, if
  cross-feature imports matter, apply the same `import/no-restricted-paths` rule used
  on the frontend — Express won't stop a stray import otherwise.

This is why the Layout above lists Nest.js first for `apps/api` when a separate
backend is needed: it makes this boundary a compiler-enforced fact instead of a lint
rule people can route around.

---

## tsconfig — the strict baseline

```jsonc
// packages/config/tsconfig.base.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "moduleResolution": "bundler",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "isolatedModules": true
  }
}
```

`noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` are not part of `strict` —
turn them on explicitly. Without `noUncheckedIndexedAccess`, `arr[i]` types as `T`
instead of `T | undefined`, silently hiding out-of-bounds access the same way an
un-null-checked platform type would in Kotlin.

Every package's own `tsconfig.json` extends the base and adds only its own `paths`/`outDir`:
```jsonc
{
  "extends": "@myapp/config/tsconfig.base.json",
  "compilerOptions": { "outDir": "dist" },
  "include": ["src"]
}
```

---

## Package Boundary Rules

TS has no compile-time equivalent of Kotlin's `internal` visibility across a module
graph — a package boundary is enforced by **not exporting** the thing, plus an ESLint
rule catching a deep import that reaches past the public entry point:

```js
// eslint.config.js
{
  rules: {
    "no-restricted-imports": ["error", {
      patterns: ["@myapp/*/src/*", "@myapp/*/dist/*"],
    }],
  },
}
```

This blocks `import { helper } from "@myapp/db/src/internal/helper"` — only the
package's declared entry point (`@myapp/db`, resolving to its `package.json#main`/`exports`)
is importable. Every package's internals live under `src/`, and only `index.ts`'s
exports are the real public surface.

---

## Common Anti-Patterns

- **Phantom dependencies** — a package uses a library it never listed in its own
  `package.json`, relying on it being hoisted by a sibling package. pnpm's strict
  linking prevents this at install time; npm/yarn classic won't catch it until the
  dependency graph shifts and the import breaks.
- **Circular package dependencies** — `packages/ui` importing from `packages/db` and
  vice versa. Turborepo will refuse to build (can't resolve a task order); the real fix
  is extracting the shared piece into a third package both depend on.
- **One giant `packages/shared`** — everything gets dumped in one catch-all package,
  and every unrelated change forces every consumer to rebuild. Same Divergent Change
  smell as a god ViewModel — split by what changes together, not by "things multiple
  apps use."

---

## Related Skills

- `ts-nextjs-app-router` — the app-level architecture contract built on top of this
  package layout
- `ts-ci-github-actions` — Turborepo remote caching wired into CI
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
| 2026-08-10 | Added "Organizing Feature Code" — frontend `features/` convention (bulletproof-react), FSD as the escalation path, Nest.js module-per-feature vs Express for `apps/api`. |
