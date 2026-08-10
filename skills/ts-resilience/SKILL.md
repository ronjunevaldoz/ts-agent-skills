---
name: ts-resilience
description: >
  Network resilience patterns for a TypeScript app — retry with exponential
  backoff and jitter, circuit breakers, timeouts, rate limiting, idempotency
  keys for safe mutation retries, and atomic contention handling for a
  limited resource (the "last seat" problem — N users racing to claim the
  same unit of inventory). Covers Cockatiel for in-process resilience,
  @upstash/ratelimit for edge/serverless rate limiting, and why a naive
  retry loop causes a thundering herd instead of recovery.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - retry
    - exponential backoff
    - jitter
    - circuit breaker
    - timeout
    - rate limiting
    - idempotency key
    - Cockatiel
    - upstash ratelimit
    - thundering herd
    - bulkhead
    - resilience
    - fault tolerance
    - last seat problem
    - inventory race condition
    - AbortSignal.timeout
---

## When to Use This Skill

Use when you need to:
- Decide how a failed network call should be retried, if at all
- Protect your own API routes/tRPC procedures from being overwhelmed
- Make a mutation (checkout, payment, booking) safe to retry without double-executing it
- Handle N users racing to claim the same limited resource (last seat, last item in stock)
- Stop calling a downstream dependency that's already failing, instead of hammering it

**Trigger keywords:** retry, exponential backoff, jitter, circuit breaker, timeout,
rate limiting, idempotency key, thundering herd, bulkhead, resilience, fault tolerance,
last seat, race condition checkout, overselling, distributed lock, AbortSignal.timeout,
429 too many requests, network resilience.

**Freshness rule:** the underlying runtime primitives shift faster than the patterns
themselves — `AbortSignal.timeout`/`AbortSignal.any` and WinterCG-aligned `fetch` are
recent additions; recheck Node's current LTS for what's native before reaching for a
library to do what the platform now does natively.

---

## Recommendation First

**Cockatiel** for in-process resilience (retry, circuit breaker, timeout, bulkhead) —
TypeScript-native, explicitly modeled on .NET's Polly, composable policies instead of
four separate libraries. **`@upstash/ratelimit`** for rate limiting that needs to work
in the Edge runtime (HTTP-based Redis, no TCP connection required — the same constraint
`ts-deploy-vercel`'s Edge-runtime section covers). **Idempotency keys** for any mutation
that moves money or claims inventory — this is what actually makes "just retry it" safe,
not the retry logic itself.

Four patterns, not one — know which problem each solves:
| Pattern | Solves |
|---|---|
| Retry + backoff | A transient failure (network blip, momentary overload) |
| Circuit breaker | A *sustained* failure — stop making it worse by retrying into a dead dependency |
| Timeout | A call that never fails, just never returns |
| Rate limiting | Protecting *your own* endpoint from too many callers, not a caller protecting itself |

---

## Retry with exponential backoff and jitter

```typescript
import { retry, handleAll, ExponentialBackoff } from "cockatiel";

const retryPolicy = retry(handleAll, {
  maxAttempts: 3,
  backoff: new ExponentialBackoff(),   // includes jitter by default
});

const result = await retryPolicy.execute(() => fetchUpstreamData());
```

**Why jitter isn't optional.** A naive retry loop (fixed delay, no jitter) causes a
thundering herd: if a dependency goes down, every caller's fixed-delay retry lands at
the same instant, re-crashing the dependency the moment it recovers. `ExponentialBackoff`
adds randomization by default — AWS's own reference formulas call this "full jitter" or
"decorrelated jitter." Never hand-roll `setTimeout(fn, attempt * 1000)` without it.

**Only retry idempotent operations without an idempotency key.** A `GET` is always safe
to retry. A `POST` that charges a card or claims a seat is not — see Idempotency keys
below before retrying any mutation.

---

## Circuit breaker

```typescript
import { circuitBreaker, handleAll, ConsecutiveBreaker } from "cockatiel";

const breaker = circuitBreaker(handleAll, {
  halfOpenAfter: 10_000,                    // try one call again after 10s
  breaker: new ConsecutiveBreaker(5),        // open after 5 consecutive failures
});

await breaker.execute(() => callFlakyPaymentProvider());
// Once open: fails fast (no network call at all) until halfOpenAfter elapses,
// then allows one trial call through to decide whether to close again.
```

Pair with retry via composition, not by nesting manually:
```typescript
import { wrap } from "cockatiel";
const policy = wrap(retryPolicy, breaker);
```

---

## Timeout

```typescript
// Native AbortSignal.timeout — no library needed as of modern Node/browser support
const response = await fetch(url, { signal: AbortSignal.timeout(5_000) });
```

A call with no timeout doesn't fail — it hangs, holding a connection/thread open
indefinitely. Every external call in `ts-api-layer`'s route handlers and tRPC procedures
needs one; "the request will eventually error" is not a timeout policy.

---

## Rate limiting

**Protecting your own endpoint** (server-side, Edge-compatible):
```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "60 s"),   // 10 requests per 60s
  analytics: true,
});

export const runtime = "edge";   // required — HTTP-based Redis, no TCP

export async function POST(req: Request) {
  const ip = req.headers.get("x-forwarded-for") ?? "unknown";
  const { success } = await ratelimit.limit(ip);
  if (!success) return new Response("Too Many Requests", { status: 429 });
  // ...
}
```

**Respecting someone else's limit** (client-side): back off on a `429`, and read
`Retry-After` if the upstream sends one — don't just retry immediately, that's the same
thundering-herd mistake as a naive retry loop.

---

## Idempotency keys — what actually makes a retry safe

A retry policy makes *calling* safe; it doesn't make the *operation* safe. If `POST
/checkout` is retried after a timeout (the first request may have actually succeeded
server-side, the response just didn't arrive), a naive retry double-charges the card.

```typescript
// Client: generate once per logical operation, reuse across retries of that operation
const idempotencyKey = crypto.randomUUID();

await retryPolicy.execute(() =>
  fetch("/api/checkout", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(order),
  })
);
```

```typescript
// Server: store the key with the result; a repeat request with the same key
// returns the cached result instead of re-executing the charge
export async function POST(req: Request) {
  const key = req.headers.get("Idempotency-Key");
  const existing = key && await db.idempotencyKey.findUnique({ where: { key } });
  if (existing) return Response.json(existing.result);

  const result = await chargeCard(order);
  if (key) await db.idempotencyKey.create({ data: { key, result } });
  return Response.json(result);
}
```

This is the real pattern behind Stripe's own `Idempotency-Key` header — verified against
their public API docs, not invented. Any payment, booking, or "claim this resource"
endpoint needs it before it's safe to sit behind a retry policy at all.

---

## The "last seat" problem — limited-resource contention

N users click "buy" on the same last unit at once. Retrying a failed purchase doesn't
cause this — the race is in the *first* attempt, when two requests both read "1 in
stock" before either has written a decrement.

```typescript
// ❌ Wrong — read-then-write race window between the two queries
const item = await db.inventory.findUnique({ where: { id } });
if (item.quantity > 0) {
  await db.inventory.update({ where: { id }, data: { quantity: item.quantity - 1 } });
  // Two concurrent requests can both pass the check above before either writes.
}

// ✓ Correct — one atomic statement, the database resolves the race
const updated = await db.$executeRaw`
  UPDATE inventory SET quantity = quantity - 1
  WHERE id = ${id} AND quantity > 0
`;
if (updated === 0) throw new SoldOutError();
```

The fix is the same shape in Prisma or Drizzle: a single `UPDATE ... WHERE quantity > 0`
statement, not a `findUnique` followed by a conditional `update`. The database's own
row-level locking during the atomic write is what actually resolves the race — no
application-level lock, queue, or `SELECT FOR UPDATE` transaction is needed for this
specific shape, though a `SELECT FOR UPDATE` transaction is the right tool when the
decision requires more than one column's worth of logic.

---

## Common Anti-Patterns

- **Fixed-delay retry with no jitter** — thundering herd on recovery, see above.
- **Retrying a mutation with no idempotency key** — the retry-safety problem doesn't
  live in the retry logic, it lives in whether the operation can safely run twice.
- **No timeout on an external call** — a hung request holds resources indefinitely
  instead of failing and letting a retry/circuit-breaker policy handle it.
- **`findUnique` then conditional `update` for limited inventory** — the race window is
  the two round-trips, not something a retry or a `UNIQUE` constraint fixes.
- **Retrying into an already-open circuit** — if a circuit breaker exists, respect it;
  a retry policy layered *outside* the breaker instead of composed with it just retries
  past the protection the breaker was supposed to provide.

---

## Related Skills

- `ts-api-layer` — where retry/timeout/circuit-breaker policies actually wrap a call
- `ts-orm-database` — the atomic-update pattern for limited-resource contention
- `ts-deploy-vercel` — Edge runtime constraint that shapes the rate-limiting choice
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
