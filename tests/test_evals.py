import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "evals/build_fixtures.py"
SCORE = ROOT / "evals/score_run.py"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True,
                          text=True, encoding="utf-8", check=False)


class EvalToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = pathlib.Path(self.temp.name)
        result = run(BUILD, "--output", self.output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def score(self, case):
        root = self.output / case
        return run(SCORE, "--case", case, "--before", root / "before", "--after", root / "after")

    def test_cases_have_unique_ids_and_built_fixtures(self):
        cases = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for case in cases:
            self.assertTrue((self.output / case["id"] / "after").is_dir())

    def test_noop_and_deletion_do_not_pass_edit_task(self):
        self.assertEqual(self.score("S2").returncode, 1)
        (self.output / "S2/after/工作稿.md").unlink()
        self.assertEqual(self.score("S2").returncode, 1)

    def test_unrelated_change_does_not_fake_task_completion(self):
        target = self.output / "S2/after/工作稿.md"
        target.write_text(target.read_text(encoding="utf-8") + "\n无关句子。", encoding="utf-8")
        self.assertEqual(self.score("S2").returncode, 1)

    def test_completed_routine_edit_passes_machine_checks(self):
        target = self.output / "S2/after/工作稿.md"
        target.write_text("# 工作稿\n\n## 一、结论\n\n## 二、方法\n\n[来源](source.md)\n", encoding="utf-8")
        result = self.score("S2")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("required: review", result.stdout)

    def test_baseline_noop_fails(self):
        result = self.score("S3")
        self.assertEqual(result.returncode, 1)
        self.assertIn("应修改但未修改", result.stdout)

    def test_missing_response_does_not_pass_conversation_task(self):
        self.assertEqual(self.score("S8").returncode, 1)

    def test_output_directory_is_not_overwritten(self):
        marker = self.output / "keep.txt"
        marker.write_text("retain", encoding="utf-8")
        result = run(BUILD, "--output", self.output)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(marker.read_text(), "retain")

    def test_numeric_case_has_actual_inputs_and_correct_result_requirement(self):
        self.assertTrue((self.output / "S5/after/data.csv").is_file())
        self.assertEqual(self.score("S5").returncode, 1)
        target = self.output / "S5/after/当前材料.md"
        target.write_text("# 当前材料\n\n汇总值：110\n", encoding="utf-8")
        self.assertEqual(self.score("S5").returncode, 0)

    def test_evidence_fixture_hash_matches_written_bytes(self):
        root = self.output / "S11/after"
        digest = hashlib.sha256((root / "demo.html").read_bytes()).hexdigest()
        self.assertIn(digest, (root / "验证记录.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
