# 学术 PPT 四种风格

`academic-ppt-styles` 是一个 Agent Skill，用于新建、改版或检查可编辑的中文学术 PPTX。它包含四种版式指南和两支 Python 脚本，可安排点击淡化、推进、按对象平滑，以及检查成稿的时间轴。

| 风格 | 适用内容 |
| --- | --- |
| [旧版学术](references/old.md) | 机构、项目与校园综述 |
| [过渡版学术](references/transition.md) | 概念关系、过程和实践路径 |
| [新版学术 A](references/new-a.md) | 逻辑讲义、专题汇报或按时间递进的内容 |
| [新版学术 B](references/new-b.md) | 图形推演、公式、反例和证明 |

## 使用

1. 从 [GitHub Releases](https://github.com/Albert-Guterres-Pluto/academic-ppt-styles/releases) 下载 ZIP 并解压。
2. 将整个 `academic-ppt-styles` 文件夹放入客户端的技能目录。可查看 [Codex、Claude Code、Cursor、Gemini CLI 和 OpenClaw 的使用说明](references/portable-use.md)。
3. 在提问时指定风格和输出。可直接引用 [SKILL.md](SKILL.md)。

> 使用 academic-ppt-styles 的新版学术风格 A。采用深绿讲义变体，把提纲做成 8 页可编辑 PPTX。例题先显示题干，再按点击显示提示和答案。

制作可编辑 PPTX 需要客户端有 PPTX 生成工具。随附的动画写入和检查脚本仅使用 Python 3 标准库。 [动画实现与核验](references/motion.md)

## 许可

MIT。公开版的四张页面对照图使用自制示例。 [许可证](LICENSE)
