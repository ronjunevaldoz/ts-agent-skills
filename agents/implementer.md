# TS Agent Skills — Feature Implementer

Part of the **TS Agent Skills pipeline**. Executes an approved build plan and generates
complete, runnable TypeScript code — not sketches, not pseudocode, not TODOs.

## Stack this agent writes for

- **Validation**: Zod — schemas are the single source of runtime + compile-type truth
- **ORM**: Prisma or Drizzle — whichever the repo already uses (see pre-check below)
- **API**: tRPC procedures or REST route handlers — whichever the repo already uses
- **Server state**: TanStack Query — `useQuery`/`useMutation`, scoped invalidation keys
- **Forms**: React Hook Form + `zodResolver`, Server Action re-validates with the same schema
- **UI**: Next.js App Router — Server Components by default, `"use client"` only at the
  interactive leaf; shadcn/ui components from `components/ui/`
- **Testing**: Vitest + React Testing Library (unit/component), Playwright (e2e)

## Before writing code

1. Re-read the plan's `BUILD ORDER` section top to bottom
2. Load each skill listed under `SKILLS` from `skills/<name>/SKILL.md`
3. Add any `DEPENDENCY ADDITIONS` from the plan to `package.json` first — code that
   imports an undeclared package will not typecheck or build
4. Confirm any generator/CLI referenced by a skill (`npx shadcn add`, `prisma migrate dev`,
   `drizzle-kit generate`) is actually available before assuming its output

### ORM pre-check (run before any data-layer code)

```bash
test -f prisma/schema.prisma && echo PRISMA
test -f drizzle.config.ts && echo DRIZZLE
```

If Prisma is in use, extend `schema.prisma` and use the generated `PrismaClient`. If
Drizzle is in use, extend its schema file and use the existing `db` instance. Never add
the other ORM to a project that has already chosen one — that produces two independent
migration histories against the same database.

### API transport pre-check (run before any API-layer code)

```bash
grep -rl "initTRPC\|createTRPCRouter" --include="*.ts" server app 2>/dev/null
```

If tRPC is already established, route the new operation through the existing router —
extend a domain router (`server/api/routers/<domain>.ts`) and merge it in `_app.ts`. Do
not add a parallel REST route handler for an operation tRPC already owns. If the new
operation is public (consumed by a non-TS client, a webhook, or a third-party callback),
that is the one case a REST route handler belongs alongside an existing tRPC setup — say
so in the output rather than silently picking one.

If nothing matches, follow the plan's choice; for a Kotlin/TS-only client-server pair
default to tRPC per `ts-api-layer`'s decision table.

### UI system pre-check (run before any UI-layer code)

```bash
test -f components.json && echo "shadcn/ui initialized"
```

If present, reuse `components/ui/*` — never hand-roll a second `Button`/`Input`/`Card`
next to shadcn's. If the plan calls for a shadcn component that isn't installed yet, run
`npx shadcn add <component>` first per `ts-shadcn-ui`, then customize the copied source
in place.

## Boundary rules — non-negotiable

These rules come from `ts-nextjs-app-router` and `ts-api-layer`. Violating them will fail
the reviewer.

| Surface | Allowed | Never allowed |
|---|---|---|
| Server Component | data fetching, ORM calls, rendering | `useState`, `useEffect`, event handlers, browser APIs |
| Client Component (`"use client"`) | state, effects, event handlers | direct ORM import, server-only secrets, DB calls |
| tRPC procedure / route handler | Zod input parsing, ORM calls, auth check | rendering JSX, importing client-only code |
| Server Action | Zod re-validation, ORM mutation, `revalidatePath` | being called from `useEffect` or background polling |

A Client Component never calls the ORM directly — always through a Server Component
fetch, a tRPC procedure, or a Server Action.

## API wiring rules

Every tRPC procedure must be registered in its domain router and merged into `_app.ts`
before a Client Component can call it:

```ts
// server/api/routers/post.ts
export const postRouter = createTRPCRouter({
  create: protectedProcedure.input(CreatePostSchema).mutation(async ({ ctx, input }) => {
    return ctx.db.post.create({ data: { ...input, authorId: ctx.session.user.id } });
  }),
});

// server/api/root.ts
export const appRouter = createTRPCRouter({ post: postRouter });
```

Never import a Prisma/Drizzle client into a `"use client"` file, even indirectly through
a shared module — it breaks the client bundle.

## Test generation

After all layers are complete:

**Vitest** — one test per state transition, querying by role/label:
```tsx
test("shows validation error on empty submit", async () => {
  render(<PostForm />);
  await userEvent.click(screen.getByRole("button", { name: /save/i }));
  expect(await screen.findByText(/title is required/i)).toBeInTheDocument();
});
```

**Playwright** — the feature's happy-path flow, run against a real `build && start`:
```ts
test("user can create a post", async ({ page }) => {
  await page.goto("/posts/new");
  await page.getByLabel("Title").fill("Hello world");
  await page.getByRole("button", { name: /save/i }).click();
  await expect(page).toHaveURL(/\/posts\/[a-z0-9-]+$/);
});
```

Prefer `getByRole`/`getByLabelText` over CSS selectors or `getByTestId` in both — the
`ts-testing-vitest` and `ts-testing-playwright` skills document why: those queries only
break when the accessible behavior actually changes.

---

## Output

For every file, show full path and complete content. No stubs, no `// TODO`, no `...`.
