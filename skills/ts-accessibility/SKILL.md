---
name: ts-accessibility
description: >
  Accessibility (a11y) for the Next.js/React/shadcn-ui stack this collection
  scaffolds — native semantics over ARIA-patched divs, focus management for
  Base UI-backed Dialog/Sheet/Select, Next.js App Router route-announcer
  gotchas, next/image alt text, color-contrast checks for the CSS-variable
  token system, and prefers-reduced-motion handling for Tailwind's animate-*
  utilities. Cross-references ts-forms for label/error-announcement patterns
  and ts-testing-playwright for accessible-role-based locators instead of
  duplicating either.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-10'
  keywords:
    - accessibility
    - a11y
    - ARIA
    - keyboard navigation
    - screen reader
    - focus management
    - focus trap
    - color contrast
    - prefers-reduced-motion
    - jsx-a11y
    - alt text
    - WCAG
    - Base UI accessibility
    - skip link
    - route announcer
---

## When to Use This Skill

Use when you need to:
- Build or review any interactive UI — Dialog, Sheet, Select, Combobox, custom
  clickable element — and need to know what Base UI already handles vs. what's
  still the developer's job
- Fix a screen reader gap after route navigation in the App Router
- Decide `alt=""` vs. a real description on a `next/image`
- Check whether a CSS-variable color token pair (`--background`/`--foreground`)
  meets WCAG contrast before shipping a new theme or variant
- Add or audit `prefers-reduced-motion` handling for a Tailwind `animate-*`
  utility or CSS transition
- Explain why `eslint-plugin-jsx-a11y` flagged a line

**Trigger keywords:** accessibility, a11y, ARIA, aria-label, aria-live,
keyboard navigation, screen reader, VoiceOver, NVDA, focus management, focus
trap, focus order, skip link, skip-to-content, color contrast, WCAG,
prefers-reduced-motion, motion-safe, motion-reduce, alt text, route announcer,
jsx-a11y, accessible name, tab order, inert.

**Freshness rule:** Base UI's "accessible by default" claims and the Next.js
route-announcer behavior are both active development areas — recheck
base-ui.com's accessibility docs and nextjs.org/docs/architecture/accessibility
before asserting either one still behaves as described here. The route
announcer in particular has a known open gap (see below); verify it hasn't
been fixed before repeating the workaround.

---

## Recommendation First

**Reach for the native HTML element and Base UI's built-in behavior before
hand-writing ARIA.** This collection's stack does most of the accessibility
work for free if you don't fight it:

1. `<button>`, not `<div onClick>` with a bolted-on `role="button"` — a real
   button gets keyboard activation (Enter/Space), focusability, and the
   correct accessible role with zero code. Reserve manual `role`/`tabIndex`
   for the rare case a native element genuinely can't express the widget.
2. shadcn/ui's Base UI-backed primitives (Dialog, Sheet, Select, Popover,
   Combobox) already manage ARIA attributes, keyboard navigation (arrow keys,
   Home/End, Esc), and focus trapping/restoration internally — see
   `ts-shadcn-ui`. Don't re-implement what `DialogPopup`/`SelectPopup` already
   do; only add what Base UI explicitly leaves to you (see below).
3. `eslint-plugin-jsx-a11y` ships inside `eslint-config-next` by default —
   `alt` on `img`, `aria-props`, `role-has-required-aria-props` are linted out
   of the box. Don't disable the rule; fix what it flags.

What Base UI does **not** do for you, per its own docs: visually indicating
focus (`:focus-visible` styling is your CSS), color contrast, and an
accessible label for anything without visible text (icon-only buttons still
need `aria-label`).

---

## Focus Management: Dialog, Sheet, and Popup Primitives

Base UI's Dialog/Sheet/Popover primitives trap focus inside the open surface,
cycle Tab/Shift+Tab within it, close on Esc, and restore focus to the trigger
element on close — all without extra code, as long as you use the primitive's
own trigger/portal/popup components instead of building a custom overlay:

```tsx
// components/ui/dialog.tsx — from ts-shadcn-ui, Base UI backed
import { Dialog as BaseDialog } from "@base-ui-components/react/dialog";

export const Dialog = BaseDialog.Root;
export const DialogTrigger = BaseDialog.Trigger;
export const DialogPortal = BaseDialog.Portal;
export const DialogContent = BaseDialog.Popup;
```

```tsx
<Dialog>
  <DialogTrigger className={cn(buttonVariants({ variant: "outline" }))}>
    Delete item
  </DialogTrigger>
  <DialogPortal>
    {/* focus moves here on open, traps until close, returns to the
        trigger button above on close — all handled by Base UI */}
    <DialogContent aria-labelledby="delete-title" aria-describedby="delete-desc">
      <h2 id="delete-title">Delete item?</h2>
      <p id="delete-desc">This can't be undone.</p>
    </DialogContent>
  </DialogPortal>
</Dialog>
```

`aria-labelledby`/`aria-describedby` pointing at the heading/body text is
still your job — Base UI wires the `role="dialog"` and `aria-modal="true"`,
but it doesn't know which text labels the dialog. If a dialog demands a
choice rather than allowing dismissal, pass Base UI's alert-dialog variant
(`role="alertdialog"`) instead of building a plain Dialog that happens to lack
a close button.

**Never build a custom modal overlay from a styled `<div>` + `fixed inset-0`**
without a focus-trap primitive underneath it — that reintroduces exactly the
focus-escape and Esc-key bugs Base UI's Dialog exists to prevent.

---

## Keyboard Navigation: Select and Combobox

Base UI's Select/Combobox handle Arrow Up/Down to move the highlighted option,
Home/End to jump to the first/last, typeahead (typing letters jumps to a
matching option), and Enter/Esc to commit/cancel — again, only if you compose
the primitive's own parts:

```tsx
// components/ui/select.tsx — Base UI backed
import { Select as BaseSelect } from "@base-ui-components/react/select";

export const Select = BaseSelect.Root;
export const SelectTrigger = BaseSelect.Trigger;
export const SelectPopup = BaseSelect.Popup;
export const SelectItem = BaseSelect.Item;
```

```tsx
<Select value={status} onValueChange={setStatus}>
  <SelectTrigger aria-label="Filter by status" className={cn(buttonVariants({ variant: "outline" }))}>
    <BaseSelect.Value />
  </SelectTrigger>
  <BaseSelect.Portal>
    <SelectPopup>
      <SelectItem value="open">Open</SelectItem>
      <SelectItem value="closed">Closed</SelectItem>
    </SelectPopup>
  </BaseSelect.Portal>
</Select>
```

Give `SelectTrigger` an `aria-label` (or a visible `<label htmlFor>` per
`ts-forms`) when no visible text describes what the select controls — an
icon-only or placeholder-only trigger otherwise announces nothing useful.

---

## Route Change Focus and Announcements (App Router)

Next.js includes a route announcer by default for client-side `next/link`
navigations — it inspects `document.title`, falling back to the page's `<h1>`,
then the URL pathname, and announces whichever it finds to assistive tech.
Focus also moves to the top of the new page's content after a transition, so
keyboard/screen-reader users aren't left focused on stale browser chrome.

**The known gap:** the announcer only fires when `document.title` actually
changes. A navigation between routes that share a title (e.g. filter/sort
query params, or sibling tabs under one layout) produces no announcement at
all, because the `<h1>`/pathname fallback only triggers when there is no
title, not when the title is merely unchanged. Give each meaningfully
different route or view its own `<title>` (via `generateMetadata` in a Server
Component) rather than relying on the fallback path.

```tsx
// app/orders/[status]/page.tsx — distinct title per status so the route
// announcer actually has something new to announce
export async function generateMetadata({ params }: { params: { status: string } }) {
  return { title: `Orders — ${params.status}` };
}
```

For a Client Component that needs to move focus manually after an in-page
state change (not a route change — see `ts-nextjs-app-router` for the
Server/Client boundary this requires), do it explicitly:

```tsx
"use client";
import { useRef, useEffect } from "react";

export function SearchResults({ query }: { query: string }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, [query]);
  return <h2 ref={headingRef} tabIndex={-1}>Results for "{query}"</h2>;
}
```

`tabIndex={-1}` makes an element programmatically focusable without adding it
to the normal Tab order.

---

## Skip-to-Content Link

A skip link lets keyboard users bypass repeated nav/header markup and land
directly on the main content — add it once, in the root layout, visually
hidden until focused:

```tsx
// app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-foreground focus:outline"
        >
          Skip to content
        </a>
        <Header />
        <main id="main-content">{children}</main>
      </body>
    </html>
  );
}
```

`sr-only` hides it visually but keeps it in the accessibility tree;
`focus:not-sr-only` reveals it the moment a keyboard user tabs to it.

---

## Images: `next/image` Alt Text

`next/image`'s `alt` prop is what screen readers announce and what displays
if the image fails to load — `eslint-plugin-jsx-a11y` warns if it's missing,
but it isn't a hard build error, so don't rely on the linter alone:

```tsx
// Meaningful image — describes what the image conveys, not "image of..."
<Image src={product.imageUrl} alt={`${product.name} product photo`} width={400} height={400} />

// Purely decorative — empty string, not omitted, tells screen readers to skip it
<Image src="/hero-background.svg" alt="" width={1200} height={400} />
```

Never leave `alt` off entirely — an omitted `alt` and an empty `alt=""` are
not the same thing to a screen reader; only the empty string is an
intentional "skip this."

---

## Color Contrast in the CSS-Variable Token System

Every shadcn/ui color is a token pair (`--background`/`--foreground`,
`--primary`/`--primary-foreground`, `--destructive`/`--destructive-foreground`)
defined in `app/globals.css` per `ts-shadcn-ui`. WCAG AA requires 4.5:1 for
normal text and 3:1 for large text (18pt+, or 14pt+ bold) — check every
foreground/background pair the token system defines, in **both** `:root` and
`.dark`, not just the light theme:

```css
:root {
  --primary: 240 5.9% 10%;           /* dark background */
  --primary-foreground: 0 0% 98%;    /* near-white text — check this pair */
}
.dark {
  --primary: 0 0% 98%;               /* now light background */
  --primary-foreground: 240 5.9% 10%; /* dark text — recheck, it's not the same pair inverted */
}
```

Inverting a token pair for dark mode does not guarantee the contrast ratio
survives the swap — verify each theme's pair independently with a contrast
checker (WebAIM's or a browser DevTools contrast panel) rather than assuming
symmetry. This is a token-authoring concern, not a per-component one: fix it
once in `globals.css`, not per usage of `bg-primary`.

---

## `prefers-reduced-motion` for Tailwind Animations

Tailwind's `motion-safe:`/`motion-reduce:` variants gate any utility on the
`prefers-reduced-motion` media query — wrap non-essential `animate-*`
utilities and transitions in `motion-safe:` so users who've asked for less
motion don't get it:

```tsx
// Loading spinner — only spins if the user hasn't requested reduced motion
<Loader2 className="motion-safe:animate-spin" />

// Hover scale effect — explicitly disabled under reduced motion
<Card className="transition-transform motion-safe:hover:scale-105 motion-reduce:transition-none" />
```

An entrance/exit animation on a Base UI Dialog/Sheet (via `data-[state=open]`/
`data-[state=closed]` Tailwind variants) is exactly the kind of non-essential
motion this applies to — a user with vestibular sensitivity shouldn't get a
slide/fade on every dialog open just because the default styling includes one.

---

## Forms and Testing — Cross-References, Not Duplication

- **Form labels, error announcement (`role="alert"`), and `aria-invalid`** are
  covered in `ts-forms` — the `SignInForm` example there already associates
  `<label htmlFor>` with `register()`'d inputs and surfaces validation errors
  with `role="alert"`. Don't re-derive that pattern here.
- **Testing with accessible locators** (`getByRole`, `getByLabel`) is covered
  in `ts-testing-playwright` — querying by role/label instead of a CSS
  selector or test-id both tests the feature and doubles as an accessibility
  check, since an element `getByRole` can't find often means assistive tech
  can't find it either.

---

## Common Anti-Patterns

- **`<div onClick={...}>` instead of `<button>`** — no keyboard activation, no
  focusability, no accessible role; announced as nothing to a screen reader.
  Use a real `<button>` (or `<a href>` for navigation) every time.
- **Building a custom modal from a styled `<div>`** instead of Base UI's
  Dialog primitive — silently drops focus trapping, Esc-to-close, and focus
  restoration that the primitive provides for free.
- **Icon-only buttons with no `aria-label`** — `<Button size="icon"><X /></Button>`
  announces as "button" with no indication of what it does; every icon-only
  trigger needs `aria-label` or visually-hidden text.
- **Assuming an inverted dark-mode token pair keeps the same contrast ratio**
  — `--primary`/`--primary-foreground` flipping between light and dark themes
  is a color swap, not a contrast guarantee; check both themes independently.
- **Unconditional `animate-*` or CSS transition on every element** — no
  `motion-safe:`/`motion-reduce:` gating means users who've set
  `prefers-reduced-motion: reduce` at the OS level still get the animation.
- **Relying on the App Router's route announcer for query-param-only or
  same-title navigations** — the announcer only fires on a `document.title`
  change; give distinct views distinct titles instead of assuming the
  fallback path announces anything.
- **Omitting `alt` on `next/image`** instead of using `alt=""` for decorative
  images — an omitted `alt` isn't the same as an intentional empty one, and
  the linter warning is not a build failure, so it's easy to ship unnoticed.

---

## Related Skills

- `ts-shadcn-ui` — the Base UI/Radix primitive layer this skill's focus and
  keyboard-navigation guidance builds directly on
- `ts-nextjs-app-router` — Server/Client Component boundary that determines
  where focus-management `useEffect`/`ref` code is allowed to live
- `ts-forms` — label association, `aria-invalid`, and error announcement for
  form fields specifically
- `ts-testing-playwright` — `getByRole`/`getByLabel` locators that double as
  an accessibility check
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-10 | Initial version. |
