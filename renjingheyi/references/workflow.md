# 人景合一 Workflow Reference

## 文件夹模式

```text
10_镜头图/
  build_shot_manifest.py        # 解析提示词 + 匹配参考图 → shot-manifest.json
  fuse_shots.py                 # 编排 generate.js 多图融合（--dry-run 不调API）
  fusion_gallery_server.py      # 集→镜号 逐镜评审网页
  start.bat                     # 智能启动
  shot-manifest.json            # 逐镜数据
  selection-state.json          # 网页保存的 confirmedShots
  candidates/
    第XX集/<镜号>/*.png          # 融合候选
  final/
    第XX集/<镜号>.png            # 确认的镜头图（交接生视频）
```

## 提示词解析（build_shot_manifest.py 第一步）

`07_绘图提示词/第XX集_*.md` 的「分镜生图提示词」表头：

```
| 镜号 | 画面目的 | 推荐平台/模型 | 主提示词 | 角色锚点 | 场景/镜头 | 光影色彩 | 负面提示词 | 参数/备注 |
```

- 抓第一个含「镜号」的表格，逐数据行解析（跳过分隔行 `---`）。
- `主提示词` 列**原样**进 manifest 的 `prompt`，绝不改写。
- `角色锚点` 列用于识别本镜出现的角色（值形如「阿妮：低盘发素色棉麻外套；姜苗：浅色睡衣」）。
- `场景/镜头`、`光影色彩` 列辅助场景匹配。
- `负面提示词` 列若为「统一负面提示词」，回到文档 `## 统一负面提示词` 段取正文。

兜底：07 不存在时解析 `06_分镜表/第XX集_*.md`：

```
| 镜号 | 时长 | 景别 | 运镜 | 画面内容提示词 | 人物台词 | 备注 |
```

`画面内容提示词` 列当 `prompt`，`景别/运镜/时长/人物台词` 进 `shot` 字段。

## 参考图匹配算法

### 人物匹配（容错）

三视图文件名形如 `04_娃娃仙姐姐，五辫阶段.png`、`08_道士___修行者，初登场.png`：

1. **归一化**：去 `^\d+_` 序号前缀 → 去扩展名 → 把 `，,、_/（）()·` 等替换为空格 → strip。
   - `04_娃娃仙姐姐，五辫阶段.png` → `娃娃仙姐姐 五辫阶段`
   - `08_道士___修行者，初登场.png` → `道士 修行者 初登场`
2. **候选名提取**：取归一化串里每个空格分段作候选名（`娃娃仙姐姐`、`五辫阶段`、`道士`、`修行者`…）。
3. **匹配**：对每镜，把「角色锚点列 + 主提示词」作文本，若某三视图的任一候选名是该文本的子串 → 命中。
4. **别名表**：项目级 `ALIASES`（脚本常量，可被 `03_角色设定/角色固定提示词.md` 校正），如 `{"阿妮":["成年阿妮","母亲","小妮儿娘"], "小妮儿":["少女妮儿","婴儿小妮儿","幼年"]}`。锚点文本含别名也命中对应三视图。
5. **置信度**：候选名整段命中=high；仅别名命中=medium；无命中=该镜无人物参考（纯场景/道具镜，正常）。

### 场景匹配

读 `02_世界观/视觉定版/scene-anchors.json` 的 `scenes[]`：

- 用每个场景的 `aliases` 对「场景/镜头列 + 主提示词」做包含匹配。
- 命中多个时，优先 `usedByShots` 含本镜号的场景（分镜驱动锁定时已记录），否则取 alias 最长匹配。
- 无 `scene-anchors.json` → 所有场景 refs 留空，标 `needsReview="场景未锁，建议先跑 changjingmeishu"`。

### 道具匹配

同理用 `props[]` 的 aliases 匹配，一镜可命中多个道具。

### needsReview

以下进 `needsReview`，网页里可手动增删参考图，agent 落盘前也应校正：

- 人物无任何 high 命中但提示词疑似有角色。
- 场景未匹配且镜头疑似有明确场地。
- 同名歧义（多个三视图都命中）。

## shot-manifest.json Schema

```json
{
  "project": "娃娃仙",
  "episode": "01",
  "title": "女儿要听娃娃仙",
  "styleAnchor": "全片风格锚点正文（取自 07 ## 全片风格锚点）",
  "globalNegative": "统一负面提示词正文",
  "promptSource": "07_绘图提示词/第01集_女儿要听娃娃仙_生图提示词.md",
  "shots": [
    {
      "no": "01",
      "prompt": "（07 主提示词原样）2026年清明前一晚，太行山脚老家旧屋卧室夜晚…竖屏9:16",
      "negative": "明星脸，真实公众人物…",
      "shot": {"景别": "中近景", "运镜": "固定镜头", "时长": "5秒",
               "台词": "阿妮：姜苗，姜生，该睡觉了…", "画面目的": "建立清明前夜睡前现实层"},
      "refs": [
        {"kind": "role", "name": "成年阿妮", "path": "../../08_生成图片/角色三视图/03_成年阿妮.png", "confidence": "high"},
        {"kind": "scene", "name": "西屋卧室·夜", "path": "../../02_世界观/视觉定版/场景/阿妮家/西屋卧室_夜.png", "confidence": "medium"}
      ],
      "candidates": [
        {"id": "ep01-s01-01", "path": "", "note": "融合候选1"}
      ],
      "needsReview": ""
    }
  ]
}
```

- `prompt` 原样、`refs.path` 相对 manifest 所在目录（网页 `/asset/` 用）。
- `candidates` 初始为占位（path 空），`fuse_shots.py` 生成后回填。
- `episode` 多集时可生成多份 manifest，或 shots 里加 `episode` 字段分组。

## selection-state.json Schema（confirmedShots 交接生视频）

`fusion_gallery_server.py` 的 `POST /api/save` 写：

```json
{
  "project": "娃娃仙",
  "episode": "01",
  "likes": {"ep01-s01-02": true},
  "finals": {"01": true},
  "notes": {"01": {"likes": "光影到位", "adjustments": "人物再靠左", "nextRound": false}},
  "exportRequested": true,
  "confirmedCount": 18, "totalShots": 18,
  "confirmedShots": [
    {"no": "01", "prompt": "（原样）…", "shot": {"景别":"中近景","运镜":"固定镜头","时长":"5秒"},
     "refs": [{"kind":"role","name":"成年阿妮","path":"…"}],
     "finalCandidate": {"id": "ep01-s01-02", "path": "candidates/第01集/01/gpt-image-2-….png"}}
  ]
}
```

`confirmedShots` 每镜的 `finalCandidate` 即该镜锁定镜头图，agent 据此拷到 `final/第XX集/<镜号>.png` 并交接阶段7。仅当 `exportRequested && confirmedCount===totalShots` 时执行导出。

## 检查清单

逐镜：

- prompt 是否与 07 原文逐字一致（未改写）？
- 人物 refs 是否选对（脸/年龄段对得上分镜角色）？
- 场景 ref 是否对应本镜场地、时段、天气？
- 道具 ref 是否齐全？
- needsReview 是否已清空或人工确认？

成片前：

- 18 镜是否都有确认的 finalCandidate？
- 同一角色跨镜头脸/服装是否一致？
- 同一场景跨镜头空间是否一致（靠场景定版保证）？
- 画幅竖屏、无文字水印、年代无穿帮？
