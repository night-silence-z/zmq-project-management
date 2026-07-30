# zmq-project-management

面向 AI 协作的自适应项目治理 skill，采用 [Agent Skills](https://agentskills.io) 开放格式，不绑定特定工具。它根据任务对项目基线和正式关口的影响，选择最小充分流程：

> **English:** Adaptive project governance for AI collaboration. It separates routine iteration, project-baseline changes, and milestone closure so agents preserve decisions, risks, versions, and handoffs without over-managing ordinary work.

| 模式 | 适用情况 |
| -- | -- |
| 轻量日常迭代 | 在既有目标、范围、定义与验收标准内推进 |
| 项目基线变化 | 改变目标、范围、定义、约束、依赖、方法或验收标准 |
| 里程碑收口 | 定稿、交付、发布、阶段验收、挂起、移交或结束 |

核心原则：

- 风险决定验证深度，项目影响决定治理模式。
- 活文档原位维护，冻结交付物才建立独立版本。
- 只记录关键决策、风险、阻塞、推翻、待确认和里程碑。
- 一次性简单任务默认不建项目骨架。

## 安装

将仓库中的 `zmq-project-management/` 复制到支持 Agent Skills 的技能目录，或使用兼容的 skills 安装工具从本仓库安装。

分发目录只包含运行 skill 必需的内容；仓库根的 `evals/`、`tests/` 和 CI 配置用于维护与回归，不需要随 skill 安装。

## 从 v1 升级

现有项目无需重组目录或删除历史材料：

1. 更新 skill 分发目录。
2. 将项目规则入口中的旧自举行替换为“默认轻量，仅在基线变化或里程碑时升级治理动作”。
3. 将 README、台账、执行清单和权威定义视为活文档，停止因普通修改复制新版本。
4. 保留已有验收记录和历史版本；从下一次任务开始应用三级模式。

## 使用

安装后直接用自然语言描述工作，例如：

- “启动一个需要跨多个会话推进的项目。”
- “继续这个项目，按最小充分流程处理。”
- “这次改变了原来的范围，请更新项目基线。”
- “这个阶段可以正式收口并交接了。”

技能会自行判断治理模式。只有在模式升级会改变管理动作时，才需要说明原因。

## 目录

```text
zmq-project-management/
  SKILL.md
  agents/openai.yaml
  references/
  assets/templates/
  scripts/
evals/
tests/
```

## 开发与验证

```text
python -m unittest discover -s tests -v
python evals/build_fixtures.py
python evals/score_run.py --help
```

行为评估同时检查“应该做什么”和“禁止做什么”，特别关注管理文件触碰数量、活文档误升版、重复记录和错误里程碑升级。

## 许可

Apache License 2.0。
