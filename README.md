# 龙虾屁屁踢

`longxia-pipiti-style` 是一个用于新建、改版和检查可编辑 PPTX 的 Agent Skill。用户给出主题和提纲时，Skill 会结合受众和讲述目标选择主风格，再按页决定图表、题块、流程或图文版式。用户点名风格或原稿时沿用指定设计。

| 风格 | 识别线索 | 同题示例 |
| --- | --- | --- |
| 旧版学术 | 通栏边条、编号标题、时间轴与大数字 | [午间温度记录](longxia-pipiti-style/references/visuals/old.png) |
| 过渡版学术 | 圆章号、胶囊和跨页关系 | [两次观测逐步展开](longxia-pipiti-style/references/visuals/transition.png) |
| 新版学术 A | 固定题头、章节索引、题块或分组 | [同一题块的两套主题色](longxia-pipiti-style/references/visuals/new-a.png) |
| 新版学术 B | 四边细框、固定图形和逐步标注 | [同一组数据的点图](longxia-pipiti-style/references/visuals/new-b.png) |

## 安装

1. 下载 [v2.0.0 ZIP](https://github.com/Albert-Guterres-Pluto/academic-ppt-styles/releases/download/v2.0.0/longxia-pipiti-style-v2.0.0.zip) 并解压。也可从仓库取用 [`longxia-pipiti-style/`](longxia-pipiti-style/SKILL.md) 整个目录。
2. 把 `longxia-pipiti-style` 放进客户端的技能目录。[跨 Agent 使用](longxia-pipiti-style/references/portable-use.md)
3. 指定任务。只给主题和提纲时，Skill 会选版式和风格。

> 使用 longxia-pipiti-style 做 8 页可编辑 PPTX。主题是校园温度观测，观众是班级同学。重点解释温差怎么变化。请自主选风格，例题按点击分步显示。

制作可编辑 PPTX 需要客户端具备相应文件工具。写入和检查动画的脚本使用 Python 3 标准库。[动画实现与核验](longxia-pipiti-style/references/motion.md)

## 从旧名称迁移

把 `academic-ppt-styles` 的调用更新为 `longxia-pipiti-style`。Codex 中可使用 `$longxia-pipiti-style`。安装目录与 ZIP 根目录也使用新名称。[v1.0.0 Release](https://github.com/Albert-Guterres-Pluto/academic-ppt-styles/releases/tag/v1.0.0)

## 许可

[MIT](LICENSE)。对照图使用自制示例和示例数据。
