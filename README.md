# zmq-project-management

一套 AI 协作场景下的项目管理规范 skill：让 AI 按统一机制管理项目全生命周期——立项访谈、精简目录、版本与产出物线、台账留痕、口径唯一性、会话开工/收工例程、交接与收尾复盘。

采用 [Agent Skills](https://agentskills.io) 开放标准，**不绑定任何特定 AI 工具**：支持该标准的工具可直接安装；不支持的工具可当纯规则文档使用（见安装方式二）。规则提炼自多个真实项目的复盘，只包含项目管理机制，不含个人偏好与环境专属配置；可按团队习惯裁剪。

> **English**: A project-governance skill for AI collaboration (Agent Skills open standard, tool-agnostic). It makes the AI keep project memory in plain files — kickoff interview, versioned deliverable lines with a current-version pointer table, an append-only ledger (decisions/reversals with "was → now → why"), single-source-of-truth for definitions, per-session startup/closing routines, and a closing retrospective. Install: copy `zmq-project-management/` into your agent's skills directory (e.g. `~/.claude/skills/`), or paste `SKILL.md` into any agent's rules file. Content is currently Chinese-only; issues and PRs welcome.

## 运行逻辑

**核心思路：把项目记忆从"AI 的会话"搬到"项目的文件"里。** AI 负责当记录员和检查员，所有状态落盘在项目目录中——会话断了、换个 AI，项目记忆都还在。

```mermaid
flowchart LR
    A[立项<br>访谈问清：产出物/受众/验收] --> B[建骨架<br>README + 台账 + 目录]
    B --> C[日常会话<br>开工读状态 → 干活落账 → 收工更新]
    C --> C
    C --> D[收尾<br>终版合流 + 资产沉淀 + 复盘]
```

> 文字版（图未渲染时看这行）：立项（访谈问清产出物/受众/验收）→ 建骨架（README+台账+目录）→ 日常会话（开工读状态 → 干活落账 → 收工更新，循环往复）→ 收尾（终版合流 + 资产沉淀 + 复盘）。

skill 在三个时刻介入：

1. **立项**：AI 逐轮追问三要素（做出什么、给谁用、如何验收），收敛后按模板生成一页启动卡和目录骨架，之后不再反复问。
2. **每次会话**：开工先读 README、台账和最近的迭代记录，快速重建上下文再干活；过程中版本升级、决策、推翻都落账；收工更新待办与当前版指针。
3. **收尾**：标记唯一终版、沉淀可复用资产、生成项目复盘。

## 优势

- **跨会话、跨 AI 不失忆**——项目状态全在文件里；多个 AI 协作时共用一套台账，互相知道对方做了什么。
- **版本永不丢**——产出只增不覆盖，当前版有唯一指针表，支持"回到 v5"式指名回滚。
- **口径不漂移**——指标、术语、契约只在权威源定义一次，产出只引用；变更触发全链路同步，交付前可用自带脚本扫描禁用词残留。
- **人不填表**——使用者只做三件事：给原料、提意见、做决策；结构化、记录、检查全部是 AI 的工作。
- **状态不含糊**——交付进度只用状态阶梯表述（探索→候选→已定稿→已交付），没有"差不多好了"。

规则不是设计出来的流程，是从多个真实项目的复盘中提炼的做法；且刻意轻量——目录用到才建，台账不记闲聊。

**与 memory-bank / superpowers 类工具的关系**：互补而非替代。它们管"怎么干活"（任务拆解、TDD、跨会话代码记忆，面向开发者）；本 skill 管"项目怎么不失控"（交付物版本线、口径唯一性、台账留痕、收尾复盘，也适合非技术使用者）。可以同装。

## 安装

### 方式一：支持 Agent Skills 标准的 AI 工具

`git clone` 本仓库（或 Download ZIP 解压）后，把其中的 `zmq-project-management/` 文件夹复制到你所用工具的 skills 目录，新会话即生效。**只需复制这一个文件夹**——仓库根的 `evals/` 是开发期评估资产，供维护者和 fork 者做回归测试用，无需安装：

| 工具 | 个人级（所有项目生效） | 项目级（仅该项目生效） |
| -- | -- | -- |
| Claude Code | `~/.claude/skills/`（Windows：`%USERPROFILE%\.claude\skills\`） | 项目根 `.claude/skills/` |
| 其他支持 Agent Skills 的工具 | 见该工具文档约定的 skills 目录 | 同左 |

验证：对 AI 说"启动一个新项目"，或按你所用工具的 skill 调用方式（如 `/zmq-project-management`）。

### 方式二：任何 AI 工具（通用，无需 skills 机制）

- 把 `SKILL.md` 正文（frontmatter 以下部分）贴入你所用工具的规则文件——如 Codex 的 `AGENTS.md`、Cursor 的 rules 文件——或在会话开头把整个文件投喂给 AI。
- 把 `references/` 与 `scripts/` 放在项目内 AI 可读取的位置（建档和收尾时会用到）。

## 用法

装好后不需要记任何命令，对 AI 说人话：

| 场景 | 你说 | AI 做 |
| -- | -- | -- |
| 开新项目 | "启动一个新项目，做××" | 发起立项访谈 → 按模板建骨架 → 进入执行 |
| 日常推进 | "继续××项目" | 读 README+台账重建上下文，接着上次干 |
| 随时留痕 | "记账" | 立即把当前进展/决策写入台账 |
| 接管旧项目 | "按规范接管这个项目" | 只读盘点 → 出现状清单 → 经你确认后重组 |
| 项目收尾 | "项目收尾" | 终版合流 → 资产沉淀 → 生成复盘 |

所有记录都是项目目录里的普通 Markdown 文件，随时可人工翻看和修改。

命令行可选项（AI 会在对应环节自动调用，也可手动执行）：`python zmq-project-management/scripts/init_project.py 项目名` 一键建项目骨架；`health_check.py 项目根` 一键体检；`check_terms.py` 交付前口径扫描。

## 目录结构

```
zmq-project-management/
  SKILL.md              规范正文（12 节）
  references/
    复盘模板.md          项目收尾时按需加载的复盘模板
    台账模板.md          建档模板（含填好示例）
    README模板.md        建档模板：总览+当前状态+指针表（含示例）
    启动卡模板.md        立项访谈的产出模板（含示例）
  scripts/              （均为标准库、无依赖，可直接运行）
    init_project.py     一键建档：基础目录+README/台账骨架+自举行
    health_check.py     项目体检：指针表指向/当前版唯一性/水位/表格空行
    check_terms.py      口径/禁用词一致性扫描器
  examples/
    示例项目/            规范落地形态的迷你示例（可对照颗粒度）
  CHANGELOG.md          版本记录
evals/
  README.md             评估套件：4 场景+陷阱题+期望行为清单+实测结论
  build_fixtures.py     评估夹具一键生成器
```

改版后建议至少复跑 evals 的 S4 陷阱场景做回归（方法见 [evals/README.md](evals/README.md)）。

## 建议自定义的点

- 跨项目资产库位置（首次项目收尾时 AI 会询问一次并记录）。
- 阶段闸门粒度、台账拆分阈值（默认 50 条/300 行）、开工读取条数（默认 20）。
- 版本文件命名风格（默认 `名称-vN.扩展名`）。
- 与飞书相关的条件规则（不用飞书可删）。

## Roadmap（规划中，欢迎 Issue/PR）

- 接入 plugin marketplace / `npx skills add` 等分发生态（待调研各家接入要求）。
- 轻量 CI：frontmatter 校验、内部引用死链检查。

## 版本与许可

当前 v1.3（2026-07-20），修订历史见 `zmq-project-management/CHANGELOG.md`；规则变更均经 evals 实测回归。本地定制建议 fork 后自立版本线，升级时对照 CHANGELOG 合并。

本仓库以 [Apache License 2.0](LICENSE) 开源，允许商用与修改。
