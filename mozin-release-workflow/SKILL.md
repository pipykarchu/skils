---
name: mozin-release-workflow
version: 1.0.0
description: "Mozin APP 发版交付流程：从验收到发布的完整工作流，包括验收表批量操作、发布文档生成、飞书云文档导入。当用户提到 V1.5/V2.0 发版、验收、发布检查清单、跨平台发版、回滚方案时使用。"
tags: [product, release, mozin, feishu]
---

# Mozin 发版交付流程

## 何时使用

- 用户要做产品验收（多维表格批量更新复核状态）
- 用户要出具发版文档（发布检查清单、回滚方案、发布执行计划、跨平台发版清单）
- 用户要把 Markdown 文档导入飞书为云文档
- 用户要把会议纪要待办转为飞书任务

## 公司规范要求（02-产研中心）

### 文档命名规范
`Mozin-项目名-文档类型-V版本号-YYYYMMDD.md`

### 05-发布与运维 必须文件（3份）
1. **发布检查清单** — 门禁状态(D1-D6)、验收结论、Go/No-Go checklist、灰度策略、监控值班
2. **部署方案** — Docker/K3s配置、CI/CD、环境变量、发布步骤（运维负责）
3. **回滚方案** — 触发条件、决策链、回滚方式、验证步骤、演练记录

### 会议新增交付物（测试交付验收时同步提交）
4. **发布执行计划** — 时间线、灰度计划、已知风险、发布后行动
5. **跨平台发版清单** — Android/iOS构建配置、权限声明、渠道、服务端依赖、配套资产

### 门禁阶段（Gate Check）
D1需求冻结 → D2技术方案 → D3开发完成 → D4测试通过 → D5产品验收 → D6发布就绪

### 关键原则
- 不跳级 — 未通过门禁不得进入下一阶段
- 有签核 — 每个交接点必须有书面签核
- 产品经理终审 — 验收结论以产品经理为准
- 退出条件 — 生产环境稳定运行24小时，无P0/P1回滚事件

## 验收表批量操作流程

### 1. 解析飞书多维表格
```bash
lark-cli base +url-resolve --url "<bitable_url>" --as user
```

### 2. 拉取全部记录
```bash
lark-cli base +record-list --base-token <token> --table-id <id> --view-id <id> --limit 200 --as user
```
注意：没有 `--page-token` 参数，用 `--limit 200` 一次取完。

### 3. 批量更新（PowerShell）

**关键坑点**：
- 必须用无BOM的UTF-8写JSON文件：
  ```powershell
  [System.IO.File]::WriteAllText("$PWD\batch.json", $json, [System.Text.UTF8Encoding]::new($false))
  ```
- `--json @file.json` 只接受**相对路径**，不接受绝对路径
- 单次最多200条记录
- select字段（单选 multiple=false）传字符串："通过"，不是数组

```bash
lark-cli base +record-batch-update --base-token <token> --table-id <id> --json "@batch.json" --as user
```

### 4. 验收判断逻辑
- 检查状态=通过 且 复核查验=待验收 → 复核标「通过」
- 检查状态=问题 且 复核查验=待验收 → 复核标「问题」+ 追加问题描述
- 检查状态=待确认 → 复核标「待确认」
- 已有问题描述的记录：在现有描述基础上追加，不要覆盖

## 文档导入飞书云文档

不要用 `+upload`（产生的是附件文件），要用 `+import`：

```bash
lark-cli drive +import --type docx --folder-token <folder> --file "本地文件.md" --name "云文档标题" --as user
```

导入后自动为飞书云文档格式（在线可编辑）。

**用户偏好**：默认都用飞书云文档格式，不要上传 .md 原始文件。上传 .md 只是中间步骤时，完成后要清理掉。

**更新云文档流程**（无 +replace 命令）：
1. 本地修改 .md 文件
2. `lark-cli drive +delete --file-token <old_token> --type docx --yes --as user` 删除旧版
3. `lark-cli drive +import --type docx --folder-token <folder> --file "更新后.md" --name "标题" --as user` 重新导入

**飞书任务创建后标完成**：用户说"已完成"的任务，用 `lark-cli task +complete` 标记。任务描述中要包含飞书云文档链接。

## 会议纪要→飞书任务

```bash
lark-cli docs +fetch --doc <doc_token> --as user  # 读取会议纪要
lark-cli task +create --summary "标题" --description "描述" --assignee ou_xxx --tasklist-id <id> --due "YYYY-MM-DD" --as user
```

## 产品身份（更新说明用）

- 产品名：**Mozin 智能摄像头耳机**（MOC.M1.Pro / Mozin Fold M1 WIFI Pro）
- 形态：带摄像头的智能耳机（不是眼镜、不是普通耳机）
- 对外名称：Mozin V1.5
- 耳机自带WiFi AP热点（不是连家用WiFi）
- 翻译是多语言（中/英/日/韩），不是仅中英
- V1.5 APP没有拍照功能（虽然BLE指令层有，但APP端未暴露给用户）
- 更新说明中突出：耳机热点配网、AI语音助手、录像控制+SRT图传预览、WiFi高速文件下载
- 不要写未通过验收的功能（如深色模式、拍照）
- "速度优化"等量化描述需有数据支撑，否则用"体验优化"
- 语音服务用阿里云DashScope ASR，不是Amazon AVS

## 飞书文件夹搜索

搜索某文件夹下的文档：
```bash
lark-cli drive +search --query "关键词" --folder-tokens <folder_token> --as user
```
注意是 `--folder-tokens`（复数），不是 `--folder-token`。

## 删除飞书文件

```bash
lark-cli drive +delete --file-token <token> --type file --yes --as user
```
必须带 `--type`（file / docx / folder 等）。

## 读取公司规范文档

02-产研中心规范文件夹 token: `BqAmfva3TlhPL8df8jYcSZwknRg`

关键文档：
- 02-项目云文档管理规范: `L7a8doIxKoxsuNxBwnScXmApnce`
- 产研中心职能白皮书V3.0: `YpBedGyslofwfRx7yIkcbYPxnxf`（注意：实际内容是人员花名册，非SOP）
- 产研中心人员花名册: `CdgBd3mBroHgHfxsF08cClcDnV1`

产品交付全流程SOP V1.3 (老版): 飞书token `DS4XdZIp8oJlChxLV8gcfsYXnqf`

**写发布文档前必须先对照公司规范**：用 `lark-cli docs +fetch --doc <token> --as user` 读取云文档管理规范，确认命名、结构、门禁要求后再写。不要凭记忆写——规范可能已更新。

## 参考文件

- [references/release-doc-templates.md](references/release-doc-templates.md) — 发布文档模板结构
