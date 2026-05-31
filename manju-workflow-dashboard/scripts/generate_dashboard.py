#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an offline HTML workflow dashboard for AI 漫剧 production."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Stage:
    no: str
    title: str
    input_: str
    tool: str
    output: str
    confirm: str
    fail: str


DEFAULT_STAGES = [
    Stage("01", "剧本导入", "05_剧本/*.md 或用户提供剧本文本", "Codex / 剧本解析 / 人工确认", "剧本清单、集数、角色名、故事口径", "标题、人物、集数、时长、平台方向已确认", "缺剧本、称呼混乱、集数不明"),
    Stage("02", "分镜拆解", "剧本、角色档案、年代设定", "script-to-storyboard / Codex", "06_分镜表/*.md / *.xlsx", "每镜有画面、时长、台词、音效、运镜", "镜头不可画、台词过长、总时长失控"),
    Stage("03", "角色道具定版", "03_角色设定、关键剧情道具", "MJ / Image2 / 即梦", "角色母版、道具母版、风格锚点", "脸、服装、年代、道具数量稳定", "换脸、服装跑偏、道具错误"),
    Stage("04", "横版静帧出图", "分镜和生图提示词", "MJ / Image2 / 即梦", "shot_01.png 到 shot_XX.png", "静帧连播能看懂故事", "构图不适合裁切、主体不清、风格不统一"),
    Stage("05", "动态镜头分级", "静帧主图、分镜表", "人工筛选 / Codex 分级", "S/A/B/C 镜头清单", "付费镜头不超过预算，S 级明确", "所有镜头都想付费、预算不可控"),
    Stage("06", "图生视频", "S/A 级静帧", "可灵 / 即梦 / Seedance 2", "videos_ai/shot_XX.mp4", "不换脸、不多手、动作可读、道具正确", "脸漂移、年代错、怪物风格错、动作糊"),
    Stage("07", "静帧动效", "B/C 级静帧", "FFmpeg / 剪映 / CapCut", "videos_static/shot_XX.mp4", "慢推、横移、快切、切黑节奏自然", "静帧停太久、运动眩晕、字幕遮脸"),
    Stage("08", "声音字幕", "剧本台词、旁白、音效表", "剪映 / TTS / 音效库", "voice.wav、preview.srt、音效轨", "关画面也能听懂故事", "音乐盖人声、字幕过长、音效乱"),
    Stage("09", "本地合成", "AI 视频、静帧动效、字幕音频", "FFmpeg / 剪映", "exports/*.mp4", "时长、字幕、音画同步通过", "丢镜头、黑帧、错序、导出参数错"),
    Stage("10", "平台导出", "横版母版", "剪映 / PR / 达芬奇", "B站横版、抖音竖版、红果竖版", "安全区、封面、标题、结尾钩子通过", "裁掉关键道具、前3秒无钩子"),
    Stage("11", "验收审核", "成片和清单", "人工 QC / Codex 清单", "08_成片检查/*.md", "故事、角色、道具、平台规范全过", "辫子数量错、称呼错、付费秒数超预算"),
    Stage("12", "返工闭环", "审核问题表", "按问题归类回到对应阶段", "返工记录、最终版", "每个问题有负责人、工具和完成状态", "只记录问题不闭环"),
]


def count_files(root: Path, pattern: str) -> int:
    return len(list(root.glob(pattern))) if root.exists() else 0


def infer_project(root: Path) -> dict:
    return {
        "name": root.name,
        "scripts": count_files(root, "05_剧本/*.md"),
        "storyboards": count_files(root, "06_分镜表/*.md"),
        "prompts": count_files(root, "07_绘图提示词/*.md"),
        "sop": count_files(root, "01_生产SOP/*.md") + count_files(root, "01_生产SOP/*.html"),
    }


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def stage_cards(stages: list[Stage]) -> str:
    cards = []
    for st in stages:
        cards.append(f"""
        <article class="stage">
          <div class="num">{esc(st.no)}</div>
          <h3>{esc(st.title)}</h3>
          <dl>
            <dt>输入</dt><dd>{esc(st.input_)}</dd>
            <dt>平台/工具</dt><dd>{esc(st.tool)}</dd>
            <dt>输出</dt><dd>{esc(st.output)}</dd>
            <dt>确认</dt><dd>{esc(st.confirm)}</dd>
            <dt>失败</dt><dd>{esc(st.fail)}</dd>
          </dl>
        </article>""")
    return "\n".join(cards)


def render_html(project: dict, stages: list[Stage], title: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{--bg:#0d1110;--panel:#17201d;--panel2:#1e2a26;--line:#33453f;--text:#edf4ef;--muted:#a8b5af;--jade:#7fb69b;--gold:#d1ad62;--cyan:#7fb3c1;--red:#c97362;}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(180deg,#0d1110,#121816);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.55}}
.wrap{{max-width:1380px;margin:auto;padding:34px 28px 58px}}
.hero,.card,.stage{{background:linear-gradient(180deg,rgba(30,42,38,.96),rgba(17,24,22,.96));border:1px solid var(--line);border-radius:10px;box-shadow:0 18px 45px rgba(0,0,0,.32)}}
.hero{{padding:28px;margin-bottom:22px}}.eyebrow{{color:var(--jade);font-size:13px;margin:0 0 8px}}h1{{margin:0;font-size:34px;line-height:1.15}}.hero p{{color:var(--muted);max-width:900px}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 0}}.metric{{padding:13px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);border-radius:8px}}.metric b{{display:block;color:var(--gold);font-size:22px}}.metric span{{color:var(--muted);font-size:12px}}
h2{{font-size:21px;margin:30px 0 14px}}.flow{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.stage{{padding:15px;position:relative;min-height:245px}}.stage:before{{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:var(--jade)}}.stage .num{{display:inline-flex;background:var(--gold);color:#101410;border-radius:999px;padding:2px 9px;font-weight:700;font-size:12px}}h3{{margin:10px 0 12px;font-size:16px}}dl{{margin:0}}dt{{float:left;clear:left;width:68px;color:var(--jade);font-size:12px;font-weight:700}}dd{{margin:0 0 8px 76px;color:var(--muted);font-size:12px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.card{{padding:18px}}.card h3{{margin-top:0}}.card li,.card p{{color:var(--muted);font-size:13px}}code{{color:var(--jade);background:rgba(127,182,155,.08);border:1px solid rgba(127,182,155,.16);border-radius:6px;padding:2px 6px}}table{{width:100%;border-collapse:collapse;border:1px solid var(--line);border-radius:10px;overflow:hidden}}th,td{{padding:12px;border-bottom:1px solid rgba(255,255,255,.07);font-size:13px;text-align:left}}th{{background:rgba(255,255,255,.05)}}td{{color:var(--muted)}}.footer{{margin-top:28px;color:var(--muted);font-size:12px;text-align:center}}
@media(max-width:1100px){{.flow{{grid-template-columns:repeat(2,1fr)}}.grid,.metrics{{grid-template-columns:1fr 1fr}}}}@media(max-width:680px){{.wrap{{padding:20px 14px 38px}}.flow,.grid,.metrics{{grid-template-columns:1fr}}h1{{font-size:27px}}}}
</style>
</head>
<body><div class="wrap">
<section class="hero">
<p class="eyebrow">皮玺玉风格 · 漫剧生产工作流</p>
<h1>{esc(title)}</h1>
<p>从剧本导入开始，到分镜、出图、图生视频、FFmpeg/剪映合成、平台导出、验收审核和返工闭环。看板用于明确每一步用什么平台、怎么确认、什么情况必须返工。</p>
<div class="metrics">
<div class="metric"><b>{esc(project["name"])}</b><span>项目</span></div>
<div class="metric"><b>{project["scripts"]}</b><span>剧本文件</span></div>
<div class="metric"><b>{project["storyboards"]}</b><span>分镜文件</span></div>
<div class="metric"><b>{project["prompts"]}</b><span>提示词文件</span></div>
</div>
</section>

<h2>端到端流程</h2>
<section class="flow">{stage_cards(stages)}</section>

<h2>平台选择</h2>
<section class="grid">
<article class="card"><h3>免费/低成本优先</h3><ul><li>MJ/Image2：角色定版、道具、封面。</li><li>即梦：中文旧村、堂屋、竹林、坟地静帧。</li><li>可灵：先跑图生视频草稿。</li></ul></article>
<article class="card"><h3>付费兜底</h3><ul><li>Seedance 2 只补最高价值动态镜头。</li><li>先 720p 草稿，验收通过再升质量。</li><li>统计付费秒数和重跑次数。</li></ul></article>
<article class="card"><h3>本地合成</h3><ul><li>FFmpeg 做静帧动效和自动粗剪。</li><li>剪映做字幕、音效、最终节奏。</li><li>先出横版母版，再裁竖版。</li></ul></article>
</section>

<h2>验收自检</h2>
<table><thead><tr><th>检查项</th><th>通过标准</th><th>失败处理</th></tr></thead><tbody>
<tr><td>剧本</td><td>人物称呼、集数、平台口径一致</td><td>回到剧本导入阶段修正</td></tr>
<tr><td>分镜</td><td>每镜有画面、时长、字幕/台词、音效</td><td>重拆不可画镜头</td></tr>
<tr><td>静帧</td><td>角色脸、服装、年代、道具数量稳定</td><td>回到角色/道具定版</td></tr>
<tr><td>视频</td><td>不换脸、不多手、不乱道具、不变风格</td><td>换平台或降级为静帧动效</td></tr>
<tr><td>合成</td><td>音画同步，字幕不遮脸，前3秒有钩子</td><td>剪辑返工</td></tr>
<tr><td>导出</td><td>B站横版清晰，竖版不裁掉关键道具</td><td>重新构图或重裁</td></tr>
</tbody></table>

<h2>常用命令</h2>
<section class="card">
<p>生成看板：</p>
<p><code>python C:\\Users\\Administrator\\.codex\\skills\\manju-workflow-dashboard\\scripts\\generate_dashboard.py --project-root "{esc(project["name"])}"</code></p>
<p>FFmpeg 预告粗剪通常在项目素材包里运行，先放好 <code>shot_01.png</code> 到 <code>shot_24.png</code>。</p>
</section>

<div class="footer">Generated by manju-workflow-dashboard · 皮玺玉风格 · Offline HTML</div>
</div></body></html>"""


def write_opener(output: Path) -> None:
    opener = output.with_name("open_workflow_dashboard.bat")
    opener.write_text('@echo off\nset "DIR=%~dp0"\nstart "" "%DIR%workflow_dashboard.html"\n', encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", default=None)
    parser.add_argument("--stages-json", type=Path, help="Optional JSON list of stage objects")
    args = parser.parse_args()

    root = args.project_root.resolve()
    output = args.output or (root / "01_生产SOP" / "workflow_dashboard.html")
    output.parent.mkdir(parents=True, exist_ok=True)
    stages = DEFAULT_STAGES
    if args.stages_json:
        data = json.loads(args.stages_json.read_text(encoding="utf-8"))
        stages = [Stage(**item) for item in data]
    title = args.title or f"{root.name} 漫剧生产工作流看板"
    html_text = render_html(infer_project(root), stages, title)
    output.write_text(html_text, encoding="utf-8")
    write_opener(output)
    print(f"dashboard: {output}")


if __name__ == "__main__":
    main()
