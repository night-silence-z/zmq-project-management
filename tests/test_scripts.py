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
            result = run_script(INIT, "demo", "--base", temp)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            root = pathlib.Path(temp) / "demo"
            self.assertTrue((root / "00_管理" / "README.md").is_file())
            self.assertTrue((root / "00_管理" / "台账.md").is_file())
            self.assertFalse((root / "01_产出").exists())
            self.assertFalse((root / "02_输入").exists())
            self.assertFalse((root / "99_归档").exists())
            self.assertFalse((root / "AGENTS.md").exists())
            self.assertFalse((root / "CLAUDE.md").exists())

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


    def test_initializer_rejects_escape_and_nonempty_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(run_script(INIT, "../escape", "--base", temp).returncode, 2)
            root = pathlib.Path(temp) / "existing"
            root.mkdir()
            (root / "user.md").write_text("keep", encoding="utf-8")
            self.assertEqual(run_script(INIT, "existing", "--base", temp).returncode, 2)
            self.assertEqual((root / "user.md").read_text(), "keep")

    def test_generic_authority_title(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(run_script(INIT, "demo", "--base", temp, "--type", "通用").returncode, 0)
            text = (pathlib.Path(temp) / "demo/00_管理/基线说明.md").read_text(encoding="utf-8")
            self.assertIn("基线说明", text)
            self.assertNotIn("{{", text)

    def test_health_uses_custom_index_without_requiring_ledger(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "index.md").write_text("# Existing index\n", encoding="utf-8")
            result = run_script(HEALTH, root, "--readme", "index.md")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_health_does_not_scan_unrelated_markdown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "index.md").write_text("# index", encoding="utf-8")
            (root / "unrelated.md").write_text("| a |\n\n| b |\n", encoding="utf-8")
            result = run_script(HEALTH, root, "--readme", "index.md")
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("表格行间", result.stdout)
            result = run_script(HEALTH, root, "--readme", "index.md", "--target", "unrelated.md")
            self.assertIn("表格行间", result.stdout)
            self.assertEqual(run_script(HEALTH, root, "--readme", "index.md", "--target", ".").returncode, 2)

    def test_health_allows_distinct_reports_and_external_pointer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            current = root / "01_产出/当前"
            current.mkdir(parents=True)
            for name in ("A", "B"):
                (current / (name + ".md")).write_text(name, encoding="utf-8")
            (root / "ledger.md").write_text("# ledger", encoding="utf-8")
            (root / "index.md").write_text(
                "| 产出物线 | 当前版文件 | 状态 | 对应关系 |\n| -- | -- | -- | -- |\n"
                "| A | [报告A](01_产出/当前/A.md) | 草稿待试用 | — |\n"
                "| B | 01_产出/当前/B.md | 已核对来源 | — |\n"
                "| C | https://example.com/report | 已交付 | — |\n", encoding="utf-8")
            result = run_script(HEALTH, root, "--readme", "index.md", "--ledger", "ledger.md", "--level", "milestone")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("[警告]", result.stdout)
            self.assertIn("未验证可访问性", result.stdout)

    def test_health_reports_duplicate_current_pointer_for_same_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "A.md").write_text("A", encoding="utf-8")
            (root / "index.md").write_text(
                "| 产出物线 | 当前版文件 | 状态 | 对应关系 |\n| -- | -- | -- | -- |\n"
                "| A | A.md | 草稿 | — |\n| A | A.md | 草稿 | — |\n", encoding="utf-8")
            result = run_script(HEALTH, root, "--readme", "index.md")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("重复当前指针", result.stdout)


if __name__ == "__main__":
    unittest.main()
