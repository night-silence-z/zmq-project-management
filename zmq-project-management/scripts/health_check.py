#!/usr/bin/env python3
"""检查显式治理指针；不递归扫描项目，也不判断业务或用户验收。"""

import argparse
import pathlib
import re
import sys
from urllib.parse import unquote


def parse_table_rows(lines, required_headers):
    required = set(required_headers)
    for index, raw in enumerate(lines):
        headers = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if not raw.strip().startswith("|") or not required.issubset(headers):
            continue
        rows = []
        for following in lines[index + 1:]:
            if not following.strip().startswith("|"):
                break
            cells = [cell.strip() for cell in following.strip().strip("|").split("|")]
            if all(set(cell) <= set("-: ") for cell in cells):
                continue
            rows.append(dict(zip(headers, cells)))
        return rows
    return []


def resolve_file(root, value):
    path = pathlib.Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def pointer_target(cell):
    # 指针表可用裸路径或一个 Markdown 链接；路径以项目根为准。
    match = re.fullmatch(r"\[[^\]]*\]\((.+)\)", cell)
    return (match.group(1) if match else cell).strip().strip("<>").strip("`")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="项目根目录")
    parser.add_argument("--readme", default="00_管理/README.md", help="入口路径，相对项目根或绝对路径")
    parser.add_argument("--ledger", default="00_管理/台账.md", help="台账路径，仅 milestone 读取")
    parser.add_argument("--level", choices=("structure", "milestone"), default="structure")
    parser.add_argument("--target", action="append", default=[], help="可重复指定需要格式检查的文件；不接受目录")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    readme = resolve_file(root, args.readme)
    ledger = resolve_file(root, args.ledger)
    targets = [resolve_file(root, item) for item in args.target]
    required = [readme, *targets] + ([ledger] if args.level == "milestone" else [])
    missing = [path for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[无法检查] 不是可读文件：{path}")
        print("请指定实际入口/台账/文件；不采用此结构不表示项目有问题。")
        return 2

    errors, warnings, infos = [], [], []
    rows = parse_table_rows(readme.read_text(encoding="utf-8-sig").splitlines(),
                            ("产出物线", "当前版文件", "状态", "对应关系"))
    if not rows:
        infos.append("没有可解析的冻结指针；未检查其他索引结构。")
    seen = set()
    for row in rows:
        name = row.get("产出物线", "").strip()
        cell = row.get("当前版文件", "").strip()
        if not name and not cell:
            continue
        if name in seen and name not in ("", "—", "-"):
            errors.append(f"『{name}』有重复当前指针；请明确成果线或组合交付关系。")
        seen.add(name)
        if cell in ("", "—", "-"):
            continue
        target = pointer_target(cell)
        if target.startswith(("https://", "http://")):
            infos.append(f"『{name}』是外部链接，未验证可访问性。")
            continue
        # 不把其他 URI 误判成本地路径；保留 Windows 盘符。
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) and not re.match(r"^[a-zA-Z]:[/\\]", target):
            infos.append(f"『{name}』使用外部 URI，未验证可访问性。")
            continue
        local = unquote(target.split("#", 1)[0])
        if not local or not resolve_file(root, local).is_file():
            errors.append(f"『{name}』指向的文件不存在：{cell}")
        if not row.get("状态", "").strip():
            warnings.append(f"『{name}』未说明交付状态。")

    if args.level == "milestone":
        pending = parse_table_rows(ledger.read_text(encoding="utf-8-sig").splitlines(),
                                   ("编号", "事项", "决策人", "截止条件", "默认方案", "影响范围"))
        active = [row for row in pending if row.get("事项", "").strip() not in ("", "—", "-")]
        if active:
            warnings.append(f"仍有 {len(active)} 个待确认项；需判断是否影响本次关口。")

    # 格式检查仅覆盖显式目标；不会因为收口扫描全部 Markdown。
    for path in dict.fromkeys(targets):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for index in range(len(lines) - 2):
            if (lines[index].strip().startswith("|") and not lines[index + 1].strip()
                    and lines[index + 2].strip().startswith("|")):
                warnings.append(f"{path}:{index + 2} 表格行间存在空行。")
                break

    for label, messages in (("错误", errors), ("警告", warnings), ("提示", infos)):
        for message in messages:
            print(f"[{label}] {message}")
    print(f"指针/结构检查完成：{len(errors)} 错误 / {len(warnings)} 警告；不代表业务验收。")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
