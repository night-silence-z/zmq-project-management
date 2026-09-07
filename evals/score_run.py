#!/usr/bin/env python3
"""比较 eval 的 before/after，并检查反过度治理约束。"""

import argparse
import fnmatch
import hashlib
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_MANAGEMENT_PREFIXES = ("00_管理/", "01_产出/执行计划/", "03_验收记录/")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def load_case(case_id):
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    for case in cases:
        if case["id"] == case_id:
            return case
    raise KeyError(case_id)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="评分三级治理行为 eval")
    parser.add_argument("--case", required=True, help="场景 ID，如 S2")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--response", help="代理实际回复/对话转录文件；行为判断仍需人工审阅")
    args = parser.parse_args()

    case = load_case(args.case)
    rules = case.get("rules", {})
    before_root = pathlib.Path(args.before).resolve()
    after_root = pathlib.Path(args.after).resolve()
    if not before_root.is_dir() or not after_root.is_dir():
        parser.error("before 和 after 必须是存在的场景目录")
    before = snapshot(before_root)
    after = snapshot(after_root)

    paths = set(before) | set(after)
    changed = sorted(path for path in paths if before.get(path) != after.get(path))
    new = sorted(path for path in after if path not in before)
    failures = []

    for path in rules.get("required_changed", []):
        if path not in changed or path not in after:
            failures.append(f"应修改但未修改：{path}")
    for path in rules.get("required_unchanged", []):
        if path in changed or path not in before or path not in after:
            failures.append(f"应保持不变且存在：{path}")

    if rules.get("response_required"):
        response = pathlib.Path(args.response) if args.response else None
        if not response or not response.is_file() or not response.read_text(encoding="utf-8").strip():
            failures.append("缺少实际回复/对话转录，无法审阅交付或澄清行为")

    for check in rules.get("artifact_checks", []):
        path = after_root / check["path"]
        if not path.is_file():
            failures.append(f"缺少产物：{check['path']}")
            continue
        content = path.read_text(encoding="utf-8")
        for fragment in check.get("contains", []):
            if fragment not in content:
                failures.append(f"产物缺少结果 {fragment!r}：{check['path']}")
        for fragment in check.get("absent", []):
            if fragment in content:
                failures.append(f"产物仍含已失效内容 {fragment!r}：{check['path']}")
        cursor = 0
        for fragment in check.get("ordered", []):
            found = content.find(fragment, cursor)
            if found < 0:
                failures.append(f"产物顺序不符 {fragment!r}：{check['path']}")
                break
            cursor = found + len(fragment)

    for prefix in rules.get("forbidden_changed_prefixes", []):
        for path in changed:
            if path.startswith(prefix.rstrip("/") + "/") or path == prefix.rstrip("/"):
                failures.append(f"禁止修改范围：{path}")

    for prefix in rules.get("forbidden_new_prefixes", []):
        for path in new:
            if path.startswith(prefix.rstrip("/") + "/") or path == prefix.rstrip("/"):
                failures.append(f"禁止新增范围：{path}")

    for pattern in rules.get("forbidden_new_globs", []):
        for path in new:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(pathlib.PurePosixPath(path).name, pattern):
                failures.append(f"禁止新增文件：{path}")

    management_prefixes = tuple(
        rules.get("management_prefixes", DEFAULT_MANAGEMENT_PREFIXES)
    )
    management_changes = [
        path for path in changed if path.startswith(management_prefixes)
    ]
    maximum = rules.get("max_management_changes")
    if maximum is not None and len(management_changes) > maximum:
        failures.append(
            f"管理文件触碰 {len(management_changes)} 个，超过上限 {maximum}："
            + ", ".join(management_changes)
        )

    result = {
        "case": case["id"],
        "review_reference_mode": case["expected_mode"],
        "machine_checks_passed": not failures,
        "behavior_review": "required: review actual response, artifacts and tool trace",
        "changed": changed,
        "new": new,
        "management_changes": management_changes,
        "failures": failures,
        "review_expectations": case["review_expectations"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
