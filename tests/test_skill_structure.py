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
        keys = [
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if line.strip() and not line.startswith(" ")
        ]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("name: zmq-project-management", frontmatter)
        self.assertLess(len(skill.splitlines()), 500)

    def test_relative_references_exist(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        references = re.findall(r"\]\(([^)]+)\)", skill)
        for relative in references:
            if "://" in relative:
                continue
            self.assertTrue((SKILL_ROOT / relative).exists(), relative)

    def test_no_legacy_mandatory_close_language(self):
        package_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in SKILL_ROOT.rglob("*.md")
        )
        self.assertNotIn("每次收工必须更新", package_text)
        self.assertNotIn("没落进台账的内容等于没发生", package_text)

    def test_openai_metadata(self):
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("display_name:", metadata)
        self.assertIn("$zmq-project-management", metadata)


if __name__ == "__main__":
    unittest.main()
