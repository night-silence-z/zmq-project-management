# zmq-project-management

一套 AI 协作场景下的项目管理规范 skill：让 AI 按统一机制管理项目全生命周期——立项访谈、精简目录、版本与产出物线、台账留痕、口径唯一性、会话开工/收工例程、交接与收尾复盘。

采用 [Agent Skills](https://agentskills.io) 开放标准，**不绑定任何特定 AI 工具**：支持该标准的工具可直接安装；不支持的工具可当纯规则文档使用（见安装方式二）。规则提炼自多个真实项目的复盘，只包含项目管理机制，不含个人偏好与环境专属配置；可按团队习惯裁剪。

## 安装

### 方式一：支持 Agent Skills 标准的 AI 工具

把 `zmq-project-management/` 文件夹复制到你所用工具的 skills 目录，新会话即生效：

| 工具 | 个人级（所有项目生效） | 项目级（仅该项目生效） |
| -- | -- | -- |
| Claude Code | `~/.claude/skills/`（Windows：`%USERPROFILE%\.claude\skills\`） | 项目根 `.claude/skills/` |
| 其他支持 Agent Skills 的工具 | 见该工具文档约定的 skills 目录 | 同左 |

验证：对 AI 说"启动一个新项目"，或按你所用工具的 skill 调用方式（如 `/zmq-project-management`）。

### 方式二：任何 AI 工具（通用，无需 skills 机制）

- 把 `SKILL.md` 正文（frontmatter 以下部分）贴入你所用工具的规则文件——如 Codex 的 `AGENTS.md`、Cursor 的 rules 文件——或在会话开头把整个文件投喂给 AI。
- 把 `references/复盘模板.md` 放在项目内 AI 可读取的位置（项目收尾时会用到）。

## 目录结构

```
zmq-project-management/
  SKILL.md              规范正文（12 节）
  references/
    复盘模板.md          项目收尾时按需加载的复盘模板
  CHANGELOG.md          版本记录
```

## 建议自定义的点

- 跨项目资产库位置（首次项目收尾时 AI 会询问一次并记录）。
- 阶段闸门粒度、台账拆分阈值（默认 50 条/300 行）、开工读取条数（默认 20）。
- 版本文件命名风格（默认 `名称-vN.扩展名`）。
- 与飞书相关的条件规则（不用飞书可删）。

## 版本

当前 v1.0（2026-07-17），修订历史见 `zmq-project-management/CHANGELOG.md`。修改建议走仓库 Issue/PR；本地定制建议 fork 后自立版本线，升级时对照 CHANGELOG 合并。
