# Development Plan

Tracks roadmap for future work — not the skill roster.
Update when planning new skills or hardening the release pipeline.

---

## Status Key

| Symbol | Meaning |
|---|---|
| ✅ | Shipped — skill is in `main`, production-ready |
| 🔧 | Known issues — skill exists but has open defects (see KNOWN_ISSUES.md) |
| 🚧 | In progress — actively being written |
| 📋 | Planned — scoped and ready to start |
| 💡 | Idea — not yet scoped |

---

## Shipped Skills

Full roster with what each skill owns, by layer: `skills/ts-expert/SKILL.md`'s
"The N Skills and What They Own" section — the single source of truth, mechanically
checked against README.md by `skills/ts-expert/scripts/validate_skill_map.py`. Do not
duplicate that list here — a hand-maintained second copy of a skill roster is a real,
confirmed failure mode (see the sibling `kmp-agent-skills` repo's own `PLAN.md` history).

---

## Open Defects

See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for tracked open items — do not duplicate its
count or contents here.

---

## Upcoming — v2

Deferred at launch, full rationale in the initial planning doc:

| Item | Priority | Description |
|---|---|---|
| `ts-audit` | HIGH | React/Next.js source-aware code-smell detectors — deliberately deferred past v1 to avoid launching with a thin, noisy detector set |
| Payments, email, i18n, feature flags, analytics skills | MEDIUM | Feature-specific, not architecture-defining — add once a real project needs one |
| `ts-storybook` / `ts-chromatic` | MEDIUM | Component workshop + visual regression |
| `ts-npm-package-publishing` | LOW | Only relevant once a consumer publishes an npm package, not for app-shaped projects |
