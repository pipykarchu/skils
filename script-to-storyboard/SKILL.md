---
name: script-to-storyboard
description: 将中文剧本、小说片段或网页内容转换为分镜头脚本。用于用户要求“剧本转分镜”“漫剧脚本”“短剧分镜”“按镜头生成AI生图提示词”“输出Markdown或Excel分镜表”，输入可为 .md、.txt、.docx、.pdf、.html 文件或网页 URL，并需要包含景别、场景、出场事物造型、时间、画面质量提示词、对白、节奏和情绪等脚本要素。
---

# 剧本转分镜脚本

## 工作流

1. 明确输入文件或 URL，以及输出格式：默认同时输出 Markdown 和 Excel。
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

真实调用 Tuzi：

```bash
$env:TUZI_API_KEY="sk-..."
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py input.md --out out
```

如果 Tuzi 后台模型名变化，先列模型：

```bash
python C:\Users\Administrator\.codex\skills\script-to-storyboard\scripts\generate_storyboard.py --list-models
```

可用环境变量覆盖模型名：

```bash
$env:TUZI_DRAFT_MODEL="DeepSeek V4 Pro"
$env:TUZI_REWRITE_MODEL="Claude Sonnet 4.6"
```

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
