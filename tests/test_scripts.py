import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "zmq-project-management"
INIT = SKILL_ROOT / "scripts" / "init_project.py"
HEALTH = SKILL_ROOT / "scripts" / "health_check.py"
TERMS = SKILL_ROOT / "scripts" / "check_terms.py"


def run_script(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


class ScriptTests(unittest.TestCase):
    def test_minimal_scaffold_creates_no_empty_delivery_dirs(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_script(INIT, "demo", "--base", temp, "--bootstrap", "none")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            root = pathlib.Path(temp) / "demo"
            self.assertTrue((root / "00_管理" / "README.md").is_file())
            self.assertTrue((root / "00_管理" / "台账.md").is_file())
            self.assertFalse((root / "01_产出").exists())
            self.assertFalse((root / "02_输入").exists())
            self.assertFalse((root / "99_归档").exists())

    def test_profile_and_full_scaffold(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_script(
                INIT,
                "analysis",
                "--base",
                temp,
                "--type",
                "分析",
                "--full",
                "--bootstrap",
                "agents",
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            root = pathlib.Path(temp) / "analysis"
            self.assertTrue((root / "00_管理" / "口径字典.md").is_file())
            self.assertTrue((root / "01_产出").is_dir())
            self.assertTrue((root / "AGENTS.md").is_file())
            self.assertFalse((root / "CLAUDE.md").exists())

    def test_health_check_accepts_empty_frozen_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            create = run_script(INIT, "demo", "--base", temp, "--bootstrap", "none")
            self.assertEqual(create.returncode, 0)
            result = run_script(HEALTH, pathlib.Path(temp) / "demo")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_health_check_reports_missing_pointer_target(self):
        with tempfile.TemporaryDirectory() as temp:
            create = run_script(INIT, "demo", "--base", temp, "--bootstrap", "none")
            self.assertEqual(create.returncode, 0)
            root = pathlib.Path(temp) / "demo"
            readme = root / "00_管理" / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace(
                "| -- | -- | -- | -- |\n\n## 权威源",
                "| -- | -- | -- | -- |\n"
                "| 报告 | 01_产出/报告-v1.md | 已定稿 | — |\n\n## 权威源",
            )
            readme.write_text(text, encoding="utf-8")
            result = run_script(HEALTH, root, "--level", "milestone")
            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("不存在", result.stdout)

    def test_term_scanner_detects_forbidden_term(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            authority = root / "authority.md"
            target = root / "output.md"
            authority.write_text(
                "| 禁用词 | 应使用 |\n| -- | -- |\n| 旧称 | 新称 |\n",
                encoding="utf-8",
            )
            target.write_text("这里仍然使用旧称。\n", encoding="utf-8")
            result = run_script(
                TERMS, "--authority", authority, "--target", target
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("旧称", result.stdout)


if __name__ == "__main__":
    unittest.main()
