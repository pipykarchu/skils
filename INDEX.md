# Codex Skills 索引

这个仓库用于存放可安装到 Codex 的 skill。每个 skill 是一个独立目录，目录里至少包含 `SKILL.md`。

## 使用方式

把需要的 skill 目录复制到本机：

```text
C:\Users\Administrator\.codex\skills\
```

成功标志：目录结构类似 `C:\Users\Administrator\.codex\skills\screenplay-director\SKILL.md`。

## Skill 列表

| Skill 名称 | 适合什么时候用 | 激活方式 | 使用示例 |
|---|---|---|---|
| `prd-writer-agent` | 想把产品想法、功能需求、MVP、改进建议整理成 PRD 时使用。它会先做需求访谈和概念对齐，再输出标准 PRD。 | 直接说“写 PRD”“帮我整理产品需求”，或显式输入 `$prd-writer-agent`。 | `$prd-writer-agent 帮我把一个 AI 漫剧生成工具整理成 MVP PRD` |
| `screenplay-director` | 想把故事、梗概、人物设定改成中文专业剧本时使用。它会做故事诊断、人物表、片段拆分和正式剧本，每个片段不超过 400 字。 | 直接说“写个剧本”“把这个故事改成剧本”，或显式输入 `$screenplay-director`。 | `$screenplay-director 写个剧本：一个外卖员在暴雨夜送最后一单，发现收餐人是三年前害他家破人亡的人` |

## 简单判断

- 要写产品需求文档，用 `prd-writer-agent`。
- 要写故事剧本、短剧、漫剧脚本，用 `screenplay-director`。

## 注意事项

- `screenplay-director` 支持兔子 API 多模型流程，但只有用户明确要求调用 API 时才应该调用。
- 调用外部 API 会消耗余额，也会把输入内容发送到第三方服务。
- API Key 不要写进仓库；默认从环境变量 `TUZI_API_KEY` 读取。
