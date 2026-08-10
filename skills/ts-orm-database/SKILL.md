---
name: ts-orm-database
description: >
  Prisma vs Drizzle decision, schema definition, and migrations for a TypeScript
  backend. Prisma is schema-first with its own DSL and the most mature migration
  tooling; Drizzle is TypeScript-first with no codegen step and a SQL-like query
  builder. Covers real schema and query code for both, plus the `prisma migrate`
  and `drizzle-kit` migration workflows.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - Prisma
    - Drizzle
    - ORM
    - schema migration
    - database
    - Postgres
    - query builder
    - prisma migrate
    - drizzle-kit
    - prisma generate
    - relations
    - N+1
    - SQL
---

## When to Use This Skill

Use when you need to:
- Choose between Prisma and Drizzle for a new TypeScript backend
- Define a schema with a relation (one-to-many, many-to-many)
- Write a typed query that joins related tables
- Set up or run a database migration

**Trigger keywords:** Prisma, Drizzle, ORM, prisma schema, drizzle-kit, prisma migrate,
prisma generate, database schema, migration, Postgres, query builder, relation, include,
findMany, drizzle-orm.

**Freshness rule:** Both ORMs ship breaking changes across majors (Prisma's engine
architecture, Drizzle's relational query API) — recheck each project's own docs before
picking a version.

---

## Recommendation First

**Prisma if the team wants the most mature migration workflow and doesn't mind a
generate step. Drizzle if the team wants schema-as-TypeScript with no codegen and
finer control over the generated SQL.**

| | Prisma | Drizzle |
|---|---|---|
| Schema | `.prisma` file, its own DSL | plain `.ts` files |
| Codegen | `prisma generate` produces a client | none — the schema *is* the typed client |
| Migrations | `prisma migrate dev`/`deploy`, best-in-class | `drizzle-kit generate`/`migrate`, thinner |
| Runtime | larger (query engine binary) | lighter, closer to raw SQL |
| Query shape | its own fluent API (`findMany`, `include`) | SQL-like builder (`select`, `.where`, `.leftJoin`) |

Don't run both in one project — pick one, since they own the migration history
differently and mixing them means two sources of truth for the schema.

---

## Prisma — Schema and Client

```prisma
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id    String @id @default(cuid())
  email String @unique
  name  String?
  posts Post[]
}

model Post {
  id        String   @id @default(cuid())
  title     String
  published Boolean  @default(false)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
  createdAt DateTime @default(now())
}
```

`prisma generate` reads this file and writes a fully-typed client into
`node_modules/.prisma/client` — every model, field, and relation is a real TS type,
regenerated on every schema change.

```ts
// query: find a user with their posts
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const user = await prisma.user.findUnique({
  where: { email: "ada@example.com" },
  include: { posts: true },
});
// user is typed as (User & { posts: Post[] }) | null
```

### Prisma migrations

```bash
npx prisma migrate dev --name add_post_published    # local: create + apply + regenerate client
npx prisma migrate deploy                             # CI/prod: apply pending migrations only, no prompts
```

`migrate dev` diffs the schema against migration history, writes a new SQL file under
`prisma/migrations/`, applies it, and reruns `prisma generate`. `migrate deploy` never
creates a migration — it only applies what's already committed, which is what CI/CD
should run.

---

## Drizzle — Schema and Client

```ts
// db/schema.ts
import { pgTable, text, boolean, timestamp, uuid } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";

export const users = pgTable("users", {
  id: uuid("id").defaultRandom().primaryKey(),
  email: text("email").notNull().unique(),
  name: text("name"),
});

export const posts = pgTable("posts", {
  id: uuid("id").defaultRandom().primaryKey(),
  title: text("title").notNull(),
  published: boolean("published").notNull().default(false),
  authorId: uuid("author_id").notNull().references(() => users.id),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
}));
```

No separate DSL, no generate step — `users` and `posts` are the schema and the typed
client's building blocks at once.

```ts
// query: find a user with their posts
import { drizzle } from "drizzle-orm/node-postgres";
import { eq } from "drizzle-orm";
import * as schema from "./db/schema";

const db = drizzle(process.env.DATABASE_URL!, { schema });

const user = await db.query.users.findFirst({
  where: eq(schema.users.email, "ada@example.com"),
  with: { posts: true },
});
// user is typed as { id, email, name, posts: Post[] } | undefined
```

The relational query API (`db.query.*`) reads like Prisma's `include`; the lower-level
builder (`db.select().from(users).leftJoin(posts, ...)`) reads like raw SQL when you
need to control the exact join.

### Drizzle migrations

```bash
npx drizzle-kit generate   # diff schema.ts against migration history, write SQL file
npx drizzle-kit migrate    # apply pending migrations
```

`drizzle-kit.config.ts` points at `db/schema.ts` and the migrations output folder —
`generate` produces plain, readable `.sql` files you can review before they ever run,
which is the point of the "finer control over generated SQL" tradeoff.

---

## Common Anti-Patterns

- **N+1 queries** — looping over users and querying posts per-user instead of using
  `include`/`with` (or a join) to fetch the relation in one round trip:
  ```ts
  // ❌ N+1 — one query per user
  for (const user of await prisma.user.findMany()) {
    const posts = await prisma.post.findMany({ where: { authorId: user.id } });
  }
  // ✓ one query
  const users = await prisma.user.findMany({ include: { posts: true } });
  ```
- **Running migrations against production without a review step** — `migrate deploy`/
  `drizzle-kit migrate` in CI should run against a diff that a human already reviewed
  (the generated SQL file in the PR), not `migrate dev`'s interactive prompt-and-apply
  flow pointed at a prod `DATABASE_URL`.
- **Committing the generated client to git** — Prisma's `node_modules/.prisma/client`
  output (or any generated Drizzle types) belongs in `.gitignore`; regenerate it in CI
  (`prisma generate` as a build step) instead of drifting a stale committed copy out of
  sync with `schema.prisma`.
- **Mixing raw SQL and the ORM's query builder for the same table** without a reason —
  breaks the type safety both tools exist to provide; drop to `$queryRaw`/`db.execute`
  only for a query the builder genuinely can't express.
- **No unique constraint on a field the app treats as unique** (`email`) — enforce it in
  the schema (`@unique` / `.unique()`), not just in application-level validation, so a
  race condition can't insert a duplicate.

---

## Related Skills

- `ts-api-layer` — the route/handler layer that calls into these queries
- `ts-project-foundation` — where the ORM package (`packages/db`) lives in the monorepo
- `ts-validation-schema` — validating input before it reaches a Prisma/Drizzle write
- `ts-resilience` — the atomic-update pattern for limited-resource ("last seat") contention
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
