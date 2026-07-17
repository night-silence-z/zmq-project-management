#!/usr/bin/env python3
"""口径/禁用词一致性扫描器（zmq-project-management）

对应 SKILL.md 第 6 节"交付前机器扫描"：从权威源文件中读取禁用词表，
扫描产出目录，报告所有命中位置。定义只在权威源出现一次，产出只引用——
本脚本负责抓"旧口径/禁用词残留"这类机器可查的漂移。

用法:
    python check_terms.py --authority 00_管理/术语与红线.md --target 01_产出
    python check_terms.py --authority 00_管理/口径字典.md --target 01_产出 --ext .md .html

权威源约定: 文件中包含表头含「禁用词」和「应使用」两列的 Markdown 表格，例如:

    | 禁用词 | 应使用 |
    | -- | -- |
    | 诊断分 | （不引入该指标，用行为/转化口径直接解释） |
    | 自然渠道 | 自然流量 |

行为:
    - 递归扫描 target 下的文本文件（默认 .md/.html/.txt），报告 文件:行号 与命中词。
    - 默认跳过归档与历史目录（99_归档、历史），旧版本合法保留旧口径；
      加 --include-archived 可强制包含。
    - 有命中 -> 退出码 1（可接入 CI）；无命中 -> 退出码 0。

仅用标准库，Python 3.8+。
"""

import argparse
import pathlib
import sys

DEFAULT_EXTS = [".md", ".html", ".txt"]
SKIP_DIR_KEYWORDS = ["99_归档", "历史", ".git", "node_modules"]


def parse_forbidden_table(authority: pathlib.Path):
    """从权威源提取 (禁用词, 应使用) 列表。"""
    rows = []
    in_table, term_idx, repl_idx = False, None, None
    for raw in authority.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("|") and "禁用词" in line:
            headers = [c.strip() for c in line.strip("|").split("|")]
            if "禁用词" in headers:
                term_idx = headers.index("禁用词")
                repl_idx = headers.index("应使用") if "应使用" in headers else None
                in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):  # 分隔行
                continue
            if term_idx is not None and term_idx < len(cells) and cells[term_idx]:
                repl = cells[repl_idx] if repl_idx is not None and repl_idx < len(cells) else ""
                rows.append((cells[term_idx], repl))
    return rows


def iter_target_files(target: pathlib.Path, exts, include_archived: bool):
    if target.is_file():
        yield target
        return
    for p in sorted(target.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if not include_archived and any(k in str(p) for k in SKIP_DIR_KEYWORDS):
            continue
        yield p


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="扫描产出中的禁用词/旧口径残留")
    ap.add_argument("--authority", required=True, help="权威源文件（含'禁用词|应使用'表）")
    ap.add_argument("--target", required=True, help="要扫描的文件或目录")
    ap.add_argument("--ext", nargs="*", default=DEFAULT_EXTS, help="扫描的扩展名，默认 .md .html .txt")
    ap.add_argument("--include-archived", action="store_true", help="包含 99_归档/历史 目录（默认跳过）")
    args = ap.parse_args()

    authority = pathlib.Path(args.authority)
    target = pathlib.Path(args.target)
    if not authority.is_file():
        print(f"[错误] 权威源不存在: {authority}")
        return 2
    if not target.exists():
        print(f"[错误] 扫描目标不存在: {target}")
        return 2

    forbidden = parse_forbidden_table(authority)
    if not forbidden:
        print(f"[提示] 权威源中未找到'禁用词|应使用'表，无可扫描项: {authority}")
        return 0

    exts = [e.lower() if e.startswith(".") else "." + e.lower() for e in args.ext]
    hits = 0
    for f in iter_target_files(target, exts, args.include_archived):
        if f.resolve() == authority.resolve():
            continue  # 权威源自身合法包含禁用词
        for lineno, line in enumerate(
            f.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for term, repl in forbidden:
                if term in line:
                    hits += 1
                    tip = f"（应使用：{repl}）" if repl else ""
                    print(f"{f}:{lineno}: 命中禁用词「{term}」{tip}")
                    print(f"    {line.strip()[:120]}")

    print("-" * 40)
    if hits:
        print(f"共 {hits} 处命中，需清理后再交付。")
        return 1
    print(f"通过：{len(forbidden)} 个禁用词，0 命中。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
