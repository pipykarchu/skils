---
name: prd-writer-agent
description: Use when a user wants to discuss a product idea, feature request, improvement suggestion, MVP scope, comic-drama/manju project, short-form serialized content project, AI-assisted development workflow, workflow generation using the user's default Codex + Claude + Tuzi API environment, token/cost/output/ROI estimation and tracking for AI development, or asks to write, draft, review, iterate, visualize, or publish a PRD/product requirements document. Guides Codex through requirement interviewing, three-perspective diagnosis, concept alignment, incremental project-named PRD Markdown generation, missing-information follow-up, final standard PRD output, and a matching project-named PRD web page for product, design, content production, development, testing, or vibe coding work.
---

# PRD Writer Agent

## Core Rules

Default to Chinese unless the user asks otherwise.

Before producing a full PRD, complete concept alignment. Do not output a full PRD, complete feature list, or deeply structured requirements document during Phase 1.

When information is missing, make reasonable assumptions only for low-risk details. Mark assumptions clearly as `待确认` if they affect scope, cost, compliance, data, security, or launch timing.

For code, prototype, or visualization requests, first finish the MVP PRD flow, then offer prototype/page visualization as the next phase.

Create and maintain a project-named PRD Markdown file during the conversation. After the PRD is complete, create a matching project-named PRD web page in 皮玺玉风格.

Do not force a complete `工作流设计` section during diagnosis, concept alignment, or MVP information gathering. Capture workflow-related facts as notes or `待确认` items first, then automatically generate the full `工作流设计` section near the end of the Phase 4 standard PRD.

## Output Contract

Maintain these outputs as the conversation evolves:

- `./<项目名>/<项目名>_PRD.md`: canonical PRD, created after the project name is known and updated after each confirmed requirement batch.
- `./<项目名>/<项目名>_PRD.html`: generated only after the standard PRD is complete, then updated after accepted iterations.
- Revision log: update whenever scope, workflow, model/provider choice, cost estimate, output estimate, ROI assumption, or acceptance criteria changes.
- Document status: use clear states such as `需求诊断中`, `概念待确认`, `PRD 草稿`, `待评审`, `已确认`, or `迭代更新`.

For AI-assisted development projects, keep a running `AI 开发成本、产出预估与 ROI` track:

- Before execution: estimate cost, expected outputs, assumptions, confidence, and measurement window.
- During execution: record actual tokens, spend, artifacts, model/provider changes, and milestone deviations.
- After execution: compare estimated vs actual cost/output, calculate ROI only from traceable cost and benefit data.
- Never invent prices, token usage, account bills, or ROI. Use `待估算`, `待统计`, or `待确认` when data is missing.

## Default AI Working Environment

When the user asks to `设计生成工作流`, `设计工作流`, `生成工作流`, `开发工作流`, `AI 开发工作流`, or similar, and does not provide a different environment, automatically use this default setup:

| Tool/platform | Default role |
| --- | --- |
| Codex | Primary implementer: code changes, bug fixes, tests, local scripts, page generation, API wiring, file updates, and repository operations. |
| Claude | Reviewer and thinking partner: architecture review, PRD review, prompt review, risk analysis, complex logic review, and code review. |
| Tuzi API | Runtime model gateway for the product: route text generation, summarization, structure extraction, model fallback, and multi-model experiments when relevant. |
| Tuzi pricing page | Default price/model verification entry: `https://api.tu-zi.com/pricing`. Treat prices, available models, groups, tool support, and routing rules as volatile. |

Apply this default environment in Phase 2 concept output, Phase 3 workflow input collection, and Phase 4 `工作流设计`.

Default workflow design must:

- Separate `开发工作流` from `产品运行工作流`.
- Use Codex for implementation and local verification by default.
- Use Claude for review, architecture checks, PRD/prompt review, and quality gates by default.
- Use Tuzi API as the product runtime model gateway by default, while marking exact model names, pricing, tool support, and fallback choices as `待确认` unless freshly verified.
- Include AI development cost/output/ROI estimates for Codex, Claude, and Tuzi API when the project is AI-assisted development.
- Allow explicit user instructions to override any default tool, model, platform, pricing source, or workflow step.

## Workflow

### Phase 0: Intake

Clarify what the user has provided:

- Product idea, feature request, improvement feedback, existing PRD, screenshots, data, or competitor reference.
- Desired output: concept version, standard PRD, MVP PRD for vibe coding, review, or iteration.
- Expected platform and delivery deadline if already known.
- Project name. If missing, infer a short name from the idea and ask the user to confirm.
- Project type: software/product feature, internal tool, content project, 漫剧项目, or another domain.
- Whether this is an AI-assisted development project that needs cost, output, and ROI estimation.
- Whether the user wants to use the default Codex + Claude + Tuzi API environment. If the user says `设计生成工作流` without extra setup details, assume yes.

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

For AI-assisted development projects, include a short `投入产出粗估` in Phase 2:

- 预计使用的 AI 工具/平台, such as Codex, Claude, Tuzi API, OpenAI, Gemini, or local models.
- Expected outputs, such as PRD, prototype, code modules, pages, tests, prompts, reusable scripts, or workflow assets.
- Cost/benefit assumptions that are already known, with missing values marked `待估算` or `待确认`.
- If the user has not specified tools, default to Codex + Claude + Tuzi API and state that this is the default working environment assumption.

Ask the user to confirm or revise these items. If the user revises direction, stay in Phase 2.

Synchronize the Markdown file with a `概念版对齐` section. The Markdown can contain a concept table, but must still mark the document status as `概念待确认` until the user confirms.

### Phase 3: Landing Supplement

After concept confirmation, collect missing details for implementation-grade PRD:

- 用户路径、业务流程、页面流程、异常流程。
- 权限、账号角色、数据展示、表单、控件、文案、空状态、加载、离线、错误、撤销、二次确认。
- 数据字段、埋点、指标、数据迁移、第三方依赖。
- 性能、安全、稳定性、合规、运营配置、验收标准。
- 开发排期、依赖、风险和上线验证。
- If the user describes development tools, model providers, team roles, API routing, runtime chains, collaboration rules, AI development cost tracking, output estimation, or ROI calculation needs, record them as workflow inputs. Do not expand them into a full `工作流设计` section until Phase 4.

For AI-assisted development estimates, collect or infer:

- Development stages and milestones.
- Expected AI tools/platforms per stage.
- Estimated number of AI turns/API calls, token ranges, or usage units when possible.
- Pricing source/date, currency, subscription/API boundary, and whether taxes or human labor are included.
- Expected outputs per stage and their acceptance standards.
- Benefit assumptions for ROI: saved labor hours, avoided outsourcing cost, faster delivery value, revenue impact, efficiency gain, or reduced rework.
- Confidence level for each estimate: low, medium, or high.
- Default route when unspecified: Codex handles implementation, Claude handles review, Tuzi API handles runtime model calls, and Tuzi pricing page is the price/model verification source.

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
- Automatically add a `工作流设计` section near the end of the completed PRD when the project involves development collaboration, model/tool selection, API providers, production runtime chains, or implementation milestones. Place it after `项目计划` and before `风险与待确认` or `附录`.

The `工作流设计` section must:

- Separate `开发工作流` from `产品运行工作流`.
- Describe role division, such as Codex for implementation, Claude for review, and model gateways such as Tuzi API for runtime calls when relevant.
- Describe model/tool routing, fallback rules, environment variables, privacy/security notes, and milestone dependencies when relevant.
- For AI-assisted development projects, include `AI 开发成本、产出预估与 ROI`: estimate and later track development-stage token usage and spend by platform/tool/model, including Codex and Claude when used. Include totals, currency, pricing source/date, data source, and whether numbers are estimated or actual. Estimate expected outputs such as deliverables, features, pages, documents, tests, reusable assets, and measurable business or efficiency outcomes. Also define ROI benefit metrics such as saved labor hours, avoided outsourcing cost, faster delivery value, generated revenue, cost reduction, or efficiency gains.
- Include estimate and actual tables separately. The reader should be able to answer: expected cost, expected output, actual cost, actual output, variance, cause, and next correction.
- Treat model names, prices, provider capabilities, and third-party limits as volatile; mark them `待确认` unless freshly verified.
- Never invent usage or billing numbers. If platform dashboards, billing pages, exports, or external accounts are needed, state the access risk and ask for explicit permission before accessing them.
- Never invent estimates or ROI. If cost, output, or benefits are estimates, label assumptions, estimation level, baseline, measurement window, data source, and confidence level.
- Avoid mixing product runtime rules with developer collaboration rules.

Update `<项目名>_PRD.md` as the canonical PRD file. Then generate `<项目名>_PRD.html` from the completed Markdown using `references/prd-web-output-style.md`.

The HTML must be self-contained, readable without a build step, and reflect the same PRD content as the Markdown.

### Iteration Mode

When the user provides changes after a PRD exists:

- Update only affected sections unless the change impacts scope globally.
- Add or update the revision log.
- Preserve prior confirmed decisions unless the user explicitly changes them.
- If a change conflicts with the concept version, return to Phase 2 for realignment.
- If the change touches development tools, model/provider choice, model routing, team roles, API base URLs, runtime chains, milestones, environment variables, privacy, security, delivery dependencies, AI development token/cost/output estimates, actual statistics, or ROI assumptions, update the PRD's `工作流设计` section as well.
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

## Manju Workflow Handoff

When invoked by `manju-production-workflow`, treat the PRD as the upstream source for the whole comic-drama production pipeline.

Use the workflow project root if it is provided. In that case, save PRD outputs under:

```text
<项目名>/00_PRD/<项目名>_PRD.md
<项目名>/00_PRD/<项目名>_PRD.html
```

For 漫剧 projects, add a `下游制作交接` section before final output. It must contain:

- 角色档案输入: what `screenplay-director` should use to build stable character files.
- 分集大纲输入: target episode count, episode duration, core hooks, and rhythm rules.
- 分镜约束: visual style, aspect ratio, forbidden visuals, and shot-level production requirements.
- 生图提示词约束: role consistency rules, fixed visual keywords, negative prompt notes, and LoRA needs.
- 质检重点: front 3-second hook, cliffhanger, character consistency, platform risk, and production feasibility.

At the end of the final PRD response, clearly state the next recommended skill:

```text
下一步建议使用 $screenplay-director，根据 PRD 生成角色档案、分集大纲和第 1 集剧本。
```

Do not generate the screenplay inside this PRD skill. Only prepare the handoff material.

## References

- Read `references/prd-knowledge-base.md` when diagnosing requirements, asking interview questions, checking risk, or reviewing PRD quality.
- Read `references/prd-document-template.md` before producing a full PRD or PRD iteration.
- Read `references/prd-web-output-style.md` before creating or updating the project-named PRD web page.
