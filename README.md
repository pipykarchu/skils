# Codex Skills

这个仓库用于存放可安装到 Codex 的个人 skill。每个 skill 是一个独立目录，目录里至少包含 `SKILL.md`。

## 安装方式

把需要的 skill 目录复制到本机 Codex skills 目录：

```text
C:\Users\Administrator\.codex\skills\
```

成功标志：

```text
C:\Users\Administrator\.codex\skills\<skill-name>\SKILL.md
```

例如：

```text
C:\Users\Administrator\.codex\skills\screenplay-director\SKILL.md
```

## Skill 列表

| Skill 名称 | 什么时候激活 | 简单用法 |
|---|---|---|
| `prd-writer-agent` | 想把产品想法、功能需求、MVP、改进建议、漫剧项目需求或 AI 开发工作流整理成 PRD 时使用。它会先做需求访谈和概念对齐，持续维护项目命名 PRD Markdown，完整版完成后生成皮玺玉风格 PRD 网页；用户说“设计生成工作流”时默认带入 Codex + Claude + Tuzi API；AI 开发项目会同步估算和记录成本、产出、ROI。 | `$prd-writer-agent 帮我把一个 AI 视频学习助手整理成 MVP PRD，并设计生成工作流` |
| `screenplay-director` | 想把故事、小说片段或散乱文字整理成中文专业剧本时使用。它会先提炼剧情大纲，自动起标题，建立人物设定角色档案，并按【场景】【人物】【动作】【台词】【镜头提示】输出，保持男女主和反派出场描述一致，创建 Markdown 和 Word 文件。 | `$screenplay-director 把这段小说整理成专业剧本，要求每段包含场景、人物、动作、台词和镜头提示` |
| `script-to-storyboard` | 想把剧本、小说片段、Word、PDF、Markdown 或网页内容拆成客观分镜头脚本，并输出可用于 AI 生图的 MD/Excel 分镜表时使用。 | `$script-to-storyboard 根据剧本文件和片段名称“妈妈病了”建立新的 MD 和 Excel 分镜脚本` |
| `storyboard-image-prompts` | 想根据剧本、世界观、分镜表、角色档案或漫剧短剧分镜生成 AI 绘图提示词，并按人物、场景、世界观规则、连续性和生产平台选择合适模型时使用。 | `$storyboard-image-prompts 根据这份剧本、世界观和分镜表生成绘图提示词，并推荐每镜使用的平台和模型` |
| `dingzhuangzao` | 想做漫剧角色定妆、角色正面肖像候选、Gemini/Image2/MJ 提示词、统一视觉评审网页、多选标心、锁脸/身体/衣服/发型、左栏平台 Key 本地保存、确认造型后三视图高清导出和总览拼图时使用。它会先读取世界观、年代设定、场景和角色资料，服装造型必须贴合项目设定。 | `$dingzhuangzao 读取这个漫剧项目的世界观和角色设定，先给每个角色生成四张正面定妆候选并做统一视觉评审页` |
| `changjingmeishu` | 想锁定漫剧场景美术、场地/子场景/关键道具参考图、氛围/色调/构图/建筑倾向、同一空间不同角度/时段/天气一致性，或把场景/道具模块并入定妆造同一个视觉评审网页并生成 `scene-anchors.json` 时使用。 | `$changjingmeishu 根据这个项目的世界观和分镜，把核心场景和关键道具并入统一视觉评审页` |
| `renjingheyi` | 想把已锁定的人物三视图、场景/道具参考图和 `07_绘图提示词` 逐镜融合成最终镜头图，并用网页评审确认镜头图时使用。 | `$renjingheyi 读取第1集提示词、人物三视图和场景定版，逐镜生成人景合一镜头图` |
| `manju-production-workflow` | 想从 0 到 1 做完整漫剧生产流水线时使用。它会协调 PRD、SOP、剧本、角色定妆、场景美术、分镜、绘图提示词、人景合一镜头图、视频生成、质检和流程看板；支持 Codex×Claude 按阶段分工。 | `$manju-production-workflow 启动漫剧项目《重生后我不再忍了》，题材都市复仇，30集，每集60秒` |
| `manju-workflow-dashboard` | 想把漫剧生产流程做成面试演示用本地 HTML 网页看板，展示项目信息、ComfyUI式节点脑图、平台选择、操作步骤、成片验收和自检时使用。 | `$manju-workflow-dashboard 给这个漫剧项目生成皮玺玉风格 ComfyUI 节点工作流看板` |

## 简单判断

- 要写产品需求文档、漫剧项目 PRD、AI 开发工作流、成本产出估算或 ROI 统计，用 `prd-writer-agent`；说“设计生成工作流”时默认使用 Codex + Claude + Tuzi API。
- 要把故事、小说或文字整理成专业剧本，并保存成 Markdown/Word，用 `screenplay-director`。
- 要按专业格式输出【场景】【人物】【动作】【台词】【镜头提示】，用 `screenplay-director`。
- 要稳定女主、男主、反派的人物设定、绘图固定提示词和禁止变化特征，也用 `screenplay-director`。
- 要把已有剧本按片段拆成镜号、时长、景别、运镜、画面内容提示词、人物台词和备注，用 `script-to-storyboard`。
- 要根据剧本、世界观、角色设定和分镜生成绘图提示词，并为不同人物、场景选择 Midjourney、OpenAI Images、Gemini/Imagen、Runway、可灵、即梦、通义万相、混元或 SD/FLUX/ComfyUI，用 `storyboard-image-prompts`。
- 要做角色定妆照、四张正面候选图、网页标心选择、Gemini Image/Image2/MJ 三版本提示词、确认造型后三视图和高清总览，用 `dingzhuangzao`。
- 要锁定场景、子场景、关键道具、空间锚点和 `scene-anchors.json`，用 `changjingmeishu`。
- 要把人物三视图、场景/道具定版和逐镜提示词融合成镜头图，用 `renjingheyi`。
- 要完整跑 PRD、SOP、剧本、角色定妆、场景美术、分镜、提示词、人景合一、视频生成、质检和流程看板，用 `manju-production-workflow`。
- 要把漫剧生产流程做成面试演示网页看板、展示项目信息、ComfyUI式节点脑图、平台选择、确认点、验收和自检，用 `manju-workflow-dashboard`。

## 0-1 漫剧工作流索引

README 就是本仓库的本地索引。完整漫剧项目从故事到成片，默认按下面 skill 顺序调度：

| 阶段 | 任务 | 引擎 | 执行方式 |
|---|---|---|---|
| 编排 | 目录 / 状态 / 调度 | Codex | 总控 |
| 1 | PRD | Codex 起草 + Claude 评审 | `prd-writer-agent` |
| 2 | 生产 SOP | Codex | 总控 |
| 3 | 角色 + 剧本 | Claude | `screenplay-director` |
| 3.5 | 角色定妆 | Claude 提示词 + Codex 执行 | `dingzhuangzao`，写入统一视觉评审页 |
| 3.6 新 | 道具场景定版 | Claude 提示词 + Codex 执行 | `changjingmeishu`，并入统一视觉评审页 |
| 4 | 分镜 | Codex + Claude 审查 | `script-to-storyboard` |
| 5 | 生图提示词 | Claude 定一致性 + Codex 格式化 | `storyboard-image-prompts` |
| 6 | 质检 | Claude | 总控落盘 |
| 6.5 新 | 人景合一镜头图 | Codex 构建 manifest + Claude 审查 | `renjingheyi` |
| 7 新 | 视频生成 | Claude 运镜/审查 + Codex 调 API/合成 | 内联（外部生视频 API / FFmpeg / 剪映） |
| 8 | 流程看板 | Codex | `manju-workflow-dashboard` |

详细顺序：

1. `prd-writer-agent`：项目定义、PRD、验收标准。
2. `manju-production-workflow`：总控、目录、状态、SOP、阶段调度。
3. `screenplay-director`：角色档案、分集大纲、剧本。
4. `dingzhuangzao`：角色定妆、候选评审、三视图。
5. `changjingmeishu`：场景美术、关键道具、空间锚点、`scene-anchors.json`。
6. `script-to-storyboard`：剧本转分镜。
7. `storyboard-image-prompts`：分镜生图提示词。
8. `renjingheyi`：人物、场景、道具逐镜融合成镜头图。
9. `manju-production-workflow`：视频片段、成片合成、质检验收。
10. `manju-workflow-dashboard`：流程看板、面试演示、复盘。

分工原则：

- Codex 负责总控、文件落盘、路径验证、脚本、manifest、网页、自动化和推送。
- Claude 负责创作、口吻、戏剧结构、角色/场景一致性、导演视角审查和成片节奏判断。
- Claude 只返回内容和审查意见；Codex 统一写文件并验证真实落盘。

## 激活方式

Codex 会根据你的需求自动判断是否使用 skill。也可以手动指定：

```text
$screenplay-director 把这段小说整理成专业剧本，每段包含场景、人物、动作、台词和镜头提示
```

```text
$script-to-storyboard 把这个剧本转成漫剧分镜表
```

```text
$storyboard-image-prompts 根据这份世界观、角色设定和分镜表生成 AI 绘图提示词，并按镜头推荐平台和模型
```

```text
$dingzhuangzao 读取项目世界观和角色设定，给主要角色生成定妆候选网页，确认后输出三视图
```

```text
$changjingmeishu 根据项目世界观和全量分镜，锁定核心场景、子场景和关键道具
```

```text
$renjingheyi 根据第1集绘图提示词、人物三视图和场景定版，生成逐镜融合候选并做网页评审
```

```text
$prd-writer-agent 帮我写一个 MVP PRD，并设计生成工作流
```

```text
$manju-production-workflow 启动漫剧项目《重生后我不再忍了》
```

## 维护规则

- 新增 skill 后，同步更新这个 `README.md`。
- 更新 skill 的用途、触发方式、外部依赖或风险说明后，同步更新这个 `README.md`。
- 更新 skill 的 UI 元数据时，同步更新对应 `agents/openai.yaml`。
- 删除或停用 skill 后，从这个 `README.md` 移除或标注“已停用”。
- 不要把 API Key、密码、私密 token 写进仓库。

## 外部 API 注意事项

- `screenplay-director` 支持兔子 API 多模型流程，但只有用户明确要求调用 API 时才应该调用。
- `script-to-storyboard` 支持通过兔子 API 先用 DeepSeek 写分镜初稿，再用 Claude 以导演编剧视角审查画面合理性、时长合理性、对话覆盖和运镜可实现性。
- `storyboard-image-prompts` 会按任务推荐外部生图平台或模型，例如 Midjourney、OpenAI Images、Gemini/Imagen、Runway、可灵、即梦、通义万相、腾讯混元、Stable Diffusion、FLUX、ComfyUI；真正使用这些平台前，应确认账号授权、额度消耗、素材上传风险和当前模型版本。
- `dingzhuangzao` / `changjingmeishu` 默认共用一个本地视觉评审网页；需要轻量 localhost Python server 来导入图、热更新 manifest 和保存 `selection-state.json`，但它不调生图 API。左栏平台 Key 面板只保存到当前浏览器 `localStorage`，不得写入项目文件或仓库。
- 真正调用 Midjourney、Gemini/Image2、Tuzi Image2 或其它生图平台前，应确认账号授权、余额消耗、参考图上传风险和当前模型版本。
- `renjingheyi` 会使用多图参考融合人物、场景和道具；真正调用多图生图/编辑接口前，应确认账号授权、额度消耗、人物/场景参考图上传风险和当前模型版本。
- `manju-production-workflow` 默认只协调本地文件和子 skill；只有用户明确要求外部模型或平台时才调用 API。
- 调用外部 API 会消耗余额，也会把输入内容发送到第三方服务。
- `prd-writer-agent` 默认工作环境是 Codex 实现、Claude 评审、Tuzi API 作为产品运行时模型网关；Tuzi 价格页 `https://api.tu-zi.com/pricing` 是默认核验入口。
- 涉及 AI 开发成本和 ROI 时，模型价格、第三方网关规则、订阅费和账单口径都可能变化；没有核验前应标记为 `待确认`。
- API Key 不要写进仓库；默认从环境变量 `TUZI_API_KEY` 读取。
