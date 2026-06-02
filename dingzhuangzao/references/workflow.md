# 定妆造 Workflow Reference

## Folder Pattern

Recommended project output:

```text
03_角色设定/
  定妆提示词/                    # package_prompts_by_role.py 输出（按角色打包）
    <角色>_定妆提示词合集.md
08_生成图片/
  定妆造/
    build_manifest.py            # 读角色档案+世界观，生成 manifest.json（含回填图片+读入提示词）
    manifest.json                # 驱动网页的数据
    casting_gallery_server.py    # 从 skill 拷入（三栏评审服务器）
    package_prompts_by_role.py   # 提示词按角色打包到 03_角色设定/定妆提示词/
    export_confirmed_looks.py    # 敲定+心仪图导出到 角色妆造敲定合集/
    start.bat                    # 智能启动（依赖检查/端口冲突/自动开浏览器）
    selection-state.json         # 网页保存的评审状态
    prompts/
      <角色>_<时期>_Gemini_Image_round01.md  # 下一版/图生图默认候选
      <角色>_<时期>_Image2_round01.md        # 整句约束
      <角色>_<时期>_MJ_round01.md            # 紧凑标签+英文负向，末尾 --ar 9:16
    candidates/
      <角色>/<时期>/image2/round-01/*.png
      <角色>/<时期>/mj/round-01/*.png
    final/
      <角色>/<时期>/turnaround.png
    overview/
      定妆造_总览.png
  角色妆造敲定合集/              # export_confirmed_looks.py 输出（确认+心仪的图）
    <角色>_<时期>_<kind>_<引擎>_<原名>.png    # kind: final / liked / ref
```

When 人物定妆 + 场景美术 are reviewed together, use one shared page:

```text
08_生成图片/
  视觉定版评审/
    manifest.json
    casting_gallery_server.py
    selection-state.json
    candidates/
      人物/<角色>/<时期>/<engine>/round-XX/*.png
      场景/<场地>/<子场景>/<变体>/<engine>/round-XX/*.png
      道具/<道具名>/<变体>/<engine>/round-XX/*.png
```

This shared page uses one tiny local Python server. The server only reads/writes local review files; it does not generate images or call external APIs. Without the server, the page can be made read-only, but 导入图、保存选择、manifest 热更新 will not be reliable.

`build_manifest.py`：
- `attach_existing_images` 扫描 `candidates/<角色>/<时期>/<engine>/round-*/` 把已生成图回填进 manifest；历史目录名与时期名不一致时用 `state(..., image_dir="旧目录名")` 做别名。
- `attach_prompts` 读 `prompts/<base>_<engine>_round01.md` 注入 `state.prompts` 供右栏显示；当角色名（如「小妮儿 / 妮儿 / 阿妮」「道士 / 修行者」）或时期名与文件前缀不一致时，用 `state(..., prompt_base="实际文件前缀")`。

## Candidate Manifest

Use this JSON shape (see SKILL.md → Manifest Schema for the full field list):

```json
{
  "project": "娃娃仙",
  "round": 1,
  "styleTone": "整体基调默认值",
  "modules": [
    {
      "name": "守护灵体与道具",
      "roles": [
        {
          "name": "娃娃仙姐姐",
          "states": [
            {
              "name": "显灵救人期",
              "worldview": {"era": "童年段 · 1990年前后", "scene": "...", "keywords": ["多条麻花辫"]},
              "groups": [
                {"engine": "Gemini Image", "images": []},
                {"engine": "Image2", "images": [{"id": "wawaxian-显灵救人期-i2-01", "path": "candidates/娃娃仙姐姐/五辫阶段/image2/round-01/01.png"}]},
                {"engine": "MJ", "images": []}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Selection State (saved by the gallery)

`POST /api/save` writes `selection-state.json`:

```json
{
  "project": "娃娃仙",
  "likes": {"<image-id>": true},
  "finals": {"<角色>::<时期>": "<被选为最终的单张 image-id>"},
  "locks": {"<角色>::<时期>": {
    "face": "<image-id>", "body": "<image-id>", "clothes": "<image-id>", "hair": "<image-id>",
    "atmosphere": "<image-id>", "color": "<image-id>", "composition": "<image-id>", "architecture": "<image-id>"
  }},
  "notes": {"<角色>::<时期>": {"likes": "...", "adjustments": "...", "nextRound": true, "nextEngine": "Gemini Image"}},
  "gen": {"<角色>::<时期>::<引擎>": true},
  "overviewRequested": true,
  "confirmedCount": 18, "totalStates": 18,
  "confirmedLooks": [
    {"module": "守护灵体与道具", "role": "娃娃仙姐姐", "state": "显灵救人期",
     "era": "童年段 · 1988年前后", "styleTone": "...",
     "final": {"engine": "Image2", "id": "...", "path": "candidates/.../02.png"},
     "alternates": [{"engine": "MJ", "id": "...", "path": "..."}],
     "locks": {"face": "...", "body": "...", "clothes": "...", "hair": "..."}}
  ],
  "genRequests": [{"role": "娃娃仙姐姐", "state": "对抗鬼物期", "engine": "MJ"}]
}
```

- `finals[<角色>::<时期>]` 是**单张** image-id（确认造型只能选一张）。`confirmedLooks[].final` 是它的完整引用，`alternates` 是同时期其它 ❤️ 心仪图。
- `locks[<角色>::<时期>]` 是下一版生成的倾向参考。人物定妆可锁 `face/body/clothes/hair`（脸/身体/衣服/发型）；场景美术/道具可锁 `atmosphere/color/composition/architecture`（氛围/色调/构图/建筑）。后续三视图、人景合一和下一版补图要优先读取这些局部参考。
- `genRequests` 是空行点击记录的「需生成」意图（角色×时期×引擎）。服务器无出图能力，agent 读到后去出图。
- 导入图存在 `candidates/<角色>/<时期>/导入/round-01/`，在网页作为「导入」行显示在 Gemini/Image2 上方。
- `confirmedLooks` is the agent's hand-off for turnaround + overview generation: each confirmed period's single final + alternates + locks. Only act on `生成总览图` when `overviewRequested` is true and `confirmedCount === totalStates`.

## Round Logic

- Round 1 explores four front portrait candidates per role/state/engine.
- The user favorites one or more candidates and writes liked traits.
- Next round prompts should preserve liked traits and only vary requested changes.
- Confirmed look freezes identity and costume; later prompts may change pose or camera but not facial identity, era styling, or clothing design unless the scene state requires it.

## Turnaround Prompt Additions

Add these constraints to confirmed-look prompts:

- same fictional actor face in all three views
- exact same hairstyle, clothing, accessories, fabric wear, and shoes
- full body, feet visible
- arms relaxed or neutral pose
- no labels, no diagram text
- plain light-gray or off-white background
- avoid dynamic lighting that hides costume detail

## Review Checklist

For each candidate:

- Does the face fit age and identity?
- Does the clothing match the era and class?
- Does the hairstyle match character setting?
- Does the image support later consistency reference?
- Does it avoid modern fashion, idol polish, anime, and public-person likeness?

For each final turnaround:

- Are there exactly three views?
- Is the whole body visible?
- Are all views the same character and outfit?
- Are back-view hairstyle and costume details visible?
- Is the image clean enough for manju production reference?
