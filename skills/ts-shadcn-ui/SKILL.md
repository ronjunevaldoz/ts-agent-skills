---
name: ts-shadcn-ui
description: >
  shadcn/ui component system, with Tailwind CSS as the underlying styling layer
  (not a separate skill). shadcn/ui isn't an npm package — the CLI copies component
  source into your own codebase, so you own and edit it directly. As of July 2026
  shadcn/ui defaults new projects to Base UI (not Radix) as the headless primitive
  layer; Radix isn't deprecated and is still fully supported as an explicit choice,
  but Base UI — built by the same team, with a render-props API instead of `asChild`
  and more primitives (Combobox, Autocomplete, Number Field) — is now the default.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - shadcn/ui
    - Base UI
    - Radix UI
    - Tailwind CSS
    - component library
    - cva
    - class-variance-authority
    - cn utility
    - dark mode
    - design tokens
    - components.json
    - headless primitives
---

## When to Use This Skill

Use when you need to:
- Set up shadcn/ui in a new or existing project (`components.json`, CLI, base color)
- Add or customize a component (Button, Dialog, Select, ...) and need to know it's
  copied source, not a black-box dependency
- Decide between Base UI (default) and Radix as the primitive layer
- Build a variant system (size, variant, state) with `cva` the way shadcn/ui does
- Wire up light/dark mode via CSS variable tokens instead of hardcoded Tailwind colors

**Trigger keywords:** shadcn/ui, shadcn add, components.json, Base UI, Radix UI,
`cn()` utility, class-variance-authority, cva, Tailwind theming, CSS variables,
`--background`, `--primary`, dark mode, headless components, copy-paste components.

**Freshness rule:** the Base UI/Radix default is a fast-moving decision — shadcn/ui
switched its default primitive layer once already (Radix → Base UI, mid-2026), and
the `init` CLI itself changed shape since then (named presets replacing a simple
base-color prompt, confirmed live 2026-08-10 — see CLI Setup below). Recheck
shadcn/ui's own changelog (ui.shadcn.com), run `npx shadcn@latest init --help`, and
the real `components.json` output before assuming anything below still matches —
this collection got burned once already by documenting an exact CLI flow that drifted.

---

## Recommendation First

**shadcn/ui is not an installed dependency — it's a code generator.** `npx shadcn@latest
add button` copies `button.tsx` into `components/ui/` in your own repo. There's no
`node_modules/shadcn-ui` package to upgrade or eject from; the component's source is
yours from the moment it's added, so editing it is expected, not a fork.

**Primitive layer: accept the CLI default (Base UI) unless the project already has
Radix components.** Base UI is shadcn/ui's default for new projects as of July 2026 —
same original author team as Radix, a render-props API instead of `asChild`, more
primitives, and active development. Radix still works and is still supported; pick it
explicitly (`shadcn` init prompts for the primitive/style choice, or pass the Radix
registry style) only when the codebase is already built on Radix or a dependency
requires it. Don't mix the two within one project — see Anti-Patterns.

---

## CLI Setup and components.json

**This skill assumes the `next` template — the CLI supports others.** `-t` accepts
`next`, `vite`, `react-router`, `start`, and `astro`; the CLI detects the framework
automatically in most cases, `-t` is only needed to override. On `vite`, the
generated `components.json` omits `"rsc": true` (no Server Components) and points
`tailwind.css` at `src/index.css`, not `app/globals.css` — everything else below
(preset, primitive layer, theming) is identical across templates. For anything
Vite-specific beyond `components.json` shape (project scaffold, path aliases in
`vite.config.ts`, dev server), see `ts-vite-spa` — this skill only covers the
shadcn/ui layer. Full CLI reference, including every template and flag: the
official [shadcn-ui/ui `skills/shadcn/cli.md`](https://github.com/shadcn-ui/ui/blob/main/skills/shadcn/cli.md),
maintained by the shadcn/ui team directly — defer to it over guessing at flags
this file doesn't cover.

```bash
npx shadcn@latest init -t next -b base -p nova
```

**Verified live 2026-08-10 against the real current CLI — this has changed since
this skill's last check.** `init` no longer asks a standalone "base color"
question; it prompts for a **preset** (`nova`/`vega`/`maia`/`lyra`/`mira`/`luma`/
`sera`/`rhea`, or `custom` for independent control over every choice), which
bundles a color scheme, icon library, and menu style together. The primitive
layer choice (`-b`) now has **three** options, not two: `base` (Base UI, the
default), `radix`, and `aria` (React Aria Components) — accept `base` unless the
project already has Radix/Aria components. Pass `-p <preset>` non-interactively;
`nova` is the closest match to what this skill previously called the "new-york"
default. It writes:

```jsonc
// components.json — real output, not the pre-preset-era shape
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "base-nova",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "iconLibrary": "lucide",
  "rtl": false,
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "menuColor": "default",
  "menuAccent": "subtle",
  "registries": {}
}
```

`tailwind.baseColor` still exists (confirmed `"neutral"` under the `nova`
preset) — a base-color *question* asked upstream of this skill (e.g.
`ts-new-project`'s intake) still maps onto something real, just via preset
selection now, not a standalone CLI flag. `style` is now the preset name
(`base-nova`), not a fixed `"new-york"`/`"default"` pair — don't assume the old
two-value enum still applies.

Adding a component pulls its source plus any primitive dependency it needs:

```bash
npx shadcn@latest add button dialog
```

`add` writes `components/ui/button.tsx` and `components/ui/dialog.tsx` directly into
the repo. If the project targets Radix instead of the Base UI default, that choice is
recorded in `components.json`'s style entry and every subsequent `add` pulls the
Radix-backed variant of that component — don't hand-swap the import in one file and
leave the rest on the other primitive.

---

## The `cn()` Utility

Every shadcn/ui component uses `cn()` to merge conditional classes without the
override collisions plain string concatenation produces:

```ts
// lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

`clsx` handles conditional/falsy class inputs; `twMerge` resolves conflicting
Tailwind utilities so the last one wins instead of both being applied:

```ts
cn("px-2 py-1", isActive && "bg-primary", className);
// className="px-4" passed in from a caller correctly overrides "px-2", not just appends
```

Without `twMerge`, `cn("px-2", "px-4")` would emit both classes and let CSS source
order (not intent) decide which wins — `twMerge` keeps only `px-4`.

---

## Variant Patterns with `cva`

shadcn/ui components define their variant props with `class-variance-authority`, not
hand-written conditionals:

```tsx
// components/ui/button.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
```

Usage — `variant`/`size` are typed, autocompleted, and impossible to typo:

```tsx
<Button variant="destructive" size="sm" onClick={handleDelete}>
  Delete
</Button>
```

A Dialog built on Base UI (the current default) uses render props instead of Radix's
`asChild`:

```tsx
// components/ui/dialog.tsx (Base UI backed)
import { Dialog as BaseDialog } from "@base-ui-components/react/dialog";

export function Dialog({ children, ...props }: BaseDialog.Root.Props) {
  return <BaseDialog.Root {...props}>{children}</BaseDialog.Root>;
}
export const DialogTrigger = BaseDialog.Trigger;
export const DialogPortal = BaseDialog.Portal;
export const DialogContent = BaseDialog.Popup;
```

```tsx
<Dialog>
  <DialogTrigger className={cn(buttonVariants({ variant: "outline" }))}>
    Open
  </DialogTrigger>
  <DialogPortal>
    <DialogContent className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
      <h2 className="text-lg font-semibold">Delete item?</h2>
      <p className="text-sm text-muted-foreground">This can't be undone.</p>
    </DialogContent>
  </DialogPortal>
</Dialog>
```

---

## Dark Mode via CSS Variable Tokens

shadcn/ui never hardcodes a Tailwind color in a component — every color is a CSS
variable token, redefined per theme:

```css
/* app/globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
  }
}
```

`tailwind.config.ts` maps these to utility classes (`bg-background`, `text-primary`,
`border-border`) via `hsl(var(--token))`, which is why `bg-primary` in the `cva`
definition above works in both themes without a single `dark:` variant — toggling the
`.dark` class on `<html>` swaps every token at once.

---

## Common Anti-Patterns

- **Treating shadcn/ui like a normal npm package** — never touching the copied
  component source, waiting for an "upstream update" that doesn't exist. The entire
  point is that `components/ui/button.tsx` is yours; not customizing it is leaving the
  main benefit on the table.
- **Mixing Radix-based and Base UI-based components in one project** — half the
  components importing `@radix-ui/react-*`, the other half `@base-ui-components/react/*`.
  Pick one primitive layer at init and keep every `add` on that style; two different
  focus-management/portal implementations in the same app produces inconsistent
  keyboard and screen-reader behavior.
- **Hardcoding colors** (`bg-slate-900`, `text-white`) in a shadcn/ui component instead
  of the token classes (`bg-background`, `text-foreground`) — breaks dark mode silently
  since the hardcoded value never responds to the `.dark` class toggle.
- **Re-implementing `cn()` as plain `clsx()`** without `tailwind-merge` — conflicting
  utility classes (`px-2` from the component, `px-4` from a caller's `className` prop)
  both end up in the DOM, and which one wins depends on CSS source order, not the
  caller's intent.
- **Adding a component's dependency primitive manually** instead of via `npx shadcn add`
  — hand-installing `@base-ui-components/react` or `@radix-ui/react-dialog` without
  running the CLI skips the version pin and copied source the CLI keeps in sync with
  `components.json`.

---

## Related Skills

- `ts-project-foundation` — the workspace/package layout `components/ui` lives inside
- `ts-nextjs-app-router` — Server/Client Component boundary for interactive shadcn/ui
  components (most need `"use client"`)
- `ts-forms` — React Hook Form + Zod paired with shadcn/ui form components
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
| 2026-08-10 | Fixed a real, live-verified drift: `init`'s CLI shape changed from a simple base-color prompt + `"new-york"`/`"default"` style to named presets (`nova`/`vega`/`maia`/etc.) and a three-way primitive choice (`base`/`radix`/`aria`, "aria" is new). Found by actually running `npx shadcn@latest init` end-to-end while live-testing `/ts-new-project`'s full pipeline — this skill's documented `components.json` output no longer matched reality. |
