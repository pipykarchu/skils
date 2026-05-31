---
name: screenplay-director
description: Turn a story, novel excerpt, raw text, outline, synopsis, character idea, or rough plot into a professional Chinese screenplay, first extract a plot outline, infer a fitting Chinese title, build stable character profile files/descriptions for consistency, write every segment with professional scene/person/action/dialogue/camera fields, and create both Markdown and Word (.docx) files. Use when the user wants to write a script, convert a novel/text into a screenplay, generate a screenplay, split a story into scenes or segments under 400 Chinese characters each, polish character dialogue, save the result as MD/Word, or run a Tuzi API multi-model workflow where DeepSeek drafts, Claude/GPT improves characters and dialogue, and Gemini checks long-form consistency.
---

# Screenplay Director

Convert the user's story into a logical, professional, shootable Chinese screenplay.

## Default Rules

- 默认用中文输出剧本、人物设定、对白、审校意见和修改建议。
- 先用大白话说明本次写作目的，再输出具体剧本内容。
- 输出 Markdown.
- 每个正式剧本片段的核心剧情内容不超过 400 个中文字符；如果内容过长，拆成更多片段。场景、人物、镜头等结构化字段可以独立列出，但仍要简洁。
- 每个片段必须有明确戏剧功能：铺垫、冲突、转折、情绪推进、信息揭示、高潮或收束。
- 每个正式剧本片段必须包含专业字段：【场景】【人物】【动作】【台词】【镜头提示】；缺一项都不算完整剧本。
- 片段书写顺序必须清楚：先交代事件发生的地点和时间，再交代出场人物，再写可见动作，再写台词/内心/独白，最后写镜头运动效果。
- 保持人物动机一致，避免角色为了剧情强行行动。
- 对白要符合人物身份、关系、情绪和场景压力。
- 优先写可见动作、可拍摄画面和可表演对白，少用解释性旁白。
- 片段之间必须有因果关系，每段结尾尽量留下钩子。
- 可以把小说、长文本、故事梗概、散乱文字整理成剧本；先提炼剧情大纲，再改写成可拍摄剧本。
- 剧本开头必须添加“剧情大纲提炼”，说明故事主线、关键事件、人物关系和改编取舍。
- 用户提供故事后，先根据故事内容想一个合适的中文标题；不要直接使用“未命名剧本”。
- 必须建立“人物设定角色档案”，并在后续片段中保持角色外貌、发型、服装、性格、口头禅、情绪表达和绘图固定提示词一致。
- 默认创建两份文件：`.md` 和 `.docx`。
- 创建文件前说明风险：会在本地写入新文件；文件名会根据标题生成；为避免覆盖已有文件，默认加时间戳。

## Professional Script Format

Write every screenplay segment in this professional order:

```md
## 片段 01：标题

【场景】地点，天气/环境，时间
【人物】人物 A（年龄，发型，服装，固定识别特征）；人物 B（年龄，发型，服装，固定识别特征）
【动作】人物在画面里能被看见的动作；冲突如何发生、升级或转折。
【台词】人物 A：（语气/状态）对白。
人物 B：（语气/状态）对白。
【镜头提示】景别、镜头运动、画面焦点、转场或运动效果。
```

Field rules:

- 【场景】必须包含地点、时间和环境状态，例如天气、光线、人群、声音、空间关系。
- 【人物】必须区分主角/配角，并沿用人物设定角色档案里的固定描述。
- 【动作】只写画面能表现出来的动作，不用抽象解释代替表演。
- 【台词】可以包含对话、内心、独白；必须标注语气或动作状态，避免所有角色说话同一种口吻。
- 【镜头提示】必须包含至少一种具体镜头信息：远景/全景/中景/近景/特写、推拉摇移跟、俯拍/仰拍、焦点变化、转场、画面运动效果。
- 镜头逻辑要顺畅：建立场景 -> 人物入画 -> 动作冲突 -> 台词反应 -> 情绪落点或钩子。
- 不要把“镜头提示”写成泛泛的“画面很好看”；必须能指导拍摄、分镜或 AI 视频生成。

## Start Conditions

When the user says "写个剧本", "把故事改成剧本", "小说改剧本", "文字整理成剧本", "启动剧本流程", "拆成片段", "生成专业剧本", "保存成 Word", "输出 MD 和 Word", or provides a story/novel/text and asks for a script, start this workflow.

Ask up to 3 short questions only if the story is too vague to write:

- 类型：电影、短剧、漫剧、短视频、广播剧，还是其他？
- 风格：现实、悬疑、喜剧、爱情、科幻、奇幻、黑色幽默，还是其他？
- 规模：几分钟、几集、多少片段？

If enough story material is present, do not ask questions. Start writing.

## Standard Workflow

### 1. Plot Outline Extraction

At the beginning of the output, extract the plot outline before writing the screenplay.

Include:

- 一句话故事：用一句话说清主角、目标、阻力和结果方向。
- 故事主线：按因果关系概括开端、发展、转折、高潮、结尾。
- 关键事件：列出必须保留的事件，删除无戏剧功能的枝节。
- 人物关系：说明主角、男主/女主、反派、配角之间的关系和矛盾。
- 改编取舍：说明从小说/原始文字改成剧本时做了哪些压缩、合并或强化。
- 类型和情绪：说明适合的类型、节奏和观众情绪曲线。

### 2. Title and File Plan

Infer a concise, marketable Chinese title from the story.

Title rules:

- 2-12 个中文字符优先；长故事可用 12-18 个中文字符。
- 标题要体现主角、核心冲突、反转、情绪或类型感。
- 避免空泛标题，例如“一个故事”“新的开始”“命运”。
- If needed, provide 2-3 title candidates and choose the strongest one before writing.

File output rules:

- If the user specifies an output directory, use it.
- Otherwise create files under the current workspace in `剧本输出/<安全标题>_<YYYYMMDD-HHMMSS>/`.
- Sanitize filename characters that are unsafe on Windows: `\ / : * ? " < > |`.
- Create:
  - `<安全标题>.md`
  - `<安全标题>.docx`
- Do not overwrite existing files. If a file exists, append a timestamp or numeric suffix.
- The `.md` file must contain the full screenplay output.
- The `.docx` file must contain the same content with readable headings and paragraphs.
- Prefer a structured Word writer such as `python-docx`. If Word generation tooling is unavailable, still create the Markdown file and clearly explain why `.docx` could not be created.

### 3. Story Diagnosis

Briefly identify:

- 核心冲突
- 主角目标
- 主要阻力
- 情绪主线
- 结局方向
- 适合的叙事结构

### 4. Character Profile Task Table

Create a stable character profile for every important role. This is mandatory for role consistency, comic production, image prompting, and LoRA training.

Use this template:

```md
### 角色名：

- 年龄：
- 身份：
- 外貌：
- 发型：
- 服装：
- 性格：
- 口头禅：
- 情绪表达：
- 人物目标：
- 人物弱点：
- 与其他角色关系：
- 核心人物变化：
  - 初期：
  - 中期：
  - 后期：
- 不同时期人物性格身份：
  - 初期身份/性格：
  - 中期身份/性格：
  - 后期身份/性格：
- 绘图固定提示词：
- 禁止变化：
```

Rules:

- 女主、男主、反派、关键配角都要有角色档案。
- “核心人物变化”写角色弧光：初期是什么人，中期被什么改变，后期变成什么人。
- “不同时期人物性格身份”用于长篇一致性：角色身份、性格可以成长，但不能无理由突变。
- “绘图固定提示词”要稳定，便于 AI 生图、漫剧分镜和 LoRA 训练。
- “禁止变化”写清不能变的识别特征，例如发色、发型、标志服装、疤痕、饰品、体型、气质。
- 角色每次出场时，都必须沿用角色档案中的固定描述；如果剧情需要换装或状态变化，必须说明原因。

Success marker:

- 女主、男主、反派每次出场都有固定描述。
- 同一角色在不同片段中的外貌、发型、服装、口头禅、情绪表达和绘图固定提示词不冲突。
- 角色成长来自剧情压力，而不是随机改性格或改身份。

### 5. Segment Plan

For each segment, include:

- 片段编号
- 片段标题
- 场景地点
- 时间
- 天气/环境
- 出场人物
- 戏剧功能
- 本段目标
- 本段冲突
- 本段结尾钩子
- 出场人物固定描述
- 镜头设计

### 6. Screenplay

Use this format for every segment:

```md
## 片段 01：标题

**戏剧功能**：本段承担的剧情作用
**本段目标**：角色在本段想完成什么
**本段冲突**：阻碍来自谁或什么

【场景】地点，天气/环境，时间
【人物】人物 A（年龄，发型，服装，固定识别特征）；人物 B（年龄，发型，服装，固定识别特征）
【动作】人物在画面里能被看见的动作；冲突如何发生、升级或转折。
【台词】人物 A：（语气/状态）对白。
人物 B：（语气/状态）对白。
【镜头提示】景别、镜头运动、画面焦点、转场或运动效果。

**情绪推进**：说明本段人物关系或心理发生了什么变化。
**结尾钩子**：用一个动作、台词、发现或反转结束本段。
```

### 7. Quality Check

Before finalizing, verify:

- 是否已经在开头完成剧情大纲提炼。
- 每个正式剧本片段是否都包含【场景】【人物】【动作】【台词】【镜头提示】。
- 【镜头提示】是否具体写出景别、镜头运动、画面焦点或转场。
- 每个片段是否不超过 400 个中文字符。
- 每个片段是否有明确戏剧功能。
- 主角目标是否清楚。
- 冲突是否逐步升级。
- 人物行为是否符合动机。
- 对白是否像人在压力下说话。
- 是否已经建立人物设定角色档案。
- 女主、男主、反派每次出场是否都有固定描述。
- 角色外貌、发型、服装、性格、口头禅、情绪表达和绘图固定提示词是否前后一致。
- 结尾是否有继续观看的动力。
- Markdown 结构是否清晰。
- 文件输出计划是否清楚，且不会覆盖已有文件。

### 8. Save Files

After drafting and quality checking, write the final Markdown content to disk and generate the Word document.

Final response must include:

- 剧本标题
- Markdown 文件路径
- Word 文件路径
- 简短说明是否已成功创建

## Manju Workflow Mode

When invoked by `manju-production-workflow`, treat the screenplay output as the middle layer between PRD and storyboard production.

If a workflow project root is provided, use this folder layout:

```text
<项目名>/03_角色设定/角色档案.md
<项目名>/03_角色设定/角色固定提示词.md
<项目名>/04_分集大纲/<项目名>_分集大纲.md
<项目名>/05_剧本/第XX集_<标题>.md
<项目名>/05_剧本/第XX集_<标题>.docx
```

If the user provides a PRD file, read it as the production boundary:

- 题材、观众、爽点、集数、每集时长 must follow the PRD.
- 画风 and output format must be reflected in the role prompt and shot-ready descriptions.
- 禁止内容 and platform risks must be respected in dialogue and scenes.
- 本版不做 must not be silently added back into the story.

Create two role-oriented handoff files for 漫剧 projects:

1. `角色档案.md`: full character profiles for writing and consistency.
2. `角色固定提示词.md`: compact drawing prompts for repeated use in storyboard and image generation.

For each episode screenplay, add a `分镜交接信息` section before file output. It must include:

- 推荐片段名称列表, matching the segment titles in the screenplay.
- 主要出场人物 and their fixed visual descriptions.
- 场景清单, with visible time and location.
- 本集画风约束, aspect ratio, and image prompt notes.
- Suggested next command using `$script-to-storyboard` with the screenplay path and segment name.

Do not generate the storyboard table inside this skill unless the user explicitly asks to combine stages. Prefer handing off to `script-to-storyboard`.

## Tuzi API Multi-Model Workflow

Use the Tuzi API workflow only when the user explicitly asks to call models, use Tuzi API, or run the DeepSeek / Claude-GPT / Gemini pipeline.

### Safety Rules

- 明确告诉用户：调用会消耗兔子 API 余额，故事内容会发送到第三方 API。
- Do not expose, print, commit, or hard-code API keys.
- Read the API key from `TUZI_API_KEY`.
- Do not call external APIs if the key is missing; tell the user how to set it.
- Do not invent model names. Use user-provided names or currently available Tuzi model names.
- If a recommended model is unavailable, choose an available model of the same type and explain the replacement.

### Endpoint

Default OpenAI-compatible endpoint:

```text
https://api.tu-zi.com/v1
```

If a client requires the base URL without `/v1`, use:

```text
https://api.tu-zi.com
```

### Model Roles

Use real available model names from Tuzi API:

| Stage | Preferred model family | Purpose |
|---|---|---|
| 初稿 | DeepSeek 系列 | 快速扩写故事、拆片段、生成初稿 |
| 人物与对白 | Claude 或 GPT 系列 | 优化人物动机、人物关系、对白和情绪层次 |
| 长篇一致性 | Gemini 系列 | 检查时间线、设定规则、伏笔回收和逻辑断裂 |

### Prompt Templates

DeepSeek draft:

```md
你是专业电影编剧。请根据以下故事生成中文剧本初稿：
- 保持故事主线完整
- 拆成多个片段
- 每个片段不超过400个中文字符
- 输出Markdown
- 强调情节推进和冲突升级
```

Claude/GPT polish:

```md
你是电影导演和对白润色师。请基于以下剧本初稿优化人物和对白：
- 强化每个人物的目标、恐惧和选择
- 删除解释性对白
- 让对白更符合人物身份和当前压力
- 保持每个片段不超过400个中文字符
- 不改变主线逻辑，除非发现明显问题
```

Gemini consistency check:

```md
你是长篇剧本一致性审校。请检查以下中文剧本：
- 时间线是否矛盾
- 人物动机是否前后一致
- 世界观规则是否稳定
- 伏笔是否有回收
- 是否有重复、断裂或逻辑跳跃
- 给出问题清单和修改建议
```

## Default Output Structure

```md
# 剧本标题

## 1. 剧情大纲提炼

## 2. 标题与文件计划

## 3. 故事诊断

## 4. 人物设定角色档案

## 5. 片段总览

## 6. 正式剧本

## 7. 后续优化建议

## 8. 文件输出
```
