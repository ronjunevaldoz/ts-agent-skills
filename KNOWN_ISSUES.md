# Known Issues

Tracks confirmed agent behavior gaps, tool limitations, and workarounds.
Resolved issues stay here for reference — they explain *why* a rule exists.

---

## Open

None yet.

---

## Resolved

### KI-001 — Generic "use ts-agent-skills to build this" never routed to `/ts-new-project`

**Status:** Resolved 2026-08-10.

**Symptom:** A real consumer-project prompt — "Use ts-agent-skills to create this
project [from a linked take-home exam spec], but analyze and summarize first, don't
execute it immediately" — never invoked `/ts-new-project`. The agent implemented a
Next.js app from scratch instead: skipped `ts-shadcn-ui` entirely, and skipped the
plan-confirmation gate even though the user explicitly asked for analysis before
execution. Root cause: nothing in `ts-expert`'s description, trigger keywords, or
`README.md` told the agent that a from-scratch project request should dispatch to the
`/ts-new-project` command rather than being implemented directly — a generic mention
of the collection's name, or a linked spec doc, doesn't match any of `ts-expert`'s
prior trigger keywords (all skill-selection-shaped: "which skill", "build order",
etc.), so nothing routed and the agent fell back to unrouted, generic Next.js
knowledge. Confirmed by comparing against `kmp-agent-skills/README.md`, which has
always stated this explicitly ("Run `/kmp-new-project` with a natural language
description," plus a routing table) — `ts-agent-skills/README.md` had zero mentions
of `/ts-new-project` anywhere.

**Fix:** Added a "Main Use Cases" section to `README.md` (mirrors `kmp-agent-skills`'
pattern) stating explicitly that a from-scratch request must invoke `/ts-new-project`,
not a generic mention of the collection. Added new trigger keywords to `ts-expert`
("new project", "create a project", "scaffold a project", "build this app",
"take-home", "use ts-agent-skills") and an explicit body statement: a request to
build/create/scaffold a new project — including from an external spec doc or a
take-home exam — is a command dispatch to `/ts-new-project`, never an ad hoc
implementation task. `/ts-new-project`'s own Step 2c already gates all code behind an
explicit confirmation, so routing correctly also satisfies "analyze first" requests
for free once the command is actually invoked.
