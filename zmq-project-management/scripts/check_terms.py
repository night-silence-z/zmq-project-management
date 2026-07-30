#!/usr/bin/env python3
"""扫描当前材料中的禁用词或旧定义残留。

仅在相关权威源变化或正式交付时按需运行，不作为日常收尾动作。
"""

import argparse
import pathlib
import sys


DEFAULT_EXTENSIONS = [".md", ".html", ".txt"]
SKIP_PARTS = {"99_归档", "历史", ".git", "node_modules"}


def parse_forbidden_table(authority):
    rows = []
    headers = None
    for raw in authority.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("|") and "禁用词" in line:
            headers = [cell.strip() for cell in line.strip("|").split("|")]
            continue
        if headers is None:
            continue
        if not line.startswith("|"):
            headers = None
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        term_index = headers.index("禁用词")
        replacement_index = headers.index("应使用") if "应使用" in headers else None
        if term_index < len(cells) and cells[term_index]:
            replacement = (
                cells[replacement_index]
                if replacement_index is not None and replacement_index < len(cells)
                else ""
            )
            rows.append((cells[term_index], replacement))
    return rows


def iter_files(target, extensions, include_archived):
    candidates = [target] if target.is_file() else sorted(target.rglob("*"))
    for path in candidates:
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        if not include_archived and any(part in SKIP_PARTS for part in path.parts):
            continue
        yield path


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="扫描禁用词和旧定义残留")
    parser.add_argument("--authority", required=True, help="含禁用词表的权威源")
    parser.add_argument("--target", required=True, help="要扫描的当前材料")
    parser.add_argument("--ext", nargs="*", default=DEFAULT_EXTENSIONS)
    parser.add_argument("--include-archived", action="store_true")
    args = parser.parse_args()

    authority = pathlib.Path(args.authority).resolve()
    target = pathlib.Path(args.target).resolve()
    if not authority.is_file():
        print(f"[错误] 权威源不存在：{authority}")
        return 2
    if not target.exists():
        print(f"[错误] 扫描目标不存在：{target}")
        return 2

    forbidden = parse_forbidden_table(authority)
    if not forbidden:
        print(f"[提示] 未找到“禁用词｜应使用”表：{authority}")
        return 0

    extensions = {
        extension.lower() if extension.startswith(".") else "." + extension.lower()
        for extension in args.ext
    }
    hits = 0
    for path in iter_files(target, extensions, args.include_archived):
        if path.resolve() == authority:
            continue
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for term, replacement in forbidden:
                if term in line:
                    hits += 1
                    tip = f"；应使用：{replacement}" if replacement else ""
                    print(f"{path}:{line_number}: 命中「{term}」{tip}")

    if hits:
        print(f"共 {hits} 处命中。")
        return 1
    print(f"通过：检查 {len(forbidden)} 个禁用词，0 命中。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
