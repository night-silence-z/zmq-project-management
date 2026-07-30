#!/usr/bin/env python3
"""检查项目治理结构；仅在里程碑时执行完整检查。"""

import argparse
import pathlib
import sys


LADDER_WORDS = [
    "探索",
    "候选",
    "已定稿",
    "已定义",
    "进行中",
    "受阻",
    "本地通过",
    "验证通过",
    "测试环境通过",
    "已交付",
    "已上线验收",
]
SKIP_PARTS = {"99_归档", "历史", ".git", "node_modules"}


def parse_table_rows(lines, required_headers):
    required = set(required_headers)
    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        headers = [cell.strip() for cell in line.strip("|").split("|")]
        if not required.issubset(headers):
            continue
        rows = []
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if not stripped.startswith("|"):
                break
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(set(cell) <= set("-: ") for cell in cells):
                continue
            rows.append(dict(zip(headers, cells)))
        return rows
    return []


def has_skipped_part(path):
    return any(part in SKIP_PARTS for part in path.parts)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="检查 zmq-project-management 项目结构")
    parser.add_argument("root", help="项目根目录")
    parser.add_argument(
        "--level",
        choices=("structure", "milestone"),
        default="structure",
        help="structure 检查基础结构；milestone 增加冻结版本与待确认检查",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    readme = root / "00_管理" / "README.md"
    ledger = root / "00_管理" / "台账.md"
    missing = [path for path in (readme, ledger) if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[错误] 缺少治理文件：{path}")
        return 2

    errors, warnings, infos = [], [], []
    readme_lines = readme.read_text(encoding="utf-8", errors="replace").splitlines()
    pointer_rows = parse_table_rows(
        readme_lines, ("产出物线", "当前版文件", "状态", "对应关系")
    )

    if not pointer_rows:
        infos.append("冻结交付物指针为空；尚无冻结交付物时属正常。")

    for row in pointer_rows:
        line_name = row.get("产出物线", "?")
        file_cell = row.get("当前版文件", "")
        status = row.get("状态", "")
        if file_cell and file_cell not in ("—", "-"):
            target = root / file_cell.replace("\\", "/")
            if not target.exists():
                errors.append(f"『{line_name}』指向的文件不存在：{file_cell}")
        if status and not any(word in status for word in LADDER_WORDS):
            warnings.append(f"『{line_name}』状态不可观察：{status}")

    if args.level == "milestone":
        produce = root / "01_产出"
        if produce.is_dir():
            current_dirs = [
                path for path in produce.rglob("当前") if path.is_dir() and not has_skipped_part(path)
            ]
            for current in current_dirs:
                files = [path for path in current.iterdir() if path.is_file()]
                if len(files) > 1:
                    warnings.append(
                        f"{current.relative_to(root)} 有 {len(files)} 个文件；"
                        "若它们属于同一产出物线，请裁决唯一当前版。"
                    )

        ledger_lines = ledger.read_text(encoding="utf-8", errors="replace").splitlines()
        pending_rows = parse_table_rows(
            ledger_lines, ("编号", "事项", "决策人", "截止条件", "默认方案", "影响范围")
        )
        if pending_rows:
            warnings.append(f"仍有 {len(pending_rows)} 个待确认项；收口时需逐项说明去向。")

    for path in sorted(root.rglob("*.md")):
        if has_skipped_part(path):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index in range(len(lines) - 2):
            if (
                lines[index].strip().startswith("|")
                and not lines[index + 1].strip()
                and lines[index + 2].strip().startswith("|")
            ):
                warnings.append(f"{path.relative_to(root)}:{index + 2} 表格行间存在空行。")
                break

    for message in errors:
        print(f"[错误] {message}")
    for message in warnings:
        print(f"[警告] {message}")
    for message in infos:
        print(f"[提示] {message}")
    print("-" * 40)
    print(f"检查完成：{len(errors)} 错误 / {len(warnings)} 警告 / {len(infos)} 提示")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
