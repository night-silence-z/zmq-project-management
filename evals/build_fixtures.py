#!/usr/bin/env python3
"""生成三级治理行为评估夹具。"""

import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parent
OUTPUT = ROOT / "generated"

README = """# 示例项目 · 项目总览

## 启动卡

本项目交付一份可核验的阶段材料，供负责人决定下一步，验收标准是结论有来源、建议有验证方式。

## 当前状态

- 阶段：执行中
- 最近结果：工作稿已形成
- 下一步：继续完善当前材料
- 阻塞：无

## 冻结交付物指针

| 产出物线 | 当前版文件 | 状态 | 对应关系 |
| -- | -- | -- | -- |

## 权威源

| 定义范围 | 权威文件 | 说明 |
| -- | -- | -- |
| 分析口径 | 00_管理/口径字典.md | 唯一权威源 |
"""

LEDGER = """# 示例项目 · 台账

## 一、跨会话待办

| # | 事项 | 状态 | 备注 |
| -- | -- | -- | -- |
| 1 | 完善当前材料 | 进行中 | — |

## 二、关键决策与待确认

### 已决策

| 编号 | 日期 | 决策 | 原因 | 影响范围 |
| -- | -- | -- | -- | -- |
| D-001 | 2026-07-30 | 分析排除短期样本 | 避免短期波动影响结论 | 全部分析 |

### 待确认

| 编号 | 事项 | 决策人 | 截止条件 | 默认方案 | 影响范围 |
| -- | -- | -- | -- | -- | -- |

## 三、关键事件

| 时间 | 阶段/语境 | 事件类型 | 内容 | 原因 | 影响与关联材料 |
| -- | -- | -- | -- | -- | -- |
"""

CALIBER = """# 口径字典

| 名称 | 定义 | 范围/样本 | 排除规则 | 来源 |
| -- | -- | -- | -- | -- |
| 核心样本 | 满足观察期要求的样本 | 全部有效记录 | 排除短期样本 | D-001 |
"""

COMMON = {
    "00_管理/README.md": README,
    "00_管理/台账.md": LEDGER,
    "00_管理/口径字典.md": CALIBER,
}

CASE_FILES = {
    "S1": {
        "项目说明.md": "# 项目说名\n\n这是一份一次性说名材料。\n",
    },
    "S2": {
        **COMMON,
        "工作稿.md": "# 工作稿\n\n## 二、方法\n\n[来源](source.md)\n\n## 一、结论\n",
        "source.md": "# 来源\n",
    },
    "S3": {
        **COMMON,
        "当前分析.md": "# 当前分析\n\n当前结果按口径字典执行。\n",
    },
    "S4": {
        **COMMON,
        "01_产出/当前/执行方案.md": (
            "# 执行方案\n\n计划使用外部数据源；许可、费用和可用性尚未确认。\n"
        ),
    },
    "S5": {
        **COMMON,
        "当前材料.md": "# 当前材料\n\n汇总值：100\n\n计算规则见口径字典。\n",
    },
    "S6": {
        **COMMON,
        "01_产出/当前/阶段报告-v1.md": (
            "# 阶段报告 v1\n\n## 结论\n\n结论 A。\n\n## 建议\n\n执行建议 A。\n\n"
            "> 缺口：结论来源和建议验证方式尚未补齐。\n"
        ),
    },
    "S7": {
        **COMMON,
        "当前工作.md": "# 当前工作\n\n下一步需要完成来源核验。\n",
    },
}


def write_tree(root, files):
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if OUTPUT.exists():
        if OUTPUT.parent != ROOT or OUTPUT.name != "generated":
            raise RuntimeError(f"拒绝清理非预期目录：{OUTPUT}")
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    for case in cases:
        case_id = case["id"]
        files = CASE_FILES[case_id]
        before = OUTPUT / case_id / "before"
        after = OUTPUT / case_id / "after"
        write_tree(before, files)
        shutil.copytree(before, after)
        (OUTPUT / case_id / "prompt.txt").write_text(case["prompt"] + "\n", encoding="utf-8")
    print(f"已生成 {len(cases)} 个评估场景：{OUTPUT}")


if __name__ == "__main__":
    main()
