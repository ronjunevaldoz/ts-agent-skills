from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, load_module

scan = load_module("scan_skill_issues", REPO_ROOT / "scripts" / "scan_skill_issues.py")


class ScanSkillIssuesTests(unittest.TestCase):
    def test_flags_oversized_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "ts-example"
            skill_dir.mkdir(parents=True)
            body = "---\nname: ts-example\ndescription: x\n---\n\n" + "line\n" * 510
            (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
            findings = scan.scan_skill(skill_dir)
            self.assertTrue(any(f["check"] == "oversized_skill_md" for f in findings))

    def test_ignores_skill_under_the_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "ts-example"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: ts-example\ndescription: x\n---\n\nBody.\n", encoding="utf-8"
            )
            findings = scan.scan_skill(skill_dir)
            self.assertEqual(findings, [])

    def test_flags_invalid_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "TS_Example"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: TS_Example\ndescription: x\n---\n\nBody.\n", encoding="utf-8"
            )
            findings = scan.scan_skill(skill_dir)
            self.assertTrue(any(f["check"] == "invalid_name" for f in findings))

    def test_flags_long_procedural_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "ts-example"
            skill_dir.mkdir(parents=True)
            long_step = "1. " + " ".join(["word"] * 25) + "\n"
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: ts-example\ndescription: x\n---\n\n{long_step}", encoding="utf-8"
            )
            findings = scan.scan_skill(skill_dir)
            self.assertTrue(any(f["check"] == "long_procedural_step" for f in findings))

    def test_scan_all_against_real_repo_is_clean(self) -> None:
        report = scan.scan_all()
        self.assertEqual(report["blocking_issues"], 0, report["findings"])


if __name__ == "__main__":
    unittest.main()
