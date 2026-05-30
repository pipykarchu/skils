# PRD Knowledge Base

## PRD Purpose

PRD means Product Requirement Document. It is the shared blueprint for product, design, development, testing, operations, and stakeholders. A good PRD helps the team understand the product direction, reduce misunderstanding, avoid rework, and judge whether the final product meets user and market needs.

PRD differs from MRD and BRD:

- MRD focuses on market demand and user behavior.
- BRD focuses on business goals and commercial feasibility.
- PRD focuses on product execution and implementation clarity.

## 漫剧项目 PRD

When the user asks for a 漫剧项目 PRD, the PRD defines what the serialized work should become. It is not mainly a software requirements document. It should make the intended story, audience, emotional experience, production format, and acceptance standard clear at a glance.

### Required Inputs

Collect or infer these fields:

- 题材: 都市、古风、复仇、恋爱、悬疑等。
- 目标观众: age band, gender skew, platform habits, content preference.
- 主角人设: identity, desire, weakness, emotional wound, contrast, transformation path.
- 爽点类型: 复仇打脸、身份反转、逆袭、强情绪拉扯、甜宠、悬念、权谋、误会解除等。
- 集数.
- 每集时长.
- 画风: 韩漫感、国漫感、写实、强情绪、快节奏、电影感, etc.
- 输出格式: 竖屏/横屏, ratio, resolution, file format, subtitle/bubble requirements, delivery package.
- 禁止内容: forbidden topics, visual limits, platform compliance, violence/sexuality/minors/political/religious constraints.
- 成功标准: what makes the project pass review; what lets the team understand what to produce.

### Interview Questions

- 这部漫剧的一句话定位是什么?
- 目标观众是谁? 他们为什么会追更?
- 前 3 秒要用什么钩子抓住观众?
- 主角最强的代入点是什么? 他/她的欲望和弱点是什么?
- 最大爽点是什么? 是复仇、逆袭、身份反转、恋爱拉扯、悬疑解谜还是其他?
- 每集 60 秒内, 情绪节奏如何安排: 开场钩子、冲突升级、反转、结尾悬念?
- 30 集或指定集数中, 哪几集是关键反转点、高潮点和收束点?
- 画风要接近什么参考? 人物、镜头、色彩、分镜节奏有什么限制?
- 输出给谁使用: 编剧、分镜师、画师、剪辑、配音、投放团队还是平台审核?
- 有哪些内容绝对不能出现?
- 成功标准是一眼看懂作品定位, 还是需要满足完播率、点击率、追更率等平台指标?

### Recommended Structure

Use this structure for 漫剧 PRD:

1. 项目概述: project name, one-line positioning, genre, total episodes, duration per episode, target platform.
2. 目标观众: audience profile, emotional expectation, viewing scenario, why they continue watching.
3. 核心卖点: main hook, emotional promise,爽点类型, differentiation.
4. 人物设定: protagonist, antagonist, key supporting roles, relationships, character arcs.
5. 世界观与故事基调: setting, tone, conflict source, taboo boundaries.
6. 剧情结构: beginning, escalation, midpoint reversal, climax, ending or next-season hook.
7. 分集节奏: table by episode with core event, emotional beat, visual focus, ending hook.
8. 画面风格: art style, composition, color, panel rhythm, character expression, reference constraints.
9. 输出格式: aspect ratio, resolution, delivery files, subtitles, bubbles, naming, package structure.
10. 禁止内容: platform compliance and creative boundaries.
11. 验收标准: content, structure, visual, rhythm, format, and business success criteria.

### Episode Rhythm Table

Use this table for serialized planning:

| 集数 | 时长 | 核心事件 | 情绪节奏 | 爽点/钩子 | 画面重点 | 结尾悬念 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 60 秒 | [事件] | [开场钩子 -> 冲突 -> 反转] | [爽点] | [画面] | [悬念] |

### Example User Prompt

```text
帮我写一份漫剧项目 PRD。
题材：都市复仇爽文
集数：30集
每集：60秒
风格：韩漫感，强情绪，快节奏
目标：适合短视频平台连载
请包含人物设定、剧情结构、分集节奏、画面风格和验收标准。
```

### Success Standard

The PRD succeeds when a reader can immediately answer:

- 这部剧是什么题材?
- 给谁看?
- 主角是谁, 凭什么让观众代入?
- 每集靠什么爽点和钩子推动追更?
- 画面应该长什么样?
- 输出什么文件?
- 什么内容不能做?
- 怎么判断这部漫剧做对了?

## Core Writing Principles

- Start with why: explain the background, market or user problem, business connection, and value.
- State who benefits: identify target users, user scenarios, and user stories.
- Make scope explicit: list MVP scope and `本版不做`.
- Avoid vague wording: replace "支持", "优化", "友好", "完善" with observable behavior, rules, data, and acceptance criteria.
- Use tables for complex information: feature lists, fields, permissions, events, risks, and schedules.
- Include corner cases: empty state, loading, offline, errors, cancellation, rollback, timeout, duplicate actions, permissions, and account exceptions.
- Consider global rules: naming, copy tone, common interaction, cross-platform behavior, data consistency, and compliance.

## Recommended PRD Structure

Use this structure as a checklist, not as a rigid rule:

1. 文档说明: version, revision log, terminology.
2. 背景简介: product background, market/user problem, business relation, value.
3. 目标与范围: goals, success metrics, target users, platforms, MVP scope, out-of-scope.
4. 产品概念设计: product concept, feature structure, information architecture, product structure.
5. 流程说明: business flow, page flow, main path, branch path, exception path.
6. 全局说明: permissions, account roles, global interactions, copy, empty/loading/offline/error states.
7. 需求说明: requirement list, detailed rules, fields, interactions, acceptance criteria, edge cases.
8. 非功能需求: performance, reliability, security, compliance, operations, analytics, data.
9. 项目规划: roadmap, milestones, owner, dependencies, risks, launch validation.
10. 工作流设计: in the final standard PRD only, describe development collaboration and product runtime workflow without mixing the two.

## Workflow Design Section

Generate `工作流设计` only when producing the final standard PRD, or when iterating an existing PRD that already has this section. During diagnosis and concept alignment, record workflow facts as notes or `待确认`.

Include this section when the project involves AI models, third-party API providers, tool routing, multi-agent collaboration, runtime pipelines, or implementation milestones.

The section should separate:

- 开发工作流: who/what builds, reviews, tests, and ships the project.
- 产品运行工作流: how the actual product processes user input and produces output.
- 模型与工具路由: which model/tool handles each task, fallback choices, and volatile provider assumptions.
- 配置与安全: API keys, base URLs, privacy, sensitive data, and third-party risk.
- AI 开发成本、产出预估与 ROI: for AI-assisted development, estimate cost and expected outputs before execution, track development-stage tokens/spend/output by platform/tool/model during execution, including Codex and Claude when used, then define benefit metrics for later ROI calculation.

For AI development cost tracking:

- Estimate before execution, then compare estimates with actuals after each milestone.
- Track by platform/tool/model and by stage when possible.
- Include input tokens, output tokens, cache/thinking/other platform-specific tokens, total tokens, amount, currency, pricing source, pricing date, and data source.
- Estimate expected outputs: PRDs, technical designs, features, pages, APIs, tests, scripts, prompts, reusable components, and business or efficiency outcomes.
- Label the estimate level: rough estimate, planning estimate, execution estimate, or actual.
- Distinguish actual billing data from estimates.
- Mark missing values as `待统计` or `待确认`.
- Do not invent usage or billing numbers. Ask for explicit permission before accessing external billing dashboards, invoices, exports, or accounts.
- Include ROI-ready benefit metrics when relevant: saved labor hours, avoided outsourcing cost, faster delivery value, generated revenue, operating cost reduction, reduced rework, or efficiency gains.
- Use a clear ROI formula, such as `AI 开发 ROI = (AI 产生总收益 - AI 开发总成本) / AI 开发总成本 * 100%`.
- For estimated benefits, record baseline, post-AI result, measurement window, data source, confidence level, and assumptions.

When users update tool choice, model provider, API routing, role division, runtime steps, milestones, privacy/security rules, token usage, development cost, output estimates, benefit assumptions, or ROI calculation, update `工作流设计` and the revision log.

## Requirement Interview Prompts

### Product Direction

- 这个产品或功能想解决的核心问题是什么?
- 用户现在怎么解决这个问题? 当前方案哪里不够好?
- 目标用户是谁? 是否能描述 1-3 个典型用户画像?
- 最关键的使用场景是什么? 发生频率和痛感强度如何?
- 这个产品最终希望达成什么结果? 有哪些可量化指标?

### Business Perspective

- 这是免费产品还是付费产品?
- 如果收费, 是一次性买断、订阅、会员增值还是交易抽佣?
- 这是验证型项目还是长期运营项目?
- 对业务、收入、留存、效率、品牌或战略有什么价值?
- 有哪些商业、运营、法务、合规或风控风险?

### Technical Perspective

- 产品形态是什么: 小程序、iOS、Android、H5、Web、Web App、插件、桌面端?
- 是否需要账号、登录、角色、权限或会员体系?
- 是否依赖现有系统、第三方服务、AI 能力、支付、消息、地图、文件、风控?
- 是否有数据存储、数据迁移、埋点、报表、隐私或安全要求?
- 是否有性能、稳定性、兼容性、设备权限或网络要求?

### MVP Scope

- 如果只做一个最小可用版本, 必须保留哪 1-3 个功能?
- 哪些功能只是增强体验, 可以后置?
- 哪些用户路径必须打通才算成功?
- 哪些异常情况必须覆盖才可以上线?
- 本版明确不做什么?

## Analysis Methods

- 5W2H: Why, What, Who, When, Where, How, How much.
- HMW: turn vague problems into solvable questions, such as "How might we reduce the manual review time for operators?"
- JTBD: identify the job the user wants to complete.
- Pain-Gain Map: map pain points to gains and opportunities.
- User Journey Mapping: split the user's path from trigger to completion.
- Function vs Need: avoid listing features without mapping them to user or business needs.
- MoSCoW: classify features into Must, Should, Could, Won't.
- Kano: classify features into basic, performance, excitement, indifferent, and reverse.

## Requirement Self-Check

### Demand Authenticity

- Does it match the core business scenario?
- Does it match user personas and user stories?
- Is there competitor evidence or user data?
- Is it a common need in similar scenarios or a one-off request?

### Quantified Value

- Can impact on core users be quantified?
- Can business contribution be quantified?
- Does it affect KPI, revenue, retention, cost, efficiency, risk, or user satisfaction?

### Feasibility

- Can current technology support it?
- Can the business or operation line support it?
- Are dependencies, cost, timeline, and resources clear?

### Risk

- Will related functions be affected?
- Will launch affect current planned work?
- Is there traffic peak, abuse, fraud, compliance, legal, security, or public opinion risk?
- Is there a clear validation method after launch?

### Priority

Consider user coverage, usage frequency, core scenario impact, core user impact, income, KPI, and product health.

## Interaction and Detail Checklist

### Flow

- List operation nodes and data interaction nodes.
- Check whether each operation is easy to understand.
- Cover second confirmation, undo, cancellation, and rollback when needed.
- Cover branch flow, reverse flow, and exception flow.
- Keep user experience path consistent.
- Mark key nodes and avoid broken flow lines.

### Page and Global States

- Define page entry, exit, transition, back path, and jump rules.
- Define empty, loading, offline, timeout, error, no-permission, no-data, and deleted states.
- Define mobile gestures such as iOS swipe back when relevant.
- Define whether web pages need to show more information or support repeated operations.

### Copy

- Copy must be clear, meaningful, typo-free, and consistent with product tone.
- Error copy should tell users what happened and what they can do next.

### Data Display

- State whether displayed data comes from server, local cache, or mixed sources.
- Define initial loading, static, real-time, scheduled, and dynamic data.
- Define empty data display and user guidance.
- Define long text truncation, numeric format, sensitive data masking, permission-value display, and expired cache prompts.
- Define sorting, filtering, pagination, and single-page data limits.

### Forms and Controls

- Define default values, placeholder, validation, length limits, special characters, sensitive words, keyboard type, and one-click clear.
- Define focus loss behavior and whether input records survive interruption.
- Define disabled state, success/failure feedback, cancelability, animation, and trigger type: red dot, toast, modal, or page notice.

### Media Input

- Define size, format, required parameters, invalid hints, upload progress, preview, re-edit, retry after failure, and whether uploaded records persist after interruption.

### Popups and Carousel

- Define trigger timing, close methods, copy, jump behavior, repeat trigger rules, and priority with other popups.
- For carousel, define data source, sorting, jump target, and display frequency.

### Special Factors

- Account: login, logout, account abnormality, membership level, paid status, account switching, multi-device conflict.
- Network: WiFi, mobile network, public network, timeout, retry, and network-change prompts.
- Server: failed data return, retry, degraded mode.
- Hardware: screen orientation, resolution, storage, SD card, hardware buttons, OS versions.
- Permissions: location, camera, microphone, album, notification, Bluetooth, or other system permissions.

## AI-Assisted PRD Workflow

Use AI in three steps:

1. 拆解需求: define problem, goal, judgment criteria, constraints.
2. 用户分析: cluster feedback, competitor findings, and data into user personas, pain points, hidden needs, and opportunities.
3. 功能梳理: convert concept into MVP feature modules, user paths, value mapping, dependencies, and priority.

AI can later help generate prototypes, but prototype work should follow confirmed MVP PRD scope.
