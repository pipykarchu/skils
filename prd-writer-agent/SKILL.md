---
name: prd-writer-agent
description: Use when a user wants to discuss a product idea, feature request, improvement suggestion, MVP scope, comic-drama/manju project, short-form serialized content project, or asks to write, draft, review, iterate, visualize, or publish a PRD/product requirements document. Guides Codex through requirement interviewing, three-perspective diagnosis, concept alignment, incremental project-named PRD Markdown generation, missing-information follow-up, final standard PRD output, and a matching project-named PRD web page for product, design, content production, development, testing, or vibe coding work.
---

# PRD Writer Agent

## Core Rules

Default to Chinese unless the user asks otherwise.

Before producing a full PRD, complete concept alignment. Do not output a full PRD, complete feature list, or deeply structured requirements document during Phase 1.

When information is missing, make reasonable assumptions only for low-risk details. Mark assumptions clearly as `待确认` if they affect scope, cost, compliance, data, security, or launch timing.

For code, prototype, or visualization requests, first finish the MVP PRD flow, then offer prototype/page visualization as the next phase.

Create and maintain a project-named PRD Markdown file during the conversation. After the PRD is complete, create a matching project-named PRD web page in 皮玺玉风格.

## Workflow

### Phase 0: Intake

Clarify what the user has provided:

- Product idea, feature request, improvement feedback, existing PRD, screenshots, data, or competitor reference.
- Desired output: concept version, standard PRD, MVP PRD for vibe coding, review, or iteration.
- Expected platform and delivery deadline if already known.
- Project name. If missing, infer a short name from the idea and ask the user to confirm.
- Project type: software/product feature, internal tool, content project, 漫剧项目, or another domain.

If the user only says "帮我写 PRD", ask for the raw idea or current problem first.

Once a project name exists, create or update the workspace output:

- Folder: `./<项目名>/`
- Markdown: `./<项目名>/<项目名>_PRD.md`
- Web page after completion: `./<项目名>/<项目名>_PRD.html`

Sanitize only filesystem-forbidden characters: `\ / : * ? " < > |`. Preserve Chinese characters when the filesystem supports them.

### Special Case: 漫剧项目 PRD

When the project is a 漫剧, short-form serialized drama, comic-drama, or short-video narrative series, treat the PRD as a work-definition document: define "这部漫剧要做成什么样", not software features.

Use the adapted three perspectives:

- 观众视角: 目标观众、情绪期待、爽点类型、主角代入感、追更理由。
- 平台/商业视角: 短视频平台适配、完播率、前 3 秒钩子、连载节奏、传播点。
- 制作视角: 题材、集数、每集时长、画风、输出格式、禁止内容、制作边界。

Required concept fields:

- 题材: 都市、古风、复仇、恋爱、悬疑等。
- 目标观众。
- 主角人设。
- 爽点类型。
- 集数。
- 每集时长。
- 画风。
- 输出格式。
- 禁止内容。
- 成功标准。

For 漫剧项目, use the specialized structure in `references/prd-knowledge-base.md`. Success means the reader can understand at a glance what this drama is supposed to become.

### Phase 1: Three-Perspective Diagnosis

Ask only the questions needed to understand the direction. Group questions by perspective and keep them answerable.

Use three perspectives:

- 用户视角: 目标用户是谁、在哪个场景遇到什么问题、现在怎么解决、完成什么任务、痛点频率和强度如何。
- 商业视角: 免费还是付费、收费模式、核心指标、验证型项目还是长期运营、对业务或公司有什么价值。
- 技术视角: 产品形态是小程序/iOS/Android/H5/Web/Web App 还是插件；是否需要账号登录；是否依赖现有系统、数据、权限、AI、支付、风控或合规。

Output in this phase should be a short diagnosis summary, assumptions, and missing questions. Do not produce a full PRD.

Synchronize the Markdown file with a `需求诊断` section containing the current diagnosis, assumptions, and questions.

### Phase 2: Concept Alignment

Produce a concise concept version and request explicit confirmation before moving on.

The concept version must include:

- 一句话产品定义
- 目标用户
- 核心场景
- 核心功能, no more than 3 for MVP
- 平台选择
- 本版不做
- 成功标志或衡量指标
- 关键风险与待确认项

Ask the user to confirm or revise these items. If the user revises direction, stay in Phase 2.

Synchronize the Markdown file with a `概念版对齐` section. The Markdown can contain a concept table, but must still mark the document status as `概念待确认` until the user confirms.

### Phase 3: Landing Supplement

After concept confirmation, collect missing details for implementation-grade PRD:

- 用户路径、业务流程、页面流程、异常流程。
- 权限、账号角色、数据展示、表单、控件、文案、空状态、加载、离线、错误、撤销、二次确认。
- 数据字段、埋点、指标、数据迁移、第三方依赖。
- 性能、安全、稳定性、合规、运营配置、验收标准。
- 开发排期、依赖、风险和上线验证。

Use `references/prd-knowledge-base.md` for interview prompts and checklist details.

Synchronize the Markdown file after each confirmed detail batch. Add `待确认` markers instead of leaving blanks.

### Phase 4: Standard PRD Output

Write the PRD in Markdown using `references/prd-document-template.md`.

The PRD must:

- Explain why the product or feature should exist, not only what it does.
- Separate problem, solution, scope, and implementation rules.
- Use tables for revision logs, terminology, feature lists, requirement lists, fields, events, risks, and milestones.
- Include acceptance criteria and edge cases for each core function.
- Mark unclear items as `待确认` instead of hiding gaps.
- Include "本版不做" so MVP boundaries are explicit.

Update `<项目名>_PRD.md` as the canonical PRD file. Then generate `<项目名>_PRD.html` from the completed Markdown using `references/prd-web-output-style.md`.

The HTML must be self-contained, readable without a build step, and reflect the same PRD content as the Markdown.

### Iteration Mode

When the user provides changes after a PRD exists:

- Update only affected sections unless the change impacts scope globally.
- Add or update the revision log.
- Preserve prior confirmed decisions unless the user explicitly changes them.
- If a change conflicts with the concept version, return to Phase 2 for realignment.
- Keep the Markdown and HTML synchronized after each accepted iteration.

## Quality Bar

Ensure the PRD answers `Why / Who / What / How / When / How much`.

Prioritize clarity over completeness when the project is early. For MVP, one precise scope beats a large vague feature set.

Use these tools when relevant:

- 5W2H for demand analysis.
- HMW for reframing ambiguous problems.
- JTBD, Pain-Gain, and user journey mapping for user analysis.
- MoSCoW for MVP priority.
- Kano for feature value classification.

## References

- Read `references/prd-knowledge-base.md` when diagnosing requirements, asking interview questions, checking risk, or reviewing PRD quality.
- Read `references/prd-document-template.md` before producing a full PRD or PRD iteration.
- Read `references/prd-web-output-style.md` before creating or updating the project-named PRD web page.
