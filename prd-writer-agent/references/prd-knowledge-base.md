# PRD Knowledge Base

## PRD Purpose

PRD means Product Requirement Document. It is the shared blueprint for product, design, development, testing, operations, and stakeholders. A good PRD helps the team understand the product direction, reduce misunderstanding, avoid rework, and judge whether the final product meets user and market needs.

PRD differs from MRD and BRD:

- MRD focuses on market demand and user behavior.
- BRD focuses on business goals and commercial feasibility.
- PRD focuses on product execution and implementation clarity.

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
