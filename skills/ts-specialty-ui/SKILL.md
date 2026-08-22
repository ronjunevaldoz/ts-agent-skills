---
name: ts-specialty-ui
description: >
  Decision guide for four narrow, optional UI libraries that solve one specific
  problem outside `ts-shadcn-ui`'s core component system: React Bits (animated/
  decorative polish), assistant-ui (AI chat interface primitives), driver.js
  (onboarding tours and feature spotlights), and Tailark (prebuilt marketing/
  landing-page blocks via the shadcn registry). Each is opt-in per-project, not
  part of the standard build order — load this skill only when one of these
  four specific needs comes up. Does NOT replace ts-shadcn-ui for core app
  components, or ts-nextjs-app-router for routing/rendering architecture.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-22'
  keywords:
    - React Bits
    - reactbits
    - animated components
    - assistant-ui
    - AI chat interface
    - chat UI
    - Thread component
    - driver.js
    - onboarding tour
    - product tour
    - feature spotlight
    - Tailark
    - landing page blocks
    - marketing blocks
    - hero section
    - shadcn registry
---

## When to Use This Skill

Use when one of these four specific needs comes up — not as a default, each is
opt-in:
- A marketing/decorative surface needs eye-catching animation (hero background,
  animated text) beyond what plain Tailwind/shadcn gives → **React Bits**
- The project needs an actual AI chat/agent interface, not a single button →
  **assistant-ui**
- A first-run experience needs a step-by-step spotlight tour of the UI →
  **driver.js**
- A marketing site needs a hero/pricing/testimonial/CTA section fast, without
  hand-building it → **Tailark**

**Trigger keywords:** React Bits, reactbits, animated hero, animated text
component, assistant-ui, AI chat UI, chat interface, Thread component,
driver.js, onboarding tour, product tour, feature spotlight, walkthrough,
Tailark, landing page blocks, marketing blocks, hero section, pricing section,
prebuilt landing page.

**Freshness rule:** all four are actively developed, community/small-team
libraries — recheck each project's own docs before relying on a specific
version, CLI flag, or peer-dependency list; this skill's version pins and
commands were verified on 2026-08-22 and will drift.

---

## Recommendation First

Load only the section below matching the actual need — these four don't
compose into one decision tree, they're four independent opt-in tools. Default
to **not** using any of them until the specific need is real: React Bits for
decorative flourish nobody asked for is the same mistake as an unrequested
abstraction — don't add animation, a chat surface, a tour, or marketing blocks
speculatively.

---

## React Bits — Animated/Decorative Components

**What it is:** an open-source, copy-paste library of 165+ animated React
components (text effects, animated backgrounds, UI flourishes) — not an npm
package you import, source becomes part of your project, same distribution
model as shadcn/ui itself.

**When:** a marketing page or hero section needs a specific animated effect
(particle background, animated gradient text) that would otherwise mean
hand-rolling Framer Motion/GSAP from scratch. Not for core app UI — buttons,
forms, tables stay in `ts-shadcn-ui`.

**Install (per component, pick one CLI):**
```bash
npx shadcn@latest add "https://reactbits.dev/r/<component-name>"
# or
npx jsrepo add github/sh20raj/react-bits/<component-name>
```

**Peer dependencies — only install what the specific component needs:**
| Dependency | Needed for |
|---|---|
| `motion` | most text animations |
| `gsap` | `AnimatedContent` and some scroll-triggered animations |
| `three` + `@types/three` | 3D components (`ASCIIText`, `ModelViewer`, `Hyperspeed`) |
| `ogl` | shader backgrounds (`Silk`, `Iridescence`, `LiquidChrome`) |

Each component's page on reactbits.dev states its exact deps — don't
preemptively install all four; add only what the component you picked needs.

**License caveat, real and worth stating:** MIT + Commons Clause. Commons
Clause restricts *selling the library itself as a hosted service* — it does
not restrict using it inside a product you build and sell. Don't let this
block normal usage, but don't repackage React Bits itself as a paid component
marketplace either.

---

## assistant-ui — AI Chat Interface Primitives

**What it is:** a TypeScript/React library of composable AI chat primitives —
`Thread`, `Message`, `Composer`, `ThreadList`, `ActionBar` — not a single
monolithic chat widget. Ships an actual npm package (`@assistant-ui/react`),
unlike the other three libraries here.

**When:** the project needs a real chat/agent surface — multi-turn
conversation, streaming responses, tool-call rendering — not a one-off "Ask
AI" button. This is new capability, not covered anywhere else in this
collection.

**Install — CLI (fastest, scaffolds styled components into the project):**
```bash
npx assistant-ui@latest init      # add to an existing Next.js project
npx assistant-ui@latest create    # new project
```

**Manual install:**
```bash
npm install @assistant-ui/react
npm install @assistant-ui/react-ai-sdk   # Vercel AI SDK runtime binding
```

**Basic wiring:**
```tsx
"use client";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/react-ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";

export function Chat() {
  const runtime = useChatRuntime();
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
```

`useChatRuntime` wires to the Vercel AI SDK out of the box — swap in
`useLangGraphRuntime`/`useDataStreamRuntime`/a custom runtime for a different
backend. Generative UI (rendering tool calls as real components, inline human
approval) is the library's main differentiator over hand-rolling a chat box.

**Primitive-layer consistency check:** the CLI's starter defaults to Base
UI (same default `ts-shadcn-ui` already uses as of July 2026) with Radix as an
alternative — pick the same one the rest of the project already uses, don't
mix.

---

## driver.js — Onboarding Tours and Feature Spotlights

**What it is:** a dependency-free, ~5kb vanilla JS library for step-by-step
product tours and element highlights — not React-specific, no built-in React
bindings.

**When:** a first-run experience needs to spotlight specific UI elements in
sequence (a numbered tour: "click here, then here"). Not for a persistent help
widget — that's a different problem.

**Install:**
```bash
npm install driver.js
```

**Recommended integration: wire it directly, skip community React wrapper
packages** (`driverjs-react`, `driver.jsx`). driver.js is already
dependency-free and its API is a handful of function calls — a wrapper adds a
second, less-mature dependency for a wrapper's worth of convenience:

```tsx
"use client";
import { useEffect } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

export function useOnboardingTour(shouldRun: boolean) {
  useEffect(() => {
    if (!shouldRun) return;
    const tour = driver({
      showProgress: true,
      steps: [
        { element: "#dashboard-nav", popover: { title: "Navigation", description: "Switch between views here." } },
        { element: "#create-button", popover: { title: "Create", description: "Start a new item here." } },
      ],
    });
    tour.drive();
  }, [shouldRun]);
}
```

**When to reach for something else instead:** driver.js runs independent of
React state — steps can't easily react to component lifecycle or conditional
rendering mid-tour. If the tour needs deep integration with React state
(steps that appear/disappear based on live app data), that's a real reason to
consider React Joyride instead — don't force driver.js past that point.

---

## Tailark — Marketing/Landing-Page Blocks

**What it is:** a shadcn/ui *registry* of marketing blocks (hero sections,
pricing tables, testimonials, CTAs, footers) — installed the same way as any
shadcn/ui component, not a separate library or component system.

**When:** a marketing/landing page needs a specific section built fast without
hand-composing it from primitives. This extends `ts-shadcn-ui`'s registry
mechanism — it is not an alternative to shadcn/ui.

**Setup — add the registry namespace to `components.json`:**
```json
{
  "registries": {
    "@tailark": "https://tailark.com/r/{name}"
  }
}
```

**Install a block:**
```bash
npx shadcn@latest add @tailark/hero-section-one
```

Browse the full catalog at tailark.com or via `registry.directory` before
picking a block name.

**Primitive-layer consistency check, same as assistant-ui above:** Tailark
ships both a Base UI base and a Radix base — its docs show a separate registry
URL per base (`/r/{name}` for Base UI, `/r/radix/{name}` for Radix). Match
whichever primitive layer the project's `ts-shadcn-ui` setup already uses.

---

## Common Anti-Patterns

- installing React Bits' full peer-dependency set (`motion`, `gsap`, `three`,
  `ogl`) up front instead of only what the specific component picked needs
- reaching for assistant-ui for a single "summarize this" button — that's a
  one-off API call, not a chat surface; assistant-ui earns its complexity once
  there's a real multi-turn thread
- pulling in a driver.js React wrapper package before confirming the plain
  `useEffect` + `driver()` call doesn't already cover it
- adding a Tailark block on the Radix registry path while the rest of the
  project already runs Base UI (or vice versa) — mismatched primitive layers
  between the app's own components and an imported block
- reaching for any of these four "because it looks nice" without a concrete
  need — see Recommendation First

---

## Related Skills

- `ts-shadcn-ui` — the core component system these four sit alongside, not
  instead of; Tailark and assistant-ui's CLI both key off its Base UI/Radix
  decision
- `ts-nextjs-app-router` — Client Component boundary matters for all four
  (assistant-ui's `Thread`, driver.js's tour hook, and most React Bits
  components need `"use client"`)
- `ts-expert` — routing and build order for the full skill set

---

## Output Style

When asked about one of these four libraries, respond in this order:
1. confirm the specific need is real (Recommendation First)
2. the install command for that one library only
3. peer dependencies, if any (React Bits only)
4. a minimal usage example
5. the one real caveat for that library (Commons Clause, no React state
   binding, primitive-layer mismatch) if applicable

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-22 | Initial release. Covers four libraries the user asked about by name: React Bits (animated components, shadcn-style copy-paste distribution, Commons Clause caveat), assistant-ui (AI chat primitives, Vercel AI SDK runtime, Base UI/Radix consistency with `ts-shadcn-ui`), driver.js (dependency-free tour library, recommends direct wiring over community React wrappers), and Tailark (shadcn registry of marketing blocks, same Base UI/Radix consistency note). Verified install commands, peer deps, and version/license details via WebSearch against each project's own docs/npm listing before writing. |
