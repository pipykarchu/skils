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
| `prd-writer-agent` | 想把产品想法、功能需求、MVP、改进建议整理成 PRD 时使用。它会先做需求访谈和概念对齐，再输出标准 PRD。 | `$prd-writer-agent 帮我把一个 AI 漫剧生成工具整理成 MVP PRD` |
| `screenplay-director` | 想把故事、小说片段或散乱文字整理成中文专业剧本时使用。它会先提炼剧情大纲，自动起标题，建立人物设定角色档案，保持男女主和反派出场描述一致，并创建 Markdown 和 Word 文件。 | `$screenplay-director 把这段小说整理成剧本，并保持男女主和反派设定一致` |
| `script-to-storyboard` | 想把剧本、小说片段、Word、PDF、Markdown 或网页内容拆成分镜头脚本，并输出可用于 AI 生图的镜头提示词时使用。 | `$script-to-storyboard 把这个剧本文件转成分镜表，输出 Markdown 和 Excel` |

## 简单判断

- 要写产品需求文档，用 `prd-writer-agent`。
- 要把故事、小说或文字整理成剧本，并保存成 Markdown/Word，用 `screenplay-director`。
- 要稳定女主、男主、反派的人物设定、绘图固定提示词和禁止变化特征，也用 `screenplay-director`。
- 要把已有剧本拆成分镜头、景别、画面描述和 AI 生图提示词，用 `script-to-storyboard`。

## 激活方式

Codex 会根据你的需求自动判断是否使用 skill。也可以手动指定：

```text
$screenplay-director 把这段小说整理成剧本，并保持女主、男主、反派设定一致
```

```text
$script-to-storyboard 把这个剧本转成漫剧分镜表
```

```text
$prd-writer-agent 帮我写一个 MVP PRD
```

## 维护规则

- 新增 skill 后，同步更新这个 `README.md`。
- 更新 skill 的用途、触发方式、外部依赖或风险说明后，同步更新这个 `README.md`。
- 删除或停用 skill 后，从这个 `README.md` 移除或标注“已停用”。
- 不要把 API Key、密码、私密 token 写进仓库。

## 外部 API 注意事项

- `screenplay-director` 支持兔子 API 多模型流程，但只有用户明确要求调用 API 时才应该调用。
- `script-to-storyboard` 支持通过兔子 API 先用 DeepSeek 写分镜初稿，再用 Claude 改对白、节奏和情绪。
- 调用外部 API 会消耗余额，也会把输入内容发送到第三方服务。
- API Key 不要写进仓库；默认从环境变量 `TUZI_API_KEY` 读取。
