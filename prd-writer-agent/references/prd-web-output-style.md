# PRD Web Output Style

Use this reference when generating `<项目名>_PRD.html` after the PRD Markdown is complete.

## File Contract

- Input source: `<项目名>_PRD.md`.
- Output file: `<项目名>_PRD.html` in the same project folder.
- Keep the HTML content aligned with the Markdown. If Markdown changes, update the HTML.
- Use a self-contained static HTML file with inline CSS and minimal inline JavaScript only when useful for navigation.
- Do not require a dev server, package install, CDN, external font, external icon library, or build step.

## 皮玺玉风格

Interpret 皮玺玉风格 as the same visual language as the personal IP site `皮玺玉 × AI 貔貅`:

- Linear-like minimalism: warm off-white background, quiet document surfaces, thin borders, 8px radius, precise spacing, and high readability.
- Brand cue: use a restrained purple-to-pink gradient (`#A78BFA -> #F472B6`) for the title accent, primary action, or one key line only.
- Secondary cue: use a very light teal/emerald wash for status, success, or flow highlights. Keep it subtle, not a full-page teal theme.
- Personal IP polish: first viewport should feel like a refined portfolio/document hybrid, not a plain export. Use a compact document hero with an eyebrow, H1, subtitle, metadata tiles, and status chips.
- Document-first: PRD content remains the product. Do not turn the page into a marketing landing page; avoid oversized hero sections, stock images, decorative gradient orbs, bokeh blobs, and card-in-card layouts.
- Mascot/assets: do not require the AI 貔貅 image or any external asset. If a local mascot asset is explicitly available, it may be used as a small brand accent, never as the main PRD content.
- Keep the page usable in shallow and dark themes when practical, using CSS variables. If no theme toggle is added, default to the warm light theme.
- Visual priority: project name, document status, version, owner, MVP scope, workflow, cost/output/ROI tables, risks, and open questions.

## Layout

Desktop:

- Top document header: eyebrow, project name, concise positioning, PRD status, version, update date, owner, and 2-4 metric tiles.
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
  --bg: #fafaf7;
  --paper: #ffffff;
  --paper-soft: #f5f3ee;
  --text: #1c1c1e;
  --text-secondary: #6b6b73;
  --text-tertiary: #9a9aa3;
  --line: #e8e6e0;
  --purple: #A78BFA;
  --pink: #F472B6;
  --accent: #c084fc;
  --success: #34d399;
  --warning: #fbbf24;
  --danger: #ef4444;
  --teal: #14b8a6;
  --gradient-brand: linear-gradient(135deg, #A78BFA 0%, #F472B6 100%);
  --shadow-brand: 0 8px 24px rgba(167, 139, 250, 0.22);
}

[data-theme="dark"] {
  --bg: #08080a;
  --paper: #131316;
  --paper-soft: #1c1c20;
  --text: #f5f5f7;
  --text-secondary: #a1a1aa;
  --text-tertiary: #71717a;
  --line: #2a2a2e;
}
```

Use system fonts:

```css
font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
font-feature-settings: "cv02", "cv03", "cv04", "cv11";
```

Do not scale font size with viewport width. Do not use negative letter spacing.

Recommended component CSS patterns:

```css
.doc-shell {
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--paper) 80%, transparent) 0%, transparent 62%),
    linear-gradient(135deg, rgba(167,139,250,0.10), rgba(167,139,250,0.04) 34%, transparent 72%),
    linear-gradient(225deg, rgba(20,184,166,0.10), rgba(20,184,166,0.04) 32%, transparent 70%);
}

.brand-text {
  background: var(--gradient-brand);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.metric-tile,
.doc-card,
.toc {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: color-mix(in srgb, var(--paper) 88%, transparent);
}
```

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

- Use status chips for `草稿`, `概念待确认`, `待评审`, `已确认`, `待确认`, `P0/P1/P2`. Chips should be 999px pills with subtle tinted backgrounds.
- Use metric tiles in the document header for 2-4 key facts such as version, status, MVP scope, total milestones, or ROI status.
- Use callout bands for assumptions, risks, and open questions. Use purple for strategy, teal/emerald for success or workflow, amber for risk.
- Use tables for lists and fields. Avoid paragraph-only PRDs.
- Use definition lists or compact grids for metadata.
- If the PRD includes Mermaid diagrams, keep the source visible in a styled `pre` block unless a renderer is already available locally.
- Use anchor links for sections.
- Use subtle hover movement only for obvious clickable controls; static PRD content should not animate.
- Honor reduced-motion preferences if any animation is included.

## Quality Checks

Before finishing:

- The HTML opens directly in a browser.
- Project name and document status are visible in the first viewport.
- Markdown and HTML have the same major sections.
- No text overlaps, no clipped table headers, and no unreadable low-contrast text.
- Mobile width around 390px remains readable.
