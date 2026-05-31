---
name: dingzhuangzao
description: Create role casting looks, portrait candidates, and character turnaround sheets for Chinese comic-drama/manju production. Use when the user asks for 定妆造, 角色定妆, 角色三视图, 角色设定照, 服装造型, 漫剧角色形象选择, MJ/Image2 prompt batches, candidate image galleries, selectable web review pages, or final overview sheets grounded in project worldview, era, scenes, and character files.
---

# 定妆造

## Purpose

Run a manju character casting workflow: read project worldview and character folders, generate era-accurate portrait candidates first, present them in a selectable web gallery, then turn confirmed looks into high-resolution front/side/back character turnaround sheets.

Default language is Chinese. Explain goals in plain Chinese before commands or file edits. Always state risks before API calls, file writes, or account usage.

## Required Context

Before writing prompts or generating images, read the project files that define visual truth:

- `02_世界观/年代设定与场景刻画.md`
- `03_角色设定/角色档案.md`
- `03_角色设定/角色固定提示词.md`
- Relevant episode scripts, shot tables, or image prompts if the user names a scene or episode

If folders differ, search for files containing `世界观`, `年代`, `场景`, `角色`, `固定提示词`, `分镜`, `生图提示词`.

Use these files to lock:

- Era, region, social class, weather, interiors/exteriors
- Costume fabrics, hairstyle, footwear, tools, dirt/wear level
- Character age, face continuity, emotional temperament
- Scene-specific makeup, damage, ritual objects, or clothing changes

## Visual Style

If the user requests `皮玺玉风格`, treat it as a project style anchor and translate it into operational prompts:

- Chinese manju / short-drama realism
- Grounded live-action casting feel, not anime, not glossy idol portrait
- Folk-horror atmosphere where appropriate
- Restrained color, textured fabric, era-accurate rural styling
- Clear facial identity suitable for later consistency reference

Do not rely only on the style name. Always include concrete visual features from the worldview files.

## Workflow

1. **Audit source files**
   - Summarize the era, region, clothing rules, and role list.
   - Identify roles and scene states: normal look, night scene look, ritual look, damaged look, aged look, ghost/monster look.

2. **Create prompt batches**
   - For each role and scene state, create two prompt versions when useful:
     - `MJ版`: Midjourney-oriented prompt with compact visual tags and no parameter spam unless the user asks.
     - `Image2版`: Image2/Tu-zi/gpt-image prompt with full sentence constraints.
   - First batch is **four front portrait candidates**, not three views.
   - Each candidate must preserve the same role identity but explore controlled variation: face shape, hairstyle detail, clothing wear, temperament, color temperature.

3. **Generate or prepare candidate images**
   - If API access is available and user approved cost/account use, generate 4 portrait candidates per model version.
   - If API is unavailable, save prompt files and build the gallery with placeholder slots or existing images.
   - Never save API keys into the project. Read keys from environment variables such as `TUZI_API_KEY`.

4. **Build the web selection page**
   - Use a local three-pane webpage driven by a manifest JSON (`scripts/casting_gallery_server.py`).
   - **Left pane**: roles grouped into modules (e.g. 主线/守护灵体与道具/家族长辈/鬼怪反派/现实层旁听). Each role is collapsible and expands to that role's time periods (states). A dot on the role marks "has a confirmed look"; a ✓ on a period marks it confirmed.
   - **Center pane**: the selected role+period. Two fixed rows — Image2 on top, MJ below — each holding four front portrait candidates. The current period's overall tone shows in a top-right `整体基调风格` card. Below the rows: `心仪的点` and `调整提示词` fields, plus `进入下一版` and `确认此时期造型` buttons.
   - **Right pane**: the worldview/scene background for that period (era, scene, space, props, costume, light, forbidden items, keyword tags) — read from `state.worldview`.
   - **Heart vs confirm are separate**: clicking an image (or its top-right ❤️) toggles a 心仪 like (multi-select). `确认此时期造型` marks the whole period final; in a confirmed period the liked images become its final reference images. Confirming with zero hearts warns the user.
   - **Bottom bar**: `生成总览图` stays disabled until every period is confirmed. It does **not** draw anything — it records the intent (`overviewRequested:true`) plus `confirmedLooks` into the saved JSON, so the agent generates the overview in the next step.
   - `保存选择`: write `selection-state.json` (likes, finals, notes, confirmedLooks, overviewRequested) to the project.

5. **Generate final turnarounds**
   - Only after user confirms a look.
   - Use the selected image(s) as reference when the tool path supports references.
   - Generate front/side/back full-body sheets per confirmed role state.
   - Prompt for consistent face, same clothing, same fabric, same hairstyle, full body, neutral background, no text, no watermark.

6. **Export production assets**
   - Save high-resolution images under a project folder such as `08_生成图片/定妆造/<角色>/<场景>/`.
   - Save JSON selection state and prompt history.
   - Build an overview sheet only after all roles/states are confirmed and the user clicked `生成总览图` (read `confirmedLooks` from the saved JSON for the reference set).
   - Report paths, selected roles, and any failed/needs-regeneration items.

## Web Gallery

Prefer creating a local manifest-driven HTML plus a tiny localhost server. Use `scripts/casting_gallery_server.py` as the reusable starting point. Copy it into the project output folder (`08_生成图片/定妆造/`) rather than editing the skill copy directly, and generate the project `manifest.json` alongside it (a `build_manifest.py` that reads the character archive + worldview file is the cleanest way — see the 娃娃仙 instance).

The server is intentionally backend-light and **never calls any image API**: it serves the page, serves `manifest.json` via `/api/manifest` (re-read from disk each request, so editing the manifest hot-reloads), serves images via `/asset/<relpath>` (path-traversal guarded), and persists the review state via `POST /api/save`. All generation happens in the agent step, not the browser.

The gallery must support:

- Module → role (collapsible) → period(state) left navigation
- Center: Image2 row over MJ row, four candidates each in early rounds, top-right tone card
- Right: per-period worldview/scene panel
- ❤️ like (multi-select) distinct from `确认此时期造型`
- Notes (`心仪的点`) and adjustment-prompt fields
- `进入下一版` / `确认此时期造型` / `生成总览图`(intent only) / `保存选择`
- Saved JSON (`selection-state.json`) with `confirmedLooks` the agent can read next

## Manifest Schema

`manifest.json` drives the whole page:

```json
{
  "project": "娃娃仙",
  "round": 1,
  "styleTone": "整体基调默认值（皮玺玉风格转译…）",
  "modules": [
    {
      "name": "守护灵体与道具",
      "roles": [
        {
          "name": "娃娃仙姐姐",
          "age": "外形十五六岁",
          "states": [
            {
              "name": "显灵救人期",
              "age": "外形十五六岁",
              "styleTone": "可选，覆盖该时期的整体基调，留空则回退到 role/manifest",
              "worldview": {
                "era": "童年段 · 1990年前后",
                "scene": "右栏正文说明",
                "space": "...", "props": "...", "costume": "...",
                "light": "...", "forbid": "...",
                "keywords": ["多条麻花辫", "灰花袄"]
              },
              "groups": [
                {"engine": "Image2", "label": "...", "images": [
                  {"id": "wawaxian-显灵救人期-i2-01", "path": "candidates/.../01.png", "note": ""}
                ]},
                {"engine": "MJ", "label": "...", "images": [ ... ]}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

- `styleTone` resolves period → role → manifest (first non-empty wins).
- `image.path` empty → renders a placeholder slot (before generation). Backfill the path after images exist.
- Group order is normalized to Image2-then-MJ regardless of authoring order; a missing engine renders an empty row.
- `modules` is optional; a flat `roles` array at the top level also works.


## Prompt Rules

For portrait candidates:

```text
角色：<name>
阶段/场景：<state>
目标：四张正面肖像候选，用于定妆选择，不生成三视图
世界观约束：<era, region, class, scene>
外貌锚点：<face, age, hair, temperament>
服装造型：<fabric, cut, color, wear, shoes/accessories>
风格：皮玺玉风格转译，真人短剧质感，民俗/年代氛围，低饱和，虚构演员脸
变化范围：四张只微调气质和造型细节，不改变年龄、身份、核心识别点
禁止：明星脸，真实人物肖像，现代潮流服饰，二次元，Q版，文字，水印
```

For final turnarounds:

```text
基于已确认形象生成角色三视图：正面、左侧面、背面并排，全身，姿势统一，服装和五官完全一致，干净浅灰背景，角色设定图，高清细节，无文字无水印。
```

## Quality Checks

Before handing off:

- Verify every role/state has saved prompt history.
- Verify gallery save JSON exists and is readable.
- Verify final turnaround images are full-body front/side/back, not random poses.
- Check costume against `年代设定与场景刻画.md`.
- Check no text/watermark appears in generated images.
- Produce a contact sheet or overview after final selection.

## Risk Notes

State these before execution when applicable:

- Generating with Tu-zi/MJ/Image2 sends prompts and possibly reference images to external services.
- API generation consumes account balance.
- Uploading reference images may expose character art to that platform.
- Local web servers occupy a localhost port until stopped.
- File writes create or update project assets; avoid overwriting unless explicitly requested.
