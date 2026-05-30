---
name: screenplay-director
description: Turn a story, outline, synopsis, character idea, or rough plot into a professional Chinese screenplay in Markdown. Use when the user wants to write a script, generate a screenplay, split a story into scenes or segments under 400 Chinese characters each, polish character dialogue, or run a Tuzi API multi-model workflow where DeepSeek drafts, Claude/GPT improves characters and dialogue, and Gemini checks long-form consistency.
---

# Screenplay Director

Convert the user's story into a logical, professional, shootable Chinese screenplay.

## Default Rules

- 默认用中文输出剧本、人物设定、对白、审校意见和修改建议。
- 先用大白话说明本次写作目的，再输出具体剧本内容。
- 输出 Markdown.
- 每个正式剧本片段不超过 400 个中文字符；如果内容过长，拆成更多片段。
- 每个片段必须有明确戏剧功能：铺垫、冲突、转折、情绪推进、信息揭示、高潮或收束。
- 保持人物动机一致，避免角色为了剧情强行行动。
- 对白要符合人物身份、关系、情绪和场景压力。
- 优先写可见动作、可拍摄画面和可表演对白，少用解释性旁白。
- 片段之间必须有因果关系，每段结尾尽量留下钩子。

## Start Conditions

When the user says "写个剧本", "把故事改成剧本", "启动剧本流程", "拆成片段", "生成专业剧本", or provides a story and asks for a script, start this workflow.

Ask up to 3 short questions only if the story is too vague to write:

- 类型：电影、短剧、漫剧、短视频、广播剧，还是其他？
- 风格：现实、悬疑、喜剧、爱情、科幻、奇幻、黑色幽默，还是其他？
- 规模：几分钟、几集、多少片段？

If enough story material is present, do not ask questions. Start writing.

## Standard Workflow

### 1. Story Diagnosis

Briefly identify:

- 核心冲突
- 主角目标
- 主要阻力
- 情绪主线
- 结局方向
- 适合的叙事结构

### 2. Character Table

List main characters with:

- 角色定位
- 目标
- 恐惧或弱点
- 与其他角色的关系
- 本剧中的变化

### 3. Segment Plan

For each segment, include:

- 片段编号
- 片段标题
- 场景地点
- 时间
- 出场人物
- 戏剧功能
- 本段目标
- 本段冲突
- 本段结尾钩子

### 4. Screenplay

Use this format for every segment:

```md
## 片段 01：标题

**场景**：地点 / 时间
**人物**：人物 A、人物 B
**戏剧功能**：本段承担的剧情作用

【画面】
描述可拍摄的视觉动作、环境、人物状态。

【行动】
人物做了什么，冲突如何发生或升级。

【对白】
人物 A：对白。
人物 B：对白。

【情绪推进】
说明本段人物关系或心理发生了什么变化。

【结尾钩子】
用一个动作、台词、发现或反转结束本段。
```

### 5. Quality Check

Before finalizing, verify:

- 每个片段是否不超过 400 个中文字符。
- 每个片段是否有明确戏剧功能。
- 主角目标是否清楚。
- 冲突是否逐步升级。
- 人物行为是否符合动机。
- 对白是否像人在压力下说话。
- 结尾是否有继续观看的动力。
- Markdown 结构是否清晰。

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

## 1. 故事诊断

## 2. 人物表

## 3. 片段总览

## 4. 正式剧本

## 5. 后续优化建议
```
