---
name: storyboard-image-prompts
description: Generate AI drawing/image prompts from screenplays, scripts, shot lists, storyboards, character bibles, or Chinese 漫剧/短剧分镜表. Use when Codex needs to convert scenes and shots into platform-ready prompts, keep character/style consistency, choose suitable image-generation platforms and models for different scenes or characters, or prepare batch prompt tables for Midjourney, OpenAI Images, Gemini/Imagen, Runway, Kling, Jimeng, Hunyuan, Tongyi Wanxiang, Stable Diffusion, FLUX, or similar tools.
---

# Storyboard Image Prompts

## Goal

Turn a script and storyboard into production-ready image prompts. Preserve the story, characters, scene continuity, camera language, and visual style while choosing a practical platform/model for each shot.

## Workflow

1. Read the source material before writing prompts:
   - script or screenplay
   - storyboard table
   - character bible, casting notes, LoRA notes, style references, or previous prompt sheets if provided
2. Extract stable visual facts:
   - character identity, age, clothing, hairstyle, body traits, expression habits
   - location, era, time of day, lighting, weather, props
   - shot size, camera angle, lens feel, motion if relevant
   - required continuity across adjacent shots
3. Choose platform/model per shot using `references/platform-model-guide.md`.
4. Write prompts in the platform's natural prompt style.
5. Output a table or spreadsheet-ready Markdown with one row per shot.
6. Add quality checks and risks when the prompt set depends on paid platforms, external accounts, uploaded references, face likeness, minors, brands, or copyrighted styles.

## Prompt Rules

Prefer objective, visible details over plot explanation. Describe what the image should show, not what the audience should understand.

Keep each shot prompt grounded in the source. Do not invent new characters, plot actions, props, or locations unless the user asks for creative expansion.

Maintain consistency by repeating the same character anchor phrase across shots:

```text
角色锚点 = Chinese name + age range + facial shape + hairstyle + signature clothing + one unique visible trait
```

For recurring characters, produce a compact character anchor block before the shot table. If reference images or LoRA names are provided, include them in the platform-specific prompt field.

Write negative prompts only for platforms that support them or when the user requests Stable Diffusion/ComfyUI-style output.

Avoid camera moves in still-image prompts unless the image model supports cinematic framing language. For pure image generation, translate movement into visible framing:

```text
推镜 -> close-up emphasis / foreground face larger in frame
横移 -> side composition / subject entering from frame edge
俯拍 -> high-angle shot
仰拍 -> low-angle shot
```

## Platform Selection

Use `references/platform-model-guide.md` whenever model choice matters, when the user asks for a suitable model, or when the task spans multiple visual needs.

Default selection logic:

- Character consistency with references: prefer Midjourney, OpenAI Images, Gemini/Imagen, Jimeng, Kling, or SD/FLUX with LoRA/IP-Adapter.
- Chinese short-drama/manju workflow: prefer Jimeng, Kling, Tongyi Wanxiang, Hunyuan, or SD/FLUX when the user needs Chinese UI/ecosystem compatibility.
- Cinematic realism and film stills: prefer Midjourney, Runway Gen-4 Image, OpenAI Images, Gemini/Imagen, Kling, or FLUX.
- Precise text rendering, diagrams, product mockups, or prompt following: prefer OpenAI Images, Gemini/Imagen, Qwen Image, or current Wanxiang models; verify current model docs before high-stakes use.
- Batch production with strict local control: prefer Stable Diffusion/ComfyUI or FLUX workflows with fixed seeds, LoRA, ControlNet/IP-Adapter, and saved node graphs.
- Highly stylized editorial or mood exploration: prefer Midjourney or FLUX, then adapt final locked prompts to the production platform.

If model/platform information could be outdated, say so and verify before recommending paid usage or a production pipeline.

## Output Format

Default to this structure unless the user asks for another format:

| 镜号 | 画面目的 | 推荐平台/模型 | 主提示词 | 角色锚点 | 场景/镜头 | 光影色彩 | 负面提示词 | 参数/备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

For each row:

- `画面目的`: one concise production note, not a plot summary.
- `推荐平台/模型`: include the reason in 5-15 Chinese characters, such as `Midjourney current - 人物氛围强`.
- `主提示词`: write in Chinese by default; add English if the selected platform performs better with English.
- `角色锚点`: repeat stable identity details exactly.
- `场景/镜头`: include shot size, angle, lens feeling, composition.
- `光影色彩`: include time, light source, contrast, palette.
- `负面提示词`: include only useful exclusions.
- `参数/备注`: include aspect ratio, seed/reference, style reference, LoRA, or consistency notes.

## Quality Checks

Before finalizing:

- Verify every storyboard shot has a prompt.
- Verify recurring characters keep the same anchor wording.
- Verify platform/model recommendations match the shot's visual need.
- Flag shots that need reference images, LoRA training, face consistency, or manual review.
- Flag any ambiguous script details instead of silently inventing them.
- Provide a short "成功标志" section for tutorial-style answers, so the user knows what a good output looks like.
