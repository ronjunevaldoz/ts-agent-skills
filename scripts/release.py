#!/usr/bin/env python3
"""
Release script for ts-agent-skills.

Usage:
    python3 scripts/release.py patch          # stable release — bug fixes
    python3 scripts/release.py minor          # stable release — new skills, new features
    python3 scripts/release.py major          # stable release — breaking changes
    python3 scripts/release.py auto           # detect bump from Conventional Commits
    python3 scripts/release.py patch --dry-run

After pushing, run:
    python3 scripts/release.py publish            # publishes the current HEAD's tag
    python3 scripts/release.py publish v1.2.3      # or an explicit tag
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
SKILLS_JSON = ROOT / "skills.json"
CHANGELOG_MD = ROOT / "CHANGELOG.md"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False) if not check \
        else subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"✅  {msg}")


def info(msg: str) -> None:
    print(f"    {msg}")


def check_clean_tree() -> None:
    result = run(["git", "status", "--porcelain"])
    if result.stdout.strip():
        fail("git working tree is not clean — commit or stash first")


def run_scan_skill_issues() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from scan_skill_issues import scan_all
    report = scan_all()
    if report["blocking_issues"]:
        fail(f"scan_skill_issues found {report['blocking_issues']} blocking issue(s)")
    ok("Skill issue scan clean")


def run_skill_map_validation() -> None:
    sys.path.insert(0, str(ROOT / "skills" / "ts-expert" / "scripts"))
    from validate_skill_map import validate_skill_map
    errors = validate_skill_map(ROOT)
    if errors:
        fail("skill map validation failed:\n" + "\n".join(errors))
    ok("Skill map validation passed")


def run_keyword_routing_validation() -> None:
    sys.path.insert(0, str(ROOT / "skills" / "ts-expert" / "scripts"))
    from validate_keyword_routing import validate_keyword_routing
    errors = validate_keyword_routing(ROOT)
    if errors:
        fail("keyword routing validation failed:\n" + "\n".join(errors))
    ok("Keyword routing validation passed")


def run_tests() -> None:
    result = run(["python3", "-m", "pytest", "-q"], check=False)
    if result.returncode != 0:
        fail("Tests are failing. Fix them before releasing.\n" + result.stdout + result.stderr)
    match = re.search(r"(\d+) passed", result.stdout)
    ok(f"All tests pass ({match.group(1) if match else '?'} passed)")


def run_release_validation() -> None:
    run_scan_skill_issues()
    run_skill_map_validation()
    run_keyword_routing_validation()
    run_tests()


def bump_version(current: str, bump: str) -> str:
    major, minor, patch = (int(p) for p in current.split("."))
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def extract_skills() -> list[dict]:
    skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        name = re.search(r"^name:\s*(.+)$", fm, re.MULTILINE)
        desc_match = re.search(r"^description:\s*[>|]-?\n((?:  .+\n?)+)", fm, re.MULTILINE)
        desc = " ".join(line.strip() for line in desc_match.group(1).splitlines()) if desc_match else ""
        skills.append({
            "name": name.group(1).strip() if name else skill_dir.name,
            "path": f"skills/{skill_dir.name}",
            "description": desc,
        })
    return skills


def update_skills_json(new_version: str) -> None:
    skills = extract_skills()
    manifest = {"version": new_version, "skills": skills}
    SKILLS_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    ok(f"skills.json updated — version {new_version}, {len(skills)} skills")


def get_previous_tag() -> str:
    result = run(["git", "describe", "--tags", "--abbrev=0", "HEAD"], check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def generate_changelog_section(new_version: str, prev_tag: str) -> str:
    import datetime
    date = datetime.date.today().isoformat()
    tag = f"v{new_version}"
    result = run(["git", "log", "--oneline", f"{prev_tag}..HEAD"] if prev_tag else ["git", "log", "--oneline"])
    lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]

    buckets: dict[str, list[str]] = {"feat": [], "fix": [], "docs": [], "chore": [], "other": []}
    for line in lines:
        _, _, rest = line.partition(" ")
        prefix = rest.split("(")[0].split(":")[0].strip().lower()
        buckets[prefix if prefix in buckets else "other"].append(f"- {rest}")

    section = [f"## [{tag}] — {date}\n"]
    for key, heading in [("feat", "Added"), ("fix", "Fixed"), ("docs", "Docs"), ("chore", "Chore"), ("other", "Other")]:
        if buckets[key]:
            section.append(f"### {heading}\n")
            section.extend(buckets[key])
            section.append("")
    return "\n".join(section)


def update_changelog(new_version: str, prev_tag: str) -> None:
    header = "# Changelog\n\nAll notable changes to ts-agent-skills are documented here.\n\n"
    existing = CHANGELOG_MD.read_text(encoding="utf-8") if CHANGELOG_MD.exists() else header
    section = generate_changelog_section(new_version, prev_tag)
    if not existing.startswith("# Changelog"):
        existing = header + existing
    body = existing[len(header):] if existing.startswith(header) else existing
    CHANGELOG_MD.write_text(header + section + "\n---\n\n" + body, encoding="utf-8")
    ok("CHANGELOG.md updated")


def git_commit_and_tag(new_version: str, tag: str, skill_count: int, dry_run: bool) -> None:
    msg = f"Release {tag}\n\n{skill_count} skills shipped. See CHANGELOG.md for details."
    if dry_run:
        info(f"[dry-run] would commit + tag {tag}")
        return
    run(["git", "add", "skills.json", "CHANGELOG.md"])
    run(["git", "commit", "-m", msg])
    run(["git", "tag", "-a", tag, "-m", msg])
    ok(f"Committed and tagged {tag}")


def cmd_publish(tag: str | None) -> int:
    if tag is None:
        result = run(["git", "describe", "--tags", "--exact-match"], check=False)
        if result.returncode != 0:
            fail("HEAD is not exactly on a tag — pass the tag explicitly: release.py publish vX.Y.Z")
        tag = result.stdout.strip()
    result = run(["git", "ls-remote", "--tags", "origin", tag], check=False)
    if not result.stdout.strip():
        fail(f"Tag {tag} not found on origin — push it first: git push origin {tag}")
    run(["gh", "release", "create", tag, "--title", tag, "--generate-notes"])
    ok(f"GitHub Release {tag} created")
    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Release pipeline for ts-agent-skills.")
    parser.add_argument("bump", choices=["patch", "minor", "major", "auto", "publish"])
    parser.add_argument("tag", nargs="?", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.bump == "publish":
        return cmd_publish(args.tag)

    check_clean_tree()
    run_release_validation()

    current = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))["version"] if SKILLS_JSON.exists() else "0.0.0"
    bump = args.bump
    if bump == "auto":
        prev_tag = get_previous_tag()
        log = run(["git", "log", f"{prev_tag}..HEAD"] if prev_tag else ["git", "log"]).stdout
        bump = "major" if re.search(r"feat!:|BREAKING CHANGE", log) else "minor" if "feat" in log else "patch"
    new_version = bump_version(current, bump)
    tag = f"v{new_version}"
    info(f"Version: {current} → {new_version}  |  Tag: {tag}")

    if args.dry_run:
        info("[dry-run] stopping before any file writes")
        return 0

    update_skills_json(new_version)
    prev_tag = get_previous_tag()
    update_changelog(new_version, prev_tag)
    skill_count = len(extract_skills())
    git_commit_and_tag(new_version, tag, skill_count, dry_run=False)

    print("\nPush when confirmed, then publish:")
    print(f"  git push origin main && git push origin {tag}")
    print(f"  python3 scripts/release.py publish {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
