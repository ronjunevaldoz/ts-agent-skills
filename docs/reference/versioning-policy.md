# Versioning Policy

Canonical rules for commits, changelogs, and releases. Agents and contributors must follow exactly.

---

## Version Tiers

| Tier | Tag | GitHub Release | CHANGELOG |
|---|---|---|---|
| **dev** | none | no | never touched manually |
| **stable** | `vX.Y.Z` | full release | auto-generated |

**dev** — commit freely; CHANGELOG is never edited manually; hook enforces Conventional Commit format.

**stable** — `python3 scripts/release.py <bump>`; CHANGELOG auto-generated from git log since last stable tag; full GitHub Release. Never create this tag manually.

---

## Commit Format

Every commit must follow Conventional Commit format — enforced by `.githooks/commit-msg`:

```
<type>[optional scope]: <description>
```

| Type | When |
|---|---|
| `feat` | New skill, script, command |
| `fix` | Bug fix in skill, script, or tooling |
| `docs` | Documentation only |
| `chore` | Version bumps, housekeeping |
| `refactor` | Restructuring, no behavior change |
| `test` | Adding or updating tests |
| `build` / `ci` | Build system, CI/CD |

Examples: `feat(skills): add ts-state-management skill` · `fix: correct Zod schema example in ts-forms` · `chore(versions): bump Next.js 15.2.0`

---

## Version Bump Decision

| What changed | Bump |
|---|---|
| Bug fix, typo, version update | `patch` |
| New skill, new command, new script | `minor` |
| Skill renamed/removed, schema broken | `major` |

---

## Release Commands

```bash
python3 scripts/release.py auto            # detects bump from Conventional Commits
python3 scripts/release.py patch --dry-run # preview without committing
```

---

## Hard Rules for Agents

1. **Never `git tag` manually** — always use `scripts/release.py`.
2. **Never edit `CHANGELOG.md`** for dev commits.
3. **Every commit must use Conventional Commit format** — hook enforces this.
4. **Do not push** tags or release commits without explicit user confirmation.
5. Stable release requires clean tree + passing tests — the script enforces this, do not bypass.

---

## Activating the Hook

```bash
git config core.hooksPath .githooks   # run once per clone
```
