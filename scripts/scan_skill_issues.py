#!/usr/bin/env python3
"""
scan_skill_issues.py — scan all SKILL.md files for quality gaps and output
a structured JSON report.

Exit codes:
  0 — no issues found
  1 — issues found (expected; not an error)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
COMMANDS_DIR = ROOT / "commands"

# agentskills.io spec: name is lowercase unicode alphanumeric + hyphens, no
# leading/trailing/double hyphen.
_AGENTSKILLS_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_AGENTSKILLS_MAX_RECOMMENDED_LINES = 500
_MAX_DESCRIPTION_CHARS = 1024
_MAX_NAME_CHARS = 64

_NUMBERED_STEP_RE = re.compile(r"^\d+\.\s+(.+)$", re.MULTILINE)
_CODE_SPAN_RE = re.compile(r"`[^`]*`")
_MAX_PROCEDURAL_WORDS = 20

# Deliberately-deferred, dated, reasoned exemptions only — never a blanket
# silence for a check. Empty at repo start; add an entry only after actually
# triaging a real violation as acceptable debt.
KNOWN_DEBT: set[tuple[str, str]] = set()

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _read_frontmatter(text: str) -> str | None:
    match = _FRONTMATTER_RE.match(text)
    return match.group(1) if match else None


def procedural_word_count(step_text: str) -> int:
    stripped = _CODE_SPAN_RE.sub("", step_text)
    return len(stripped.split())


def scan_skill(skill_dir: Path) -> list[dict]:
    findings: list[dict] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return findings
    name = skill_dir.name
    text = skill_md.read_text(encoding="utf-8")

    if not _AGENTSKILLS_NAME_RE.match(name):
        findings.append({"skill": name, "check": "invalid_name", "severity": "HIGH"})

    lines = text.count("\n")
    if lines > _AGENTSKILLS_MAX_RECOMMENDED_LINES and (name, "oversized_skill_md") not in KNOWN_DEBT:
        findings.append({
            "skill": name, "check": "oversized_skill_md", "severity": "MEDIUM",
            "detail": f"{lines} lines (limit {_AGENTSKILLS_MAX_RECOMMENDED_LINES}) — split into references/*.md",
        })

    frontmatter = _read_frontmatter(text)
    if frontmatter is None:
        findings.append({"skill": name, "check": "missing_frontmatter", "severity": "HIGH"})
    else:
        desc_match = re.search(r"description:\s*>?\s*\n((?:  .+\n?)+)", frontmatter)
        description = desc_match.group(1) if desc_match else ""
        if len(description) > _MAX_DESCRIPTION_CHARS and (name, "description_approaching_limit") not in KNOWN_DEBT:
            findings.append({
                "skill": name, "check": "description_approaching_limit", "severity": "LOW",
                "detail": f"{len(description)} chars (limit {_MAX_DESCRIPTION_CHARS})",
            })

    for ref_md in (skill_dir / "references").glob("*.md") if (skill_dir / "references").is_dir() else []:
        ref_lines = ref_md.read_text(encoding="utf-8").count("\n")
        if ref_lines > _AGENTSKILLS_MAX_RECOMMENDED_LINES:
            findings.append({
                "skill": name, "check": "oversized_reference_md", "severity": "MEDIUM",
                "detail": f"{ref_md.name}: {ref_lines} lines (limit {_AGENTSKILLS_MAX_RECOMMENDED_LINES})",
            })

    for match in _NUMBERED_STEP_RE.finditer(text):
        word_count = procedural_word_count(match.group(1))
        if word_count > _MAX_PROCEDURAL_WORDS:
            findings.append({
                "skill": name, "check": "long_procedural_step", "severity": "LOW",
                "detail": f"{word_count} words (limit {_MAX_PROCEDURAL_WORDS}): {match.group(1)[:60]}...",
            })

    return findings


def scan_commands() -> list[dict]:
    findings: list[dict] = []
    if not COMMANDS_DIR.is_dir():
        return findings
    for cmd_md in COMMANDS_DIR.glob("*.md"):
        lines = cmd_md.read_text(encoding="utf-8").count("\n")
        if lines > _AGENTSKILLS_MAX_RECOMMENDED_LINES:
            findings.append({
                "skill": cmd_md.stem, "check": "oversized_command_md", "severity": "MEDIUM",
                "detail": f"{lines} lines (limit {_AGENTSKILLS_MAX_RECOMMENDED_LINES})",
            })
    return findings


def scan_all() -> dict:
    all_findings: list[dict] = []
    if SKILLS_DIR.is_dir():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.is_dir():
                all_findings.extend(scan_skill(skill_dir))
    all_findings.extend(scan_commands())

    blocking = [f for f in all_findings if f["severity"] in ("HIGH", "MEDIUM")]
    return {
        "total_issues": len(all_findings),
        "blocking_issues": len(blocking),
        "findings": all_findings,
    }


def main() -> int:
    report = scan_all()
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        for finding in report["findings"]:
            print(f"[{finding['severity']}] {finding['skill']}: {finding['check']} — {finding.get('detail', '')}")
        if not report["findings"]:
            print("OK: no issues found")
    return 1 if report["blocking_issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
