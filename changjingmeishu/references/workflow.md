# 场景美术 Workflow Reference

## 文件夹模式

```text
08_生成图片/视觉定版评审/        # 推荐：人物定妆 + 场景/道具同页评审
  manifest.json                  # 人物模块 + 场景模块 + 道具模块合并
  casting_gallery_server.py      # 从 dingzhuangzao 拷入
  selection-state.json           # 网页保存的统一锁定状态
  candidates/
    人物/<角色>/<时期>/<engine>/round-XX/*.png
    场景/<场地>/<子场景>/<变体>/<engine>/round-XX/*.png
    道具/<道具名>/<变体>/<engine>/round-XX/*.png

02_世界观/视觉定版/
  build_scene_manifest.py        # 读分镜+世界观，生成 manifest.json
  manifest.json                  # 驱动评审网页（casting 兼容）
  casting_gallery_server.py      # 从 dingzhuangzao 拷入
  start.bat                      # 智能启动（依赖检查/端口冲突/自动开浏览器）
  selection-state.json           # 网页保存的锁定状态
  scene-anchors.json             # 锁定场景锚点+路径（给人景合一自动匹配）
  candidates/
    <场地>/<子场景>/<变体>/*.png
  场景/
    <场地>/<子场景>_<变体>.png   # 锁定的场景定版
  道具/
    <道具名>/<道具名>.png         # 锁定的道具定版
```

统一评审页需要一个轻量本地 Python server，负责导入图、读取本地图片、热更新 manifest、保存 `selection-state.json`。它不调生图 API、不上传素材；纯静态 HTML 只适合只读演示，不适合正式确认。

## 分镜驱动提取算法（防组合爆炸）

`build_scene_manifest.py` 的核心是**反推**，不是穷举：

1. 遍历 `06_分镜表/第XX集_*.md`（兜底 `07_绘图提示词`）所有镜头行。
2. 对每镜，从「画面内容提示词/主提示词」抽地点关键词，从「景别」抽角度，从「光影色彩/画面提示词」抽时段+天气。
3. 归并成 `(场地, 子场景, 角度, 时段, 天气)` 组合键，记录 `usedByShots=[镜号…]`。
4. **只有出现过的组合才进 manifest**。一个场地的有效组合通常 3-8 个。
5. 同一组合被多镜复用时合并，usedByShots 累加——证明「按需」且高复用值得锁。

关键词词典（项目可扩充，放脚本顶部常量）：

```python
LOCATION_HINTS = {"阿妮家":["旧屋","卧室","堂屋","院","灶台","偏房"], "河沟":["河","河边","河沟"],
                  "竹林":["竹林"], "坟地":["坟","墓"], ...}
ANGLE_HINTS = {"俯视":["俯拍","俯视"], "仰视":["仰拍","仰视"], "平视":["平视"],
               "远景":["远景","全景"], "近景":["近景","特写","大特写"]}
TIME_HINTS = {"白天":["白天","烈日","正午","清晨","清早","早"], "黄昏":["傍晚","黄昏","夕阳"],
              "夜":["夜","夜晚","油灯","床头灯","深夜"]}
WEATHER_HINTS = {"晴":["晴","烈日","阳光"], "阴":["阴","乌云"], "雨":["雨","下雨"], "雾":["雾","迷雾"]}
```

匹配不确定时，宁可少锁（标 `needsReview`），不要乱造组合。

## Manifest Schema（casting 兼容）

直接喂给 `dingzhuangzao/casting_gallery_server.py`，或合并进 `08_生成图片/视觉定版评审/manifest.json`，复用其「模块→条目→变体→候选」结构。语义重映射如下：

```json
{
  "project": "娃娃仙",
  "round": 1,
  "styleTone": "真实人物质感，竖屏9:16，民俗恐怖志怪，低饱和，太行山旧村，与已锁人物画风统一",
  "modules": [
    {
      "name": "阿妮家（太行山脚旧屋）",
      "roles": [
        {
          "name": "西屋卧室",
          "states": [
            {
              "name": "夜·油灯暖光",
              "styleTone": "可选覆盖",
              "worldview": {
                "era": "回忆段·1985前后·夜",
                "scene": "旧屋西屋卧室夜晚，床头小灯，旧木床旧被褥（取自分镜镜号01/03/08）",
                "space": "【空间锚点·禁止变化】西屋朝南木门在右，土墙，靠北墙旧木床，床头柜在床右，窗在床对面墙",
                "props": "床头柜、带密码锁的小盒子、红布包",
                "costume": "出场人物：阿妮+姜苗+姜生；位置：阿妮俯身床边，两孩在床上；交互：盖被/讲故事",
                "light": "床头暖暗灯，窗外冷色弱光，低饱和",
                "forbid": "现代家具、空调、现代灯具、错误年代电器",
                "keywords": ["旧木床", "床头柜", "暖暗光", "镜号01/03/08"]
              },
              "groups": [
                {"engine": "Gemini Image", "label": "场景概念图（下一版/图生图）", "images": []},
                {"engine": "Image2", "label": "场景概念图（整句约束）", "images": [
                  {"id": "aniJia-西屋-夜-01", "path": "", "note": "Image2 候选1"}
                ]},
                {"engine": "MJ", "label": "场景概念图（紧凑标签）", "images": []}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

- `worldview.space` = **spaceAnchor**，是场景版的「禁止变化」，同子场景所有时段/天气共享同一锚点。
- `worldview.costume` 字段在场景语境里复用为「出场人物 + 位置关系 + 交互关系」（右栏展示）。
- `keywords` 末尾带 `镜号XX` 标明 usedByShots，体现分镜驱动。
- `image.path` 空 → 网页占位框，生成/导入后回填。

## Selection State

`casting_gallery_server.py` 的 `POST /api/save` 写 `selection-state.json`，结构与定妆造一致（`likes/locks/finals/notes/confirmedLooks/genRequests/overviewRequested`）。`confirmedLooks` 里每个已确认变体的 `final`、`alternates` 和 `locks` 就是该场景/道具的锁定参考。

## scene-anchors.json（给人景合一）

确认后由 agent 从 selection-state + manifest 汇总导出，是 `renjingheyi` 自动匹配场景的依据：

```json
{
  "project": "娃娃仙",
  "scenes": [
    {
      "module": "阿妮家（太行山脚旧屋）",
      "subscene": "西屋卧室",
      "variant": "夜·油灯暖光",
      "aliases": ["西屋", "卧室", "旧屋卧室"],
      "spaceAnchor": "西屋朝南木门在右，土墙，靠北墙旧木床…",
      "usedByShots": ["01", "03", "08"],
      "path": "场景/阿妮家（太行山脚旧屋）/西屋卧室_夜·油灯暖光.png"
    }
  ],
  "props": [
    {"name": "带密码锁的小盒子", "aliases": ["小盒子", "密码盒"],
     "usedByShots": ["04", "05"], "path": "道具/带密码锁的小盒子/带密码锁的小盒子.png"}
  ]
}
```

`aliases` 是为了让 `renjingheyi` 用子串/别名匹配镜头里的场景说法（脚本提取 + 人工校正）。

## 检查清单

锁定每个场景变体前后：

- 这个变体在分镜里真的出现过吗？（usedByShots 非空）
- 同子场景不同时段，space 锚点是否完全一致？
- 画风/年代/光影与已锁人物是否统一？
- props 是否齐全（分镜里该场景出现的关键道具都列了）？
- forbid 是否挡住了错误年代/现代物件？

关键道具：

- 道具外形是否符合分镜描述、不会和别的道具混淆？
- 是否值得独立锁定（多镜复用 / 是剧情核心道具）？
