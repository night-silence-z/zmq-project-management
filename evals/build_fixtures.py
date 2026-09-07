#!/usr/bin/env python3
"""生成三级治理行为评估夹具。"""

import argparse
import hashlib
import json
import tempfile
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parent

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
        "data.csv": "id,value\n1,60\n2,50\n",
        "00_管理/口径字典.md": CALIBER + "\n本次汇总：data.csv 的 value 列全部求和。两条记录均满足样本规则。\n",
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


# 原始材料与评分规则分开；评估执行者只获得 prompt 和 after 工作区。
CASE_FILES["S6"]["00_管理/README.md"] = README.replace(
    "| -- | -- | -- | -- |\n\n## 权威源",
    "| -- | -- | -- | -- |\n| 阶段报告 | 01_产出/当前/阶段报告-v1.md | 冻结评审快照，未验收 | — |\n\n## 权威源"
)
DEMO = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>团队事项 Demo</title>
<form id="task-form"><label>标题<input id="title" required></label>
<label>备注<textarea id="note" required></textarea></label><button>提交</button></form>
<p id="result"></p><script>
document.querySelector('#task-form').addEventListener('submit', e => {
  e.preventDefault();
  localStorage.setItem('draft', JSON.stringify({
    title: document.querySelector('#title').value, note: document.querySelector('#note').value
  }));
  document.querySelector('#result').textContent = '已在本地保存';
});
</script></html>
"""
REQUIREMENTS = """# 当前需求
目的：团队成员登记事项，第一版用于负责人初步体验提交过程；暂不接入后端。
- R1 标题必填。来源：用户要求；已实现，待用户试用。
- R2 备注必填。来源：用户要求；已实现，待用户试用。
- 实现边界：AI 暂定采用 localStorage 模拟提交，不会同步给其他人。
"""
CASE_FILES.update({
    "S8": {"背景.md": "# 项目背景\n\n暂无已确认的用户角色、业务流程或方案。\n"},
    "S9": {**COMMON, "demo.html": DEMO, "当前需求.md": REQUIREMENTS},
    "S10": {
        **COMMON,
        "00_管理/README.md": "# 两份工作报告\n\n报告A、报告B都是活文档，均使用 data/clean.csv 的全部有效记录。\nA：金额概览，使用金额求和。B：工作量概览，使用记录计数，不分析金额。\n共享约定见口径字典，无其他上下游成果。\n",
        "00_管理/口径字典.md": "# 共享约定\n\nid 唯一；金额单位元；每条记录代表一件已完成事项，无额外过滤。\n",
        "data/clean.csv": "id,amount\n1,40\n2,50\n",
        "报告A.md": "# 金额概览\n\n输入：data/clean.csv；方法：amount 列求和。\n合计：90 元。\n",
        "报告B.md": "# 工作量概览\n\n输入：data/clean.csv；方法：按 id 计数，不使用 amount 列。\n事项数：2。\n",
    },
    "S11": {"demo.html": DEMO, "当前需求.md": REQUIREMENTS,
        "验证记录.md": "# 检查证据\n\n目标文件 demo.html 的 SHA256：" + hashlib.sha256(DEMO.encode("utf-8")).hexdigest() +
        "\n已用浏览器验证：空标题或空备注被表单校验阻止；两者非空时本地保存并提示成功。\n环境：本地静态页面，Chrome；此后文件、输入与运行环境未改变。\n未验证：真实业务适用性。用户尚未试用。\n"}
})


def write_tree(root, files):
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="新建或空的隔离目录；默认系统临时目录")
    args = parser.parse_args()
    output = pathlib.Path(args.output).resolve() if args.output else pathlib.Path(tempfile.mkdtemp(prefix="zmq-evals-"))
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error("输出目录必须不存在或为空；不会删除旧评估结果。")
    output.mkdir(parents=True, exist_ok=True)

    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    for case in cases:
        case_id = case["id"]
        files = CASE_FILES[case_id]
        before = output / case_id / "before"
        after = output / case_id / "after"
        write_tree(before, files)
        shutil.copytree(before, after)
        (output / case_id / "prompt.txt").write_text(case["prompt"] + "\n", encoding="utf-8")
    print(f"已生成 {len(cases)} 个评估场景：{output}")


if __name__ == "__main__":
    main()
