---
name: ts-validation-schema
description: >
  Zod as the single runtime-validation backbone for the whole stack — schema-first
  types via `z.infer`, `.parse` vs `.safeParse`, and composing schemas with `.extend`/
  `.pick`/`.omit`/`.merge`. Covers the three places one schema should be reused instead
  of reinvented: forms (paired with React Hook Form), API request/response boundaries,
  and environment variable validation at startup. Foundational — skip it and the forms,
  API, and env-config skills each reinvent validation inconsistently.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Zod
    - schema validation
    - z.infer
    - safeParse
    - runtime validation
    - type inference
    - env validation
    - schema composition
    - form validation
    - API validation
    - z.object
    - discriminated union
---

## When to Use This Skill

Use when you need to:
- Define a data shape that needs both a compile-time type and a runtime check
- Validate a form submission, an API request body, or `process.env`
- Share one validation rule across client and server instead of duplicating it
- Explain why `.parse()` crashed a request handler, or why a TS type and actual
  runtime data have drifted apart

**Trigger keywords:** Zod, z.object, z.infer, safeParse, parse, schema validation,
runtime validation, .extend, .pick, .omit, .merge, discriminated union, env.ts,
process.env validation.

**Freshness rule:** Zod 4 changed error-shape APIs (`.flatten()`/`.format()` vs the
newer `z.treeifyError()`) from Zod 3 — check the installed major version before
assuming an error-handling shape.

---

## Recommendation First

**Zod, one schema per shape, `z.infer` for the type.** Never hand-write a TS
`interface` alongside a schema that validates the same data.

Why: a hand-written type and a hand-written runtime check are two sources of truth
that silently drift — the type says a field is required, a validator three files away
forgot to enforce it. Zod collapses both into one definition: the schema *is* the
runtime check, and `z.infer<typeof schema>` derives the compile-time type from it, so
they cannot disagree.

```ts
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  age: z.number().int().positive(),
});

type User = z.infer<typeof UserSchema>; // { id: string; email: string; age: number }
```

---

## `.parse` vs `.safeParse`

`.parse` throws a `ZodError` on failure — only use it where a throw is the correct
control flow (a startup script, a test, code already inside a try/catch you own).
`.safeParse` never throws; it returns a discriminated union you branch on. Default to
`.safeParse` anywhere user input or network data enters the system.

```ts
const result = UserSchema.safeParse(input);

if (!result.success) {
  // result.error is a ZodError — result.data does not exist on this branch
  console.error(result.error.flatten().fieldErrors);
  return { ok: false as const, errors: result.error.flatten().fieldErrors };
}

// result.data is fully typed as User here
return { ok: true as const, user: result.data };
```

`result.error.flatten()` gives `{ formErrors: string[]; fieldErrors: Record<string,
string[]> }` — the shape both a form's per-field error display and an API's JSON error
response want.

---

## Schema Composition — Share a Base, Don't Copy It

`.extend`, `.pick`, `.omit`, and `.merge` derive a new schema from an existing one so
two related shapes (create vs update, full vs partial) can't drift the way two
hand-copied `interface`s would.

```ts
const BaseUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  role: z.enum(["admin", "member"]),
});

// Create: server generates id, client never sends one
const CreateUserSchema = BaseUserSchema;
type CreateUserInput = z.infer<typeof CreateUserSchema>;

// Update: every field optional, id required to target the row
const UpdateUserSchema = BaseUserSchema.partial().extend({
  id: z.string().uuid(),
});
type UpdateUserInput = z.infer<typeof UpdateUserSchema>;

// Public read: strip fields that should never leave the server
const PublicUserSchema = BaseUserSchema.omit({ email: true }).extend({
  id: z.string().uuid(),
});
```

`.pick({ email: true })` keeps only the named keys; `.omit` drops them; `.merge`
combines two object schemas. Add a field to `BaseUserSchema` once and every derived
schema picks it up automatically — no separate edit per file.

---

## Env Var Validation — Fail at Boot, Not Mid-Request

Validate `process.env` once, at module load, so a missing `DATABASE_URL` crashes the
process on startup with a clear message — not a `Cannot read properties of undefined`
three files deep during a request.

```ts
// env.ts
import { z } from "zod";

const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  STRIPE_SECRET_KEY: z.string().startsWith("sk_"),
  PORT: z.coerce.number().int().default(3000),
});

const parsed = EnvSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment variables:", parsed.error.flatten().fieldErrors);
  throw new Error("Invalid environment variables — see above.");
}

export const env = parsed.data; // typed: { DATABASE_URL: string; NODE_ENV: ...; ... }
```

Import `env` everywhere instead of touching `process.env` directly:

```ts
import { env } from "./env";
const client = new PrismaClient({ datasourceUrl: env.DATABASE_URL });
```

`z.coerce.number()` converts the string every env var actually is into the number the
app wants — `process.env.PORT` is always `string | undefined`, never `number`.

---

## One Schema, Two Boundaries — Form and API Route

The actual point of this skill: define the shape once, import it on both sides. A
mismatch between what the client validates and what the server accepts is the whole
class of bug this prevents.

```ts
// schemas/create-post.ts — shared by client and server
import { z } from "zod";

export const CreatePostSchema = z.object({
  title: z.string().min(1, "Title is required").max(120),
  body: z.string().min(10, "Body must be at least 10 characters"),
});
export type CreatePostInput = z.infer<typeof CreatePostSchema>;
```

```tsx
// app/posts/new/post-form.tsx — client, paired with React Hook Form
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CreatePostSchema, type CreatePostInput } from "@/schemas/create-post";

export function PostForm() {
  const form = useForm<CreatePostInput>({ resolver: zodResolver(CreatePostSchema) });
  // form.formState.errors.title.message is populated straight from the schema
}
```

```ts
// app/api/posts/route.ts — server, same schema, no duplicated rules
import { CreatePostSchema } from "@/schemas/create-post";

export async function POST(req: Request) {
  const result = CreatePostSchema.safeParse(await req.json());
  if (!result.success) {
    return Response.json({ errors: result.error.flatten().fieldErrors }, { status: 400 });
  }
  const post = await db.post.create({ data: result.data });
  return Response.json(post, { status: 201 });
}
```

Client-side validation is a UX convenience (instant feedback, no round trip) — it is
never a security boundary. The API route validates independently with the same
schema because a request can bypass the form entirely (curl, another client, a bug).

---

## Common Anti-Patterns

- **Hand-writing a TS `interface` next to a schema for the same shape** instead of
  `z.infer`ing the type — the two are now two sources of truth that will eventually
  disagree; delete the `interface`, derive it.
- **Using `.parse()` in a request handler with no try/catch** — an invalid request
  body throws a `ZodError` that becomes an unhandled 500 instead of a clean 400. Use
  `.safeParse()` at every request boundary.
- **Validating the same shape with hand-rolled `if (!body.email) ...` checks in three
  different files** (a form, a route handler, a background job) — one schema import
  replaces all three and can't silently drift between them.
- **Trusting client-side Zod validation as the security boundary** — a form's
  `zodResolver` prevents a bad submit button click; it does nothing against a direct
  `fetch`/curl request. Re-validate on the server with the same schema.
- **Re-declaring `CreateUserSchema` and `UpdateUserSchema` from scratch** instead of
  deriving `UpdateUserSchema` from a shared base with `.partial().extend(...)` — every
  field added later needs the edit made in only one place.

---

## Related Skills

- `ts-forms` — React Hook Form + Zod resolver wiring, expanded past the minimal
  example here
- `ts-api-layer` — tRPC/route-handler request validation built on these schemas
- `ts-project-foundation` — the package layout a shared `schemas/` directory lives in
- `ts-nextjs-app-router` — Server Actions that parse `FormData` through a Zod schema
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
