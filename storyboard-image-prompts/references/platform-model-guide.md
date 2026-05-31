# Platform and Model Guide

Use this guide to choose a practical image-generation target for each shot. Model names change often; verify official docs before paid production runs or when the user asks for the latest option.

## Quick Decision Table

| Need | Prefer | Why |
| --- | --- | --- |
| Strong character mood and beautiful cinematic stills | Current Midjourney model; use V7 default or newer V8.x if available in the user's account | Fast visual exploration, strong aesthetics, good style/reference controls |
| Precise instruction following, text in image, product/detail control | OpenAI Images `gpt-image-1.5`, `gpt-image-1`, or current official image model | Strong prompt adherence and editing workflows |
| Gemini ecosystem, multimodal reference understanding, Imagen access | Gemini/Imagen current official model | Useful when source analysis and image generation sit in the same Google workflow |
| Cinematic keyframes for video pipeline | Runway `gen4_image`, `gen4_image_turbo`, or current Runway image model | Useful for image-to-video continuity and film-style frames |
| Chinese short-drama/manju, domestic platform delivery | 即梦/Jimeng 4.x, 可灵/Kling, 通义万相/Qwen Image, 腾讯混元 | Chinese UI/ecosystem, common in local AI video/image workflows |
| Maximum reproducibility and local pipeline control | Stable Diffusion XL, SD3.x, FLUX, ComfyUI | Fixed seeds, LoRA, ControlNet, IP-Adapter, batch automation |
| Character locked by custom training | SD/FLUX LoRA workflow, then optional Midjourney/OpenAI reference tests | Best when the same face/clothing must survive many shots |

## Shot-Based Heuristics

### Character Close-Up

Prefer models with reference image or character consistency support. Use exact anchor wording and include visible identity details. If the same protagonist appears in many shots, recommend reference images or LoRA.

Prompt focus:

```text
人物面部结构, 发型, 服装, 表情, 眼神, 近景/特写, 背景虚化, 光源方向
```

### Wide Establishing Shot

Prefer models strong at environment design and cinematic composition. Character details matter less than geography, architecture, era, scale, weather, and lighting.

Prompt focus:

```text
地点类型, 年代, 建筑/街道/室内布局, 人物站位, 天气, 时间, 景别, 构图
```

### Action or Conflict Shot

Prefer models that follow pose/action instructions well, or use ControlNet/OpenPose in SD/ComfyUI if pose precision is required.

Prompt focus:

```text
动作瞬间, 身体姿态, 道具关系, 画面动势, 运动模糊, 紧张光影
```

### Emotional Dialogue Shot

Prefer models with strong face expression and cinematic lighting. Keep dialogue content out of the prompt unless visible text is required.

Prompt focus:

```text
双人站位, 视线关系, 表情差异, 肩越肩/正反打, 近景, 情绪光线
```

### Product, Prop, or Text-Heavy Shot

Prefer OpenAI Images or Gemini/Imagen. If exact Chinese text must appear, warn that manual correction or design software may still be needed.

Prompt focus:

```text
物品形状, 材质, 标签内容, 手持关系, 清晰可读, 干净背景
```

## Platform Notes

- Midjourney: use concise visual prompts, style/reference images, aspect ratio, and version/style parameters when available. Good for look development and cinematic atmosphere.
- OpenAI Images: use explicit instructions, editing/masking when needed, and clear constraints for text, layout, or brand-safe product work.
- Gemini/Imagen: use when multimodal interpretation, Google ecosystem, or current Imagen models are preferred.
- Runway: use for keyframes that will become video shots; keep prompts cinematic and continuity-aware.
- Kling/Jimeng/Tongyi/Hunyuan: use for Chinese production workflows, especially when the user will continue in Chinese AI video platforms.
- Stable Diffusion/FLUX/ComfyUI: use when the output must be reproducible, automated, locally controlled, or integrated with LoRA/ControlNet/IP-Adapter.

## Recommendation Wording

Always explain the choice briefly:

```text
推荐：Midjourney current。理由：这一镜是主角情绪特写，重点是脸部美感、氛围和电影感。
推荐：ComfyUI + FLUX LoRA。理由：主角连续出现 30 镜，需要固定脸和服装。
推荐：OpenAI Images gpt-image-1.5。理由：画面包含海报文字和明确构图，要求遵循提示词。
推荐：即梦 4.6。理由：中文分镜组图和多参考图输入更贴近国内漫剧生产。
推荐：wan2.7-image-pro。理由：需要组图、较高分辨率和中文文字控制。
```

If the user has a fixed platform subscription, prioritize that platform and adapt prompts to its style instead of forcing a different tool.
