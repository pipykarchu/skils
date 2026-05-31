---
name: manju-workflow-dashboard
description: Create local HTML workflow dashboards for AI 漫剧/短剧 production pipelines, especially interview/demo boards with project information, ComfyUI-style node graphs/mind maps, operation steps, platform choices, review gates, and self-check QA. Use when the user wants “网页看板”, “工作流看板”, “可视化工作流”, “脑图”, “ComfyUI风格”, “面试演示”, “皮玺玉风格”, or a low-cost platform-selection board for MJ/Image2/即梦/可灵/Seedance/FFmpeg/剪映.
---

# Manju Workflow Dashboard

## Purpose

Generate an offline, local HTML dashboard that explains an AI 漫剧 production workflow end to end. Keep it practical and interview-ready: show project information, a ComfyUI-like node graph/mind map, what file enters each stage, which platform to use, how to confirm the output, and what self-check must pass before moving on.

## Default Output

Create an HTML file in the project, usually:

```text
<project>/01_生产SOP/workflow_dashboard.html
```

Also create an ASCII-named open script if helpful:

```text
<project>/01_生产SOP/open_workflow_dashboard.bat
```

Use offline HTML/CSS by default. Do not depend on CDN, Mermaid, login services, or remote assets unless the user asks.

## Interview/Demo Mode

Default new dashboards to an interview demonstration layout:

- Put project identity and production target in the first screen.
- Make the workflow graph the hero, visually similar to ComfyUI: dark canvas, connected nodes, colored node groups, compact ports, and visible flow from input to export.
- Include an explanation path for how to present the workflow in 3-5 minutes.
- Show both "what I operate" and "how I verify it": platform confirmation, acceptance criteria, fail conditions, and返工入口.
- Keep it local/offline so it can open during an interview without network risk.

## Dashboard Scope

Cover the full workflow:

1. 剧本导入
2. 分镜拆解
3. 角色/道具定版
4. 横版或竖版静帧出图
5. 图生视频平台选择
6. Seedance/可灵/即梦兜底策略
7. FFmpeg/剪映合成
8. B 站/抖音/红果版本导出
9. 验收审核
10. 自检返工

For each stage show:

- Input files
- Tool/platform
- Output files
- Confirmation method
- Fail conditions
- Next action

## Style

Default to “皮玺玉风格” unless the user specifies another visual style. Load `references/pixiyu-style.md` when detailed styling guidance is needed.

Core visual direction:

- Dark jade, ink black, muted gold, cyan-gray accents
- Cinematic, practical dashboard, not SaaS marketing
- Dense but readable cards/tables
- Low-glow borders, film-grain feeling, no decorative orb blobs
- Workflow is the hero; avoid oversized marketing sections
- ComfyUI-inspired node graph for workflow overview; avoid remote diagram libraries.

## Platform Decision Rules

Use this default platform logic:

- MJ/Image2: character boards, key stills, cover, prop close-ups
- 即梦: Chinese rural scenes, old village, bamboo forest, hall, graveyard stills
- 可灵: first choice for free/low-cost image-to-video tests
- Seedance 2: paid fallback only for highest-value dynamic shots
- FFmpeg: deterministic static-image motion and rough assembly
- 剪映/CapCut: subtitle, audio, final rhythm, manual polish

When budget matters, recommend:

1. Static-image rough cut first
2. Free/low-cost 可灵/即梦 dynamic tests
3. Seedance only for failed S-level shots
4. Export one horizontal master first, then crop vertical versions

## Workflow

1. Inspect project files: `05_剧本`, `06_分镜表`, `07_绘图提示词`, `09_素材与参考`, and existing SOP files.
2. Identify the production target: trailer, full episode, B 站横版, 抖音竖版, or multi-platform package.
3. Build stage data from actual project files when available. If files are missing, create sensible placeholders and mark them as pending.
4. Generate the dashboard HTML. Prefer the bundled script:

```powershell
python C:\Users\Administrator\.codex\skills\manju-workflow-dashboard\scripts\generate_dashboard.py --project-root "<project-path>"
```

5. Add or update a simple `.bat` opener if the path contains Chinese characters.
6. Validate by checking the HTML exists and contains: `面试演示版`, `ComfyUI式节点脑图`, `剧本导入`, `AI 视觉生产中枢`, `平台确认表`, and `验收审核与自检`.

## Bundled Resources

- `scripts/generate_dashboard.py`: deterministic offline HTML dashboard generator.
- `references/pixiyu-style.md`: visual rules for 皮玺玉风格.
- `references/acceptance-checks.md`: acceptance, audit, and self-check checklist.

Read references only when the user asks for deeper style, audit, or acceptance details.
