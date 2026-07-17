#!/usr/bin/env python3
"""项目建档脚手架（zmq-project-management）

对应 SKILL.md 第 3 节：建档是机械、重复、必须一致的环节——用脚本一键生成
基础目录与骨架文件，AI 只负责按 references/ 模板填内容（立项访谈产出的启动卡等）。

用法:
    python init_project.py 项目名 [--base 工作区目录] [--type 分析|开发|汇报]
                                  [--minimal] [--no-bootstrap]

行为:
    - 在 base（默认当前目录）下创建 项目名/ 及基础 4 目录：
        00_管理/（README.md + 台账.md 骨架）、01_产出/当前/、01_产出/历史/、
        02_输入/、99_归档/
    - --minimal 只建 00_管理/ 与 01_产出/（轻量项目）。
    - --type 追加领域扩展：
        分析 -> 03_数据/ 04_脚本/ 00_管理/口径字典.md
        开发 -> 03_验收记录/ 00_管理/契约清单.md
        汇报 -> 00_管理/术语与红线.md
    - 默认在项目根写入 CLAUDE.md 与 AGENTS.md 自举行（--no-bootstrap 关闭）。
    - 目标目录已存在且非空时拒绝执行（应走 SKILL.md 第 2 节"存量项目接管"），退出码 2。

骨架结构与 references/ 中的模板保持一致；若修改模板结构，须同步本脚本。
仅用标准库，Python 3.8+。
"""

import argparse
import datetime
import pathlib
import sys

BOOTSTRAP_LINE = "本项目按 zmq-project-management 规范管理，会话开工/收工按其例程执行。\n"

README_SKELETON = """# {name} · 项目总览

## 启动卡

（待立项访谈收敛后按 references/启动卡模板.md 填写；用户签核后冻结，变更走台账决策）

## 当前状态（每次收工更新）

- 阶段：待立项
- 一句话进展：项目骨架已创建
- 下一步：完成立项访谈，填写启动卡
- 阻塞：无
- 最近更新：{now}

## 当前版指针表

| 产出物线 | 当前版文件 | 状态 | 对应关系 |
| -- | -- | -- | -- |

## 权威源清单

| 口径类型 | 权威文件 | 说明 |
| -- | -- | -- |
"""

LEDGER_SKELETON = """# {name} · 台账

## 一、待办

| # | 事项 | 状态 | 备注 |
| -- | -- | -- | -- |
| 1 | 完成立项访谈并签核启动卡 | 待启动 | — |

## 二、决策与待确认

### 已决策

| 编号 | 日期 | 决策 | 原因 | 影响范围 |
| -- | -- | -- | -- | -- |

### 待确认

| 编号 | 事项 | 决策人 | 截止条件 | 默认方案 | 影响范围 |
| -- | -- | -- | -- | -- | -- |

## 三、迭代记录（只增不删）

| 时间 | 阶段 | 事件类型 | 内容 | 原因 | 影响与关联文档 |
| -- | -- | -- | -- | -- | -- |
| {now} | 立项 | 进展 | 项目骨架由 init_project.py 创建 | — | 00_管理/ |

> 一致性扫描水位：已扫至第 1 条（{today}）
"""

CALIBER_SKELETONS = {
    "口径字典.md": "# {name} · 口径字典\n\n> 定义只在本文件出现一次，产出只引用（\"口径见字典 vN\"）。\n\n## 指标口径\n\n| 指标 | 定义 | 分母/样本 | 剔除规则 | 生效版本 |\n| -- | -- | -- | -- | -- |\n\n## 禁用与替换\n\n| 禁用词 | 应使用 |\n| -- | -- |\n",
    "契约清单.md": "# {name} · 契约清单\n\n> 接口与数据契约的唯一权威源；实现与文档冲突时以此为准或列出请裁决。\n\n| 契约点 | 当前口径 | 来源 | 状态 | 备注 |\n| -- | -- | -- | -- | -- |\n",
    "术语与红线.md": "# {name} · 术语与红线\n\n> 对外表述的唯一权威源。\n\n## 标准术语\n\n| 术语 | 标准写法 | 说明 |\n| -- | -- | -- |\n\n## 禁用与替换\n\n| 禁用词 | 应使用 |\n| -- | -- |\n",
}

TYPE_EXTENSIONS = {
    "分析": {"dirs": ["03_数据", "04_脚本"], "caliber": "口径字典.md"},
    "开发": {"dirs": ["03_验收记录"], "caliber": "契约清单.md"},
    "汇报": {"dirs": [], "caliber": "术语与红线.md"},
}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="按 zmq-project-management 规范创建项目骨架")
    ap.add_argument("name", help="项目名（将作为目录名）")
    ap.add_argument("--base", default=".", help="工作区目录，默认当前目录")
    ap.add_argument("--type", choices=sorted(TYPE_EXTENSIONS), help="领域扩展：分析/开发/汇报")
    ap.add_argument("--minimal", action="store_true", help="只建 00_管理 与 01_产出")
    ap.add_argument("--no-bootstrap", action="store_true", help="不写 CLAUDE.md/AGENTS.md 自举行")
    args = ap.parse_args()

    root = pathlib.Path(args.base) / args.name
    if root.exists() and any(root.iterdir()):
        print(f"[拒绝] {root} 已存在且非空——请走 SKILL.md 第 2 节『存量项目接管』流程，不要覆盖。")
        return 2

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    today = now[:10]
    created = []

    dirs = ["00_管理", "01_产出/当前", "01_产出/历史"]
    if not args.minimal:
        dirs += ["02_输入", "99_归档"]
    if args.type:
        dirs += TYPE_EXTENSIONS[args.type]["dirs"]
    for d in dirs:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(str(p.relative_to(root.parent)))

    files = {
        root / "00_管理" / "README.md": README_SKELETON.format(name=args.name, now=now),
        root / "00_管理" / "台账.md": LEDGER_SKELETON.format(name=args.name, now=now, today=today),
    }
    if args.type:
        cal = TYPE_EXTENSIONS[args.type]["caliber"]
        files[root / "00_管理" / cal] = CALIBER_SKELETONS[cal].format(name=args.name)
    if not args.no_bootstrap:
        files[root / "CLAUDE.md"] = BOOTSTRAP_LINE
        files[root / "AGENTS.md"] = BOOTSTRAP_LINE
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        created.append(str(path.relative_to(root.parent)))

    print(f"已创建项目骨架：{root}")
    for c in created:
        print(f"  {c}")
    print("下一步：进行立项访谈（SKILL.md 第 1 节），按 references/启动卡模板.md 填写启动卡并请用户签核。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
