import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "evals" / "build_fixtures.py"
SCORE = ROOT / "evals" / "score_run.py"


class EvalToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        result = subprocess.run(
            [sys.executable, str(BUILD)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode:
            raise AssertionError(result.stderr + result.stdout)

    def test_cases_are_cross_domain_and_machine_readable(self):
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 7)
        self.assertEqual({case["expected_mode"] for case in cases}, {
            "无需建档",
            "轻量日常迭代",
            "项目基线变化",
            "轻量日常迭代＋强化验证",
            "里程碑收口",
        })

    def test_unchanged_routine_fixture_passes_file_constraints(self):
        case = ROOT / "evals" / "generated" / "S2"
        result = subprocess.run(
            [
                sys.executable,
                str(SCORE),
                "--case",
                "S2",
                "--before",
                str(case / "before"),
                "--after",
                str(case / "after"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_baseline_fixture_requires_authority_and_ledger_changes(self):
        case = ROOT / "evals" / "generated" / "S3"
        result = subprocess.run(
            [
                sys.executable,
                str(SCORE),
                "--case",
                "S3",
                "--before",
                str(case / "before"),
                "--after",
                str(case / "after"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("应修改但未修改", result.stdout)


if __name__ == "__main__":
    unittest.main()
