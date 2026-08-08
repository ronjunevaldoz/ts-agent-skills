---
name: ts-testing-vitest
description: >
  Vitest + React Testing Library for unit and component tests — native ESM, no
  transform-config fighting, esbuild-fast, and Vite config reuse when the project
  already runs Vite. Covers component tests via `render`/`screen`/`userEvent`,
  mocking with `vi.fn()`/`vi.mock()`, and testing custom hooks with `renderHook`.
  Testing philosophy: assert what the user sees and does, never internal state.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Vitest
    - React Testing Library
    - unit test
    - component test
    - renderHook
    - userEvent
    - vi.mock
    - vi.fn
    - testing-library
    - jsdom
    - screen
    - mocking fetch
    - custom hook test
---

## When to Use This Skill

Use when you need to:
- Write a unit test for a function, module, or utility
- Write a component test that renders a React component and asserts on its output
- Test a custom hook in isolation
- Mock a module, a function, or a `fetch`/API call in a test
- Decide whether a test belongs here or in an e2e suite

**Trigger keywords:** Vitest, vi.fn, vi.mock, vi.spyOn, React Testing Library, RTL,
render, screen, getByRole, userEvent, renderHook, jsdom, happy-dom, test coverage,
component test, unit test.

**Freshness rule:** Vitest's browser-mode API and RTL's async utilities have shifted
across majors — recheck current docs before relying on a specific matcher or config
shape.

---

## Recommendation First

**Vitest over Jest**, React Testing Library on top, jsdom (or `happy-dom` for speed)
as the DOM environment.

Why:
- Native ESM — no `babel-jest`/`ts-jest` transform config to fight when the rest of
  the project is already ESM
- esbuild-based — a large suite runs in a fraction of Jest's time, and watch mode
  reruns only affected files
- If the project already has a `vite.config.ts`, Vitest reads the same aliases,
  plugins, and env handling — one config, not two

Don't reach for Jest on a new project. Only keep Jest on an existing codebase where
migrating hundreds of existing tests isn't worth the diff yet.

```ts
// vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
  },
});
```

```ts
// vitest.setup.ts
import "@testing-library/jest-dom/vitest";
```

---

## Testing Library Philosophy

Query the way a user finds things — role and accessible name first, text second.
Never reach into a component's internal state or call its instance methods directly;
if you can't get there through the rendered DOM, the test is coupled to
implementation, not behavior.

Query priority (RTL's own order, follow it): `getByRole` > `getByLabelText` >
`getByPlaceholderText` > `getByText` > `getByDisplayValue` > `getByTestId` (last
resort).

```tsx
// Counter.tsx
export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount((c) => c + 1)}>Increment</button>
    </div>
  );
}
```

```tsx
// Counter.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { Counter } from "./Counter";

describe("Counter", () => {
  it("increments the count when the button is clicked", async () => {
    const user = userEvent.setup();
    render(<Counter />);

    expect(screen.getByText("Count: 0")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /increment/i }));

    expect(screen.getByText("Count: 1")).toBeInTheDocument();
  });
});
```

`getByRole("button", { name: /increment/i })` fails if the button has no accessible
name — the test doubles as an accessibility check for free.

---

## Mocking — Functions, Modules, and Fetch

```ts
// vi.fn() — a bare mock function, assert on calls
import { vi, expect, it } from "vitest";

it("calls the callback with the new value", () => {
  const onChange = vi.fn();
  onChange("next");
  expect(onChange).toHaveBeenCalledWith("next");
  expect(onChange).toHaveBeenCalledTimes(1);
});
```

```ts
// vi.mock() — replace an entire module
// UserGreeting.tsx imports `getCurrentUser` from "./session"
import { vi, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserGreeting } from "./UserGreeting";
import { getCurrentUser } from "./session";

vi.mock("./session", () => ({
  getCurrentUser: vi.fn(),
}));

describe("UserGreeting", () => {
  it("greets the current user", () => {
    vi.mocked(getCurrentUser).mockReturnValue({ name: "Ada" });
    render(<UserGreeting />);
    expect(screen.getByText("Hello, Ada")).toBeInTheDocument();
  });
});
```

```ts
// Mocking a fetch call — stub global fetch per test
import { vi, describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { UserProfile } from "./UserProfile";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "1", name: "Ada Lovelace" }),
    }),
  );
});

it("renders the fetched user name", async () => {
  render(<UserProfile userId="1" />);
  expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith("/api/users/1");
});
```

`findByText` (async) waits for the state update after the fetch resolves —
`getByText` would fail because it doesn't wait.

---

## Testing a Custom Hook

```ts
// useCounter.ts
export function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  const increment = () => setCount((c) => c + 1);
  return { count, increment };
}
```

```ts
// useCounter.test.ts
import { renderHook, act } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useCounter } from "./useCounter";

describe("useCounter", () => {
  it("increments from the initial value", () => {
    const { result } = renderHook(() => useCounter(5));

    expect(result.current.count).toBe(5);

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(6);
  });
});
```

`act()` flushes the state update synchronously before the next assertion — omit it
and `result.current` reads the stale value.

---

## What NOT to Unit Test Here

Full user flows across multiple pages (login → navigate → checkout), real network
calls, real browser behavior (actual navigation, actual cookies) — that's
`ts-testing-playwright`'s job. A Vitest/RTL test renders **one component, one hook,
or one function in isolation**, with everything around it mocked or stubbed. If a
test needs a real running server or spans more than one route, it's an e2e test, not
a unit test.

---

## Common Anti-Patterns

- **Testing implementation details** — reaching into a component instance or internal
  state instead of asserting on rendered output. If refactoring the component's
  internals (same behavior, different state shape) breaks the test, the test was
  wrong, not the refactor.
- **`getByTestId` as the first choice** — skips the accessibility signal `getByRole`/
  `getByLabelText` give for free. Reach for `data-testid` only when no accessible
  query can find the element (e.g., a purely decorative wrapper).
- **Not awaiting `userEvent` calls** — every `userEvent` method (`.click()`,
  `.type()`, `.selectOptions()`) is async in modern versions. A missing `await`
  causes the assertion to run before the interaction's effects land, producing a
  flaky test that fails only sometimes.
- **Snapshot-testing everything** — a full-component snapshot breaks on any markup
  change, trivial or not, and reviewers stop reading the diff. Snapshot small, stable
  output; assert explicit expectations everywhere else.
- **Mocking what you're supposed to be testing** — mocking the component under test's
  own child logic away entirely can leave a test that passes even when the real
  integration is broken. Mock the boundary (network, module dependency), not the
  subject.

---

## Related Skills

- `ts-testing-playwright` — the e2e counterpart: real browser, real navigation, full
  user flows across pages. Use it instead of Vitest/RTL for anything spanning more
  than one component in isolation.
- `ts-expert` — routing and build order for the full skill set
- `ts-project-foundation` — monorepo layout Vitest config lives inside
- `ts-nextjs-app-router` — Server Components can't be unit-rendered the same way;
  test the Client Component leaves and extract server logic into testable functions
- `ts-forms` — React Hook Form + Zod validation, a common component-test target
- `ts-ci-github-actions` — wiring `vitest run` into the CI gate

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
