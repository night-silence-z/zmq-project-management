#!/usr/bin/env python3
"""项目健康检查（zmq-project-management）

对应 SKILL.md 第 9 节：把一致性收口中"确定性可查"的部分下沉为脚本——
指针表指向、当前版唯一性、台账扫描水位、表格空行。语义级不一致仍由整体扫描兜底。

用法:
    python health_check.py 项目根目录 [--stale 20]

检查项:
    [错误] 00_管理/README.md 或 台账.md 缺失
    [错误] 指针表中"当前版文件"指向的文件不存在
    [警告] 指针表"状态"列出现阶梯词之外的表述（如"差不多好了"）
    [警告] 某产出物线的 当前/ 目录中文件数 > 1（当前版应唯一）
    [提示] 台账迭代记录数 - 扫描水位 >= --stale（默认 20）→ 该做整体扫描了
    [警告] Markdown 表格行间出现空行（飞书同步会断裂）——跳过 99_归档/历史

退出码: 有[错误]→1；仅警告/提示→0；结构缺失无法检查→2。
仅用标准库，Python 3.8+。
"""

import argparse
import pathlib
import re
import sys

LADDER_WORDS = ["探索", "候选", "已定稿", "已交付", "已定义", "本地通过", "测试环境通过", "已上线验收"]
SKIP_KEYWORDS = ["99_归档", "历史", ".git", "node_modules"]


def parse_table_rows(lines, header_keyword):
    """返回表头含 header_keyword 的表格的数据行（cells 列表的列表）。"""
    rows, in_table, headers = [], False, []
    for ln in lines:
        s = ln.strip()
        if s.startswith("|") and header_keyword in s and not in_table:
            headers = [c.strip() for c in s.strip("|").split("|")]
            in_table = True
            continue
        if in_table:
            if not s.startswith("|"):
                break
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
    return headers, rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="按 zmq-project-management 规范体检项目")
    ap.add_argument("root", help="项目根目录")
    ap.add_argument("--stale", type=int, default=20, help="扫描水位滞后阈值（默认 20 条）")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    errors, warns, infos = [], [], []

    readme = root / "00_管理" / "README.md"
    ledger = root / "00_管理" / "台账.md"
    if not readme.is_file() or not ledger.is_file():
        print(f"[错误] 缺少 {readme if not readme.is_file() else ledger}——项目未按规范建档，先走建档或接管流程。")
        return 2

    # 1) 指针表：文件存在性 + 状态阶梯词
    headers, rows = parse_table_rows(readme.read_text(encoding="utf-8").splitlines(), "产出物线")
    if not rows:
        infos.append("指针表为空（尚无产出物线，立项早期属正常）。")
    for cells in rows:
        line_name = cells[0] if cells else "?"
        file_cell = cells[1] if len(cells) > 1 else ""
        status = cells[2] if len(cells) > 2 else ""
        if file_cell and file_cell not in ("—", "-"):
            target = root / file_cell.replace("\\", "/")
            if not target.exists():
                errors.append(f"指针表『{line_name}』指向的文件不存在：{file_cell}")
        if status and not any(w in status for w in LADDER_WORDS):
            warns.append(f"指针表『{line_name}』状态“{status}”不在阶梯词表内（应为：{'/'.join(LADDER_WORDS)}）")

    # 2) 各线 当前/ 唯一性
    produce = root / "01_产出"
    if produce.is_dir():
        current_dirs = [produce / "当前"] + [p / "当前" for p in produce.iterdir() if p.is_dir() and p.name != "当前"]
        for cd in current_dirs:
            if cd.is_dir():
                files = [f for f in cd.iterdir() if f.is_file()]
                if len(files) > 1:
                    warns.append(f"{cd.relative_to(root)} 内有 {len(files)} 个文件——当前版应唯一：{', '.join(f.name for f in files)}")

    # 3) 台账水位
    ledger_lines = ledger.read_text(encoding="utf-8").splitlines()
    _, iter_rows = parse_table_rows(ledger_lines, "事件类型")
    n = len(iter_rows)
    m = re.search(r"已扫至第\s*(\d+)\s*条", "\n".join(ledger_lines))
    watermark = int(m.group(1)) if m else 0
    if not m:
        warns.append("台账未找到一致性扫描水位行（『已扫至第 X 条』）。")
    if n - watermark >= args.stale:
        infos.append(f"迭代记录 {n} 条、水位 {watermark} 条，滞后 {n - watermark} ≥ {args.stale}——按 SKILL.md 第 9 节该做整体扫描了。")

    # 4) 表格空行（飞书断裂）
    for f in sorted(root.rglob("*.md")):
        if any(k in str(f) for k in SKIP_KEYWORDS):
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        for i in range(len(lines) - 2):
            if lines[i].strip().startswith("|") and not lines[i + 1].strip() and lines[i + 2].strip().startswith("|"):
                # 空行后若是"表头+分隔行"，视为一张新表（合法），不是同一张表被拆断
                nxt = lines[i + 3].strip() if i + 3 < len(lines) else ""
                if nxt.startswith("|") and set(nxt.strip("|").replace("|", "")) <= set("-: "):
                    continue
                warns.append(f"{f.relative_to(root)}:{i + 2} 表格行间有空行（飞书同步会断裂）")
                break  # 每文件报一次即可

    for e in errors:
        print(f"[错误] {e}")
    for w in warns:
        print(f"[警告] {w}")
    for i in infos:
        print(f"[提示] {i}")
    print("-" * 40)
    print(f"检查完成：{len(errors)} 错误 / {len(warns)} 警告 / {len(infos)} 提示")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
