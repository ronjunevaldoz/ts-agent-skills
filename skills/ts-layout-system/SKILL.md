---
name: ts-layout-system
description: >
  Drafts low-fidelity screen wireframes for a Next.js project before real
  implementation — gray-box JSX, no real styling, viewable live via the dev
  server instead of an ASCII sketch. Creates docs/layout-system/ (component
  table + region notes per screen) plus a dev-only wireframe route under
  app/(dev)/wireframes/ that never ships to production. Settles where things
  go before ts-shadcn-ui settles what they look like.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-10'
  keywords:
    - layout system
    - wireframe
    - screen layout
    - low-fi mockup
    - mock UI
    - component registry
    - layout spec
    - docs layout-system
    - screen structure
    - dev route
    - private route group
---

## When to Use This Skill

Use when you need to:
- Sketch a new screen's layout before writing the real components
- Record what a screen looks like after a layout change
- Give a reviewer something to actually look at before real styling exists

**Trigger keywords:** layout system, wireframe, screen layout, mock UI, low-fi
mockup, mock design, draft screen, screen structure, component registry,
layout docs, design screen, sketch layout, plan screen.

**Freshness rule:** Next.js's private-folder/route-group conventions
(`_folder`, `(folder)`) are stable API, but recheck the App Router docs if a
Next.js major version changes routing resolution.

---

## Recommendation First

**Low-fidelity JSX, not ASCII.** A Next.js app already renders in a browser —
sketching the layout as real (if ugly) JSX and viewing it through the actual
dev server gives real visual fidelity for free: proportions, wrapping,
scroll behavior, responsive breakpoints. An ASCII text grid can't show any
of that, and needs manual alignment upkeep no compiler checks.

Two artifacts per screen:
- `docs/layout-system/<screen>.md` — component table + region notes (the spec, reviewable as text)
- `app/(dev)/wireframes/<screen>/page.tsx` — the actual live gray-box JSX (the visual, reviewable in a browser)

Never invent a third format (no separate design tool, no image export) —
these two files are the whole system.

---

## Directory Structure

```
docs/layout-system/
├── _components.md              <- shared component registry (read this first)
├── <screen-name>.md            <- one file per distinct screen
└── <screen-name>.md

app/(dev)/wireframes/
├── inbox/page.tsx               <- live low-fi JSX for the "inbox" screen
└── settings/page.tsx
```

- `(dev)` is a Next.js **route group** — parentheses are stripped from the
  URL, so this renders at `/wireframes/inbox`, not `/(dev)/wireframes/inbox`.
  A route group (not a private `_folder`) is required here specifically
  because private folders are excluded from routing entirely — nothing
  would be reachable in the browser to review.
- Screen files: kebab-case, named after the screen (`inbox.md`, `settings.md`)
- `_components.md` uses a leading underscore so it sorts first

---

## The Dev-Only Guard

Every file under `app/(dev)/` must refuse to render in production — a
wireframe route is scaffolding, not a shipped page:

```tsx
// app/(dev)/wireframes/inbox/page.tsx
import { notFound } from "next/navigation";

export default function InboxWireframe() {
  if (process.env.NODE_ENV === "production") notFound();

  return (
    <div className="flex h-screen">
      <div className="w-16 border-r bg-muted p-2 text-xs">[nav]</div>
      <div className="w-56 border-r bg-muted p-2 text-xs">[thread list]</div>
      <div className="flex-1 p-2 text-xs">
        <div className="border-b bg-muted p-4">[thread header]</div>
        <div className="flex-1 bg-muted/50 p-4">[message body, scroll]</div>
        <div className="border-t bg-muted p-2">[reply input]</div>
      </div>
    </div>
  );
}
```

Every region is a plain `<div>` with a `border` + `bg-muted` (a neutral
Tailwind/shadcn token, not a hardcoded color) and a `[bracketed label]` —
no real component, no real copy, no real data. That's deliberate: this
stage settles layout only, `ts-shadcn-ui` settles the actual look
downstream, so a wireframe can never end up looking like the shipped app.

Add a top-level `app/(dev)/wireframes/page.tsx` index listing every drafted
screen as a link, so reviewing the whole set is one page load.

---

## Layout Patterns

Four named shapes cover most screens. **Pick the closest match and state which one
in the screen's spec file — don't ask the user to choose.** Layout is cheap to
change (it's reviewed live in Step 3, not locked in), so recommend one and let the
review catch a wrong pick, the same way `ts-shadcn-ui`'s base color gets a
recommended default instead of an open-ended question.

**Pattern A — nav + side panel + main.** Dashboard-shaped screens: a persistent
icon nav rail, a secondary list/filter panel, and the primary content area.

```tsx
<div className="flex h-screen">
  <div className="w-16 border-r bg-muted p-2 text-xs">[nav]</div>
  <div className="w-56 border-r bg-muted p-2 text-xs">[side panel]</div>
  <div className="flex-1 p-4 text-xs">[main content]</div>
</div>
```

**Pattern B — nav + main only.** Same nav rail, no secondary panel — content fills
the rest (tabs, a card grid, a single form).

```tsx
<div className="flex h-screen">
  <div className="w-16 border-r bg-muted p-2 text-xs">[nav]</div>
  <div className="flex-1 p-4 text-xs">
    <div className="border-b bg-muted p-2">[tabs]</div>
    <div className="grid grid-cols-3 gap-4 p-4">
      <div className="aspect-square bg-muted">[card]</div>
      <div className="aspect-square bg-muted">[card]</div>
      <div className="aspect-square bg-muted">[card]</div>
    </div>
  </div>
</div>
```

**Pattern C — modal/sheet overlay.** The underlying screen stays mounted; a dialog
or sheet renders on top. Draw the base screen dimmed, the overlay on top.

```tsx
<div className="relative flex h-screen">
  <div className="flex-1 bg-muted/30 p-4 text-xs">[base screen, dimmed]</div>
  <div className="absolute inset-0 flex items-center justify-center bg-black/20">
    <div className="w-96 border bg-background p-4 text-xs">
      <div className="border-b pb-2">[sheet title]</div>
      <div className="py-2">[sheet content]</div>
    </div>
  </div>
</div>
```

**Pattern D — full-screen, no nav.** Login, onboarding, splash, error pages — no
persistent chrome at all.

```tsx
<div className="flex h-screen items-center justify-center bg-muted/20">
  <div className="w-96 bg-muted p-6 text-xs">[centered content]</div>
</div>
```

---

## `docs/layout-system/<screen>.md` — The Spec

```markdown
# Inbox

## Pattern

A — nav + side panel + main. Thread list is the side panel, message view is main.

## Regions

| Region | Content | Notes |
|---|---|---|
| Nav | Icon-only side rail | Always visible |
| Thread list | Scrollable list of conversations | Empty state: "No messages yet" |
| Thread header | Selected thread's participant name | |
| Message body | Scrollable message history | `[scroll]` |
| Reply input | Text input + send button | Disabled while sending |

## Responsive notes

Below `md`: thread list and message body are separate views (tap a thread to
navigate in), not side-by-side columns.

## Wireframe

Live at `/wireframes/inbox` (`pnpm dev` first). See
`app/(dev)/wireframes/inbox/page.tsx`.
```

## `_components.md` — Component Registry

```markdown
# Component Registry

| Component | Used in | Real implementation |
|---|---|---|
| Nav rail | Every screen | `ts-shadcn-ui` sidebar primitive, not yet built |
| Thread list item | Inbox | New — needs a `ThreadListItem` component |
```

Update this file as real components get built — it starts as "not yet
built" placeholders during this step, and each row's last column gets
filled in during `ts-shadcn-ui`/feature implementation.

---

## Bootstrap (project has no layout-system yet)

1. From the confirmed MVP scope (`ts-new-project` Step 2), list every screen.
2. For each screen: pick the closest Layout Pattern (A/B/C/D above) and note it —
   don't ask, recommend one and let the visual review in step 4 catch a wrong pick.
3. For each screen: write `docs/layout-system/<screen>.md` (Pattern + Regions),
   then `app/(dev)/wireframes/<screen>/page.tsx` starting from that pattern's
   template, customized with the screen's real regions.
4. Write the `/wireframes` index page linking all of them.
5. Print the list of URLs and ask the reviewer to run `pnpm dev` and look —
   this is a visual review, not a fixed-choice question, so don't force an
   `AskUserQuestion` popup here. Wait for actual feedback in the next
   message before moving on.

---

## Common Anti-Patterns

- **Using real shadcn/ui components in a wireframe.** Defeats the purpose —
  a wireframe that already looks polished stops getting layout-only
  feedback and starts getting styling feedback too early.
- **Skipping the production guard.** A wireframe route left reachable in
  production is dead, confusing UI shipped to real users.
- **Using a private folder (`_wireframes`) instead of a route group
  (`(dev)`).** Private folders are excluded from routing entirely — nobody
  could ever open the URL to review it.
- **Letting `_components.md` drift from what's actually implemented.** It's
  a living registry, not a one-time snapshot — update it as real components
  replace placeholder rows.
- **Writing the spec file without the JSX file, or vice versa.** The text
  spec and the live visual are both required; the spec alone can't be
  reviewed in a browser, and the JSX alone has no written record of *why*
  each region exists.

---

## Validation Checklist

| Check | Expected |
|---|---|
| Both files exist per screen | `docs/layout-system/<screen>.md` and `app/(dev)/wireframes/<screen>/page.tsx` |
| Production guard present | Every wireframe `page.tsx` calls `notFound()` when `NODE_ENV === "production"` |
| No real components used | Every region is a plain `<div>` with a `[label]`, not a real `ts-shadcn-ui` component |
| Index page exists | `app/(dev)/wireframes/page.tsx` links every drafted screen |
| `_components.md` current | Every component referenced in a screen file is listed |
| Pattern stated | Every screen's spec file names which of the four Layout Patterns it uses |

---

## Related Skills

- `ts-nextjs-app-router` — the route-group/private-folder mechanics this
  skill's dev-only routing relies on
- `ts-shadcn-ui` — the real component system that replaces every
  gray-box placeholder once layout is agreed
- `ts-project-foundation` — where `docs/` and `app/` already live in the
  monorepo layout
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-10 | Initial version. |
| 2026-08-10 | Added four named Layout Patterns (A/B/C/D), ported from `kmp-layout-system`'s ASCII patterns as JSX templates. The agent picks the closest match per screen and states it in the spec file — not asked, consistent with the visual-review-catches-a-wrong-pick approach the rest of this skill already uses. |
