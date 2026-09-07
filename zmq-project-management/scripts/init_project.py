#!/usr/bin/env python3
"""为需要跨会话治理的项目创建最小骨架。

默认只创建 README 和台账；项目自举指针需要显式选择。输入、产出与归档目录
仅在实际使用或显式传入 --full 时创建。
"""

import argparse
import datetime
import pathlib
import sys


SKILL_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
BOOTSTRAP_LINE = (
    "本项目使用 zmq-project-management；默认采用轻量日常迭代，"
    "仅在项目基线变化或里程碑关口时升级治理动作。\n"
)

PROFILE_TEMPLATES = {
    "分析": ("口径字典.md", "口径字典.md.tmpl"),
    "开发": ("契约清单.md", "契约清单.md.tmpl"),
    "汇报": ("术语与事实.md", "术语与事实.md.tmpl"),
    "通用": ("基线说明.md", "契约清单.md.tmpl"),
}


def render_template(name, values):
    path = TEMPLATE_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"模板不存在：{path}")
    text = path.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="创建 zmq-project-management 最小项目骨架")
    parser.add_argument("name", help="项目名，也作为目录名")
    parser.add_argument("--base", default=".", help="工作区目录，默认当前目录")
    parser.add_argument("--type", choices=sorted(PROFILE_TEMPLATES), help="可选权威源模板")
    parser.add_argument(
        "--full",
        action="store_true",
        help="显式创建 01_产出、02_输入和 99_归档；默认不建空目录",
    )
    parser.add_argument(
        "--bootstrap",
        choices=("both", "agents", "claude", "none"),
        default="none",
        help="显式选择项目自举指针；默认不写 AGENTS.md 或 CLAUDE.md",
    )
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="兼容旧参数，等同 --bootstrap none",
    )
    args = parser.parse_args()

    base = pathlib.Path(args.base).resolve()
    root = (base / args.name).resolve()
    if root.parent != base or root == base:
        print("[拒绝] 项目名必须是工作区下的单一目录名。")
        return 2
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        print(f"[拒绝] {root} 已存在且非空；请先只读盘点，不要覆盖。")
        return 2

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    values = {"PROJECT_NAME": args.name, "NOW": now,
              "AUTHORITY_TITLE": "基线说明" if args.type == "通用" else "契约清单"}
    files = {
        root / "00_管理" / "README.md": render_template("README.md.tmpl", values),
        root / "00_管理" / "台账.md": render_template("台账.md.tmpl", values),
    }

    if args.type:
        output_name, template_name = PROFILE_TEMPLATES[args.type]
        files[root / "00_管理" / output_name] = render_template(template_name, values)

    bootstrap = "none" if args.no_bootstrap else args.bootstrap
    if bootstrap in ("both", "agents"):
        files[root / "AGENTS.md"] = BOOTSTRAP_LINE
    if bootstrap in ("both", "claude"):
        files[root / "CLAUDE.md"] = BOOTSTRAP_LINE

    created = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path.relative_to(root.parent))

    if args.full:
        for relative in ("01_产出", "02_输入", "99_归档"):
            path = root / relative
            path.mkdir(parents=True, exist_ok=True)
            created.append(path.relative_to(root.parent))

    print(f"已创建最小项目骨架：{root}")
    for path in created:
        print(f"  {path}")
    print("下一步：围绕实际场景和第一版用途澄清尚未明确的目标；骨架不代表已确认基线。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
