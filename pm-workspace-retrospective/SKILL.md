---
name: pm-workspace-retrospective
description: 深度扫描产品经理工作区/项目目录，产出量化复盘报告（目录结构、量化数据、方法论痕迹、述职亮点、冗余分析）。当用户要求"深度扫描 D:\... 目录"、"产出复盘报告/工作复盘"、"找述职亮点素材"、"统计技能数量/日报数/文档数/原型数/自动化脚本数"时使用。所有数据必须真实可溯源，禁止编造。
---

# PM 工作区深度扫描与复盘报告

面向产品经理（皮玺玉 / Mozin / 牧之音工作区）的复盘类任务：扫描工作目录 → 产出结构化中文《XX复盘报告》。典型触发：述职前全盘扫描、月报/季报复盘、技能库盘点、"帮我看看这个目录里有什么产出"。

## 核心铁律

1. **禁止编造**：报告中的每一个数字、路径、文件名必须是真实扫描结果，可逐条溯源。拿不到就写"未扫描到/待确认"，绝不估算填充。
2. **排除目录先行**：工作区含大量历史副本（`_remote-audit`、`_worktrees`、`_migration-quarantine`、`_archive`、`backup`、`node_modules`、`.git`、`.global-model-runtime`、`_同名不同版本`、`.tmp`），不排除则数据翻倍失真。排除清单见 scripts/scan-workspace.ps1 默认值。
3. **报告落盘位置**：与已有述职报告/复盘报告同目录（如 `D:\AI\AI产品工作\本机\`），命名 `XX复盘报告_YYYYMMDD.md`。
4. **完成后更新 handoff.md**：在该工作区 handoff 的"当前任务"顶部追加一行 ✅ 标记，写明报告路径 + 3-5 条关键发现，供主代理并入述职/月报。

## 工作流（6 步）

1. **顶层结构**：`Get-ChildItem -Path <root> -Directory` 与 `-File` 分开列，同时记录体积（`Measure-Object -Property Length -Sum`）。
2. **2-3 层递归**：对每个顶层目录做 `-Recurse -Depth 1/2`，用 `$_.FullName.Replace($base,'')` 输出相对路径，避免超长绝对路径刷屏。
3. **关键数据文件**：优先读 handoff.md（当前任务/已完成/卡住/踩坑）、已有述职报告（量化口径锚点，如"306 技能/298 索引"）、索引 CSV（`Import-Csv` + `Group-Object` 分类统计）、日报/周报/月报（真实工作量数据，如"179 项产出 🟢88.8%"）。
4. **量化统计**：`Import-Csv` 行数（比 Get-Content 数行可靠）；按扩展名 Group-Object 看工作区构成；按顶层目录 Group-Object 看分布；目录体积排序找冗余。
5. **写报告**：用 templates/pm-retrospective-report.md 的 7 章骨架，填充真实数据。
6. **收尾**：验证文件写入（Get-Item 大小），更新 handoff.md。

## PowerShell 扫描陷阱（Windows PowerShell 5.1）

- **exit_code=1 常为误报**：管道尾 `Select-Object`/`Format-Table`/`Group-Object` 等会令 `$LASTEXITCODE=1`，但输出内容完全正常。**不要**因此判定命令失败或重试循环。判断依据是输出内容本身。
- **含中文括号的路径必须用变量拼接**：`"D:\...\1.5版（耳机MVP）\PRD"` 内联会解析失败；先 `$base = "D:\...\1.5版（耳机MVP）"` 再用 `"$base\PRD"`。
- **中文 markdown 用 `-Encoding UTF8` 读取**（`Get-Content ... -Encoding UTF8`），默认编码会乱码（如技能/handoff.md 显示为 GBK 乱码）。乱码文件直接跳过并在报告标注，不要强行解读。
- **空目录要交叉验证**：某目录为空（如 1.5版/PRD）不代表内容丢失——内容可能迁到兄弟目录（初版app/Mozin_APP_V1.5_PRD.md）。报告里写明"空目录，内容实际在 X 下"。
- **双份统计防重**：同一工程可能嵌套副本（如 初版app/ 内含 Mozin-Android-MultiDevice-Prototype 完整副本），发现后作为"冗余点"写入报告而非删除。

## 报告结构（7 章，见 templates/pm-retrospective-report.md）

1. 头部元信息（范围/时间/排除目录/数据口径）
2. 总体概览表（顶层目录数、文件总数、体积、各资产计数）
3. 目录结构树（2-3 层）+ 关键子结构特写
4. 关键量化数据（按资产分组：技能/汇报/产品线/工作量佐证）
5. 方法论痕迹识别（PRD/原型/验收/复盘/技能沉淀/handoff/自动化 七类）
6. 述职亮点素材（每条带可引用文件路径，按"素材 + 证据路径"格式）
7. 重复/冗余/可优化点（按"空间冗余 > 内容重复 > 待治理 > 整洁度 > 流程建议"分级）+ 结论

## 支持文件

- `scripts/scan-workspace.ps1` — 可复用扫描脚本：文件数/扩展名分布/顶层分组/目录体积，内置排除清单。
- `templates/pm-retrospective-report.md` — 7 章报告骨架模板，复制后填充。

## 验证

- 报告内每个数字都能指向一条真实路径（抽查 2-3 条）。
- 与既有 handoff/述职中的口径核对（如 技能索引 298 vs 目录 306 的差值要如实呈现为"待核对"）。
- 报告落盘 + handoff 更新两件事都完成才算收尾。
