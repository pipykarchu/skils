---
name: changjingmeishu
description: Lock reusable scene/location and key-prop reference art for Chinese comic-drama/manju production, parallel to dingzhuangzao but for environments instead of characters. Use when the user asks for 场景美术, 场景定版, 场景概念图, 场景参考图, 道具定版, 关键道具参考, 美术设定, 锁定场景, 分镜场地, 同一场景不同角度/天气/时段一致, scene concept art, locked environment plates, or a selectable web gallery for scenes grounded in storyboard usage, worldview, era, and locked character looks.
---

# 场景美术（场景与道具定版）

## 定位

把世界观和分镜里反复出现的**场地、子场景、关键道具**，像定妆造锁人物一样转成视觉参考图并锁定。锁定后的场景/道具图，是 `renjingheyi`（人景合一）逐镜融合的环境与道具基准，全剧一次锁定，防止跨镜头穿帮。

与 `dingzhuangzao` 平级、对称：

| 概念 | dingzhuangzao（人物） | changjingmeishu（场景） |
|---|---|---|
| 模块 module | 角色分组 | 大场地（如：阿妮家、河沟、竹林） |
| 条目 role | 角色 | 子场景（外景 / 院落 / 西屋卧室 / 灶房） |
| 变体 state | 时期/场景态 | 角度 × 时段 × 天气（如：俯视-夜-阴雨） |
| 候选 | 四张正面肖像 | 四张场景概念图（生成或导入） |
| 右栏 | 世界观场景 | 场景美术依据（出场人物、位置关系、交互、中心构图） |
| 禁止变化 | 脸/服装锚点 | 空间锚点（墙体/门窗/陈设布局） |

默认中文。执行写文件、调用外部生图 API、上传素材前先说明风险。不主动调 API。

## 核心铁律

1. **分镜驱动按需锁定（防组合爆炸）**。绝不穷举「子场景 × 角度 × 时段 × 天气」全组合。先扫所有分镜，统计每个场地**实际用到**哪些组合，**只锁这些**。一个场地常见的也就 3-8 个有效组合。
2. **空间锚点固定，只变光线/天气/时段（防穿帮）**。同一个西屋卧室，白天和夜晚必须是同一个空间——墙体、门窗位置、炕/家具布局、关键陈设是固定锚点；**只允许光线、色温、天气、时段变化**。这是人物「禁止变化」概念在场景上的对应，必须写进每个子场景的 `spaceAnchor`。
3. **场景画风与已锁人物统一**。读 `03_角色设定/定妆造/` 或 `08_生成图片/角色三视图/` 已锁人物的画风、年代、光影，场景必须同源（真人短剧质感 / 民俗年代 / 低饱和等），不另立画风。
4. **服务器不调 API**。复用 `dingzhuangzao/casting_gallery_server.py` 做评审，所有生图在 agent 步骤做。
5. **默认与定妆造同页评审**。如果项目同时在做人物定妆和场景美术，不新开第二套网页；把场景/道具模块并入 `08_生成图片/视觉定版评审/manifest.json`，与人物模块共用同一个本地评审页和 `selection-state.json`。

## 必读上下文

写场景提示词、生成参考图前，先读定义视觉真实的项目文件：

- `02_世界观/年代设定与场景刻画.md`（若无则搜含 `世界观`/`年代`/`场景` 的文件）
- `06_分镜表/第XX集_*.md` 全部分镜（提取场地与组合的唯一权威来源）
- `07_绘图提示词/第XX集_*.md` 的「场景/镜头」「光影色彩」列（已有的场景描述，直接复用，不重写）
- `03_角色设定/角色档案.md`、已锁人物图（统一画风、确认场景里会出现谁）

## 工作流

### 1. 扫分镜，反推场地清单

遍历每集分镜的「画面内容提示词 / 主提示词」「景别」「场景/镜头」列，提取：

- **场地（module）**：地点名（阿妮家、娘子关河沟、竹林、偏房…）。
- **子场景（role）**：同一场地里的不同空间（院门口 / 堂屋 / 西屋 / 灶房 / 河边）。
- **变体（state）= 角度 × 时段 × 天气**：从景别+运镜+光影列推断（远景俯视、夏日烈日、夜晚油灯、清晨冷光…）。
- 记录每个组合**被哪些镜号引用**（usedByShots），证明它「按需」存在。

输出场地清单供用户确认，再生成 manifest。

### 2. 生成 manifest（build_scene_manifest.py）

`build_scene_manifest.py` 读分镜+世界观，产出 **casting 兼容 manifest**，可直接喂给 `casting_gallery_server.py`；若人物定妆已存在统一评审页，则把本阶段产出的 modules 合并进同一个 manifest：

- module → role(子场景) → state(角度×时段×天气) → groups（候选槽）。
- 每个 state 的 `worldview` 字段复用为**场景美术依据**：
  - `era`：时段/年代（如「回忆段·1983夏·白天」）
  - `scene`：该子场景该变体的画面说明（取自分镜/07 场景列）
  - `space`：**空间锚点（spaceAnchor）——禁止变化的墙体门窗陈设布局**
  - `props`：该场景里出现的关键道具
  - `costume` → 复用为「出场人物 + 位置关系 + 交互关系」
  - `light`：光线/色温/天气
  - `forbid`：禁止项（现代物件、错误年代元素）
  - `keywords`：关键标签 + `usedByShots` 镜号
- 默认候选行沿用 `Gemini Image / Image2 / MJ` 引擎槽（可只用一组）。也可换成「生成版 / 导入版」。

### 3. 评审与锁定（复用定妆造服务器）

把 `dingzhuangzao/scripts/casting_gallery_server.py` 拷进输出目录，指向本 skill 的 manifest 运行；若是人物+场景同页，优先使用统一目录：

```bash
python casting_gallery_server.py --manifest manifest.json --out selection-state.json --port 8791
```

推荐统一目录：

```text
08_生成图片/视觉定版评审/
```

左栏同页展示「人物定妆 · 角色→时期」和「场景美术 · 场地→子场景→变体」、中栏候选+❤️心仪+局部锁定、右栏依据和提示词，机制与定妆造完全一致。场景/道具模块的倾向按钮是 `氛围` / `色调` / `构图` / `建筑`，用于在同一版候选里锁定下一版需要沿用的局部参考。用户 ❤️ 选图 + `确认此变体` 锁定，被心仪的图成为该变体最终参考。`生成总览图` 仅记录意图。

需要后端：需要一个轻量 localhost Python server 来导入图片、读取本地图片、热更新 manifest、保存 `selection-state.json`。它不是生图后端，不调外部 API。只做静态展示时可以不用后端，但不能完成正式审核闭环。

### 4. 导出定版参考图

- 生成（用户授权后，agent 调生图工具）或导入候选图，回填 manifest `image.path`。
- 确认后，把锁定参考图导出到：

```text
02_世界观/视觉定版/场景/<场地>/<子场景>_<变体>.png
02_世界观/视觉定版/道具/<道具名>/<道具名>.png
```

- 同时保存 `scene-anchors.json`（每个锁定场景的 spaceAnchor + 路径），供 `renjingheyi` 自动匹配。

## 与人景合一的交接

锁定产物是 `renjingheyi` 的输入：

- `02_世界观/视觉定版/场景/<场地>/<子场景>_<变体>.png` —— 多图融合的环境参考
- `02_世界观/视觉定版/道具/<道具名>/<道具名>.png` —— 道具参考
- `scene-anchors.json` —— 场景名/别名 → 锚点 + 文件路径映射，给 `renjingheyi/build_shot_manifest.py` 自动匹配场景到镜头

## 输出目录

```text
02_世界观/视觉定版/
  build_scene_manifest.py        # 从 skill 拷入
  manifest.json                  # 驱动评审网页
  casting_gallery_server.py      # 从 dingzhuangzao 拷入
  start.bat                      # 智能启动
  selection-state.json           # 网页保存的锁定状态
  scene-anchors.json             # 锁定场景锚点+路径（给人景合一）
  candidates/<场地>/<子场景>/<变体>/*.png
  场景/<场地>/<子场景>_<变体>.png   # 锁定的场景定版
  道具/<道具名>/<道具名>.png         # 锁定的道具定版
```

## 质量检查

- 每个锁定场景的变体都能在分镜里找到引用镜号（无凭空场景）。
- 同一子场景的不同时段/天气，空间锚点（墙/门/陈设）一致，只光线天气变。
- 场景画风、年代、光影与已锁人物统一。
- 关键道具参考图与分镜描述一致（如带密码锁的小盒子不退化成首饰盒）。
- 无文字水印，无错误年代现代物件。

## 风险提示（执行前说明）

- 调生图工具会把场景提示词/参考图上传第三方，消耗额度、有原创素材泄露风险。
- 仅在用户明确授权后生成；未授权只产 manifest 和提示词，用占位槽。
- API key 只从环境变量读，绝不写进项目。
- 本地评审服务器占用 localhost 端口直到停止。
- 文件写入不覆盖用户原稿，需改动追加版本/时间戳。
