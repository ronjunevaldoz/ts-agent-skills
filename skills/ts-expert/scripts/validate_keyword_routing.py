#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

_TRIGGER_RE = re.compile(r"\*\*Trigger keywords:\*\*\s*(.+?)(?=\n\n|\Z)", re.DOTALL)
_ALTERNATIVE_RE = re.compile(r"[Aa]lternative to `([a-z0-9-]+)`")


def _keywords(text: str) -> set[str]:
    match = _TRIGGER_RE.search(text)
    if not match:
        return set()
    return {kw.strip().lower() for kw in match.group(1).split(",") if kw.strip()}


def validate_keyword_routing(repo_root: Path) -> list[str]:
    skills_dir = repo_root / "skills"
    errors: list[str] = []
    keywords_by_skill: dict[str, set[str]] = {}
    alternatives: dict[str, str] = {}

    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        name = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8")
        kws = _keywords(text)
        if not kws:
            errors.append(f"{name}: missing '**Trigger keywords:**' line")
        keywords_by_skill[name] = kws

        alt_match = _ALTERNATIVE_RE.search(text)
        if alt_match:
            alternatives[name] = alt_match.group(1)

    # Two skills explicitly documented as alternatives must not share a trigger
    # keyword — that ambiguity is exactly what routing exists to prevent.
    for name, alt_of in alternatives.items():
        if alt_of not in keywords_by_skill:
            continue
        overlap = keywords_by_skill.get(name, set()) & keywords_by_skill[alt_of]
        if overlap:
            errors.append(f"{name} and its alternative {alt_of} share trigger keywords: {sorted(overlap)}")

    return errors


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate keyword routing coverage across all skills.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args(argv)

    errors = validate_keyword_routing(args.repo_root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    skill_count = len(list((args.repo_root / "skills").glob("*/SKILL.md")))
    print(f"OK: {skill_count} skills have keyword routing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
