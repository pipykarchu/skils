---
name: renjingheyi
description: Fuse locked character turnaround sheets, locked scene/prop reference art, and the existing per-shot image prompts into final composed shot images for Chinese comic-drama/manju production, one shot at a time. Use when the user asks for 人景合一, 人景融合, 场景人物合成, 分镜镜头图, 镜头合成, 按分镜出镜头图, 把人物放进场景, 多图参考合成, 角色场景道具融合, or a selectable web gallery to review fused shots before video generation. Reads existing prompts from 07_绘图提示词 (does not rewrite them), pulls locked refs, and composes via a multi-reference image model.
---

# 人景合一（逐镜头融合）

## 定位

把三样**已锁定**的素材，按分镜逐镜合成最终镜头图：

1. 人物三视图（`08_生成图片/角色三视图/` 或 `03_角色设定/定妆造/`，由 `dingzhuangzao` 锁定）
2. 场景/道具定版参考图（`02_世界观/视觉定版/`，由 `changjingmeishu` 锁定）
3. **已生成好的分镜提示词**（`07_绘图提示词/第XX集_*.md`，由 `storyboard-image-prompts` 生成）

融合引擎用支持多参考图的生图模型（默认 `gpt-image-2` 的 `/v1/images/edits` 多图端点），把人物图+场景图+道具图一起作参考、提示词作指令，逐镜出若干候选，网页评审确认。确认的镜头图是阶段7生视频的镜头基准。

默认中文。写文件、调外部 API、上传素材前先说明风险。不主动调 API。

## 第一铁律：复用已有提示词，绝不重写

**本 skill 不发明、不改写任何提示词。** 镜头的画面描述一律来自既有产物：

1. 首选 `07_绘图提示词/第XX集_*.md` 的「分镜生图提示词」表格 —— `主提示词` 列原样取用。
2. 兜底 `06_分镜表/第XX集_*.md` 的「画面内容提示词」列。

`build_shot_manifest.py` 自动解析这些表格。融合时只在 `主提示词` 外**追加固定的融合约束**（见 `references/fusion-prompt-rules.md`），不动原始画面描述。如发现提示词本身有问题，报告给用户去 `storyboard-image-prompts` 修，不在这里改。

## 数据流

```
07_绘图提示词/第XX集_*.md  ──┐  (主提示词 + 角色锚点列 + 场景/镜头 + 负面)
06_分镜表/第XX集_*.md      ──┤  (兜底画面提示词 + 景别/运镜/时长/台词)
08_生成图片/角色三视图/*.png ─┤  (人物参考，自动匹配)
02_世界观/视觉定版/场景|道具/ ┤  (场景/道具参考，读 scene-anchors.json 匹配)
                             ↓
        build_shot_manifest.py → shot-manifest.json（逐镜：prompt原样 + refs + 候选占位 + needsReview）
                             ↓
        fuse_shots.py（编排 generate.js 多图融合，--dry-run 不调API）→ candidates/*.png 回填
                             ↓
        fusion_gallery_server.py（集→镜号 三栏评审，❤️心仪 + 确认镜头图）
                             ↓
        selection-state.json（confirmedShots）→ 交接阶段7生视频
```

## 必读上下文

- `07_绘图提示词/第XX集_*.md`（首选提示词源）
- `06_分镜表/第XX集_*.md`（兜底 + 景别/运镜/时长/台词）
- `08_生成图片/角色三视图/*.png`（人物参考；文件名有序号前缀和特殊字符，匹配要容错）
- `02_世界观/视觉定版/scene-anchors.json`（场景/道具锚点+路径；无则提示先跑 `changjingmeishu`）
- `03_角色设定/角色固定提示词.md`（角色锚点别名校正）

## 工作流

### 1. 构建逐镜 manifest（build_shot_manifest.py）

```bash
python build_shot_manifest.py --project-root <项目根> --episode 01 [--out shot-manifest.json] [--print]
```

脚本做三件事：

1. **解析提示词表格**：逐行取 `镜号 / 主提示词(原样) / 角色锚点列 / 场景/镜头 / 负面 / 景别 / 运镜 / 时长 / 台词`。
2. **自动匹配参考图**：
   - 人物：从「角色锚点」列 + 主提示词文本识别本镜角色，模糊匹配三视图文件名（去 `^\d+_` 序号、去标点、子串包含 + 别名表）。
   - 场景：读 `scene-anchors.json`，用 aliases 对主提示词/场景列做包含匹配。
   - 道具：同理匹配道具锚点。
3. **输出 shot-manifest.json**：每镜带 `prompt`(原样)、`refs:[{kind,name,path}]`、`negative`、`shot:{景别,运镜,时长,台词}`、`candidates:[]`(占位)、`matchConfidence`、`needsReview`(低置信标记)。

低置信/未匹配项进 `needsReview`，由 agent 校正或在网页里手动增删参考图。

### 2. 生成融合候选（fuse_shots.py）

```bash
# 干跑：不调 API，只打印每镜将执行的命令 + 参考图清单
python fuse_shots.py --manifest shot-manifest.json --dry-run

# 实跑（需用户授权，消耗额度，上传素材到第三方）
export TUZI_API_KEY=sk-...
python fuse_shots.py --manifest shot-manifest.json --tool <gpt-image-2/generate.js路径> --n 2
```

对每镜：拼 `主提示词 + 融合约束`，把 refs 的 PNG 逐个作 `--image` 传给 `generate.js`，竖屏 `--size 1024x1536`，输出到 `candidates/第XX集/<镜号>/`，回填 manifest。

### 3. 逐镜评审（fusion_gallery_server.py）

```bash
python fusion_gallery_server.py --manifest shot-manifest.json --out selection-state.json --port 8792
```

三栏：左栏 集→镜号（✓已确认）；中栏 该镜融合候选（❤️心仪多选）+ 用到的参考图缩略图 + **只读原始主提示词** + 调整提示词/心仪的点 + `进入下一版`/`确认此镜镜头图`；右栏 景别/运镜/时长/台词/场景说明。底部 全部确认后 `导出镜头图`（仅记录意图）。服务器**不调任何 API**。

### 4. 导出与交接

确认后导出锁定镜头图到 `10_镜头图/第XX集/<镜号>.png`，`selection-state.json` 的 `confirmedShots` 交接阶段7生视频。

## 输出目录

```text
10_镜头图/
  build_shot_manifest.py / fuse_shots.py / fusion_gallery_server.py   # 从 skill 拷入
  shot-manifest.json
  selection-state.json
  start.bat
  candidates/第XX集/<镜号>/*.png
  final/第XX集/<镜号>.png        # 确认的镜头图
```

## 在总控工作流里的位置

实现 `manju-production-workflow` 的**阶段7前半（镜头图合成）**，承接阶段5的 `07_绘图提示词` 和阶段3.5/3.6锁定的人物/场景/道具，产出阶段7生视频所需的镜头基准图。前置依赖：

- 人物三视图已锁（`dingzhuangzao`）
- 场景/道具已锁（`changjingmeishu`，产出 `scene-anchors.json`）
- 分镜提示词已生成（`storyboard-image-prompts`）

若场景未锁，提示用户先跑 `changjingmeishu`；可降级为「只用人物参考 + 提示词」融合，但跨镜头场景一致性弱。

## 质量检查

- 每个分镜镜号都有对应 manifest 条目和（生成后）候选图。
- `prompt` 字段与 `07_绘图提示词` 原文一致（未被改写）。
- 人物/场景/道具参考图匹配正确，needsReview 项已校正。
- 融合图人物五官/服装与三视图一致、场景与定版一致、景别构图符合分镜。
- 无文字水印，画幅竖屏 9:16，年代无穿帮。

## 风险提示（执行前说明）

- 多图融合 API 消耗额度远高于文本，批量前估算 镜头数×候选数 并告知用户。
- 提示词和人物/场景参考图会上传到第三方平台，有原创素材泄露风险。
- 多图融合一致性不稳定，需逐镜评审多候选选优，必要时调整提示词重出。
- 仅用户明确授权后调 API；未授权用 `--dry-run` 只准备命令和参考图清单。
- API key 只从环境变量读，绝不写进项目。本地服务器占用端口直到停止。
