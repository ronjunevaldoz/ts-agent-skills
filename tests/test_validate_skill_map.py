from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, load_module

validate_skill_map = load_module(
    "validate_skill_map", REPO_ROOT / "skills" / "ts-expert" / "scripts" / "validate_skill_map.py"
)


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_repo(root: Path) -> None:
    _write(root, "skills/ts-foo/SKILL.md", "foo")
    _write(root, "skills/ts-bar/SKILL.md", "bar")
    _write(
        root, "skills/ts-expert/SKILL.md",
        "## The 3 Skills and What They Own\n\nts-foo, ts-bar, ts-expert\n",
    )
    _write(root, "README.md", "ts-foo ts-bar ts-expert\n3 skills covering the stack.\n")


class ValidateSkillMapTests(unittest.TestCase):
    def test_passes_on_a_consistent_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_repo(root)
            self.assertEqual(validate_skill_map.validate_skill_map(root), [])

    def test_flags_header_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_repo(root)
            _write(root, "skills/ts-expert/SKILL.md", "## The 99 Skills and What They Own\n")
            errors = validate_skill_map.validate_skill_map(root)
            self.assertTrue(any("declares 99 skills but repo has 3" in e for e in errors))

    def test_flags_stale_count_phrase_in_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_repo(root)
            _write(root, "README.md", "ts-foo ts-bar ts-expert\n2 skills covering the stack.\n")
            errors = validate_skill_map.validate_skill_map(root)
            self.assertTrue(any("missing the current count phrase" in e for e in errors))

    def test_validates_the_real_repo(self) -> None:
        errors = validate_skill_map.validate_skill_map(REPO_ROOT)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
