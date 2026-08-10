---
name: ts-api-layer
description: >
  The client/server contract shape decision for a TypeScript app — tRPC vs REST
  route handlers (Next.js `app/api/*/route.ts` or a separate Nest.js/Express
  backend). tRPC gives end-to-end type safety with zero codegen when client and
  server are both TypeScript in the same monorepo; REST is required the moment a
  non-TS client, a public API, or a versioned/OpenAPI contract enters the picture.
  Covers procedure design, Zod input validation, and the error-handling shape for
  both.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - tRPC
    - REST
    - route handlers
    - API layer
    - type-safe API
    - procedures
    - OpenAPI
    - Zod validation
    - TRPCError
    - Next.js API routes
    - query
    - mutation
    - public API
    - API versioning
---

## When to Use This Skill

Use when you need to:
- Decide whether a new endpoint should be a tRPC procedure or a REST route handler
- Design a tRPC router with input validation and typed errors
- Write a Next.js route handler with proper status codes
- Explain why a mobile team or third-party integrator can't consume a tRPC API

**Trigger keywords:** tRPC, REST API, route handler, `app/api`, procedure, query,
mutation, OpenAPI, public API, API contract, TRPCError, Zod input validation,
API versioning, third-party integration.

**Freshness rule:** tRPC's router/procedure API has changed across major versions
(v10 → v11) — recheck the installed `@trpc/server` version's docs before writing
router code.

---

## Recommendation First

| Scenario | Choice |
|---|---|
| TS client + TS server, same monorepo, no external consumers | **tRPC** |
| Mobile app, third-party integrator, or any non-TS client | **REST route handlers** |
| Need a stable, versioned contract independent of the TS client's release cycle | **REST route handlers** |
| Need auto-generated OpenAPI/Swagger docs for external consumers | **REST route handlers** |
| Webhook receiver (Stripe, GitHub, etc.) | **REST route handlers** — the caller dictates the contract, not you |
| Internal admin dashboard calling its own Next.js backend | **tRPC** |

Why tRPC wins inside the boundary: the router's input/output types flow straight
into the client via TypeScript inference — no `.d.ts` generation step, no OpenAPI
spec to keep in sync, no hand-written client SDK. A renamed field breaks the build
at the call site instead of at runtime in production.

Why that same property disqualifies tRPC outside the boundary: type inference only
works because the client imports the server's `AppRouter` type. A mobile app in
Swift/Kotlin, or a third party hitting your API from Python, has no TypeScript
compiler to infer against — they need an HTTP contract with a spec, not a type.

A project can run both: tRPC for the app's own frontend, REST for anything public
(webhooks, a versioned `/api/v1/*` surface, mobile). Don't force one pattern where
the other fits better.

---

## tRPC — Router, Procedure, Client Call

```ts
// server/trpc.ts
import { initTRPC } from "@trpc/server";

const t = initTRPC.create();
export const router = t.router;
export const publicProcedure = t.procedure;
```

```ts
// server/routers/post.ts
import { z } from "zod";
import { router, publicProcedure } from "../trpc";
import { db } from "../db";

export const postRouter = router({
  byId: publicProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const post = await db.post.findUnique({ where: { id: input.id } });
      if (!post) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Post not found" });
      }
      return post;
    }),

  create: publicProcedure
    .input(z.object({ title: z.string().min(1), body: z.string().min(1) }))
    .mutation(async ({ input }) => {
      return db.post.create({ data: input });
    }),
});
```

```ts
// server/routers/_app.ts
import { router } from "../trpc";
import { postRouter } from "./post";

export const appRouter = router({ post: postRouter });
export type AppRouter = typeof appRouter; // this type, not codegen, is the contract
```

Client side — `useQuery`/`useMutation` come straight from the router's inferred
types, no separate client SDK:

```tsx
"use client";
import { trpc } from "@/lib/trpc-client";

function PostView({ id }: { id: string }) {
  const { data: post, isLoading } = trpc.post.byId.useQuery({ id });
  const createPost = trpc.post.create.useMutation({
    onSuccess: () => utils.post.byId.invalidate(),
  });

  if (isLoading) return <Skeleton />;
  return <h1>{post?.title}</h1>; // post is typed as Post | undefined, inferred
}
```

The input schema on `byId` is the only validation code written — no separate
request DTO, no manual `if (!id) throw`.

---

## REST — Route Handler with Zod and Status Codes

```ts
// app/api/posts/[id]/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "@/server/db";

const ParamsSchema = z.object({ id: z.string().uuid() });

export async function GET(
  _req: NextRequest,
  { params }: { params: { id: string } },
) {
  const parsed = ParamsSchema.safeParse(params);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid id" }, { status: 400 });
  }

  const post = await db.post.findUnique({ where: { id: parsed.data.id } });
  if (!post) {
    return NextResponse.json({ error: "Post not found" }, { status: 404 });
  }

  return NextResponse.json(post, { status: 200 });
}
```

```ts
// app/api/posts/route.ts
const CreatePostSchema = z.object({
  title: z.string().min(1),
  body: z.string().min(1),
});

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = CreatePostSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Validation failed", issues: parsed.error.flatten() },
      { status: 422 },
    );
  }

  const post = await db.post.create({ data: parsed.data });
  return NextResponse.json(post, { status: 201 });
}
```

Every route handler validates its own input — nothing upstream guarantees a
request body matches the shape the client's form sent. See `ts-validation-schema`
for the Zod schema patterns reused across both layers.

---

## Error Handling Shape

**tRPC** — typed errors via `TRPCError`, one of a fixed code enum
(`BAD_REQUEST`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`,
`INTERNAL_SERVER_ERROR`, etc.). The client's `error.data?.code` is typed, so a
UI can branch on it without string-matching a message:

```ts
throw new TRPCError({ code: "FORBIDDEN", message: "Not your post" });
```

```tsx
const { error } = trpc.post.byId.useQuery({ id });
if (error?.data?.code === "NOT_FOUND") return <NotFoundPage />;
```

**REST** — HTTP status code is the contract, not a custom code field buried in
the body:
- `400` — malformed request (bad params, unparseable JSON)
- `401` — no/invalid auth
- `403` — authenticated but not allowed
- `404` — resource doesn't exist
- `409` — conflict (duplicate create, stale update)
- `422` — well-formed but fails validation (Zod `safeParse` failure)
- `500` — unhandled server error, never leak the raw error message to the client

A REST client checks `res.status`, not a parsed body field, to decide how to
react — keep the body's `error` field for human-readable detail only.

---

## Common Anti-Patterns

- **Building a public API in tRPC.** A mobile app or third-party integrator has
  no TS compiler to infer `AppRouter` against — they need REST + OpenAPI, not a
  "just call the tRPC endpoint with curl" workaround that leaks tRPC's batching/
  envelope format as an undocumented wire protocol.
- **Skipping input validation on a REST route handler** because "the frontend
  already validates it." A route handler is a public HTTP endpoint the moment it
  exists — anyone can `curl` it with any body. Validate server-side regardless of
  what the client does.
- **N+1 queries inside a tRPC procedure.** Because a procedure looks like a
  plain async function, it's easy to loop a `db.query` call per item instead of
  batching. The type safety at the boundary doesn't protect against a slow
  resolver — profile procedures the same way you'd profile any DB-calling code.
- **Returning `200` with an `{ error: ... }` body on a REST handler.** Breaks
  every HTTP client's default error handling (`fetch` won't throw, `axios`
  won't reject) — use the actual status code.
- **One tRPC router file with every procedure in it.** Split by domain
  (`post.ts`, `user.ts`, `comment.ts`) and merge in `_app.ts`, same reasoning as
  not dumping every REST route in one file.

---

## Related Skills

- `ts-validation-schema` — the Zod schemas reused as both tRPC procedure inputs
  and REST route handler validation
- `ts-data-fetching` — TanStack Query patterns underneath tRPC's `useQuery`/
  `useMutation`, and plain `fetch` for REST
- `ts-orm-database` — Prisma/Drizzle calls made from inside procedures and route
  handlers
- `ts-auth` — session/token checks shared by tRPC middleware and REST route
  handlers
- `ts-resilience` — retry, timeout, circuit breaker, and idempotency keys for calls
  made through this layer
- `ts-nextjs-app-router` — route handlers live at `app/api/*/route.ts` inside
  this routing structure
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
