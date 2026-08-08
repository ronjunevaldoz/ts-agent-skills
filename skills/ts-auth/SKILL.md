---
name: ts-auth
description: >
  Auth.js (formerly NextAuth) vs Clerk vs Lucia decision for a Next.js/TypeScript
  app, plus the session-vs-JWT tradeoff and real route-protection code. Getting
  this wrong means either shipping a managed auth bill you didn't need, or
  hand-rolling session logic a maintained library already solved. Covers
  middleware, Server Component, and Server Action/API route protection.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Auth.js
    - NextAuth
    - Clerk
    - Lucia
    - session
    - JWT
    - OAuth
    - middleware auth
    - protected route
    - Server Action auth
    - httpOnly cookie
    - password hashing
    - session revocation
---

## When to Use This Skill

Use when you need to:
- Pick an auth library/service for a new Next.js app
- Protect a route, Server Component, Server Action, or API route
- Decide between a JWT session and a database-backed session
- Explain why a logged-out user can still hit a Server Action

**Trigger keywords:** Auth.js, NextAuth, Clerk, Lucia, sign in, sign out, OAuth
provider, session cookie, JWT, middleware auth, protected route, auth.ts,
getServerSession, currentUser, withAuth, password hashing.

**Freshness rule:** all three libraries change fast — Auth.js v5's API differs
from v4, Clerk ships new SDK helpers regularly, and Lucia deprecated its own
core package in favor of documented patterns. Recheck each project's current
docs before wiring auth; do not assume an API shape from training data.

---

## Recommendation First

| Situation | Pick |
|---|---|
| Side project, fast MVP, want it done today | **Clerk** |
| Cost-sensitive, or need full control over OAuth providers/session storage | **Auth.js** |
| Need full manual control over session/auth logic, Auth.js/Clerk's opinions don't fit | **Lucia** |

**Auth.js** (formerly NextAuth) — free, self-hosted, huge built-in OAuth provider
ecosystem (Google, GitHub, dozens more with a few lines of config). You own the
session storage (DB adapter or JWT). More setup work than Clerk, but no per-user
billing and no vendor lock-in on the auth flow itself.

**Clerk** — managed/hosted, fastest to ship. Prebuilt UI components (`<SignIn />`,
`<UserButton />`) mean no auth screens to build. Has a real cost at scale (per
monthly-active-user pricing) and less control over the auth flow — you're inside
Clerk's session model and redirect conventions.

**Lucia** — not a framework, a lightweight auth *library*: you write the sign-in
route, the session table, the cookie handling yourself, using Lucia's helpers for
the parts that are easy to get wrong (session token generation/validation). Full
manual control, smallest footprint, most implementation work. Reach for it when
Auth.js's adapter model or Clerk's hosted UI don't fit the product (e.g. a custom
multi-tenant session shape).

Don't default to Clerk for a cost-sensitive project that will scale past a few
thousand users — the per-MAU bill adds up. Don't default to Lucia for an MVP —
you're rebuilding session/cookie plumbing a maintained library already ships.

---

## Middleware — Route Protection at the Edge

Runs before the page renders; cheapest place to redirect an unauthenticated user.

```ts
// middleware.ts (Auth.js v5)
export { auth as middleware } from "@/auth";

export const config = {
  matcher: ["/dashboard/:path*", "/settings/:path*"],
};
```

```ts
// auth.ts — Auth.js v5 config with a callback that gates matched routes
import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [GitHub],
  callbacks: {
    authorized({ auth, request }) {
      const isLoggedIn = !!auth?.user;
      const isProtected = request.nextUrl.pathname.startsWith("/dashboard");
      if (isProtected && !isLoggedIn) return false; // redirects to sign-in
      return true;
    },
  },
});
```

Clerk's equivalent — `clerkMiddleware` with an explicit route matcher, since Clerk
protects nothing by default:

```ts
// middleware.ts (Clerk)
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isProtectedRoute = createRouteMatcher(["/dashboard(.*)", "/settings(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) await auth.protect();
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
```

Middleware alone is not enough — see the anti-pattern below on checking auth only
at the edge/UI and not in the mutation itself.

---

## Server Component Session Check

```tsx
// app/dashboard/page.tsx
import { redirect } from "next/navigation";
import { auth } from "@/auth"; // Auth.js v5

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) redirect("/sign-in");

  return <div>Welcome, {session.user.name}</div>;
}
```

Clerk equivalent:

```tsx
import { redirect } from "next/navigation";
import { currentUser } from "@clerk/nextjs/server";

export default async function DashboardPage() {
  const user = await currentUser();
  if (!user) redirect("/sign-in");

  return <div>Welcome, {user.firstName}</div>;
}
```

---

## Server Action / API Route — Re-check Auth at the Mutation

Middleware and layout checks protect page navigation, not the mutation endpoint
itself — a Server Action or route handler can be invoked directly, bypassing
whatever redirect logic sits in front of the page.

```ts
// app/actions.ts
"use server";
import { auth } from "@/auth";

export async function deletePost(postId: string) {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");

  await db.post.delete({ where: { id: postId, authorId: session.user.id } });
}
```

```ts
// app/api/posts/[id]/route.ts
import { auth } from "@/auth";
import { NextResponse } from "next/server";

export async function DELETE(req: Request, { params }: { params: { id: string } }) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  await db.post.delete({ where: { id: params.id, authorId: session.user.id } });
  return NextResponse.json({ ok: true });
}
```

Note the `authorId: session.user.id` in the `where` clause — auth checks who is
logged in, authorization checks whether *this* user owns *this* row. Both matter.

---

## Session vs JWT

| | JWT session | DB-backed session |
|---|---|---|
| Lookup cost | None — decode + verify signature | One DB read per request |
| Revocation | Can't revoke before expiry (logout just deletes the client cookie) | Instant — delete the row |
| Payload size | Grows the cookie itself | Cookie holds only an opaque session ID |
| Good fit | Stateless APIs, short-lived tokens, high request volume | Anything needing "log out everywhere," ban a user immediately, admin-kill a session |

Auth.js defaults to JWT sessions but supports a database `session` strategy via
an adapter (Prisma, Drizzle) — switch to it when instant revocation matters more
than avoiding a DB hop. Clerk and Lucia's session-table pattern are DB-backed by
default. Pick JWT for throughput, DB sessions for control; there's no way to get
both without a middle ground (e.g. short JWT expiry + a revocation denylist).

---

## Common Anti-Patterns

- **Storing a JWT in `localStorage`** instead of an httpOnly cookie — any XSS on
  the page can read `localStorage` and exfiltrate the token. An httpOnly cookie
  is invisible to JavaScript entirely.
- **Checking auth only in middleware/UI, not in the Server Action or API route**
  — a Server Action is a public HTTP endpoint under the hood; skipping the
  in-action check means anyone who can guess the action's signature can call it
  unauthenticated.
- **Rolling your own password hashing** (`md5`, a homemade salt scheme) instead
  of a maintained library (`bcrypt`, `argon2`, or the hashing the auth library
  already provides) — password hashing has known failure modes a general-purpose
  dev doesn't need to rediscover.
- **Trusting the client-sent user ID** instead of re-deriving it from the
  session on the server — a hidden form field or request body claiming
  `userId: "123"` is not proof of identity.
- **No `authorized`/ownership check in the query itself** — verifying the user
  is logged in but not that they own the row being mutated (see the
  `authorId: session.user.id` example above).

---

## Related Skills

- `ts-nextjs-app-router` — Server Component/Server Action boundary this auth
  layer sits inside
- `ts-api-layer` — API route conventions, of which auth-gated routes are a subset
- `ts-orm-database` — the session/user table an Auth.js DB adapter or Lucia needs
- `ts-validation-schema` — validating sign-up/sign-in payloads with Zod
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
