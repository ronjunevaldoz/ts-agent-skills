---
name: ts-impeccable
description: >
  Guidance for using Impeccable (impeccable.style), a real third-party Claude
  Code plugin that detects and removes "AI slop" design tells — purple-to-blue
  gradients, Inter-for-everything, cards nested in cards, gray text on colored
  backgrounds, bounce/elastic easing. This skill does NOT reimplement
  Impeccable's 23 commands or 59 detector rules — it's a routing/decision
  guide for when to install it, how it composes with ts-shadcn-ui and
  ts-nextjs-app-router, and where in the project lifecycle to run it. Defer to
  Impeccable's own docs (impeccable.style, github.com/pbakaus/impeccable) for
  command behavior itself.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-22'
  keywords:
    - Impeccable
    - impeccable.style
    - AI slop
    - AI-generated design
    - design quality
    - anti-pattern detector
    - purple gradient
    - generic UI
    - design polish
    - design audit
    - design critique
    - looks like AI made it
---

## When to Use This Skill

Use when:
- A UI looks generic or "AI-made" — purple gradients, Inter everywhere, cards
  stacked in cards, predictable hero-with-gradient-blob layout
- Starting a new project's visual design and wanting a structured
  init → build → polish flow instead of ad hoc styling decisions
- About to ship a page/feature and want a design-quality pass before it goes
  out (accessibility, responsive, visual hierarchy)

Do NOT use this skill to look up what a specific `/impeccable` command does in
detail — read the command reference at impeccable.style or the repo's own
`skill/reference/*.md` instead; re-deriving that here would drift stale.

**Trigger keywords:** Impeccable, impeccable.style, AI slop, looks like AI
made this, generic UI, purple gradient, design audit, design critique, design
polish, anti-pattern detector, design quality.

**Freshness rule:** Impeccable ships frequently (v3.6.0 as of 2026-08-22,
31 published versions) — recheck impeccable.style or the GitHub repo for
current command names/counts before relying on a specific number; this
skill's own counts will drift.

---

## Recommendation First

**Install Impeccable directly rather than asking this collection to
reimplement any part of it.** It's a real, actively maintained, Apache-2.0
tool built on Anthropic's own `frontend-design` skill — 61,500+ GitHub stars,
maintained by Paul Bakaus, pushed within the last day as of this writing. Its
59 deterministic detector rules run with no LLM and no API key (CLI/browser
extension), which this collection has no reason to duplicate.

This skill's job is narrower: know when to reach for it and how it fits
alongside `ts-shadcn-ui`/`ts-nextjs-app-router`, not to re-document its
commands.

---

## Install

**Option 1 — Claude Code plugin marketplace (simplest for this stack):**
```bash
/plugin marketplace add pbakaus/impeccable
```
Then open `/plugin`, install Impeccable from the list, and run `/impeccable init`.

**Option 2 — CLI installer (works across multiple agent harnesses):**
```bash
npx impeccable install
```
Detects `.claude`/`.codex`/`.cursor`/etc. in the project, asks project vs.
global scope. `--providers=claude,codex,cursor` and `--scope=project|global`
skip the prompts for scripted installs.

**Option 3 — Git submodule (teams that want it vendored and version-pinned):**
```bash
git submodule add https://github.com/pbakaus/impeccable .impeccable
npx impeccable link --source=.impeccable --providers=claude
```

Reload the harness after any install method.

---

## Where This Fits in the Project Lifecycle

```
ts-project-foundation → ts-nextjs-app-router → ts-shadcn-ui
                                                     |
                                          /impeccable init (once, early)
                                                     |
                                   build features (ts-forms, ts-data-fetching, ...)
                                                     |
                                     /impeccable polish  (before shipping a page)
                                     /impeccable audit   (a11y, responsive, perf)
```

`/impeccable init` writes `PRODUCT.md` (durable product facts: audience,
platform, voice) and offers `DESIGN.md` (visual system: colors, type,
components) — run it once per project, early, same phase as `ts-shadcn-ui`'s
initial theme setup. Don't run it per-feature; it's meant to capture durable
context that later commands read, not a per-page ritual.

Run `/impeccable polish` or `/impeccable audit` as a pre-ship gate on a
specific page/feature — this pairs naturally with `ts-review-changes`'s own
review step, but checks visual/design quality specifically, which
`ts-review-changes` doesn't cover.

---

## Command Reference (pointer, not a copy)

Impeccable ships 23 commands under one entry point (`/impeccable <command>
<target>`) — `init`, `craft`, `shape`, `critique`, `audit`, `polish`, `bolder`,
`quieter`, `distill`, `harden`, `onboard`, `animate`, `colorize`, `typeset`,
`layout`, `delight`, `overdrive`, `clarify`, `adapt`, `optimize`, `document`,
`extract`, `live`. Full behavior for each lives in Impeccable's own
`skill/reference/<command>.md` files and impeccable.style — don't re-derive
command semantics here, they change across releases.

The four most relevant to this collection's own workflow:
| Command | When |
|---|---|
| `/impeccable init` | Once, early — writes `PRODUCT.md`/`DESIGN.md` |
| `/impeccable critique` | UX review — hierarchy, clarity, before investing in polish |
| `/impeccable polish` | Final pass before shipping a page/feature |
| `/impeccable audit` | Technical design checks — a11y, performance, responsive |

---

## Anti-Patterns Impeccable Catches (examples, not the full 59)

Verified from Impeccable's own README — illustrative, not exhaustive:
- overused fonts (Arial, Inter, browser/system defaults) with no deliberate
  choice behind them
- gray text on colored backgrounds
- pure black/gray with no tint
- cards wrapped inside cards
- bounce/elastic easing (reads as dated, not intentional)

If a page exhibits these without Impeccable installed, that's the signal to
install it rather than hand-writing a one-off fix — the detector catches the
whole class, not just the instance in front of you.

---

## Common Anti-Patterns (in how this skill gets used)

- reaching for this skill to answer "what does `/impeccable polish` actually
  do" — that question belongs to Impeccable's own docs, not here
- running `/impeccable init` per-feature instead of once per project — it
  captures durable product context, not per-page state
- treating Impeccable as a replacement for `ts-shadcn-ui` — it's a design
  *quality* layer on top of whatever component system is already chosen, not
  a component library itself
- skipping the install and asking an agent to manually replicate the 59
  detector rules from memory — they're deterministic and versioned upstream;
  hand-replication drifts immediately

---

## Related Skills

- `ts-shadcn-ui` — the component system Impeccable's design-quality pass
  layers on top of; not an alternative to it
- `ts-nextjs-app-router` — the app whose pages get audited/polished
- `ts-review-changes` — code-correctness review; pair with Impeccable's
  `/audit`/`/polish` for the design-quality half of a pre-ship check
- `ts-expert` — routing and build order for the full skill set

---

## Output Style

When asked about eliminating AI-slop design, respond in this order:
1. confirm Impeccable isn't already installed (check for `.claude/skills/impeccable`,
   `.impeccable/`, or `PRODUCT.md`)
2. the install command (plugin marketplace, by default)
3. `/impeccable init` if no `PRODUCT.md` exists yet
4. the specific command for the actual need (`critique`, `polish`, `audit`, etc.) —
   point at Impeccable's own reference for exact behavior, don't guess at it

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-22 | Initial release. User asked whether impeccable.style could eliminate AI-slop design and requested a skill for it. Verified real (not another inflated-star repo like the earlier ECC evaluation): `pbakaus/impeccable`, Apache-2.0, 61,500+ stars, actively pushed, built on Anthropic's own `frontend-design` skill, npm package at v3.6.0. Deliberately scoped as a routing/decision skill, not a reimplementation — confirmed no existing skill in this collection referenced it, and confirmed Impeccable already ships as a directly-installable Claude Code plugin, so duplicating its 23 commands or 59 detector rules here would only drift stale. |
