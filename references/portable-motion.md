# 跨平台动画脚本

宿主能生成静态 PPTX 并运行 Python 3 时，可用 `scripts/add_motion.py` 添加原生动画。适用于新稿中的静态页。选定页已有动画或切换时，使用能编辑既有时间轴的工具。

先用可用工具导出有可编辑对象的静态 PPTX。用 [inspect_motion.py](../scripts/inspect_motion.py) 查看要处理的页和其中的对象名。跨页平滑时，在导出工具或选择窗格中为前后两页的对应对象设置相同且各页唯一的 `!!` 开头名称。

```console
python "scripts/inspect_motion.py" "草稿.pptx" --pages 6 7 8 --shapes
```

在工作目录建立 UTF-8 的 JSON 计划。按实际页码与对象名修改下例。页号按 PPTX 放映顺序从 1 开始。每个内层列表就是一次点击，同组对象同时淡入。题干等入场可见对象无需列入计划。

```json
{
  "slides": {
    "6": {
      "transition": {"type": "fade", "duration_ms": 700},
      "fade_clicks": [
        ["提示标签", "提示正文"],
        ["答案标签", "答案正文"]
      ]
    },
    "8": {
      "transition": {"type": "morph", "duration_ms": 1500}
    }
  }
}
```

- `fade_clicks` 目标须为唯一命名的顶层对象。可用整个组作为目标。可选 `fade_ms` 默认为 500 毫秒。
- `transition.type` 支持 `fade`、`push` 和 `morph`。平滑填写进入页。旧版播放器可读取平滑的兼容淡化分支。推进可选 `direction` 为 `l`、`r`、`u` 或 `d`。需要直接切页时省略 `transition`。
- 脚本写入一个新的 PPTX，仅编辑计划指定的静态页。保留原稿。命令示例中的相对脚本路径以技能目录为基准，调用时按实际位置调整。

```console
python "scripts/add_motion.py" "草稿.pptx" "动画计划.json" "成稿.pptx"
python "scripts/inspect_motion.py" "成稿.pptx" --pages 6 8
```

核对每个动画目标、触发顺序、时长和切换。有支持这些效果的播放器时，放映核对逐步揭示和平滑对象配对。
