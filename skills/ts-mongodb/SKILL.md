---
name: ts-mongodb
description: >
  MongoDB as the document-database alternative to `ts-orm-database`'s SQL/Prisma-Drizzle
  path — Mongoose vs the native `mongodb` Node.js driver, document mapping at the
  repository boundary, change streams for real-time reads, and indexing basics. Use
  when data is genuinely document-shaped or append-heavy, not as a default choice; the
  SQL-vs-NoSQL decision itself lives in `ts-orm-database` and `ts-expert`. Covers real
  schema/model code for both driver choices, tied back to `ts-validation-schema` for
  the native-driver path.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - MongoDB
    - Mongoose
    - document database
    - NoSQL
    - native driver
    - ObjectId
    - change streams
    - watch
    - indexing
    - explain
    - aggregation pipeline
    - repository
    - document mapping
    - Zod
---

## When to Use This Skill

Use when you need to:
- Decide whether a feature's data actually belongs in MongoDB instead of Postgres
- Choose between Mongoose and the native `mongodb` driver for a Node/TypeScript backend
- Define a MongoDB schema/model with TypeScript types, with or without Mongoose
- Keep `ObjectId` and driver-specific types out of the rest of the app
- Subscribe to real-time data changes with `watch()`, or decide that polling is simpler

**Trigger keywords:** MongoDB, Mongoose, mongodb driver, ObjectId, collection, document,
change stream, watch(), aggregation pipeline, NoSQL, ensureIndex, explain(), schema.

**Freshness rule:** the native driver's typed API (`Collection<T>`) and Mongoose's
TypeScript inference (`InferSchemaType`) both move across majors — recheck each
package's own docs before pinning a version.

---

## When to Reach for This Over SQL

The full SQL-vs-NoSQL decision tree lives in `ts-orm-database`'s "Recommendation
First" section and in `ts-expert` — read those before defaulting here. In short,
MongoDB earns its place when:

- **The data is genuinely document-shaped and variable-structure** — a form-builder's
  submitted answers, a CMS's per-content-type fields, anything where a rigid SQL
  column set would mean constant migrations or a sprawling EAV table.
- **The access pattern is append-heavy and rarely joined** — event logs, audit trails,
  time-series/metrics data written once and read back mostly by time range, not by
  relation.
- **The team is already committed to Mongo's query model** — an existing Mongo
  deployment, existing operational expertise, or a query pattern (aggregation
  pipelines) the team already leans on.

Reach for `ts-orm-database` (Prisma or Drizzle over Postgres) by default. Relational
data with real joins, transactions across multiple entities, or a need for strong
schema enforcement at the database level belongs there, not here.

---

## Recommendation First

**Mongoose if the team wants schema validation, a TypeScript-friendly model layer, and
population baked into the database layer. The native `mongodb` driver if the team is
already using Zod for validation and wants one source of truth for shape instead of
two.**

| | Mongoose | Native driver (`mongodb`) |
|---|---|---|
| Schema | `Schema` object, its own validation DSL | none — plain TS types + your own validator |
| Types | `InferSchemaType<typeof schema>` | hand-written interface or `z.infer` |
| Validation | built into the schema (`required`, `minlength`, custom validators) | your responsibility — Zod recommended |
| Relations | `.populate()` — join-like document resolution | manual `$lookup` aggregation or app-level fetch |
| Middleware/hooks | `pre`/`post` save, validate, remove hooks | none — do it explicitly in the repository |
| Abstraction cost | a full ODM layer between you and the driver | thin wrapper close to the wire protocol |

**Recommendation:** if the team already reaches for Zod everywhere else in this stack
(`ts-validation-schema`, forms, API boundaries), use the **native driver + a shared Zod
schema** — Mongoose's validation DSL then duplicates a job Zod already does, and you'd
be maintaining two schemas (Mongoose's and Zod's) for the same shape. Reach for
**Mongoose** when the team wants the ODM conveniences (hooks, population, a
batteries-included model layer) and isn't already Zod-first, or when population across
documents is used heavily enough that hand-writing `$lookup` aggregations everywhere
would be worse than the abstraction cost.

Don't run both in one project on the same collections — pick one write path, since
Mongoose's document instances and the native driver's plain documents aren't the same
type at the boundary.

---

## Mongoose — Schema and Model

```ts
// models/user.model.ts
import { Schema, model, type InferSchemaType } from "mongoose";

const userSchema = new Schema(
  {
    email: { type: String, required: true, unique: true },
    name: { type: String },
    role: { type: String, enum: ["member", "admin"], default: "member" },
  },
  { timestamps: true },
);

export type UserDoc = InferSchemaType<typeof userSchema>;
export const UserModel = model("User", userSchema);
```

`InferSchemaType` derives the TypeScript type from the schema definition, the same
"one definition, derived type" principle `ts-validation-schema` establishes for Zod —
the schema *is* the source of truth, not a hand-written `interface` kept in sync
by hand.

```ts
// query: find a user, populate their posts
const user = await UserModel.findOne({ email: "ada@example.com" })
  .populate<{ posts: PostDoc[] }>("posts")
  .lean();
```

`.lean()` returns a plain JS object instead of a full Mongoose document instance —
use it on read paths where you don't need document methods (`.save()`, hooks), which
is most reads. Skipping `.lean()` on a hot read path is a real, measurable cost:
every full document instance carries Mongoose's change-tracking machinery.

---

## Native Driver — Collection + Zod Schema

```ts
// schemas/user.ts — the one shape, shared with forms/API per ts-validation-schema
import { z } from "zod";

export const userSchema = z.object({
  email: z.string().email(),
  name: z.string().optional(),
  role: z.enum(["member", "admin"]).default("member"),
});

export type UserInput = z.infer<typeof userSchema>;
```

```ts
// db/users.ts
import { MongoClient, type Collection, type WithId, type Document } from "mongodb";
import { userSchema, type UserInput } from "../schemas/user";

interface UserDocument extends Document {
  email: string;
  name?: string;
  role: "member" | "admin";
  createdAt: Date;
}

const client = new MongoClient(process.env.MONGODB_URI!);
const users: Collection<UserDocument> = client.db("app").collection("users");

export async function createUser(input: UserInput) {
  const parsed = userSchema.parse(input); // validate before it ever touches the driver
  const { insertedId } = await users.insertOne({ ...parsed, createdAt: new Date() });
  return insertedId;
}
```

Same schema-as-source-of-truth principle as Mongoose's `InferSchemaType`, just with
Zod doing the deriving instead of the ODM — validate with `userSchema.parse()` before
the write, and there is exactly one place that defines what a "user" looks like.

---

## Document Mapping / Repository Boundary

Same principle `ts-orm-database` establishes for Prisma/Drizzle: nothing downstream
of the data-access layer should see a driver type. For Mongo that means `ObjectId`,
`WithId<Document>`, and Mongoose document instances never leave the repository — map
to a plain TypeScript type at the edge.

```ts
// repository/user.repository.ts
import { ObjectId } from "mongodb";

export interface User {
  id: string;       // not ObjectId
  email: string;
  name?: string;
  role: "member" | "admin";
}

function toDomain(doc: WithId<UserDocument>): User {
  return {
    id: doc._id.toString(),
    email: doc.email,
    name: doc.name,
    role: doc.role,
  };
}

export async function findUserById(id: string): Promise<User | null> {
  const doc = await users.findOne({ _id: new ObjectId(id) });
  return doc ? toDomain(doc) : null;
}
```

Route handlers, services, and UI code work with `User` and a plain `string` id. They
never construct an `ObjectId`, never import from `mongodb`, and never call
`.populate()` — all of that stays inside `repository/`.

---

## Change Streams

`watch()` opens a real-time subscription to insert/update/delete/replace events on a
collection (or the whole database) — MongoDB pushes changes as they happen instead of
the client polling.

```ts
// repository/user.repository.ts
export function watchUsers(onChange: (user: User) => void) {
  const stream = users.watch([{ $match: { operationType: { $in: ["insert", "update"] } } }]);
  stream.on("change", (event) => {
    if ("fullDocument" in event && event.fullDocument) {
      onChange(toDomain(event.fullDocument as WithId<UserDocument>));
    }
  });
  return () => stream.close();
}
```

**Reach for it when:** the UI genuinely needs to react live to a change made by
another process — a real-time dashboard, a collaborative view, a background job
publishing a status update another part of the app needs to react to immediately.

**Don't reach for it when** `ts-data-fetching`'s TanStack Query `refetchInterval` or a
manual `invalidateQueries()` after a mutation is enough — most "real-time-ish" UI
needs are actually "update after my own action" or "tolerable a few seconds stale,"
both of which polling/refetch handles with far less operational surface (no
long-lived connection to manage, no replica-set requirement — change streams need a
replica set, they don't work against a standalone MongoDB instance).

---

## Indexing

A query without a matching index does a full collection scan — MongoDB walks every
document in the collection to find matches, and that cost grows linearly with
collection size. This is the same "measure, don't guess" principle the rest of this
skill collection applies: don't assume an index exists or is being used, check.

```ts
await users.createIndex({ email: 1 }, { unique: true });
```

```ts
// verify the index is actually used
const plan = await users.find({ email: "ada@example.com" }).explain("executionStats");
console.log(plan.executionStats.executionStages.stage); // "IXSCAN", not "COLLSCAN"
```

`explain()` shows the real query plan. `COLLSCAN` means no index was used — on a small
collection that's invisible; on a large one it's the difference between a millisecond
lookup and a multi-second scan under load. Add the index, rerun `explain()`, confirm
`IXSCAN` before moving on.

---

## Common Anti-Patterns

- **Leaking `ObjectId` or Mongoose document instances outside the data-access layer**
  — passing a raw Mongo document into a service or component instead of mapping to a
  plain type at the repository boundary; see Document Mapping above.
- **An unindexed query on a large collection** — a filter on a field with no index
  does a full `COLLSCAN`; run `explain()` before assuming a query is fast, not after
  it's slow in production.
- **Mongoose schema validation *and* a separate Zod schema for the same shape** —
  duplicates validation logic in two places that will drift; pick one source of truth
  per the Recommendation above (native driver + Zod, or Mongoose alone).
- **Reaching for MongoDB by default** without the real decision `ts-orm-database` and
  `ts-expert` already establish — relational data with real joins belongs in Postgres
  via Prisma/Drizzle, not shoehorned into documents because Mongo felt familiar.
- **Using change streams for ordinary CRUD screens** — a plain repository call plus
  TanStack Query refetch/invalidation is simpler and doesn't require a replica set;
  reserve `watch()` for genuinely real-time needs.

---

## Related Skills

- `ts-orm-database` — the SQL/Prisma-Drizzle alternative this skill is the NoSQL
  counterpart to; read its "Recommendation First" section for the SQL-vs-NoSQL call
- `ts-validation-schema` — the Zod schema reused for native-driver validation
- `ts-data-fetching` — TanStack Query polling/refetch as the simpler alternative to
  change streams for most "real-time-ish" UI
- `ts-api-layer` — the route/handler layer that calls into these repositories
- `ts-background-jobs` — a job that writes to Mongo and needs to notify the app is a
  change-stream vs job-callback decision
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
