---
name: feishu-modao-product-workflow
title: 飞书→墨刀产品原型工作流
description: |
  飞书PRD/需求池 → Hermes分析 → 墨刀MCP生成HTML原型 → 飞书评论闭环反馈。
  已验证可自动化的完整链路，阶段1-3全自动，阶段4-5通过飞书评论实现反馈闭环。

version: "2.0.0"
author: "皮玺玉 (Mozin 产品经理)"
created: "2025-01-16"
updated: "2026-07-17"

category: "product-engineering"
tags:
  - workflow-automation
  - product-management
  - feishu
  - modao
  - hermes-agent

trigger_conditions:
  - "用户提供飞书文档URL，要求生成墨刀原型"
  - "用户说: 飞书→墨刀工作流"
  - "用户说: 自动化原型生成"
  - "用户说: 从PRD生成原型"

prerequisites:
  - "Hermes Agent 已安装且配置墨刀MCP"
  - "lark-cli 已授权（user身份）"
  - "飞书文档URL或token"
  - "墨刀MCP令牌（个人空间）"

---

# 飞书→墨刀产品原型工作流

## 核心链路（已验证）

```
飞书PRD → lark-cli拉取 → Hermes分析需求 → 墨刀MCP生成原型 → 预览确认 → 手动移入团队空间 → 飞书评论反馈 → 迭代
```

## 工作流阶段

### 阶段1：需求采集（全自动 ✅）

从飞书拉取PRD/需求池内容：

```powershell
lark-cli docs +fetch --doc <文档token> --doc-format markdown --as user
```

**文档token提取：** 飞书URL `https://xxx.feishu.cn/docx/EP4gdbGkfokArgxIorrcrL9Ln0e` 中最后一段 `EP4gdbGkfokArgxIorrcrL9Ln0e` 即为token。

**输出：** Markdown格式的完整PRD内容。

---

### 阶段2：智能分析（全自动 ✅）

Hermes直接分析PRD文本，提取：
- 核心页面列表（首页、详情页、设置页等）
- 每页的组件结构（输入框、按钮、导航、列表等）
- 交互说明（页面跳转、状态切换）
- 设计风格要求

无需额外AI工具API — Hermes本身即为AI分析引擎。

---

### 阶段3：原型生成（全自动 ✅）

调用墨刀MCP生成HTML原型：

```
mcp__modao__generate_html(user_input="基于PRD内容生成原型...")
```

**墨刀MCP可用工具（共7个）：**

| 工具 | 用途 |
|------|------|
| `generate_html` | 生成HTML原型（最常用） |
| `generate_react` | 生成React原型 |
| `generate_vue` | 生成Vue原型 |
| `generate_image` | AI生成图片 |
| `generate_prd` | 生成PRD文档 |
| `generate` | 通用生成 |
| `get_account_status` | 查询积分和账号状态 |

**输出：**
- 预览链接（可直接浏览器查看）
- 墨刀任务链接（在墨刀平台管理）
- HTML源码

**限制：**
- 仅写入个人空间，团队空间需手动移动
- 消耗墨刀AI积分
- 无法程序化创建项目文件夹

---

### 阶段4：设计审阅（半自动 ⚠️）

1. PM预览原型链接，确认大方向
2. 在墨刀APP中将原型文件移动到团队空间对应文件夹
3. 设计师/PM在墨刀中查看，**在飞书PRD文档中留下评论反馈**

> ⚠️ 墨刀MCP无法读取原型评论，所以反馈统一回到飞书。

**飞书评论规范：**
```
🔴 [重做] 具体问题描述
🟡 [调整] 具体优化建议
🟢 [建议] 非必要改进
```

---

### 阶段5：反馈迭代（半自动 ⚠️）

1. Hermes通过lark-cli读取飞书文档评论
2. 汇总反馈要点
3. 基于反馈重新生成/调整原型（重新调用墨刀MCP）
4. 更新预览链接

```powershell
# 读取文档评论（如有评论API）
lark-cli docs +fetch --doc <token> --scope keyword --keyword "🔴|🟡" --as user
```

**替代方案：** 如果评论结构化不足，PM直接把反馈贴在PRD正文中的"反馈汇总"段落，Hermes下次读取时即可识别。

---

## 配置

### Hermes config.yaml 中的墨刀MCP配置

```yaml
mcp_servers:
  modao:
    url: https://modao.cc/agent-py/ai/mcp
    headers:
      modao-token: "你的墨刀MCP令牌"
    timeout: 180
```

**获取令牌：** 墨刀网页端 → AI设置 → MCP令牌

### lark-cli授权

确保已完成 `lark-cli auth` 且有文档读取权限（user身份）。

---

## 完整操作示例

```
用户: 帮我把这个飞书PRD生成墨刀原型
      https://xxx.feishu.cn/docx/EP4gdbGkfokArgxIorrcrL9Ln0e

Hermes操作:
1. lark-cli docs +fetch --doc EP4gdbGkfokArgxIorrcrL9Ln0e --doc-format markdown --as user
2. 分析PRD，提取页面结构和交互需求
3. 调用 mcp__modao__generate_html 生成原型
4. 返回预览链接和任务链接给用户
```

---

## 已知限制

1. **墨刀MCP仅支持个人空间** — 生成后需手动移到团队
2. **无法读取墨刀评论** — 反馈循环走飞书
3. **积分消耗** — 每次生成消耗墨刀AI积分，用 `get_account_status` 查余额
4. **单次生成上限** — 复杂项目建议分页面批次生成

## 效果指标

- 需求→原型：从2-3天 → 15分钟（实测）
- 自动化覆盖：阶段1-3全自动（60%流程）
- 人工干预：阶段4-5需人工确认和移动文件
