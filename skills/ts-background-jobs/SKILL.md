---
name: ts-background-jobs
description: >
  Offloading long-running work off the HTTP request/response cycle in a
  Next.js/Vercel-deployed TypeScript app — sending a batch of emails,
  processing an uploaded video, generating a report, calling a slow
  third-party API. Covers Vercel Cron Jobs for scheduled work, QStash for
  one-off event-triggered jobs with HTTP-based retries, and BullMQ/Inngest
  for sophisticated queue orchestration. Every serverless function has a
  hard execution-time ceiling; this skill is about what runs past it.
license: Apache-2.0
metadata:
  author: ts-agent-skills
  last-updated: '2026-08-08'
  keywords:
    - background jobs
    - queue
    - BullMQ
    - Inngest
    - QStash
    - Vercel Cron
    - cron job
    - worker
    - job queue
    - async processing
    - long-running task
    - maxDuration
    - serverless timeout
    - retry
    - idempotency
---

## When to Use This Skill

Use when you need to:
- Run work that won't finish inside a serverless function's execution limit
- Schedule recurring work (nightly cleanup, daily digest email)
- Trigger a one-off background job from a request handler and return immediately
- Decide between Vercel Cron, QStash, and a dedicated queue (BullMQ/Inngest)
- Make sure a retried or duplicate-delivered job doesn't run its side effect twice

**Trigger keywords:** background job, queue, BullMQ, Inngest, QStash, Vercel Cron,
cron job, worker, job queue, async processing, long-running task, maxDuration,
serverless timeout, function timeout, offload work, job orchestration, scheduled task,
event-triggered job.

**Freshness rule:** Vercel's exact `maxDuration` ceiling (default and max) changes by
plan and by Vercel's own release cadence — verify the current numbers against
vercel.com/docs before quoting one. The pattern (a hard ceiling exists, respect it) is
stable; the number isn't.

---

## Recommendation First

A serverless function has a hard execution-time ceiling, configurable up to a
plan-dependent maximum via `maxDuration` in route config — but it is still a ceiling,
not a suggestion. Anything that can plausibly exceed it (a batch of emails, a video
transcode, a report over a large dataset, a slow third-party API) does not belong
inline in a request handler. Trigger it and return.

Three real options, one decision axis — is the trigger a clock or an event, and how
sophisticated does orchestration need to be:

| Trigger / need | Use |
|---|---|
| Scheduled/recurring (nightly, daily digest) | Vercel Cron Jobs |
| One-off, event-triggered, simple retry needs | QStash |
| Job priorities, complex retry/backoff, job dependencies, or a long-lived worker is available | BullMQ (Redis) or Inngest |

Don't reach past the first row that fits. Vercel Cron for anything driven by a clock.
QStash for "user clicked something, now go do slow work" without standing up
infrastructure. A dedicated queue only once you need orchestration Cron/QStash don't
give you, or you're not on Vercel serverless at all.

---

## Vercel Cron Jobs — scheduled work

`vercel.json`:
```json
{
  "crons": [
    { "path": "/api/cron/nightly-cleanup", "schedule": "0 3 * * *" }
  ]
}
```

Route handler:
```typescript
// app/api/cron/nightly-cleanup/route.ts
import { NextResponse } from "next/server";

export const maxDuration = 60; // seconds — verify current plan ceiling before relying on this

export async function GET(req: Request) {
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return new NextResponse("Unauthorized", { status: 401 });
  }

  await runNightlyCleanup();
  return NextResponse.json({ ok: true });
}
```

Vercel invokes cron routes with a `Bearer ${CRON_SECRET}` header itself when
`CRON_SECRET` is set — checking it stops anyone else from hitting the route and
triggering the job on demand. No auth check on a cron route means anyone who guesses
the path can re-run it.

Use this only when the trigger is genuinely time-based. A cron job that polls a table
every minute looking for new work to do is an event-triggered job wearing a schedule —
use QStash or a queue instead.

---

## QStash — one-off, event-triggered work

Publish from a request handler, return immediately instead of blocking on the slow work:
```typescript
// app/api/reports/route.ts
import { Client } from "@upstash/qstash";

const qstash = new Client({ token: process.env.QSTASH_TOKEN! });

export async function POST(req: Request) {
  const { reportId } = await req.json();

  await qstash.publishJSON({
    url: `${process.env.APP_URL}/api/jobs/generate-report`,
    body: { reportId },
    retries: 3,
  });

  return Response.json({ status: "queued" });
}
```

Receiving route — QStash calls this back over HTTP, so the handler must verify the
request actually came from QStash:
```typescript
// app/api/jobs/generate-report/route.ts
import { verifySignatureAppRouter } from "@upstash/qstash/nextjs";

async function handler(req: Request) {
  const { reportId } = await req.json();
  await generateReport(reportId); // must be safe to run twice — see Idempotency below
  return Response.json({ ok: true });
}

export const POST = verifySignatureAppRouter(handler);
```

This is the same connectionless HTTP model `ts-resilience` already covers for
`@upstash/ratelimit` — no long-lived TCP connection to manage, which is why it works
from serverless and Edge where a persistent connection isn't available. QStash owns
retry delivery on failure; you don't hand-roll the retry loop.

---

## BullMQ / Inngest — dedicated queue orchestration

Reach for this once you need job priorities, complex backoff policies, job
dependencies/workflows, or you have a long-lived process to run a worker in (BullMQ
needs a persistent worker — it does not run as a Vercel serverless function). Don't
duplicate `ts-resilience`'s retry/backoff content here — the same exponential-backoff-
with-jitter reasoning applies to a queue's retry policy; point at that skill instead of
re-deriving it.

Producer (can run from a serverless route — only the worker needs a long-lived process):
```typescript
import { Queue } from "bullmq";
import { Redis } from "ioredis";

const connection = new Redis(process.env.REDIS_URL!);
const reportQueue = new Queue("reports", { connection });

await reportQueue.add(
  "generate-report",
  { reportId },
  { attempts: 3, backoff: { type: "exponential", delay: 5_000 } }
);
```

Worker (long-lived process — a separate deployment, not a Vercel function):
```typescript
import { Worker } from "bullmq";

new Worker(
  "reports",
  async (job) => {
    await generateReport(job.data.reportId); // idempotent — jobs can retry or redeliver
  },
  { connection }
);
```

Inngest is the managed alternative to self-hosting BullMQ + Redis: same
orchestration capabilities (retries, dependencies, step functions), but delivered as
HTTP calls into a Next.js route handler, so it works on Vercel serverless without a
standing worker process. Pick BullMQ when you already run a long-lived process
somewhere and want full control; pick Inngest when you want the orchestration without
giving up serverless deployment.

---

## Idempotency — a retried job must be safe to run twice

QStash retries on a non-2xx response. BullMQ retries on a thrown error. Both can also
redeliver a job that actually succeeded if the success response was lost in transit.
Either way, the job handler will sometimes run more than once for the same logical
unit of work — this is the exact idempotency-key problem `ts-resilience` covers in
depth (client generates a key once per operation, server checks it before re-executing
the side effect). Apply that pattern here rather than re-explaining it: a job that
sends an email or charges a card needs the same "check before execute" guard as any
retried mutation.

---

## Common Anti-Patterns

- **Running a long task inline in a request handler** — works in dev, then a real
  upload/report/API call exceeds `maxDuration` in production and the request just dies.
  Trigger the job and return; don't block the response on it.
- **A background job with no idempotency handling** — a retried or redelivered job
  double-sends the email or double-charges the card. Idempotency isn't optional once
  a job sits behind any retry mechanism — see Idempotency above.
- **Polling for job completion instead of using a webhook/callback** — a client loop
  that hits `GET /jobs/:id/status` every two seconds burns requests and adds latency a
  callback wouldn't have. QStash and Inngest both support callback-based completion;
  use it when it's available instead of hand-rolling polling.
- **A cron route with no auth check** — anyone who finds the path can re-trigger a
  scheduled job on demand. Check `CRON_SECRET` (or equivalent) on every cron route.
- **Reaching for BullMQ/Inngest for a single scheduled task** — that's what Vercel Cron
  is for. A dedicated queue is for orchestration complexity, not for "run this once a
  day."

---

## Related Skills

- `ts-resilience` — retry/backoff and idempotency keys both apply directly to job
  delivery and job handlers; this skill points at it rather than duplicating it
- `ts-deploy-vercel` — `maxDuration`, Edge vs Node runtime, and the deployment
  environment these patterns run in
- `ts-api-layer` — a route handler is usually what triggers or receives a job
- `ts-expert` — routing and build order for the full skill set

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-08 | Initial version. |
