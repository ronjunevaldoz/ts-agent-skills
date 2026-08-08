---
name: ts-state-management
description: >
  Client-side React state management compared head-to-head — Redux Toolkit vs
  Zustand vs React Context, with a real decision tree instead of a single pick.
  Covers when each genuinely fits, migration cost between them, and testing
  implications. Also draws the line every team blurs: fetched API data is
  server state and belongs in TanStack Query (`ts-data-fetching`), not in any
  of these three.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Redux
    - Redux Toolkit
    - Zustand
    - React Context
    - useContext
    - useReducer
    - client state
    - server state
    - state management
    - TanStack Query
    - prop drilling
    - createSlice
    - Redux DevTools
    - global store
    - selector
---

## When to Use This Skill

Use when you need to:
- Choose between Redux Toolkit, Zustand, and React Context for a piece of state
- Decide whether state belongs in a client store at all, or in TanStack Query instead
- Migrate state from one of these three to another as requirements grow
- Explain why a component re-renders too often when it consumes Context

**Trigger keywords:** Redux, Redux Toolkit, RTK, createSlice, Zustand, React Context,
useContext, useReducer, global state, client state, prop drilling, state management,
Redux DevTools, store, provider.

**Freshness rule:** Redux Toolkit's recommended patterns (RTK Query, `createSlice`
defaults) and Zustand's API have both shifted across major versions — recheck each
library's own docs before starting a new store.

---

## Recommendation First

There is no single winner here — unlike most picks in this skill set, this is a real,
contested decision. Pick based on the decision tree below, not on habit.

| State kind | Best fit | Why |
|---|---|---|
| Data fetched from an API (users, posts, prices) | **TanStack Query** (`ts-data-fetching`), not any of these three | It's a cache with a server source of truth, not client state — see below |
| Read by many components, changes rarely (theme, current user, locale) | **React Context** | No extra dependency; infrequent updates mean the re-render cost of Context is a non-issue |
| Client-only UI state (modal open, filter panel, wizard step, sidebar collapsed) | **Zustand** | Minimal boilerplate, no `<Provider>` wrapper, selector-based reads avoid unnecessary re-renders |
| Complex app-wide state needing middleware (logging, persistence, undo/redo) or a large team wanting enforced patterns | **Redux Toolkit** | Middleware ecosystem, Redux DevTools time-travel, `createSlice` conventions keep a big team consistent |
| Frequently-updating state (form field on every keystroke, mouse position) read by only a few components | **Local `useState`, not any global store** | Hoist only as far as the state is actually shared — see `ts-project-foundation`'s sibling skill on hoisting for the KMP analog of this rule |

The decision tree, in order:

```
Is this data that was fetched from a server/API?
├── YES → TanStack Query (ts-data-fetching). Stop — it is not client state.
└── NO
    ├── Does it change rarely and get read broadly (theme, auth user, locale)?
    │   └── YES → React Context (+ useReducer if the value has multiple fields)
    ├── Is it client-only UI state, no middleware/time-travel need?
    │   └── YES → Zustand
    ├── Does it need middleware (persist, logging, undo/redo) or DevTools
    │   time-travel, or does a large team need enforced action/reducer conventions?
    │   └── YES → Redux Toolkit
    └── Is it local to one component or a couple of siblings?
        └── YES → useState / useReducer, hoisted only as far as needed — no store at all
```

---

## React Context + `useReducer` — Rarely-Changing, Broadly-Read State

```tsx
// theme-context.tsx
import { createContext, useContext, useReducer, type ReactNode } from "react";

type Theme = "light" | "dark";
type Action = { type: "TOGGLE" } | { type: "SET"; theme: Theme };

function themeReducer(state: Theme, action: Action): Theme {
  switch (action.type) {
    case "TOGGLE":
      return state === "light" ? "dark" : "light";
    case "SET":
      return action.theme;
  }
}

const ThemeContext = createContext<Theme | null>(null);
const ThemeDispatchContext = createContext<React.Dispatch<Action> | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, dispatch] = useReducer(themeReducer, "light");
  return (
    <ThemeContext.Provider value={theme}>
      <ThemeDispatchContext.Provider value={dispatch}>
        {children}
      </ThemeDispatchContext.Provider>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const theme = useContext(ThemeContext);
  if (theme === null) throw new Error("useTheme must be used within ThemeProvider");
  return theme;
}

export function useThemeDispatch() {
  const dispatch = useContext(ThemeDispatchContext);
  if (dispatch === null) throw new Error("useThemeDispatch must be used within ThemeProvider");
  return dispatch;
}
```

Splitting state and dispatch into two Contexts (as above) means a component that only
dispatches doesn't re-render when the theme value changes. Do this from the start for
any Context holding more than a trivial value — see the anti-pattern section for what
happens when you don't.

---

## Zustand — Client-Only UI State, No Provider

```ts
// use-wizard-store.ts
import { create } from "zustand";

type WizardState = {
  step: number;
  formData: Record<string, unknown>;
  next: () => void;
  back: () => void;
  setField: (key: string, value: unknown) => void;
  reset: () => void;
};

export const useWizardStore = create<WizardState>((set) => ({
  step: 0,
  formData: {},
  next: () => set((s) => ({ step: s.step + 1 })),
  back: () => set((s) => ({ step: Math.max(0, s.step - 1) })),
  setField: (key, value) =>
    set((s) => ({ formData: { ...s.formData, [key]: value } })),
  reset: () => set({ step: 0, formData: {} }),
}));
```

```tsx
// Selector — component only re-renders when `step` changes, not on every formData edit
function WizardProgress() {
  const step = useWizardStore((s) => s.step);
  return <span>Step {step + 1} of 4</span>;
}

// No <Provider> needed anywhere in the tree — the store is a module-level singleton
function WizardNav() {
  const { next, back } = useWizardStore((s) => ({ next: s.next, back: s.back }));
  return (
    <div>
      <button onClick={back}>Back</button>
      <button onClick={next}>Next</button>
    </div>
  );
}
```

The selector (`useWizardStore((s) => s.step)`) is what Context can't do cheaply —
Zustand only re-renders a component when the *selected slice* changes, not on every
store update.

---

## Redux Toolkit — App-Wide State With Middleware

```ts
// cart-slice.ts
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

type CartItem = { productId: string; quantity: number };
type CartState = { items: CartItem[] };

const initialState: CartState = { items: [] };

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    addItem: (state, action: PayloadAction<CartItem>) => {
      const existing = state.items.find((i) => i.productId === action.payload.productId);
      if (existing) existing.quantity += action.payload.quantity;
      else state.items.push(action.payload); // Immer under the hood — this "mutation" is safe
    },
    removeItem: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((i) => i.productId !== action.payload);
    },
  },
});

export const { addItem, removeItem } = cartSlice.actions;
export default cartSlice.reducer;
```

```ts
// store.ts
import { configureStore } from "@reduxjs/toolkit";
import cartReducer from "./cart-slice";

export const store = configureStore({
  reducer: { cart: cartReducer },
  // middleware, persistence, logging plug in here — this is the point of RTK
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

```tsx
// Typed hooks, not the raw useSelector/useDispatch — avoids repeating <RootState> everywhere
import { useDispatch, useSelector, type TypedUseSelectorHook } from "react-redux";
import type { RootState, AppDispatch } from "./store";

export const useAppDispatch: () => AppDispatch = useDispatch;
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

`createSlice` mutates state directly inside reducers because Immer wraps it — this is
not a Redux Toolkit-specific shortcut you should worry about, it produces a real
immutable update under the hood. Reach for Redux Toolkit only when you actually need
the middleware chain or DevTools time-travel — otherwise it's more ceremony than
Zustand for the same result.

---

## Migration Cost Between Them

| From → To | Cost | Notes |
|---|---|---|
| Context → Zustand | Low | Both are "just read a value" at the call site; swap `useContext` for a Zustand selector hook, drop the `<Provider>` |
| Zustand → Redux Toolkit | Medium | Actions/reducers need to be split into a slice; async logic (`set` inside an async function) becomes a thunk or RTK Query endpoint |
| Redux Toolkit → Zustand | Medium | Simpler in practice — collapse slice + actions + selectors into one `create()` call; lose middleware/DevTools unless Zustand's own devtools middleware is added |
| Context → Redux Toolkit | Medium-High | Usually done because Context started needing what only RTK provides (middleware, DevTools) — the reducer logic mostly transfers, the Provider wiring doesn't |

Migrating **out of** frequently-updating Context and into Zustand is the most common
real-world migration: a team starts with Context for "just one piece of shared state,"
it grows, re-renders become visible, and Zustand's selectors fix it without a full
Redux rewrite.

---

## Testing Implications

- **Zustand** — a store is a plain object with functions; call `useWizardStore.getState().next()` directly in a test, or reset with `useWizardStore.setState(initialState, true)` between tests. No provider needed in test setup.
- **Redux Toolkit** — test reducers as pure functions (`cartSlice.reducer(state, addItem(...))`) without rendering anything; for component tests, wrap in a real `<Provider store={testStore}>` with a fresh `configureStore()` per test so state doesn't leak between tests.
- **Context** — component tests must wrap in the real `<ThemeProvider>` (or a test-only provider with fixed values); a component using `useContext` without its provider throws in tests the same way it does in production, which is a feature — it catches a missing provider early.

See `ts-testing-vitest` for the harness these patterns run under.

---

## The Server-State Trap

This is the most important thing this skill teaches: **data fetched from an API is
not client state**, and putting it in Redux, Zustand, or Context is the single most
common state-management mistake in React apps.

Server state is different in kind from client UI state:
- It's owned by a source of truth you don't control (the server) — your copy is a cache, not the truth
- It goes stale — someone else can change it
- Fetching it is async and can fail, retry, or race
- Multiple components may want the same data without knowing about each other

Redux/Zustand/Context have no opinion about any of that. Putting fetched data in one
of them means hand-building: loading/error state per request, cache invalidation,
refetch-on-window-focus, deduplication of simultaneous requests, and stale-data
handling — all of which TanStack Query (`ts-data-fetching`) already does correctly.

```ts
// ❌ Wrong — API data in a Zustand store, hand-rolled loading/error/cache
const useUserStore = create<{
  user: User | null;
  loading: boolean;
  error: string | null;
  fetchUser: (id: string) => Promise<void>;
}>((set) => ({
  user: null,
  loading: false,
  error: null,
  fetchUser: async (id) => {
    set({ loading: true, error: null });
    try {
      const user = await fetch(`/api/users/${id}`).then((r) => r.json());
      set({ user, loading: false });
    } catch (e) {
      set({ error: String(e), loading: false });
    }
  },
}));

// ✓ Correct — TanStack Query owns the fetch, cache, loading, error, and staleness
function useUser(id: string) {
  return useQuery({ queryKey: ["user", id], queryFn: () => fetchUser(id) });
}
```

The rule of thumb: if the state's source of truth lives on a server, it's TanStack
Query's job. If the state is invented by the UI itself and has no server copy (is this
modal open, which wizard step, which filter is checked), it's Zustand/Redux/Context's
job.

---

## Common Anti-Patterns

- **Fetched API data in a global store** — see above. Storing `users`, `products`, or
  any server-owned collection in Redux/Zustand/Context instead of TanStack Query means
  hand-rolling cache invalidation you'll get wrong.
- **One giant global store for everything** — a single Zustand store or Redux root
  reducer holding cart state, UI state, and feature flags together means an unrelated
  change forces every consumer to re-check. Split stores/slices by concern, the same
  way `ts-project-foundation` splits packages by what changes together.
- **A single Context value object causing every consumer to re-render** — `<AppContext
  value={{ user, theme, cart, notifications }}>` means any one field changing
  re-renders every component reading *any* field, because the whole object is one
  Context value. Split into separate Contexts per concern (`UserContext`,
  `ThemeContext`), or move the frequently-changing piece to Zustand instead.
- **Reaching for Redux Toolkit by default** — bringing in the middleware/DevTools/slice
  machinery for what's actually a couple of UI booleans is unrequested weight; start
  with Zustand or Context and upgrade only when a real middleware need shows up.
- **Prop drilling instead of Context, for state that's genuinely broad and rarely
  changes** — threading `theme` through six layers of components that don't use it
  themselves is the exact case Context exists for; don't avoid it out of habit once
  the drilling is 3+ levels deep and the value changes rarely.

---

## Related Skills

- `ts-data-fetching` — TanStack Query, the correct home for server state; read this
  first if you're unsure whether something belongs here at all
- `ts-project-foundation` — package/module boundaries this store logic lives inside
- `ts-forms` — form state usually stays local (React Hook Form) rather than in any of
  these three, even when the form is complex
- `ts-testing-vitest` — the test harness for store/reducer/Context tests above
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
