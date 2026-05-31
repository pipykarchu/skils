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
   - Use a local webpage with role blocks.
   - Under each role, split by scene/state.
   - Show MJ and Image2 candidate groups separately, each with four front portrait images.
   - Allow favorite marking, multi-select, notes for "心仪的点", and an adjustment prompt field.
   - Provide buttons:
     - `进入下一版`: generate another candidate round from favorites + notes.
     - `确认造型`: mark final reference for turnaround generation.
     - `保存选择`: write JSON state to the project.

5. **Generate final turnarounds**
   - Only after user confirms a look.
   - Use the selected image(s) as reference when the tool path supports references.
   - Generate front/side/back full-body sheets per confirmed role state.
   - Prompt for consistent face, same clothing, same fabric, same hairstyle, full body, neutral background, no text, no watermark.

6. **Export production assets**
   - Save high-resolution images under a project folder such as `08_生成图片/定妆造/<角色>/<场景>/`.
   - Save JSON selection state and prompt history.
   - Build an overview sheet after all roles/states are confirmed.
   - Report paths, selected roles, and any failed/needs-regeneration items.

## Web Gallery

Prefer creating a local static HTML plus a tiny localhost save server. Use `scripts/casting_gallery_server.py` as a reusable starting point when helpful. Copy or adapt it into the project rather than editing the skill copy directly.

The gallery must support:

- Role section -> scene/state subsection -> MJ/Image2 candidate group
- Four portrait candidates per group in early rounds
- Favorite/star selection
- Notes field for preferred traits
- Adjustment prompt field
- Confirmed final look state
- Saved JSON that Codex can read in the next step

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
