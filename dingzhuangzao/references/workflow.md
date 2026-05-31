# 定妆造 Workflow Reference

## Folder Pattern

Recommended project output:

```text
08_生成图片/
  定妆造/
    build_manifest.py     # 读角色档案+世界观，生成 manifest.json
    manifest.json         # 驱动网页的数据
    casting_gallery_server.py  # 从 skill 拷入
    start.bat             # 智能启动（依赖检查/端口冲突/自动开浏览器）
    selection-state.json  # 网页保存的评审状态
    prompts/
      <角色>_<时期>_MJ_round01.md
      <角色>_<时期>_Image2_round01.md
    candidates/
      <角色>/<时期>/image2/round-01/*.png
      <角色>/<时期>/mj/round-01/*.png
    final/
      <角色>/<时期>/turnaround.png
    overview/
      定妆造_总览.png
```

`build_manifest.py` 的 `attach_existing_images` 会扫描 `candidates/<角色>/<时期>/<engine>/round-*/` 自动把已生成图片回填进 manifest；历史目录名与时期名不一致时，用 `state(..., image_dir="旧目录名")` 做别名。

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
  "finals": {"<角色>::<时期>": true},
  "notes": {"<角色>::<时期>": {"likes": "...", "adjustments": "...", "nextRound": true}},
  "overviewRequested": true,
  "confirmedCount": 18, "totalStates": 18,
  "confirmedLooks": [
    {"module": "守护灵体与道具", "role": "娃娃仙姐姐", "state": "显灵救人期",
     "era": "童年段 · 1990年前后", "styleTone": "...",
     "refs": [{"engine": "Image2", "id": "...", "path": "candidates/.../02.png"}]}
  ]
}
```

`confirmedLooks` is the agent's hand-off for turnaround + overview generation: each confirmed period plus its liked reference images. Only act on `生成总览图` when `overviewRequested` is true and `confirmedCount === totalStates`.

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
