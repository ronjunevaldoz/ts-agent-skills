# /ts-verify $ARGUMENTS

**TS Agent Skills** — verify that a change to this skills collection is correct by
running the full local validation pipeline: quality scan, skill-map sync, keyword
routing coverage, and the Python test suite.

Target repo root: `$ARGUMENTS` (defaults to `.` if empty)

This command validates the skills collection itself (`skills/`, `commands/`,
`scripts/`), not a scaffolded consumer app — there is no separate CI-mirroring
concern here since this repo has no build/lint/test of its own beyond these scripts
and pytest.

---

## Step 1 — Skill quality scan

```bash
python3 scripts/scan_skill_issues.py
```

Checks every `SKILL.md` for structural quality gaps: oversized files (>500 lines),
invalid `name`/`description` frontmatter, and other agentskills.io spec violations.

Expected: `OK: no issues found`

Any finding is a blocker. List each verbatim — do not proceed to Step 2 until this
passes or the user explicitly overrides.

---

## Step 2 — Skill map sync

```bash
python3 skills/ts-expert/scripts/validate_skill_map.py --repo-root "${ARGUMENTS:-.}"
```

Confirms `ts-expert`'s skill table, dependency graph, and Build Order actually match
the directories under `skills/` — catches a skill added or removed without updating
the router.

Expected: exit code 0, no drift reported.

---

## Step 3 — Keyword routing coverage

```bash
python3 skills/ts-expert/scripts/validate_keyword_routing.py --repo-root "${ARGUMENTS:-.}"
```

Confirms every skill has trigger keywords and every entry in `ts-expert`'s Skill
Invocation Map resolves to a real skill.

Expected: exit code 0, no coverage gaps reported.

---

## Step 4 — Python test suite

```bash
python3 -m pytest -q
```

Runs the full test suite (`tests/test_scan_skill_issues.py`,
`tests/test_validate_skill_map.py`, `tests/test_validate_keyword_routing.py`,
`tests/test_release.py`) — unit coverage for the three scripts above plus the
release tooling.

On failure: list each failing test name and the assertion that broke.

---

## Step 5 — Summary

```
VERIFY: <repo root>

  Step 1 — Skill quality scan:     PASS | FAIL (<N> issues)
  Step 2 — Skill map sync:         PASS | FAIL
  Step 3 — Keyword routing:        PASS | FAIL
  Step 4 — pytest:                 PASS | FAIL (<N> tests failed)

RESULT: PASS | FAIL
```

On `FAIL`: list the specific blockers and which step produced them.
On `PASS`: print the result and offer to run `/ts-review-changes` next if there's an
uncommitted diff.

---

## Notes

- Steps 1-3 are read-only static checks — they never modify a `SKILL.md`. If Step 1
  or 2 flags something, fix the source file and re-run rather than trying to patch
  around the check.
- If a step is blocked and the user wants to skip it, note the skip in the summary
  with the reason — do not silently omit it.
