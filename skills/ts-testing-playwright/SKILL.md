---
name: ts-testing-playwright
description: >
  Playwright end-to-end testing — real browser, real navigation, a full user flow
  across multiple pages instead of one component in isolation. Covers locator
  best practices, the storageState auth fixture for reusing a logged-in session
  across tests, CI wiring against a production build, and toHaveScreenshot as a
  lightweight visual regression check. The e2e counterpart to ts-testing-vitest's
  unit/component layer, not a replacement for it.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Playwright
    - e2e test
    - end-to-end testing
    - getByRole
    - storageState
    - toHaveScreenshot
    - browser automation
    - CI e2e
    - visual regression
    - locator
    - auth fixture
    - playwright install
    - page object
    - production build testing
---

## When to Use This Skill

Use when you need to:
- Test a full user flow across multiple pages — sign-up → onboarding → dashboard
- Verify something only a real browser can catch: navigation, redirects, cookies,
  a form submit that hits a real backend
- Set up auth once and reuse it across a whole test suite instead of logging in
  in every test
- Wire e2e tests into CI against a real built app, not the dev server
- Catch an unintended visual change with a screenshot diff, without adopting a
  dedicated visual-testing tool

**Trigger keywords:** Playwright, e2e test, end-to-end test, page.goto, getByRole,
getByLabel, storageState, toHaveScreenshot, browser automation, playwright install,
playwright.config, test fixture, visual regression.

**Freshness rule:** Playwright ships frequently and browser binaries drift with it —
recheck `npx playwright --version` and the current docs before pinning a version in CI.

---

## Recommendation First

**Playwright for e2e, not for anything a component test already covers.** If the
question is "does this one component render the right thing given these props,"
that's `ts-testing-vitest` (Vitest + React Testing Library) — fast, no browser, no
network. If the question is "can a real user actually sign up, get redirected, and
see their dashboard," that's Playwright — a real Chromium/Firefox/WebKit instance,
real navigation, real cookies.

Don't reach for e2e to test something a unit test already proves. A slow e2e suite
that re-verifies form-validation logic component tests already cover just makes CI
slower without adding confidence. Reserve Playwright for the seams between pages and
systems that a component test physically cannot see.

---

## A Full User Flow Test

```ts
// e2e/onboarding.spec.ts
import { test, expect } from "@playwright/test";

test("sign up and land on the dashboard", async ({ page }) => {
  await page.goto("/sign-up");

  await page.getByLabel("Email").fill("new-user@example.com");
  await page.getByLabel("Password").fill("correct-horse-battery-staple");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page).toHaveURL("/onboarding");
  await page.getByRole("button", { name: "Get started" }).click();

  await page.getByLabel("Team name").fill("Acme Inc");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL("/dashboard");
  await expect(page.getByRole("heading", { name: "Welcome, Acme Inc" })).toBeVisible();
});
```

`expect(page).toHaveURL(...)` and `toBeVisible()` auto-wait and auto-retry — no
manual polling needed. This one test crosses three routes and a real form submit;
that's the shape only an e2e test can verify.

---

## Locators: Accessibility-First, Not CSS

Same philosophy as React Testing Library — query by what a user or screen reader
sees, not by implementation details:

```ts
// ✓ Resilient to styling and markup changes
await page.getByRole("button", { name: "Submit" }).click();
await page.getByLabel("Email").fill("user@example.com");
await page.getByText("Order confirmed").waitFor();

// ❌ Breaks the moment a class name or DOM nesting changes
await page.locator(".btn.btn-primary.submit-btn").click();
await page.locator("div > form > div:nth-child(2) > input").fill("user@example.com");
```

`getByRole`/`getByLabel`/`getByText` describe *what the element is*, so a CSS
refactor or a design-system swap doesn't break the test. Fall back to `data-testid`
only for an element with no accessible role or text (a decorative drag handle, a
canvas).

---

## Auth Fixture: Log In Once, Reuse the Session

Logging in inside every test multiplies suite runtime by the number of tests. Log in
once in a setup project, save the browser's `storageState`, and every real test
starts already authenticated.

```ts
// e2e/auth.setup.ts
import { test as setup, expect } from "@playwright/test";

const authFile = "playwright/.auth/user.json";

setup("authenticate", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("test-user@example.com");
  await page.getByLabel("Password").fill(process.env.E2E_TEST_PASSWORD!);
  await page.getByRole("button", { name: "Log in" }).click();
  await expect(page).toHaveURL("/dashboard");

  await page.context().storageState({ path: authFile });
});
```

```ts
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  webServer: {
    command: "pnpm build && pnpm start",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], storageState: "playwright/.auth/user.json" },
      dependencies: ["setup"],
    },
  ],
});
```

Every test in the `chromium` project now starts as a logged-in user — no per-test
login flow. A test that specifically needs to be logged *out* just overrides
`storageState: undefined` for that one test.

---

## CI Wiring: Against a Production Build

```yaml
# .github/workflows/e2e.yml
name: e2e
on: [pull_request]
jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: pnpm }
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps
      - run: pnpm exec playwright test
        env:
          E2E_TEST_PASSWORD: ${{ secrets.E2E_TEST_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

`playwright install --with-deps` installs both the browser binaries and the OS-level
libraries Chromium/WebKit need on a bare CI runner — skip `--with-deps` locally where
those libraries already exist, but CI needs it every time. The `webServer` block in
`playwright.config.ts` (above) runs `pnpm build && pnpm start`, not `pnpm dev` — see
Anti-Patterns for why that distinction matters.

---

## Visual Regression: `toHaveScreenshot()`

Playwright ships a built-in screenshot-diff assertion — reach for it before adding a
dedicated visual-testing tool like Chromatic; it needs zero new infrastructure and
covers "did this page's layout silently break" for most projects.

```ts
test("dashboard visual snapshot", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveScreenshot("dashboard.png", { maxDiffPixelRatio: 0.02 });
});
```

First run generates the baseline (`--update-snapshots`); every run after diffs
against it and fails on a pixel mismatch past the threshold. Baselines are
platform-specific (font rendering differs by OS) — generate and commit them from the
same OS the CI runner uses, or run the whole suite inside a container. Reach for
Chromatic/Percy instead once the team needs cross-browser diffing, PR-level visual
review UI, or baseline approval workflows this built-in check doesn't have.

---

## Common Anti-Patterns

- **CSS selectors instead of role/label locators** — `.locator(".btn-primary")`
  breaks on any class rename or CSS framework swap; `getByRole("button", { name })`
  only breaks if the button's accessible name actually changes.
- **`page.waitForTimeout(2000)` instead of an auto-waiting assertion** — a fixed
  sleep is either too slow (wastes CI time on every run) or too fast (flakes under
  load). `expect(locator).toBeVisible()` / `toHaveURL()` retry until the condition is
  true or a real timeout is hit — use those instead.
- **Running e2e in CI against the dev server** — `next dev`/`vite dev` skip
  production optimizations (bundling, minification, some SSR behavior) and can hide
  a bug that only exists in the built output. Wire `webServer.command` to a real
  `build && start`, as shown above.
- **Re-testing component-level logic in Playwright** — form-field validation
  messages, button disabled states, and other single-component behavior belong in
  `ts-testing-vitest`; duplicating that coverage in a browser just makes the e2e
  suite slower for no extra confidence.
- **Skipping `--with-deps` in CI** — works locally where the OS libraries are
  already present, then fails in a fresh CI container with missing shared-library
  errors that look nothing like a Playwright problem.

---

## Related Skills

- `ts-testing-vitest` — the unit/component test layer for one component in
  isolation; use it for anything Playwright would be overkill for
- `ts-ci-github-actions` — the CI workflow file this suite's job slots into
- `ts-expert` — routing and build order for the full skill set
- `ts-nextjs-app-router` — the app whose routes and Server Actions these flows
  exercise end-to-end

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
