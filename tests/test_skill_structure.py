import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "zmq-project-management"


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter_and_size(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        frontmatter = skill.split("---", 2)[1]
        keys = {line.split(":", 1)[0] for line in frontmatter.splitlines()
                if line.strip() and not line.startswith(" ")}
        self.assertEqual(keys, {"name", "description", "metadata"})
        self.assertIn("name: zmq-project-management", frontmatter)
        self.assertLess(len(skill.splitlines()), 500)

    def test_all_markdown_relative_references_resolve_within_package(self):
        for document in SKILL_ROOT.rglob("*.md"):
            for relative in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if "://" in relative or relative.startswith("#"):
                    continue
                target = (document.parent / relative.split("#", 1)[0]).resolve()
                self.assertTrue(target.is_relative_to(SKILL_ROOT.resolve()), str(target))
                self.assertTrue(target.exists(), f"{document}: {relative}")

    def test_openai_metadata(self):
        metadata = (SKILL_ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            self.assertIn(key, metadata)
        self.assertIn("$zmq-project-management", metadata)


if __name__ == "__main__":
    unittest.main()
