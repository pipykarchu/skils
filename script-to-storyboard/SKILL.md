---
name: script-to-storyboard
description: 将中文剧本、小说片段或网页内容转换为分镜头脚本。用于用户要求“剧本转分镜”“漫剧脚本”“短剧分镜”“按镜头生成AI生图提示词”“输出Markdown或Excel分镜表”，输入可为 .md、.txt、.docx、.pdf、.html 文件或网页 URL，并需要包含景别、场景、出场事物造型、时间、画面质量提示词、对白、节奏和情绪等脚本要素。
---

# 剧本转分镜脚本

## 工作流

1. 明确输入文件或 URL、片段名称、输出格式：默认同时输出 Markdown 和 Excel。
2. 优先运行 `scripts/generate_storyboard.py` 生成结构化分镜。真实调用前提醒用户：Tuzi API 会消耗额度，需要 `TUZI_API_KEY`。
3. 使用两阶段模型流程：
   - 初稿：DeepSeek V4 Pro，负责拆分剧情、补齐镜头字段、生成客观画面描述。
   - 润色：Claude Sonnet 4.6，负责改对白、节奏和情绪，同时保持画面描述直观客观。
4. 检查输出是否满足每个镜头至少包含：镜号、时长、景别、场景、时间、出场事物造型、画面描述、运镜、对白、音效、AI 生图提示词、负面提示词、备注。
5. 若用户要继续生成图片，把 `AI 生图提示词` 列作为后续图像生成输入，不要把对白或抽象情绪直接塞进画面提示词。

## 快速命令

先做本地干跑验证，不访问 API：

```bash
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py input.md --out out --dry-run
```

按片段名称生成新文件：

```bash
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py input.md --segment "片段 01：妈妈病了" --out out
```

成功标志：输出目录里出现 `input_片段 01_妈妈病了_分镜脚本.md` 和 `input_片段 01_妈妈病了_分镜脚本.xlsx`。

真实调用 Tuzi：

```bash
$env:TUZI_API_KEY="sk-..."
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py input.md --out out
```

如果用户说“用这个技能，根据剧本和片段名称建立新文件”，优先要求或定位这两项：

- 剧本文件路径或网页 URL。
- 片段名称，例如 `片段 01：妈妈病了`、`妈妈病了`、`夜路出发`。

然后运行 `--segment`，不要把全文都送进模型。

如果 Tuzi 后台模型名变化，先列模型：

```bash
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py --list-models
```

可用环境变量覆盖模型名：

```bash
$env:TUZI_DRAFT_MODEL="DeepSeek V4 Pro"
$env:TUZI_REWRITE_MODEL="Claude Sonnet 4.6"
```

## 漫剧工作流交接

当由 `manju-production-workflow` 调用时，本 skill 负责把 `screenplay-director` 生成的剧本文件变成镜头级生产表。

优先读取这些上游文件：

```text
<项目名>/03_角色设定/角色档案.md
<项目名>/03_角色设定/角色固定提示词.md
<项目名>/05_剧本/第XX集_<标题>.md
```

默认输出到：

```text
<项目名>/06_分镜表/第XX集_分镜脚本.md
<项目名>/06_分镜表/第XX集_分镜脚本.xlsx
<项目名>/07_绘图提示词/第XX集_生图提示词.md
```

分镜提示词必须沿用 `角色固定提示词.md` 中的稳定描述。不要把同一个角色写成不同发色、发型、年龄段、体型或标志服装，除非剧本明确说明剧情原因。

如果脚本当前只导出分镜 Markdown/Excel，则在最终回复中说明 `AI 生图提示词` 列已经可作为提示词包使用；只有用户要求单独整理提示词包时，再创建 `07_绘图提示词` 文件。

每集完成后，给 `manju-production-workflow` 的交接信息必须包括：

- 分镜 Markdown 路径。
- 分镜 Excel 路径。
- 是否读取了角色档案。
- 是否发现角色一致性问题。
- 下一步建议：出图、质检或修改剧本。

## 输出要求

- 全部中文。
- 描述要直观、客观、可生图，避免华丽辞藻。
- 景别使用常见词：远景、全景、中景、近景、特写、大特写、俯拍、仰拍、过肩镜头。
- 时间写成可见信息：清晨、白天、黄昏、夜晚、雨夜、室内灯光等。
- 出场事物造型写清人物年龄段、服装、发型、关键道具、环境陈设。
- 画面质量提示词写入 `AI 生图提示词`，例如：清晰构图、主体明确、电影感灯光、细节完整、无文字水印、横版 16:9。
- 对白和音效要服务节奏，不要破坏画面提示词的可控性。

## 参考资料

- `references/prompt-guidelines.md`：两阶段模型提示词和字段规范。
- `scripts/generate_storyboard.py`：读取文件、调用 Tuzi、导出 Markdown/Excel 的 MVP 脚本。
