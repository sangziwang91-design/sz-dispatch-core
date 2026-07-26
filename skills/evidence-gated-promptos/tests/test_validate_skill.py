from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_skill", ROOT / "scripts" / "validate_skill.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillValidationTests(unittest.TestCase):
    def test_repository_skill_is_valid(self) -> None:
        self.assertEqual(MODULE.validate(ROOT), [])

    def test_invalid_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Bad_Name"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: Bad_Name\ndescription: test\n---\n", encoding="utf-8"
            )
            errors = MODULE.validate(root)
            self.assertTrue(any("name must" in error for error in errors))

    def test_missing_frontmatter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "missing-frontmatter"
            root.mkdir()
            (root / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
            errors = MODULE.validate(root)
            self.assertIn("SKILL.md must start with YAML frontmatter", errors)


if __name__ == "__main__":
    unittest.main()
