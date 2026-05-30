# PRD Web Output Style

Use this reference when generating `<项目名>_PRD.html` after the PRD Markdown is complete.

## File Contract

- Input source: `<项目名>_PRD.md`.
- Output file: `<项目名>_PRD.html` in the same project folder.
- Keep the HTML content aligned with the Markdown. If Markdown changes, update the HTML.
- Use a self-contained static HTML file with inline CSS and minimal inline JavaScript only when useful for navigation.
- Do not require a dev server, package install, CDN, external font, external icon library, or build step.

## 皮玺玉风格

Interpret 皮玺玉风格 as a clean product-manager review document style:

- 白底、克制、清爽，有产品经理笔记感。
- 大标题醒目，正文安静，信息密度适中，适合评审和交付。
- 用青绿、蓝、浅紫、玫红作少量高亮，不做单一色系页面。
- 使用细线、浅色底、左侧强调线、状态标签、表格和编号，让结构清楚。
- 不使用装饰性渐变球、浮夸营销 hero、暗色大背景或卡片套卡片。
- 视觉重点放在项目名、文档状态、MVP 范围、核心功能、风险和待确认项。

## Layout

Desktop:

- Top document header: project name, PRD status, version, update date, owner.
- Left sticky table of contents if the document is long.
- Main content width around 960-1120px.
- Sections are separated by whitespace, subtle borders, or left accent bars.
- Tables use sticky or high-contrast headers when practical.

Mobile:

- Collapse the table of contents into a horizontal top nav or simple section list.
- Tables must scroll horizontally instead of compressing text.
- Text must not overflow buttons, tags, table cells, or section headers.

## Visual Tokens

Suggested CSS variables:

```css
:root {
  --bg: #fbfcfd;
  --paper: #ffffff;
  --text: #24272f;
  --muted: #6d7280;
  --line: #e7eaf0;
  --green: #17b26a;
  --cyan: #06b6d4;
  --blue: #2563eb;
  --purple: #8b5cf6;
  --pink: #ec4899;
  --warning: #f59e0b;
  --danger: #ef4444;
}
```

Use system fonts:

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
```

Do not scale font size with viewport width. Do not use negative letter spacing.

## Required Page Sections

The web page should render these PRD areas when present:

1. 文档说明 and revision log.
2. 背景与目标.
3. MVP 范围 and 本版不做.
4. 产品方案: feature structure, information structure, flows.
5. 全局规则.
6. 需求列表 and requirement details.
7. 非功能需求.
8. 埋点与数据.
9. 项目计划.
10. 风险与待确认.

## Component Guidance

- Use status chips for `草稿`, `概念待确认`, `待评审`, `已确认`, `待确认`, `P0/P1/P2`.
- Use callout bands for assumptions, risks, and open questions.
- Use tables for lists and fields. Avoid paragraph-only PRDs.
- Use definition lists or compact grids for metadata.
- If the PRD includes Mermaid diagrams, keep the source visible in a styled `pre` block unless a renderer is already available locally.
- Use anchor links for sections.

## Quality Checks

Before finishing:

- The HTML opens directly in a browser.
- Project name and document status are visible in the first viewport.
- Markdown and HTML have the same major sections.
- No text overlaps, no clipped table headers, and no unreadable low-contrast text.
- Mobile width around 390px remains readable.
