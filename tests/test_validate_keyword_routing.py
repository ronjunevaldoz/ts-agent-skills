from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import REPO_ROOT, load_module

validate_keyword_routing = load_module(
    "validate_keyword_routing",
    REPO_ROOT / "skills" / "ts-expert" / "scripts" / "validate_keyword_routing.py",
)


def _write(root: Path, rel_path: str, content: str) -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ValidateKeywordRoutingTests(unittest.TestCase):
    def test_flags_missing_trigger_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "skills/ts-foo/SKILL.md", "No trigger line here.\n")
            errors = validate_keyword_routing.validate_keyword_routing(root)
            self.assertTrue(any("missing" in e for e in errors))

    def test_passes_with_trigger_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "skills/ts-foo/SKILL.md", "**Trigger keywords:** foo, bar.\n\nBody.\n")
            self.assertEqual(validate_keyword_routing.validate_keyword_routing(root), [])

    def test_flags_alternative_pair_keyword_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "skills/ts-a/SKILL.md", "**Trigger keywords:** shared, unique-a.\n\nBody.\n")
            _write(
                root, "skills/ts-b/SKILL.md",
                "**Trigger keywords:** shared, unique-b.\n\nAlternative to `ts-a`.\n",
            )
            errors = validate_keyword_routing.validate_keyword_routing(root)
            self.assertTrue(any("share trigger keywords" in e for e in errors))

    def test_validates_the_real_repo(self) -> None:
        errors = validate_keyword_routing.validate_keyword_routing(REPO_ROOT)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
