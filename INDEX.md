# Codex Skills 索引

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

## Skill 列表

| Skill 名称 | 什么时候激活 | 简单用法 |
|---|---|---|
| `prd-writer-agent` | 想把产品想法、功能需求、MVP、改进建议、漫剧项目需求或 AI 开发工作流整理成 PRD，并需要同步维护 PRD Markdown、生成皮玺玉风格网页、估算/统计 AI 开发成本产出和 ROI 时使用。用户说“设计生成工作流”时默认带入 Codex + Claude + Tuzi API。 | `$prd-writer-agent 帮我把一个 AI 视频学习助手整理成 MVP PRD，并设计生成工作流` |
| `screenplay-director` | 想把故事、梗概、人物设定改成中文专业剧本时使用。 | `$screenplay-director 写个剧本：一个小白兔的故事` |
| `script-to-storyboard` | 想把剧本、小说片段、Word、PDF、Markdown 或网页内容拆成分镜头脚本，并输出可用于 AI 生图的 MD/Excel 分镜表时使用。 | `$script-to-storyboard 根据剧本文件和片段名称“妈妈病了”建立新的 MD 和 Excel 分镜脚本` |
| `manju-production-workflow` | 想从 0 到 1 串联漫剧 PRD、SOP、角色档案、剧本、分镜、AI 生图提示词和质检时使用。 | `$manju-production-workflow 启动漫剧项目《重生后我不再忍了》，题材都市复仇，30集，每集60秒` |

## 快速判断

- 要写产品需求文档、漫剧项目 PRD、AI 开发工作流、成本产出估算或 ROI 统计，用 `prd-writer-agent`；说“设计生成工作流”时默认使用 Codex + Claude + Tuzi API。
- 要写故事剧本、短剧、漫剧脚本，用 `screenplay-director`。
- 要把已有剧本按片段拆成分镜头、景别、画面描述和 AI 生图提示词，用 `script-to-storyboard`。
- 要完整跑一套漫剧生产流水线，用 `manju-production-workflow`。

## 注意事项

- `screenplay-director` 支持兔子 API 多模型流程，但只有用户明确要求调用 API 时才应该调用。
- `script-to-storyboard` 支持通过兔子 API 先用 DeepSeek 写分镜初稿，再用 Claude 改对白、节奏和情绪。
- `manju-production-workflow` 是总控 skill，默认只协调本地文件和子 skill；只有用户明确要求外部模型或平台时才调用 API。
- 调用外部 API 会消耗余额，也会把输入内容发送到第三方服务。
- `prd-writer-agent` 默认工作环境是 Codex 实现、Claude 评审、Tuzi API 作为产品运行时模型网关；Tuzi 价格页 `https://api.tu-zi.com/pricing` 是默认核验入口。
- `prd-writer-agent` 涉及 AI 开发成本和 ROI 时，不能编造 token、金额、产出或收益；缺数据时标记为 `待估算`、`待统计` 或 `待确认`。
- API Key 不要写进仓库；默认从环境变量 `TUZI_API_KEY` 读取。
