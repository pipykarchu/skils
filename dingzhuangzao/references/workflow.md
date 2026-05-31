# 定妆造 Workflow Reference

## Folder Pattern

Recommended project output:

```text
08_生成图片/
  定妆造/
    manifest.json
    selection-state.json
    prompts/
      <角色>_<场景>_MJ.md
      <角色>_<场景>_Image2.md
    candidates/
      <角色>/<场景>/mj/round-01/*.png
      <角色>/<场景>/image2/round-01/*.png
    final/
      <角色>/<场景>/turnaround.png
    overview/
      定妆造_总览.png
```

## Candidate Manifest

Use this JSON shape for gallery state:

```json
{
  "project": "娃娃仙",
  "round": 1,
  "roles": [
    {
      "name": "娃娃仙姐姐",
      "states": [
        {
          "name": "五辫阶段",
          "groups": [
            {
              "engine": "image2",
              "promptFile": "prompts/娃娃仙姐姐_五辫阶段_Image2.md",
              "images": [
                {"id": "wawa-01", "path": "candidates/娃娃仙姐姐/五辫阶段/image2/round-01/01.png"}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

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
