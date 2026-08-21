# Adoption Roadmap Mode

Part of `ts-audit`. Load this file when working on: adoption roadmap mode.

---

Findings mode (the default, see main SKILL.md) answers "what's wrong with this code."
Roadmap mode answers a different question: "this project has none of this collection's
conventions yet — what order should I adopt them in?" Use roadmap mode when the request
is about a brownfield project with little or no existing structure, not a specific
smell in specific code.

## State Signals

Check each of these before building the plan — file presence and `package.json`
dependencies, no AST parsing needed:

| Signal | How to check |
|---|---|
| Strict TypeScript | `tsconfig.json`'s `"strict"` value — per `ts-project-foundation`'s baseline, this should be `true` |
| Monorepo layout | `turbo.json` and `pnpm-workspace.yaml` present at root |
| CI | `.github/workflows/*.yml` present, and whether it runs lint/typecheck/test/build |
| Validation | `zod` in `package.json` dependencies |
| State management | Redux/Zustand/Context usage — grep for `createStore`, `create(` (Zustand), or heavy prop-drilling with no library at all |
| Auth | `next-auth`/`@auth/*`/`lucia`/`@clerk/*` in dependencies |
| Testing | `vitest.config.ts` and/or `playwright.config.ts` present |
| Accessibility | Any `aria-label`/`role=` usage at all in `components/` — zero hits across a UI-heavy project is the real signal, not a single missing instance |
| API layer convention | tRPC router or a consistent REST route-handler shape, vs. ad hoc `fetch` calls scattered through client components |

## Adoption Plan

| Condition | Priority | Skill | Reason | Action |
|---|---|---|---|---|
| `tsconfig.json` has no `"strict": true` | HIGH | `ts-project-foundation` | Every other convention assumes strict-mode type safety; adding it later means fixing every new type error the flip reveals at once | Turn on `strict` first, before adopting anything else — fix errors file by file, not in one pass |
| No CI at all | HIGH | `ts-ci-github-actions` | Nothing catches a regression before merge — every other adoption step below is unguarded without this | Add lint/typecheck/test/build as one workflow before making structural changes |
| Client components calling `fetch` directly, no schema | HIGH | `ts-validation-schema` | Every request/response boundary re-invents its own ad hoc shape, and none of it is type-checked against runtime data | Add Zod at the highest-traffic boundary first, expand outward |
| No consistent API layer (ad hoc `fetch` calls) | MEDIUM | `ts-api-layer` | No single contract between client and server — every route is its own convention | Pick tRPC or REST route handlers once, migrate the highest-traffic endpoint first |
| No state-management convention (prop-drilling or ad hoc Context) | MEDIUM | `ts-state-management` | Every new feature invents its own answer to "where does this state live" | Pick one approach for the whole project; migrate the most-drilled prop chain first |
| No tests at all | MEDIUM | `ts-testing-vitest` | Migrating structure with no tests risks invisible regressions in the exact code being touched | Add tests for the first feature being migrated, before migrating it |
| Monorepo present but no `import/no-restricted-paths` boundary rule | MEDIUM | `ts-project-foundation` | Nothing stops a feature from reaching into another feature's internals | Add the ESLint boundary rule, fix violations feature by feature |
| Zero `aria-label`/`role=` usage across a UI-heavy project | MEDIUM | `ts-accessibility` | Not one missing instance — no accessibility convention exists yet anywhere in the UI | Start with the highest-traffic interactive components (nav, primary CTAs), not every file at once |
| Auth exists but sessions aren't re-validated server-side | HIGH | `ts-auth` | A client-only or middleware-only check is bypassable by a direct request to a Server Action/route handler | Add the server-side check at the actual data-access boundary, not just the UI gate |

## Output Format

```
==========================================================
  TS ADOPTION ROADMAP
  Project: <path>
==========================================================

Current state:
  TypeScript strict : <yes/no>
  Monorepo layout   : <turbo+pnpm / single-package>
  CI                : <none / lint+typecheck+test+build / partial>
  Validation        : <zod / none>
  State management  : <library name / prop-drilling / ad hoc Context>
  Auth              : <library name / none>
  Testing           : <vitest+playwright / one of / none>
  Accessibility     : <aria usage found / none found>

Adoption plan (<count> items):

  1. [HIGH] <skill>
     Why:    <reason>
     Action: <action>

  2. ...

Run in findings mode (no roadmap request) to check for code-level violations
in whatever's already been adopted.
```

State first, then the plan, HIGH priority first — same shape as findings mode, so a
reader who's seen one output format recognizes the other immediately.
