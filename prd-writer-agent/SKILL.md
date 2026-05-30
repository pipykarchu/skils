---
name: prd-writer-agent
description: Use when a user wants to discuss a product idea, feature request, improvement suggestion, MVP scope, or asks to write, draft, review, or iterate a PRD/product requirements document. Guides Codex through requirement interviewing, three-perspective diagnosis, concept alignment, missing-information follow-up, and final standard PRD output for product, design, development, testing, or vibe coding work.
---

# PRD Writer Agent

## Core Rules

Default to Chinese unless the user asks otherwise.

Before producing a full PRD, complete concept alignment. Do not output a full PRD, complete feature list, or deeply structured requirements document during Phase 1.

When information is missing, make reasonable assumptions only for low-risk details. Mark assumptions clearly as `待确认` if they affect scope, cost, compliance, data, security, or launch timing.

For code, prototype, or visualization requests, first finish the MVP PRD flow, then offer prototype/page visualization as the next phase.

## Workflow

### Phase 0: Intake

Clarify what the user has provided:

- Product idea, feature request, improvement feedback, existing PRD, screenshots, data, or competitor reference.
- Desired output: concept version, standard PRD, MVP PRD for vibe coding, review, or iteration.
- Expected platform and delivery deadline if already known.

If the user only says "帮我写 PRD", ask for the raw idea or current problem first.

### Phase 1: Three-Perspective Diagnosis

Ask only the questions needed to understand the direction. Group questions by perspective and keep them answerable.

Use three perspectives:

- 用户视角: 目标用户是谁、在哪个场景遇到什么问题、现在怎么解决、完成什么任务、痛点频率和强度如何。
- 商业视角: 免费还是付费、收费模式、核心指标、验证型项目还是长期运营、对业务或公司有什么价值。
- 技术视角: 产品形态是小程序/iOS/Android/H5/Web/Web App 还是插件；是否需要账号登录；是否依赖现有系统、数据、权限、AI、支付、风控或合规。

Output in this phase should be a short diagnosis summary, assumptions, and missing questions. Do not produce a full PRD.

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

### Phase 3: Landing Supplement

After concept confirmation, collect missing details for implementation-grade PRD:

- 用户路径、业务流程、页面流程、异常流程。
- 权限、账号角色、数据展示、表单、控件、文案、空状态、加载、离线、错误、撤销、二次确认。
- 数据字段、埋点、指标、数据迁移、第三方依赖。
- 性能、安全、稳定性、合规、运营配置、验收标准。
- 开发排期、依赖、风险和上线验证。

Use `references/prd-knowledge-base.md` for interview prompts and checklist details.

### Phase 4: Standard PRD Output

Write the PRD in Markdown using `references/prd-document-template.md`.

The PRD must:

- Explain why the product or feature should exist, not only what it does.
- Separate problem, solution, scope, and implementation rules.
- Use tables for revision logs, terminology, feature lists, requirement lists, fields, events, risks, and milestones.
- Include acceptance criteria and edge cases for each core function.
- Mark unclear items as `待确认` instead of hiding gaps.
- Include "本版不做" so MVP boundaries are explicit.

### Iteration Mode

When the user provides changes after a PRD exists:

- Update only affected sections unless the change impacts scope globally.
- Add or update the revision log.
- Preserve prior confirmed decisions unless the user explicitly changes them.
- If a change conflicts with the concept version, return to Phase 2 for realignment.

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
