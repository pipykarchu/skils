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
| `prd-writer-agent` | 想把产品想法、功能需求、MVP、改进建议、漫剧项目需求或 AI 开发工作流整理成 PRD 时使用。它会先做需求访谈和概念对齐，持续维护项目命名 PRD Markdown，完整版完成后生成皮玺玉风格 PRD 网页；AI 开发项目会同步估算和记录成本、产出、ROI。 | `$prd-writer-agent 帮我把一个 AI 视频学习助手整理成 MVP PRD，并估算 Codex/Claude 开发成本、产出和 ROI` |
| `screenplay-director` | 想把故事、小说片段或散乱文字整理成中文专业剧本时使用。它会先提炼剧情大纲，自动起标题，建立人物设定角色档案，保持男女主和反派出场描述一致，并创建 Markdown 和 Word 文件。 | `$screenplay-director 把这段小说整理成剧本，并保持男女主和反派设定一致` |
| `script-to-storyboard` | 想把剧本、小说片段、Word、PDF、Markdown 或网页内容拆成分镜头脚本，并输出可用于 AI 生图的镜头提示词时使用。 | `$script-to-storyboard 把这个剧本文件转成分镜表，输出 Markdown 和 Excel` |
| `manju-production-workflow` | 想从 0 到 1 做完整漫剧生产流水线时使用。它会协调 PRD、SOP、角色档案、剧本、分镜、AI 生图提示词和质检。 | `$manju-production-workflow 启动漫剧项目《重生后我不再忍了》，题材都市复仇，30集，每集60秒` |

## 简单判断

- 要写产品需求文档、漫剧项目 PRD、AI 开发工作流、成本产出估算或 ROI 统计，用 `prd-writer-agent`。
- 要把故事、小说或文字整理成剧本，并保存成 Markdown/Word，用 `screenplay-director`。
- 要稳定女主、男主、反派的人物设定、绘图固定提示词和禁止变化特征，也用 `screenplay-director`。
- 要把已有剧本拆成分镜头、景别、画面描述和 AI 生图提示词，用 `script-to-storyboard`。
- 要完整跑 PRD、SOP、剧本、分镜、提示词和质检，用 `manju-production-workflow`。

## 激活方式

Codex 会根据你的需求自动判断是否使用 skill。也可以手动指定：

```text
$screenplay-director 把这段小说整理成剧本，并保持女主、男主、反派设定一致
```

```text
$script-to-storyboard 把这个剧本转成漫剧分镜表
```

```text
$prd-writer-agent 帮我写一个 MVP PRD，并估算 AI 开发成本、产出和 ROI
```

```text
$manju-production-workflow 启动漫剧项目《重生后我不再忍了》
```

## 维护规则

- 新增 skill 后，同步更新这个 `README.md`。
- 新增 skill 后，同步更新 `INDEX.md`。
- 更新 skill 的用途、触发方式、外部依赖或风险说明后，同步更新这个 `README.md`。
- 更新 skill 的 UI 元数据时，同步更新对应 `agents/openai.yaml`。
- 删除或停用 skill 后，从这个 `README.md` 移除或标注“已停用”。
- 不要把 API Key、密码、私密 token 写进仓库。

## 外部 API 注意事项

- `screenplay-director` 支持兔子 API 多模型流程，但只有用户明确要求调用 API 时才应该调用。
- `script-to-storyboard` 支持通过兔子 API 先用 DeepSeek 写分镜初稿，再用 Claude 改对白、节奏和情绪。
- `manju-production-workflow` 默认只协调本地文件和子 skill；只有用户明确要求外部模型或平台时才调用 API。
- 调用外部 API 会消耗余额，也会把输入内容发送到第三方服务。
- 涉及 AI 开发成本和 ROI 时，模型价格、第三方网关规则、订阅费和账单口径都可能变化；没有核验前应标记为 `待确认`。
- API Key 不要写进仓库；默认从环境变量 `TUZI_API_KEY` 读取。
