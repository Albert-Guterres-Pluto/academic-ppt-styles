# 跨 Agent 使用

解压后保留 `longxia-pipiti-style` 整个文件夹及其名称。根目录的 `SKILL.md` 使用 YAML 的 `name`、`description`，图例、指南和脚本均随包提供。 [Agent Skills 规范](https://agentskills.io/specification)

| 客户端 | 放置技能文件夹的位置 |
| --- | --- |
| Claude Code | 项目 `.claude/skills/` 或个人 `~/.claude/skills/`。 [Claude Code](https://code.claude.com/docs/en/skills#choose-where-skills-load) |
| Cursor | 项目 `.agents/skills/` 或 `.cursor/skills/`。 [Cursor](https://cursor.com/docs/skills#skill-directories) |
| Gemini CLI | 项目 `.agents/skills/` 或 `.gemini/skills/`。 [Gemini CLI](https://geminicli.com/docs/cli/skills/) |
| OpenClaw | 工作区的 `skills/`。有多个本地 Agent 时，可放到共享的 `~/.openclaw/skills/`。 [OpenClaw](https://docs.openclaw.ai/tools/skills#installing-from-clawhub) |
| Codex | 放入当前客户端加载的技能目录，通过 `$longxia-pipiti-style` 调用。 |

支持自动加载时，提及技能名和需要的风格。只有文件读取能力时，请将整个目录放在会话可访问的位置，并给出入口路径。示例提示词如下。

> 阅读 `longxia-pipiti-style/SKILL.md` 。根据主题和讲述目标把这份提纲做成 8 页可编辑 PPTX。例题先显示题干，再按点击显示提示和答案。

远程 Agent 环境也需要能读到技能文件和要处理的稿件。制作 PPTX 需要该 Agent 能创建或编辑文件。附带的两个 PPTX 脚本可用 Python 3 离线运行，放映效果以目标播放器为准。
