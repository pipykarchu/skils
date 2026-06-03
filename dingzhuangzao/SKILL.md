---
name: dingzhuangzao
description: Create role casting looks and character three-view turnaround sheets for Chinese comic-drama/manju production. Use when the user asks for 定妆造, 角色定妆, 角色三视图, 角色设定照, 服装造型, 漫剧角色形象选择, MJ/Image2 prompt batches, candidate galleries, selectable web review pages, or final overview sheets grounded in project worldview, era, scenes, and character files.
---

# 定妆造

## Purpose

Run a manju character casting workflow: read project worldview and character folders, generate era-accurate front/side/back three-view character candidates, present them in a selectable web gallery, and keep every confirmed look as a high-resolution turnaround reference.

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
   - Character casting batches are **three-view turnaround candidates** by default: each candidate is one image sheet with front view, side view, and back view of the same full-body character.
   - Each candidate must preserve the same role identity across all three views while exploring controlled variation between candidates: face shape, hairstyle detail, clothing wear, temperament, color temperature.

3. **Generate or prepare candidate images**
   - If API access is available and user approved cost/account use, generate 4 three-view turnaround candidates per model version.
   - If API is unavailable, save prompt files and build the gallery with placeholder slots or existing images.
   - Never save API keys into the project. Read keys from environment variables such as `TUZI_API_KEY`.

4. **Build the web selection page**
   - Use a local three-pane webpage driven by a manifest JSON (`scripts/casting_gallery_server.py`).
   - **Left pane**: roles grouped into modules (e.g. 主线/守护灵体与道具/家族长辈/鬼怪反派/现实层旁听). Each role is collapsible and expands to that role's time periods (states). A dot on the role marks "has a confirmed look"; a ✓ on a period marks it confirmed.
   - **Center pane**: the selected role+period. Candidate rows are shown as 导入(if any) → Gemini Image → Image2 → MJ → other engines. 人物定妆 rows hold up to four three-view turnaround candidates; 场景/道具 rows hold visual concept candidates. The current period's overall tone shows in a top-right `整体基调风格` card. Below the rows: `心仪的点` and `调整提示词` fields, plus `进入下一版（三视图）` and `确认此时期造型` buttons for character modules.
   - **Right pane**: the worldview/scene background for that period (era, scene, space, props, costume, light, forbidden items, keyword tags) plus copyable Gemini/Image2/MJ prompt blocks — read from `state.worldview` and `state.prompts`.
   - **Heart vs confirm are separate**: clicking an image (or its top-right ❤️) toggles a 心仪 like (multi-select). `确认此时期造型` marks the whole period final; in a confirmed period the liked images become its final reference images. Confirming with zero hearts warns the user.
   - Every image card supports review cleanup and inspection: `删除` performs a soft delete only (records `deleted` in `selection-state.json`, clears related hearts/finals/locks, and never removes the disk image file); double-clicking a real image opens a large preview lightbox.
   - **Bottom bar**: `生成总览图` stays disabled until every period is confirmed. It does **not** draw anything — it records the intent (`overviewRequested:true`) plus `confirmedLooks` into the saved JSON, so the agent generates the overview in the next step.
   - Every image card can additionally lock partial references. 人物定妆 modules show `脸` / `身体` / `衣服` / `发型`; 场景美术/道具 modules show `氛围` / `色调` / `构图` / `建筑`. These locks are saved into `selection-state.json` and carried in `confirmedLooks[].locks` for later 下一版三视图生成、场景融合、人景合一.
   - `保存选择`: write `selection-state.json` (likes, locks, finals, notes, confirmedLooks, genRequests, overviewRequested) to the project.

5. **Generate / refine turnarounds**
   - 定妆造生成目标始终是三视图：正面、侧面、背面并排，全身，姿势统一。
   - The `进入下一版（三视图）` action records `nextRoundRequests[].outputType = "character_turnaround_3view"` in `selection-state.json`; the next agent step must generate three-view sheets, not another portrait-only batch.
   - Use the selected image(s), hearts, and local locks as references when the tool path supports references.
   - Prompt for consistent face, same clothing, same fabric, same hairstyle, full body, neutral background, no text, no watermark.

6. **Export production assets**
   - Save high-resolution images under a project folder such as `08_生成图片/定妆造/candidates/<角色>/<时期>/<engine>/round-XX/`.
   - Save JSON selection state and prompt history.
   - Package prompts by character into `03_角色设定/定妆提示词/<角色>_定妆提示词合集.md` (use `package_prompts_by_role.py`; merge life-stage aliases of the same person into one file).
   - Collect confirmed + ❤️ liked images into `08_生成图片/角色妆造敲定合集/` named `<角色>_<时期>_<kind>_<引擎>_<原名>` where `kind` is `final` / `liked` / `ref` (use `export_confirmed_looks.py`, which reads `confirmedLooks[].final`, `confirmedLooks[].alternates`, and backward-compatible `confirmedLooks[].refs` from `selection-state.json`).
   - Build an overview sheet only after all roles/states are confirmed and the user clicked `生成总览图` (read `confirmedLooks` from the saved JSON for the reference set).
   - Report paths, selected roles, and any failed/needs-regeneration items.

## Hand-off to storyboard-image-prompts

定妆造 and `storyboard-image-prompts` are **separate skills for two pipeline stages** — do not merge them. 定妆造 locks each character's look per period (three-view turnaround casting + review gallery + confirmed master). `storyboard-image-prompts` consumes a **storyboard/shot table** and writes per-shot prompts. The storyboard does not exist during casting, so merging would fold an unusable stage into this one and cause skill-routing collisions.

The contract between them is the **character anchor**: once a look is confirmed here, hand its locked anchor (Chinese name + age range + face/hair/signature clothing + one unique visible trait, from the confirmed reference image and the period's prompt) to `storyboard-image-prompts`, which repeats that anchor verbatim across every shot of that character. Keep era styling, clothing design, and facial identity frozen unless a scene state requires change.

## Casting prompts (this skill's own prompts)

定妆造 writes its **own** casting prompts (not the shot prompts). For each role × period write prompt files under `08_生成图片/定妆造/prompts/`:

- `<角色>_<时期>_Gemini_Image_round01.md` or `<角色>_<时期>_Gemini Image_round01.md` — image-to-image / next-round default three-view prompt when the project uses Gemini/Image2 free quota
- `<角色>_<时期>_Image2_round01.md` — full-sentence three-view constraints
- `<角色>_<时期>_MJ_round01.md` — compact tags + English negatives; append a wide ratio such as `--ar 16:9` for a three-view sheet unless the user specifies another layout

Four three-view turnaround candidates per file, same identity with controlled variation. `build_manifest.py` reads these into each `state.prompts` so the gallery shows them in the right panel (below the worldview block, with copy buttons). The style-tone wording is the project's own (e.g. 故事项目风格), not a named-artist style, unless the user asks.

## Web Gallery

Prefer creating a local manifest-driven HTML plus a tiny localhost server. Use `scripts/casting_gallery_server.py` as the reusable starting point. Copy it into the project output folder (`08_生成图片/定妆造/`) rather than editing the skill copy directly, and generate the project `manifest.json` alongside it (a `build_manifest.py` that reads the character archive + worldview file is the cleanest way — see the 娃娃仙 instance).

The server is intentionally backend-light for normal review: it serves the page, serves `manifest.json` via `/api/manifest` (re-read from disk each request, so editing the manifest hot-reloads), serves images via `/asset/<relpath>` (path-traversal guarded), and persists the review state via `POST /api/save`. Empty candidate cards also support optional double-click generation through `/api/generate-slot` after the user confirms cost; this reads `TUZI_API_KEY` from the environment only, writes the generated image into `candidates/...`, updates the matching `manifest.json` slot, and must never save API keys.

### Unified page with changjingmeishu

When a project also uses `changjingmeishu`, prefer **one shared visual review page** instead of two separate review pages:

```text
08_生成图片/视觉定版评审/
  manifest.json
  casting_gallery_server.py
  selection-state.json
  candidates/
    人物/<角色>/<时期>/<engine>/round-XX/*.png
    场景/<场地>/<子场景>/<变体>/<engine>/round-XX/*.png
    道具/<道具名>/<变体>/<engine>/round-XX/*.png
```

Use one manifest with modules such as `人物定妆 · 主线角色`, `人物定妆 · 反派`, `场景美术 · 阿妮家`, `道具定版 · 护身物`. The webpage, import button, save state, likes, finals, local locks, and `confirmedLooks` are all shared. Exporters can later split confirmed results into `03_角色设定/定妆造/`, `02_世界观/视觉定版/场景/`, and `02_世界观/视觉定版/道具/`.

Backend requirement: this is a tiny local Python server, not an image-generation backend. It is needed for upload/import, hot-reloading the manifest, serving local images safely, and saving `selection-state.json`. A pure static HTML version is acceptable only for read-only interview display.

The gallery must support:

- Module → role (collapsible) → period(state) left navigation; module titles are sticky
- Center: rows are 导入(if any) → Gemini Image → Image2 → MJ → other engines; 人物定妆 rows show four three-view candidates each in early rounds; 场景/道具 rows show visual concept candidates; a single 导入图(≤4) button in the center header (imports land as a 导入 row above Gemini/Image2 via `/api/import`, saved to `candidates/<角色>/<时期>/导入/round-01/`)
- Empty Gemini/Image2/MJ rows display four small candidate cards by default. Single-click records a **generate intent** (`STATE.gen`, persisted as `genRequests`); for 人物定妆, `genRequests[].outputType` must be `character_turnaround_3view`. Double-clicking an empty non-Midjourney card asks the user to confirm API cost, then calls `/api/generate-slot` and writes the generated image back into that card's manifest slot. Midjourney/MJ remains a manual channel when the provider endpoint is unavailable; empty Midjourney cards copy the MJ prompt and open the user's MJimage page (`https://mj1mage.zeabur.app/`) instead of calling `/api/generate-slot`. Empty `图生图` placeholder cards are different: single-click opens a local file picker, uploads the chosen PNG/JPG/WebP into that exact slot through `/api/upload-slot`, and updates the matching `manifest.json` image path instead of creating a separate 导入 row.
- Right: per-period tone card (top) → worldview/scene panel → 定妆提示词 block (Gemini/Image2/MJ with copy buttons)
- ❤️ like (multi-select) distinct from `确认此时期造型`; only clicking the heart toggles like. Clicking the card body must not toggle ❤️ during normal browsing; it only selects the final image while the page is in multi-liked pick-one mode. **Confirm is single-select** — `finals[period]` stores one image id (0 likes → prompt; 1 like → auto-final; multiple → pick-one mode)
- Lock buttons are independent from ❤️ and final confirmation. 人物模块：`脸` / `身体` / `衣服` / `发型`; 场景/道具模块：`氛围` / `色调` / `构图` / `建筑`. Use them when one candidate has the right face but another candidate has better body proportion/costume, or when one scene candidate has better mood but another has better composition/building structure.
- Left navigation bottom: include a collapsible `平台 Key` panel for Nano Banana Pro / Seedream 5 / Midjourney / Image2 / 可灵 / 即梦 / Seedance. Values are stored only in the current browser `localStorage` (`visualReviewProviderKeys`) and must never be written to `selection-state.json`, project files, skill files, or Git.
- Key actions (❤️ / 删除 / 双击预览 / 空卡双击生成 / 图生图空卡上传 / 进入下一版 / 确认此造型 / 导入 / 生成意图) **auto-save** to `selection-state.json`; the `保存选择` button is a manual fallback. Double-click preview does not modify state; empty-card double-click can consume API balance after confirmation; 图生图空卡上传 only copies the selected local image into project assets and updates `manifest.json`.
- Dark/light theme toggle (🌙/☀ in header), persisted to localStorage, defaults to system `prefers-color-scheme`
- Saved JSON (`selection-state.json`) with `confirmedLooks` (each with a single `final` + `alternates` + `locks`), `deleted`, `genRequests`, and `nextRoundRequests` the agent reads next. For 人物定妆, both request arrays must produce three-view sheets; deleted cards must be skipped by export/overview/generation steps.

## Helper scripts (per project, in `08_生成图片/定妆造/` or `08_生成图片/视觉定版评审/`)

- `build_manifest.py` — reads character archive + worldview, emits `manifest.json`; backfills existing images (`attach_existing_images`) and reads prompts into `state.prompts` (`attach_prompts`). Use `image_dir=`/`prompt_base=` on a `state()` when a folder/file name differs from the period name.
- `casting_gallery_server.py` — the three-pane review server (copied from this skill).
- `package_prompts_by_role.py` — packages per-period prompts into per-character collection files under `03_角色设定/定妆提示词/`.
- `export_confirmed_looks.py` — copies confirmed + liked images into `08_生成图片/角色妆造敲定合集/`.
- `start.bat` — smart launcher (dependency check, port-conflict kill/switch/cancel, auto-open browser).

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
                "era": "童年段 · 1988年前后",
                "scene": "右栏正文说明",
                "space": "...", "props": "...", "costume": "...",
                "light": "...", "forbid": "...",
                "keywords": ["多条麻花辫", "灰花袄"]
              },
              "prompts": {
                "base": "娃娃仙姐姐_五辫阶段",
                "image2": "## 候选01_...\\n整句提示词全文",
                "mj": "## 候选01_...\\n紧凑标签 ... --ar 9:16"
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
- `prompts` is injected by `build_manifest.py`'s `attach_prompts` from the per-period prompt files; the right panel shows it with copy buttons. Omit it when no prompt file exists.
- `image.path` empty → renders a placeholder slot (before generation). Backfill the path after images exist.
- Group order is normalized to Image2-then-MJ regardless of authoring order; a missing engine renders an empty row.
- `modules` is optional; a flat `roles` array at the top level also works.


## Prompt Rules

For character three-view candidates:

```text
角色：<name>
阶段/场景：<state>
目标：四张角色三视图定妆候选。每张候选都是一张横版角色设定图，包含同一角色的正面、侧面、背面三视图，全身，脚完整可见，姿势统一，用于定妆选择
世界观约束：<era, region, class, scene>
外貌锚点：<face, age, hair, temperament>
服装造型：<fabric, cut, color, wear, shoes/accessories>
风格：皮玺玉风格转译，真人短剧质感，民俗/年代氛围，低饱和，虚构演员脸
三视图要求：同一张图内三视图必须是同一虚构演员脸、同一发型、同一服装、同一鞋袜和配饰；正面/侧面/背面并排，比例一致，干净浅灰或米灰背景
变化范围：四张候选之间只微调气质和造型细节，不改变年龄、身份、核心识别点
禁止：明星脸，真实人物肖像，现代潮流服饰，二次元，Q版，文字，水印
```

For next-round / final turnarounds:

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
