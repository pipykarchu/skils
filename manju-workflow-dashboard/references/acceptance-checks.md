# 漫剧工作流看板验收与自检

## Stage Gate Checks

For every stage, include:

- Input exists
- Output path is named
- Platform or local tool is specified
- Human confirmation method is clear
- Fail/retry condition is clear
- Next stage is clear

## Script Import

- Script files exist in `05_剧本` or are explicitly marked pending.
- Episode count and trailer/full-episode target are clear.
- Character names and relationship terms are consistent.

## Storyboard

- Shot count and total duration are stated.
- Aspect ratio is stated.
- Each shot has visual content, subtitle/dialogue, and sound notes.

## Image Generation

- Character/prop anchors exist before batch generation.
- Platform allocation is explicit: MJ/Image2/即梦 or other.
- Output naming convention is stated, for example `shot_01.png`.

## Video Generation

- S/A/B/C shot priority is stated.
- Paid tools are limited to high-value shots.
- Free/low-cost tools are tried before Seedance when budget matters.
- Fail conditions include face drift, extra hands, wrong prop count, wrong era, wrong monster style.

## Assembly

- FFmpeg or editing app path is specified.
- Master export format is stated.
- Subtitle, audio, and rough cut outputs are named.

## Platform Export

- B 站 horizontal or vertical strategy is explicit.
- 抖音/红果 crop or recut strategy is explicit.
- Safe area for vertical cropping is stated if using a horizontal master.

## Final Acceptance

- First 3 seconds have a hook.
- Main story can be understood with audio only.
- Key props are visible.
- Paid video seconds are counted.
- Each fail item has a retry owner/tool.
