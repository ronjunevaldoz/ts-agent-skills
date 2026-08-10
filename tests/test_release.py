from __future__ import annotations

import unittest

from _helpers import REPO_ROOT, load_module

release = load_module("release", REPO_ROOT / "scripts" / "release.py")


class BumpVersionTests(unittest.TestCase):
    def test_patch(self) -> None:
        self.assertEqual(release.bump_version("1.2.3", "patch"), "1.2.4")

    def test_minor_resets_patch(self) -> None:
        self.assertEqual(release.bump_version("1.2.3", "minor"), "1.3.0")

    def test_major_resets_minor_and_patch(self) -> None:
        self.assertEqual(release.bump_version("1.2.3", "major"), "2.0.0")


class ExtractSkillsTests(unittest.TestCase):
    def test_extracts_every_real_skill(self) -> None:
        skills = release.extract_skills()
        names = {s["name"] for s in skills}
        self.assertIn("ts-expert", names)
        self.assertIn("ts-project-foundation", names)
        self.assertEqual(len(skills), 16)


if __name__ == "__main__":
    unittest.main()
