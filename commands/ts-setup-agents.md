# /ts-setup-agents $ARGUMENTS

**TS Agent Skills** — bootstrap `.claude/AGENTS.md` in a consumer project that
already has `ts-agent-skills` installed (`npx skills add
ronjunevaldoz/ts-agent-skills`). Run this once right after install, or again
after a `ts-agent-skills` update to refresh a stale routing table.

`$ARGUMENTS` is optional — a path to the consumer project root (defaults to `.`).

This exists because a generic request ("use ts-agent-skills to build this")
doesn't reliably route anywhere on its own — the acting agent has to semantically
match the request against `ts-expert`'s description and keywords, which is
best-effort, not guaranteed. `AGENTS.md` is read automatically at the start of
every session in this project, so the routing rule below is a structural
guarantee instead of a hope.

---

## Step 1 — Confirm ts-agent-skills is installed here

Check for `.claude/skills/ts-expert/SKILL.md` (or `.agents/skills/ts-expert/SKILL.md`
for a cross-client install). If neither exists, stop and tell the user to run
`npx skills add ronjunevaldoz/ts-agent-skills` first — this command only writes
the bootstrap file, it doesn't install skills itself.

---

## Step 2 — Check for an existing `AGENTS.md`

If `.claude/AGENTS.md` already exists, print its current content and ask via
`AskUserQuestion`:

- **Overwrite** — replace entirely with the template below
- **Merge routing section only** — keep everything else, replace/add just the
  `## Routing` section
- **Skip** — leave it as-is

Don't silently clobber a project's own customizations.

---

## Step 3 — Write `.claude/AGENTS.md`

```markdown
# Agent Instructions — <PROJECT_NAME>

This project uses [ts-agent-skills](https://github.com/ronjunevaldoz/ts-agent-skills)
— TypeScript/Next.js architecture skills, installed under `.claude/skills/`.

## Routing

- **New project / from-scratch build request** — including "use ts-agent-skills
  to build this," a linked spec doc, or a take-home exam — run
  `/ts-new-project <description>`. Never implement ad hoc: that skips the
  plan-confirmation gate, the wireframe review, and this collection's own
  architecture decisions (including `ts-shadcn-ui` — a from-scratch Next.js app
  that isn't using shadcn/ui is a sign this routing was skipped).
- **Reviewing a diff** — run `/ts-review-changes`.
- **Auditing existing code for smells/architecture drift** — run `/ts-audit`
  (if installed; deferred until the skill exists).
- **Unsure which skill applies** — load `ts-expert` first; it routes to the
  right skill and the Build Order.

## Verify

This project's own check: `pnpm turbo run lint typecheck test build` — the same
command CI runs. `/ts-verify` (if present) checks the `ts-agent-skills`
collection itself, not this project — don't confuse the two.
```

Fill `<PROJECT_NAME>` from `package.json`'s `name` field, or the directory name
if absent. Drop the `/ts-audit` line if that skill isn't installed yet — check
`.claude/skills/ts-audit/` before including it.

---

## Step 4 — Summary

```
AGENTS.md written: <path>

Routing rule active: new-project requests now dispatch to /ts-new-project
automatically, every session — not dependent on keyword matching.

Re-run /ts-setup-agents after updating ts-agent-skills to a new version, in
case the routing table above needs to change.
```

---

## Related

- `ts-new-project` — the command this bootstrap exists to route to reliably
- `ts-expert` — routing and build order for the full skill set
- [`kmp-agent-skills`](https://github.com/ronjunevaldoz/kmp-agent-skills)'
  `/kmp-setup-agents` — the mature sibling command this is a right-sized
  version of; that one also handles module-graph detection, Codex/Gemini
  translation, and a Bash allowlist — none of which this collection needs yet
  at its current size
