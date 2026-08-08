---
name: ts-ci-github-actions
description: >
  GitHub Actions CI for a TypeScript/Next.js/Turborepo monorepo — lint, typecheck,
  test, and build jobs, per-package Turborepo remote caching, and pnpm frozen-lockfile
  installs. The direct analog of a Gradle CI matrix: without this, every other skill
  in this collection produces code nobody's checking. Assumes the pnpm workspace +
  Turborepo layout from ts-project-foundation.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - GitHub Actions
    - CI/CD
    - Turborepo
    - pnpm
    - remote cache
    - monorepo CI
    - frozen lockfile
    - affected packages
    - turbo run
    - lint
    - typecheck
    - vitest
    - workflow YAML
---

## When to Use This Skill

Use when you need to:
- Set up GitHub Actions CI for a new or existing TypeScript/Next.js/Turborepo monorepo
- Add lint, typecheck, test, or build jobs that only run on packages actually affected by a PR
- Wire Turborepo remote caching into CI so builds don't redo unchanged work
- Explain why CI is slow, why a cache never hits, or why a stale lockfile passed locally but failed in CI

**Requires:** `ts-project-foundation` pnpm workspace + Turborepo layout.

**Trigger keywords:** GitHub Actions, CI pipeline, Turborepo remote cache, turbo run,
pnpm frozen-lockfile, affected packages, monorepo CI, workflow YAML, CI is slow,
cache miss, TURBO_TOKEN, setup-node, pnpm install CI, PR checks, build workflow.

**Freshness rule:** `actions/setup-node`'s pnpm caching support and Turborepo's remote
cache signature/env vars have both changed across major versions — recheck current
docs before pinning versions in a new project.

---

## Recommendation First

**One workflow file, one job, `turbo run` doing the fan-out** — not four separate
GitHub Actions jobs for lint/typecheck/test/build.

Why:
- Turborepo already parallelizes tasks across packages using its own task graph;
  splitting that across GitHub Actions jobs just adds duplicate `pnpm install` and
  checkout overhead for work Turborepo would've scheduled anyway
- a single `turbo run lint typecheck test build --filter=...[origin/main]` only
  touches packages actually affected by the PR — the same principle as running only
  the Gradle modules a change touches, not the whole multi-module graph
- Turborepo remote caching means a second run (or a different contributor's branch
  touching the same packages) skips re-executing tasks entirely, not just re-uses
  `node_modules`

Split into multiple jobs only once a single job's wall-clock time becomes the
bottleneck (e.g. E2E tests that need a browser matrix) — see `ts-testing-playwright`
for that case specifically.

---

## Complete `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}

jobs:
  ci:
    name: Lint, Typecheck, Test, Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2 # turbo needs the previous commit to diff against

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint, typecheck, test, build (affected packages only)
        run: pnpm turbo run lint typecheck test build --filter=...[origin/main]
```

For `push` to `main` (no PR base to diff against), fall back to running everything:

```yaml
      - name: Lint, typecheck, test, build
        run: |
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            pnpm turbo run lint typecheck test build --filter=...[origin/${{ github.base_ref }}]
          else
            pnpm turbo run lint typecheck test build
          fi
```

`turbo.json` needs matching task definitions for this to cache correctly:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "lint": { "outputs": [] },
    "typecheck": { "dependsOn": ["^build"], "outputs": [] },
    "test": { "dependsOn": ["^build"], "outputs": ["coverage/**"] },
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] }
  }
}
```

`outputs: []` on `lint`/`typecheck` tells Turborepo there's no artifact to cache
besides the pass/fail result itself — still hash-cached, just nothing to restore to disk.

---

## Turborepo Remote Caching

Without remote caching, only the runner filesystem is cached (nothing persists
between separate PRs by different contributors touching the same package). Remote
caching shares the cache across every CI run and every developer's machine:

```bash
# one-time setup, from a local machine with Vercel/Turborepo auth
npx turbo login
npx turbo link
```

Then set these as repo secrets/variables (**Settings → Secrets and variables → Actions**):

| Name | Type | Purpose |
|---|---|---|
| `TURBO_TOKEN` | Secret | Auth token for the remote cache |
| `TURBO_TEAM` | Variable | Team/org slug the cache is scoped to |

Self-hosting instead of Vercel's remote cache (e.g. via `turborepo-remote-cache` on
your own infra) only changes `TURBO_API`/`TURBO_TOKEN` values — the workflow YAML
above is unchanged either way.

---

## pnpm Store Caching

`actions/setup-node@v4`'s `cache: 'pnpm'` input handles this automatically — it
locates the pnpm store via `pnpm/action-setup` (which must run *before*
`setup-node` in the step order, as shown above) and caches it keyed on
`pnpm-lock.yaml`'s hash. No separate `actions/cache` step is needed, and none should
be added — a hand-rolled `actions/cache` step for the store is exactly the kind of
duplicate, driftable caching logic `cache: 'pnpm'` exists to replace.

---

## Common Anti-Patterns

- **Running `pnpm install` without `--frozen-lockfile`** — CI silently regenerates
  `pnpm-lock.yaml` when it drifts from `package.json`, masking a lockfile that's
  actually out of sync and letting a broken dependency resolution reach `main`.
- **Running the full monorepo's lint/test/build on every PR** instead of
  `--filter=...[origin/main]` — a one-line change to `packages/ui` shouldn't force
  every unrelated app in the monorepo to rebuild and retest.
- **Skipping `TURBO_TOKEN`/`TURBO_TEAM`** — Turborepo still works without remote
  caching, but every PR pays full cold-cache cost since nothing persists across runs
  or contributors; this is the single biggest lever on CI wall-clock time.
- **`fetch-depth: 1` (the default) with `--filter=...[origin/main]`** — Turborepo's
  git-based affected-package diff needs history to compare against; a shallow
  checkout makes the filter fail or silently treat everything as affected.
- **Splitting lint/typecheck/test/build into four separate GitHub Actions jobs**
  before Turborepo's own task graph and cache have been given a chance to do that
  parallelization — four jobs means four `pnpm install`s and four checkouts for work
  one job's `turbo run` already schedules concurrently.

---

## Related Skills

- `ts-project-foundation` — the pnpm workspace + Turborepo layout this CI workflow assumes
- `ts-testing-vitest` — the `test` task this workflow's `turbo run` invokes
- `ts-testing-playwright` — E2E tests, usually split into their own job/matrix once they need a browser
- `ts-deploy-vercel` — the deploy step that typically follows a green CI run
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
