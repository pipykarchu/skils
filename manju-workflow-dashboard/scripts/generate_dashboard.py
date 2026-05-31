#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an offline ComfyUI-style workflow dashboard for AI manju production."""

from __future__ import annotations

import argparse
import csv
import html
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Node:
    id: str
    x: int
    y: int
    w: int
    h: int
    kind: str
    title: str
    body: str
    meta: str


@dataclass(frozen=True)
class Edge:
    source: str
    target: str


NODES = [
    Node("script", 30, 80, 210, 116, "input", "剧本导入", "05_剧本、原始纪要、PRD", "确认集数/主线/称呼"),
    Node("storyboard", 310, 55, 220, 122, "process", "分镜拆解", "06_分镜表、镜头时长、台词", "每镜可画可剪"),
    Node("character", 310, 215, 220, 122, "process", "角色/道具定版", "角色母版、娃娃、姜、年代服装", "脸/服装/道具稳定"),
    Node("hub", 610, 120, 245, 150, "hub", "AI 视觉生产中枢", "把镜头分成静帧、图生视频、付费兜底三类", "成本优先，质量兜底"),
    Node("image", 935, 35, 230, 120, "tool", "MJ / Image2 / 即梦", "横版关键静帧、封面、角色定版", "先静帧过审"),
    Node("video", 935, 195, 230, 120, "tool", "可灵 / 即梦视频", "S/A镜头图生视频测试", "先跑低成本草稿"),
    Node("seedance", 935, 355, 230, 120, "paid", "Seedance 2 兜底", "只补最高价值失败镜头", "记录付费秒数"),
    Node("style", 610, 340, 245, 118, "style", "皮玺玉光影", "暗玉、墨黑、冷金、雾霭、胶片质感", "统一视觉风格"),
    Node("tasks", 1235, 115, 230, 126, "output", "提示词任务清单", "image/video task manifests", "批量生产可追踪"),
    Node("ffmpeg", 1235, 310, 230, 124, "process", "FFmpeg 静帧动效", "慢推、横移、切黑、粗剪", "不用付费先成片"),
    Node("edit", 1530, 210, 230, 132, "process", "剪映 / CapCut 合成", "字幕、旁白、音效、节奏", "音画同步"),
    Node("bili", 1815, 105, 210, 118, "export", "B站横版", "1920x1080 主母版", "封面/前三秒钩子"),
    Node("vertical", 1815, 285, 210, 118, "export", "抖音 / 红果竖版", "9:16裁切与安全区检查", "不裁掉关键道具"),
]

EDGES = [
    Edge("script", "storyboard"),
    Edge("script", "character"),
    Edge("storyboard", "hub"),
    Edge("character", "hub"),
    Edge("hub", "image"),
    Edge("hub", "video"),
    Edge("hub", "seedance"),
    Edge("style", "image"),
    Edge("style", "video"),
    Edge("image", "tasks"),
    Edge("video", "tasks"),
    Edge("seedance", "tasks"),
    Edge("tasks", "ffmpeg"),
    Edge("ffmpeg", "edit"),
    Edge("edit", "bili"),
    Edge("edit", "vertical"),
]

PLATFORM_ROWS = [
    ("剧本/PRD", "Codex + 本地文档", "标题、集数、主角称呼、现实线/故事线是否一致", "PRD与分集剧本"),
    ("角色/道具定版", "MJ / Image2 / 即梦", "脸、年龄、服装、娃娃五根辫子、姜盒是否稳定", "角色母版、道具母版"),
    ("横版静帧", "Image2 / MJ / 即梦", "16:9构图可裁竖版，人物和道具无遮挡", "shot_XX.png"),
    ("图生视频", "可灵 / 即梦视频", "不换脸、不多手、不乱道具，动作读得清", "videos_ai/shot_XX.mp4"),
    ("付费兜底", "Seedance 2", "只用于S级失败镜头，先低清测试再升质量", "付费镜头记录"),
    ("本地成片", "FFmpeg + 剪映/CapCut", "字幕、音效、旁白、节奏、横竖版安全区", "B站横版/竖版导出"),
]

QA_ROWS = [
    ("故事", "现实线、故事线、结尾扫墓逻辑能闭环", "回到PRD/剧本修正"),
    ("人物称呼", "姜苗、姜生、阿妮、小妮儿、姥姥姥爷称呼统一", "统一台词和字幕"),
    ("道具连续性", "娃娃辫子数量、红布姜、密码盒、火堆等关键道具不乱", "回到静帧或图生视频返工"),
    ("平台成本", "先静帧粗剪，免费/低成本动态图过审后再花钱", "降低镜头等级或改静帧动效"),
    ("画面安全区", "横版主母版可裁竖版，字幕不遮脸不遮关键道具", "重排字幕或重构图"),
    ("发布前检查", "前三秒有钩子，封面明确，音画同步，字幕无错字", "剪映/FFmpeg返工"),
]

DEMO_STEPS = [
    ("1", "先讲项目", "《娃娃仙》是民俗恐怖志怪漫剧，现实线由阿妮给姜苗、姜生讲故事，故事线回到小妮儿被娃娃仙护主。"),
    ("2", "再讲链路", "从剧本导入开始，拆分镜、定角色道具、出静帧、跑图生视频、本地合成、横版发布、竖版裁切。"),
    ("3", "突出成本", "静帧和FFmpeg先把片子跑通，可灵/即梦做动态测试，Seedance只给S级失败镜头兜底。"),
    ("4", "展示审核", "每个节点都有输入、输出、确认点和失败条件，面试时说明这是可复用的生产管线。"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def count_files(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return len(list(root.glob(pattern)))


def find_preview_csv(root: Path) -> Path | None:
    candidates = [
        root / "09_素材与参考" / "预告剪辑版" / "manifests" / "preview_shots.csv",
        root / "09_素材与参考" / "预告剪辑版" / "preview_shots.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(root.glob("**/preview_shots.csv"))
    return matches[0] if matches else None


def read_preview_stats(root: Path) -> dict[str, object]:
    csv_path = find_preview_csv(root)
    stats: dict[str, object] = {"shots": "待确认", "duration": "按项目文件", "dynamic": "按镜头分级"}
    if not csv_path:
        return stats

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except OSError:
        return stats

    if rows:
        stats["shots"] = f"{len(rows)}镜"
        total = 0.0
        for row in rows:
            try:
                total += float(row.get("duration", "") or 0)
            except ValueError:
                pass
        if total:
            stats["duration"] = f"{int(round(total))}秒"
        dynamic = 0
        for row in rows:
            text = " ".join(str(row.get(k, "")) for k in ("motion", "platform", "priority"))
            if row.get("priority", "").strip().upper() in {"S", "A"} or re.search("可灵|Seedance|图生视频|视频", text):
                dynamic += 1
        if dynamic:
            stats["dynamic"] = f"{dynamic}条动态镜头"
    return stats


def infer_project(root: Path) -> dict[str, object]:
    scripts = count_files(root / "05_剧本", "*.md")
    storyboards = count_files(root / "06_分镜表", "*.md")
    prompts = count_files(root / "07_绘图提示词", "*.md")
    sop = count_files(root / "01_生产SOP", "*.md") + count_files(root / "01_生产SOP", "*.html")
    preview = read_preview_stats(root)
    episode_value = f"{scripts}集" if scripts else "待确认"

    return {
        "name": root.name,
        "root": str(root),
        "episodes": episode_value,
        "duration": preview["duration"],
        "shots": preview["shots"],
        "dynamic": preview["dynamic"],
        "scripts": scripts,
        "storyboards": storyboards,
        "prompts": prompts,
        "sop": sop,
    }


def render_edges() -> str:
    by_id = {node.id: node for node in NODES}
    parts = []
    for edge in EDGES:
        src = by_id[edge.source]
        dst = by_id[edge.target]
        x1 = src.x + src.w
        y1 = src.y + src.h // 2
        x2 = dst.x
        y2 = dst.y + dst.h // 2
        mid = x1 + max(55, (x2 - x1) // 2)
        parts.append(
            f'<path d="M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}" '
            'fill="none" stroke="rgba(136,185,162,.62)" stroke-width="2.2" marker-end="url(#arrow)"/>'
        )
    return "\n".join(parts)


def render_nodes() -> str:
    parts = []
    for node in NODES:
        parts.append(
            f"""
        <article class="node {esc(node.kind)}" style="left:{node.x}px;top:{node.y}px;width:{node.w}px;height:{node.h}px">
          <div class="node-head"><span class="port"></span><strong>{esc(node.title)}</strong><span class="port out"></span></div>
          <p>{esc(node.body)}</p>
          <small>{esc(node.meta)}</small>
        </article>"""
        )
    return "\n".join(parts)


def render_platform_rows() -> str:
    return "\n".join(
        f"<tr><td>{esc(stage)}</td><td>{esc(tool)}</td><td>{esc(check)}</td><td>{esc(output)}</td></tr>"
        for stage, tool, check, output in PLATFORM_ROWS
    )


def render_qa_rows() -> str:
    return "\n".join(
        f"<tr><td>{esc(item)}</td><td>{esc(pass_rule)}</td><td>{esc(fix)}</td></tr>"
        for item, pass_rule, fix in QA_ROWS
    )


def render_demo_steps() -> str:
    return "\n".join(
        f"""
        <article class="step">
          <b>{esc(no)}</b>
          <div><h3>{esc(title)}</h3><p>{esc(body)}</p></div>
        </article>"""
        for no, title, body in DEMO_STEPS
    )


def render_detail_script() -> str:
    return """<script>
    const flowDetails = {
      teaser: {
        title: "横版预告分镜",
        summary: "不是直接做正片，而是先用完整故事资产核算成本，拆出最适合面试和平台测试的剪辑先行版。",
        steps: [
          "导入故事、纪要和PRD，确认主线、人物称呼和结尾逻辑。",
          "生成分集剧本，保证完整故事能连续讲完。",
          "把分集剧本转成分镜脚本，确认每集可画、可剪、可生产。",
          "核算付费视频成本，判断是否先做全片。",
          "改为剪辑先行版：重新生成预告剪辑剧本和预告分镜。"
        ],
        outputs: ["分集剧本", "分集分镜", "预告剪辑剧本", "预告分镜"]
      },
      stills: {
        title: "横版静帧",
        summary: "先把视频生产变成可控的图片资产，解决人物、场景、道具和构图统一问题。",
        steps: [
          "按预告分镜提取每镜画面主体、景别、动作和字幕重点。",
          "统一项目视觉风格和年代限制。",
          "用MJ/Image2/即梦生成16:9横版静帧。",
          "检查角色、服装、场景、道具是否一致。",
          "能用静帧讲清楚故事后，再决定哪些镜头值得动态化。"
        ],
        outputs: ["shot_XX.png", "角色母版", "道具母版"]
      },
      grade: {
        title: "镜头分级",
        summary: "核心是省钱：不是所有镜头都跑图生视频，而是按价值分配平台和预算。",
        steps: [
          "S级：剧情爆点或记忆点，优先动态图。",
          "A级：有动态会加分，但静帧动效也能讲清楚。",
          "B/C级：信息交代、环境、道具、字卡，默认静帧动效。",
          "低成本平台失败后，才进入Seedance兜底。",
          "记录平台、失败原因、是否值得继续花钱。"
        ],
        outputs: ["S/A/B/C镜头表", "兜底清单", "返工优先级"]
      },
      video: {
        title: "可灵 / 即梦图生视频",
        summary: "低成本优先处理S/A级镜头，先验证动作成立，再决定是否升质量。",
        steps: [
          "用已审核通过的静帧作为首帧或参考图。",
          "提示词只写关键动作，减少模型自由发挥。",
          "先跑低清或免费额度版本。",
          "检查不换脸、不多手、道具不乱、动作可读。",
          "通过后进入粗剪，不通过则降级或转Seedance。"
        ],
        outputs: ["动态图草稿", "可用动态图", "失败原因记录"]
      },
      seedance: {
        title: "Seedance 2 兜底",
        summary: "付费平台只服务最值得花钱的失败镜头，避免预算失控。",
        steps: [
          "只接收低成本平台失败、但剧情价值很高的镜头。",
          "先跑短时长低成本测试。",
          "确认动作、脸、道具和氛围后再升质量。",
          "普通镜头不进入Seedance。",
          "每次重跑记录成本、失败点和最终是否采用。"
        ],
        outputs: ["S级兜底视频", "付费秒数记录", "重跑记录"]
      },
      static: {
        title: "剪映 / FFmpeg静帧动效",
        summary: "B/C级镜头不用烧钱，用推拉摇移、切黑、字幕和音效形成运动感。",
        steps: [
          "把静帧按镜头顺序放入素材目录。",
          "FFmpeg自动生成慢推、横移、轻缩放等基础动效。",
          "剪映补字幕、音效、环境声、黑场和节奏点。",
          "恐怖镜头用短促切换和音效制造惊悚。",
          "静帧停留太久就缩短时长或加转场。"
        ],
        outputs: ["videos_static", "粗剪素材", "字幕音效节奏点"]
      },
      edit: {
        title: "粗剪合成",
        summary: "把三路素材统一成一个可看的横版母版，先验证故事是否成立。",
        steps: [
          "合并图生视频、静帧动效、字卡、字幕、旁白和音效。",
          "检查前3秒钩子、中段信息、结尾情绪落点。",
          "关掉画面只听声音，确认故事仍然听得懂。",
          "关掉声音只看画面，确认关键道具看得清。",
          "发现问题回到对应节点，不整条链路重做。"
        ],
        outputs: ["横版粗剪", "问题清单", "返工节点"]
      },
      bili: {
        title: "平台横版预告",
        summary: "横版是主母版，负责完整情绪、画面质感和面试展示效果。",
        steps: [
          "导出16:9横版母版。",
          "检查封面、标题、前三秒钩子和结尾记忆点。",
          "确保字幕不遮脸、不遮关键道具。",
          "保留题材氛围，同时保证故事能看懂。",
          "横版通过后再进入竖版裁切。"
        ],
        outputs: ["横版MP4", "封面", "标题文案"]
      },
      vertical: {
        title: "裁竖版",
        summary: "竖版不是重新做一遍，而是从横版母版裁切，并检查安全区。",
        steps: [
          "从横版母版裁9:16，优先保人物脸和关键道具。",
          "必要时重排字幕位置。",
          "把节奏压得更短，强化开头钩子。",
          "检查竖版平台安全区和封面可读性。",
          "导出竖版后与横版一起归档。"
        ],
        outputs: ["竖版MP4", "安全区检查", "平台发布包"]
      }
    };

    function renderFlowDetail(key) {
      const detail = flowDetails[key] || flowDetails.teaser;
      document.getElementById("detailTitle").textContent = detail.title;
      document.getElementById("detailSummary").textContent = detail.summary;
      document.getElementById("detailSteps").innerHTML = detail.steps.map(function(step) {
        return "<li>" + step + "</li>";
      }).join("");
      document.getElementById("detailOutputs").innerHTML = detail.outputs.map(function(item) {
        return "<span>" + item + "</span>";
      }).join("");
    }

    document.querySelectorAll(".flow-hit").forEach(function(hit) {
      hit.addEventListener("click", function() { renderFlowDetail(hit.dataset.detail); });
      hit.addEventListener("keydown", function(event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          renderFlowDetail(hit.dataset.detail);
        }
      });
    });

    renderFlowDetail("teaser");
  </script>"""


def render_file_entry(project: dict[str, object]) -> str:
    root = Path(str(project["root"]))
    entries = [
        ("PRD/SOP", root / "00_PRD"),
        ("剧本", root / "05_剧本"),
        ("分镜表", root / "06_分镜表"),
        ("绘图提示词", root / "07_绘图提示词"),
        ("预告素材包", root / "09_素材与参考" / "预告剪辑版"),
        ("自动化脚本", root / "10_自动化脚本"),
    ]
    return "\n".join(
        f'<li><span>{esc(label)}</span><code>{esc(path)}</code></li>' for label, path in entries
    )


def render_html(project: dict[str, object], title: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{
      --bg:#090f0d; --panel:#13201d; --panel2:#1b2a25; --line:#314b42;
      --text:#eef6f1; --muted:#9fb3ab; --jade:#84c7a7; --gold:#d4ad5f;
      --cyan:#7ab8c5; --red:#d27b67; --purple:#a78bd8; --shadow:rgba(0,0,0,.38);
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; color:var(--text); font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;
      background:
        radial-gradient(circle at 18% 8%, rgba(132,199,167,.11), transparent 32%),
        linear-gradient(180deg,#08100e 0%,#0f1714 45%,#090d0c 100%);
      line-height:1.55;
    }}
    .wrap {{ max-width:1480px; margin:0 auto; padding:28px 24px 48px; }}
    .hero {{
      display:grid; grid-template-columns:1.3fr .9fr; gap:18px; align-items:stretch;
      border:1px solid rgba(132,199,167,.22); border-radius:14px;
      background:linear-gradient(135deg,rgba(24,42,37,.96),rgba(11,18,16,.96));
      box-shadow:0 24px 70px var(--shadow); overflow:hidden;
    }}
    .hero-main {{ padding:26px 28px; }}
    .eyebrow {{ margin:0 0 8px; color:var(--jade); font-size:13px; letter-spacing:0; }}
    h1 {{ margin:0; font-size:34px; line-height:1.16; letter-spacing:0; }}
    .hero-main p:last-child {{ max-width:820px; color:var(--muted); margin-bottom:0; }}
    .meta-card {{
      padding:20px; border-left:1px solid rgba(255,255,255,.08);
      background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.015));
    }}
    .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .metric {{
      min-height:76px; padding:12px; border:1px solid rgba(255,255,255,.08);
      background:rgba(255,255,255,.04); border-radius:9px;
    }}
    .metric b {{ display:block; color:var(--gold); font-size:22px; line-height:1.1; }}
    .metric span {{ display:block; color:var(--muted); font-size:12px; margin-top:7px; }}
    h2 {{ margin:28px 0 12px; font-size:21px; letter-spacing:0; }}
    .caption {{ margin:0 0 14px; color:var(--muted); font-size:13px; }}
    .simple-flow {{
      padding:18px; border:1px solid rgba(132,199,167,.34); border-radius:14px;
      background:rgba(7,10,9,.46); box-shadow:inset 0 0 0 1px rgba(255,255,255,.025), 0 16px 40px rgba(0,0,0,.28);
    }}
    .flow-row {{ display:flex; align-items:stretch; gap:10px; }}
    .flow-row + .flow-row {{ margin-top:12px; }}
    .flow-node {{
      flex:1; min-height:78px; padding:13px 14px; border:1px solid rgba(255,255,255,.08);
      border-left:5px solid var(--accent,var(--jade)); border-radius:10px;
      background:linear-gradient(180deg,rgba(27,37,33,.98),rgba(16,22,20,.98));
      display:flex; flex-direction:column; justify-content:center;
    }}
    .flow-node strong {{ display:block; font-size:16px; line-height:1.25; }}
    .flow-node span {{ display:block; margin-top:5px; color:var(--muted); font-size:12px; }}
    .flow-node.decision {{
      border-color:rgba(212,173,95,.36); border-left-color:var(--gold);
      background:linear-gradient(180deg,rgba(45,39,25,.96),rgba(18,21,18,.96));
    }}
    .flow-arrow {{
      width:34px; min-width:34px; display:grid; place-items:center;
      color:var(--gold); font-size:26px; font-weight:800;
    }}
    .branch-row {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:12px; }}
    .branch-card {{
      padding:14px; border:1px solid rgba(255,255,255,.08); border-top:4px solid var(--accent,var(--jade));
      border-radius:10px; background:rgba(255,255,255,.035);
    }}
    .branch-card b {{
      display:inline-flex; margin-bottom:8px; padding:2px 8px; border-radius:999px;
      background:var(--accent,var(--jade)); color:#08100d; font-size:12px;
    }}
    .branch-card strong {{ display:block; font-size:15px; }}
    .branch-card span {{ display:block; margin-top:5px; color:var(--muted); font-size:12px; }}
    .merge-note {{ margin:12px 0; color:var(--gold); text-align:center; font-size:13px; font-weight:700; }}
    .flowchart-panel {{
      padding:18px; background:rgba(7,10,9,.5); border:1px solid rgba(132,199,167,.34);
      border-radius:14px; overflow:auto; box-shadow:inset 0 0 0 1px rgba(255,255,255,.025), 0 16px 40px rgba(0,0,0,.28);
    }}
    .flowchart-svg {{ display:block; min-width:1180px; width:100%; height:auto; }}
    .flow-hit {{ fill:transparent; cursor:pointer; pointer-events:all; }}
    .flow-hit:focus {{ outline:none; }}
    .flow-box {{ fill:#17231f; stroke:rgba(132,199,167,.72); stroke-width:2; rx:12; }}
    .flow-box.start {{ stroke:rgba(212,173,95,.85); fill:#211e14; }}
    .flow-box.video {{ stroke:rgba(132,199,167,.82); fill:#14231d; }}
    .flow-box.paid {{ stroke:rgba(210,123,103,.9); fill:#261815; }}
    .flow-box.local {{ stroke:rgba(167,139,216,.88); fill:#1d1a28; }}
    .flow-box.export {{ stroke:rgba(122,184,197,.9); fill:#142127; }}
    .flow-diamond {{ fill:#2d2719; stroke:rgba(212,173,95,.92); stroke-width:2; }}
    .flow-line {{
      fill:none; stroke:rgba(212,173,95,.78); stroke-width:3; stroke-linecap:round;
      stroke-linejoin:round; marker-end:url(#flowArrow);
    }}
    .flow-line.branch {{ stroke:rgba(132,199,167,.7); }}
    .flow-line.fail {{ stroke:rgba(210,123,103,.78); }}
    .flow-line.local {{ stroke:rgba(167,139,216,.78); }}
    .flow-text {{ fill:var(--text); font-size:18px; font-weight:760; text-anchor:middle; dominant-baseline:middle; }}
    .flow-small {{ fill:var(--muted); font-size:13px; text-anchor:middle; dominant-baseline:middle; }}
    .flow-label {{ fill:#111611; font-size:13px; font-weight:800; text-anchor:middle; dominant-baseline:middle; }}
    .label-pill {{ fill:var(--gold); rx:12; }}
    details.detail-graph {{
      display:none; margin-top:18px; border:1px solid var(--line); border-radius:12px;
      background:rgba(7,10,9,.35); overflow:hidden;
    }}
    details.detail-graph > summary {{
      cursor:pointer; padding:14px 16px; color:var(--gold); font-weight:780; list-style:none;
    }}
    details.detail-graph > summary::-webkit-details-marker {{ display:none; }}
    details.detail-graph > summary::after {{
      content:"展开"; float:right; color:var(--muted); font-size:12px; font-weight:400;
    }}
    details.detail-graph[open] > summary::after {{ content:"收起"; }}
    .node-detail {{
      margin-top:14px; display:grid; grid-template-columns:280px 1fr; gap:14px;
      border:1px solid rgba(132,199,167,.28); border-radius:12px;
      background:linear-gradient(180deg,rgba(27,37,33,.96),rgba(16,22,20,.96));
      box-shadow:0 16px 40px rgba(0,0,0,.28); overflow:hidden;
    }}
    .detail-aside {{ padding:16px; border-right:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.03); }}
    .detail-aside b {{ display:block; color:var(--gold); font-size:15px; margin-bottom:8px; }}
    .detail-aside p {{ margin:0; color:var(--muted); font-size:12px; }}
    .detail-body {{ padding:16px; }}
    .detail-body h3 {{ margin:0 0 8px; font-size:18px; }}
    .detail-body p {{ margin:0 0 12px; color:var(--muted); font-size:13px; }}
    .detail-body ol {{ margin:0; padding-left:22px; color:var(--text); }}
    .detail-body li {{ margin:0 0 7px; font-size:13px; }}
    .detail-output {{ margin-top:12px; display:flex; flex-wrap:wrap; gap:8px; }}
    .detail-output span {{
      padding:4px 8px; border-radius:999px; background:rgba(132,199,167,.12);
      border:1px solid rgba(132,199,167,.22); color:var(--jade); font-size:12px;
    }}
    .board {{
      position:relative; height:548px; overflow:auto; border-radius:14px;
      border:1px solid rgba(132,199,167,.2);
      background:
        linear-gradient(rgba(255,255,255,.028) 1px, transparent 1px),
        linear-gradient(90deg,rgba(255,255,255,.028) 1px, transparent 1px),
        #0c1311;
      background-size:24px 24px;
      box-shadow:inset 0 0 0 1px rgba(0,0,0,.25), 0 18px 54px var(--shadow);
    }}
    .canvas {{ position:relative; width:2070px; height:525px; }}
    .links {{ position:absolute; inset:0; width:2070px; height:525px; pointer-events:none; }}
    .node {{
      position:absolute; border:1px solid rgba(132,199,167,.28); border-radius:10px;
      background:linear-gradient(180deg,rgba(27,42,37,.97),rgba(13,19,17,.97));
      box-shadow:0 12px 30px rgba(0,0,0,.34); overflow:hidden;
    }}
    .node-head {{
      display:flex; align-items:center; justify-content:space-between; gap:8px;
      padding:9px 10px; min-height:38px; border-bottom:1px solid rgba(255,255,255,.08);
      background:rgba(132,199,167,.08);
    }}
    .node strong {{ font-size:14px; color:var(--text); }}
    .node p {{ margin:10px 12px 4px; color:var(--muted); font-size:12px; }}
    .node small {{ display:block; margin:0 12px; color:var(--gold); font-size:11px; }}
    .port {{ width:9px; height:9px; border-radius:50%; background:var(--jade); box-shadow:0 0 10px rgba(132,199,167,.8); flex:0 0 auto; }}
    .out {{ background:var(--gold); box-shadow:0 0 10px rgba(212,173,95,.8); }}
    .input .node-head {{ background:rgba(122,184,197,.12); }}
    .tool .node-head {{ background:rgba(132,199,167,.12); }}
    .paid .node-head {{ background:rgba(210,123,103,.14); }}
    .style .node-head {{ background:rgba(167,139,216,.14); }}
    .export .node-head {{ background:rgba(212,173,95,.14); }}
    .hub {{ border-color:rgba(212,173,95,.52); }}
    .hub .node-head {{ background:rgba(212,173,95,.16); }}
    .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .panel {{
      border:1px solid rgba(132,199,167,.2); border-radius:12px;
      background:linear-gradient(180deg,rgba(25,39,35,.94),rgba(13,19,17,.94));
      box-shadow:0 16px 42px var(--shadow);
    }}
    .panel-inner {{ padding:18px; }}
    .steps {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
    .step {{
      display:flex; gap:12px; padding:14px; border:1px solid rgba(255,255,255,.08);
      border-radius:10px; background:rgba(255,255,255,.035);
    }}
    .step b {{
      display:grid; place-items:center; width:30px; height:30px; border-radius:50%;
      background:var(--gold); color:#111611; flex:0 0 auto;
    }}
    .step h3 {{ margin:0 0 5px; font-size:14px; }}
    .step p {{ margin:0; color:var(--muted); font-size:12px; }}
    table {{ width:100%; border-collapse:collapse; overflow:hidden; border-radius:12px; }}
    th,td {{ padding:12px 13px; border-bottom:1px solid rgba(255,255,255,.08); text-align:left; vertical-align:top; font-size:13px; }}
    th {{ color:var(--jade); background:rgba(255,255,255,.04); }}
    td {{ color:var(--muted); }}
    .file-list {{ list-style:none; padding:0; margin:0; display:grid; gap:9px; }}
    .file-list li {{ display:grid; grid-template-columns:110px 1fr; gap:10px; align-items:start; }}
    .file-list span {{ color:var(--jade); font-size:13px; }}
    code {{
      display:block; color:#c7e5d6; white-space:normal; overflow-wrap:anywhere;
      background:rgba(132,199,167,.075); border:1px solid rgba(132,199,167,.14);
      border-radius:7px; padding:7px 8px; font-family:Consolas,"Microsoft YaHei",monospace; font-size:12px;
    }}
    .footer {{ margin-top:22px; text-align:center; color:var(--muted); font-size:12px; }}
    @media (max-width: 980px) {{
      .hero,.grid,.steps {{ grid-template-columns:1fr; }}
      .flow-row {{ flex-direction:column; }}
      .flow-arrow {{ width:100%; min-width:0; min-height:24px; transform:rotate(90deg); }}
      .branch-row {{ grid-template-columns:1fr; }}
      .node-detail {{ grid-template-columns:1fr; }}
      .detail-aside {{ border-right:0; border-bottom:1px solid rgba(255,255,255,.08); }}
      .meta-card {{ border-left:0; border-top:1px solid rgba(255,255,255,.08); }}
      .wrap {{ padding:18px 12px 34px; }}
      h1 {{ font-size:27px; }}
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="hero-main">
        <p class="eyebrow">面试演示版 · ComfyUI式节点脑图 · 皮玺玉风格</p>
        <h1>{esc(title)}</h1>
        <p>这张看板用于现场演示：把一个民俗恐怖志怪漫剧项目，从剧本导入、分镜拆解、AI出图、图生视频、FFmpeg/剪映合成，到B站横版发布和竖版裁切，完整呈现为可讲解、可落地、可验收的节点化工作流。</p>
      </div>
      <aside class="meta-card">
        <div class="meta-grid">
          <div class="metric"><b>{esc(project["episodes"])}</b><span>分集规模</span></div>
          <div class="metric"><b>{esc(project["duration"])}</b><span>预告/成片时长</span></div>
          <div class="metric"><b>{esc(project["shots"])}</b><span>镜头任务</span></div>
          <div class="metric"><b>{esc(project["dynamic"])}</b><span>动态镜头策略</span></div>
        </div>
      </aside>
    </section>

    <h2>01 · 一眼看懂的主流程</h2>
    <p class="caption">面试先讲这条主线：预告怎么从分镜变成静帧，再按镜头等级走不同平台，最后合成横版并裁竖版。</p>
    <section class="flowchart-panel" aria-label="横版预告主流程图">
      <svg class="flowchart-svg" viewBox="0 0 1320 560" role="img" aria-label="横版预告到横竖版发布流程">
        <defs>
          <marker id="flowArrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">
            <path d="M0,0 L10,5 L0,10 Z" fill="rgba(212,173,95,.9)"></path>
          </marker>
        </defs>
        <rect class="flow-box start" x="20" y="220" width="150" height="82"></rect>
        <text class="flow-text" x="95" y="250">横版</text>
        <text class="flow-text" x="95" y="276">预告分镜</text>
        <path class="flow-line" d="M170 261 H235"></path>
        <rect class="flow-box" x="245" y="220" width="150" height="82"></rect>
        <text class="flow-text" x="320" y="250">横版</text>
        <text class="flow-text" x="320" y="276">静帧</text>
        <path class="flow-line" d="M395 261 H465"></path>
        <polygon class="flow-diamond" points="545,194 625,261 545,328 465,261"></polygon>
        <text class="flow-text" x="545" y="250">镜头</text>
        <text class="flow-text" x="545" y="276">分级</text>
        <path class="flow-line branch" d="M625 261 C675 261 670 92 730 92"></path>
        <rect class="label-pill" x="645" y="116" width="44" height="24"></rect>
        <text class="flow-label" x="667" y="128">S级</text>
        <rect class="flow-box video" x="730" y="52" width="170" height="82"></rect>
        <text class="flow-text" x="815" y="82">可灵 / 即梦</text>
        <text class="flow-text" x="815" y="108">图生视频</text>
        <path class="flow-line fail" d="M625 261 H730"></path>
        <rect class="label-pill" x="648" y="232" width="72" height="24"></rect>
        <text class="flow-label" x="684" y="244">失败兜底</text>
        <rect class="flow-box paid" x="730" y="220" width="170" height="82"></rect>
        <text class="flow-text" x="815" y="261">Seedance 2</text>
        <path class="flow-line local" d="M625 261 C675 261 670 430 730 430"></path>
        <rect class="label-pill" x="642" y="384" width="54" height="24"></rect>
        <text class="flow-label" x="669" y="396">B/C级</text>
        <rect class="flow-box local" x="730" y="390" width="170" height="82"></rect>
        <text class="flow-text" x="815" y="420">剪映 / FFmpeg</text>
        <text class="flow-text" x="815" y="446">静帧动效</text>
        <path class="flow-line branch" d="M900 93 C960 93 950 261 1000 261"></path>
        <path class="flow-line fail" d="M900 261 H1000"></path>
        <path class="flow-line local" d="M900 431 C960 431 950 261 1000 261"></path>
        <rect class="flow-box start" x="1000" y="220" width="130" height="82"></rect>
        <text class="flow-text" x="1065" y="250">粗剪</text>
        <text class="flow-text" x="1065" y="276">合成</text>
        <path class="flow-line" d="M1130 261 C1148 261 1148 211 1160 211"></path>
        <rect class="flow-box export" x="1160" y="170" width="140" height="82"></rect>
        <text class="flow-text" x="1230" y="200">横版预告</text>
        <text class="flow-text" x="1230" y="226">发布</text>
        <path class="flow-line" d="M1230 252 V320"></path>
        <rect class="flow-box export" x="1160" y="320" width="140" height="82"></rect>
        <text class="flow-text" x="1230" y="350">裁竖版</text>
        <text class="flow-text" x="1230" y="376">发布</text>
        <rect class="flow-hit" data-detail="teaser" x="20" y="220" width="150" height="82" tabindex="0"><title>查看预告分镜流程</title></rect>
        <rect class="flow-hit" data-detail="stills" x="245" y="220" width="150" height="82" tabindex="0"><title>查看横版静帧流程</title></rect>
        <polygon class="flow-hit" data-detail="grade" points="545,194 625,261 545,328 465,261" tabindex="0"><title>查看镜头分级流程</title></polygon>
        <rect class="flow-hit" data-detail="video" x="730" y="52" width="170" height="82" tabindex="0"><title>查看图生视频流程</title></rect>
        <rect class="flow-hit" data-detail="seedance" x="730" y="220" width="170" height="82" tabindex="0"><title>查看Seedance兜底流程</title></rect>
        <rect class="flow-hit" data-detail="static" x="730" y="390" width="170" height="82" tabindex="0"><title>查看静帧动效流程</title></rect>
        <rect class="flow-hit" data-detail="edit" x="1000" y="220" width="130" height="82" tabindex="0"><title>查看粗剪合成流程</title></rect>
        <rect class="flow-hit" data-detail="bili" x="1160" y="170" width="140" height="82" tabindex="0"><title>查看横版发布流程</title></rect>
        <rect class="flow-hit" data-detail="vertical" x="1160" y="320" width="140" height="82" tabindex="0"><title>查看竖版发布流程</title></rect>
      </svg>
    </section>

    <section class="node-detail" id="nodeDetail" aria-live="polite">
      <aside class="detail-aside">
        <b>点击流程图模块查看细节</b>
        <p>面试时先讲主流程，再按对方追问点击展开对应节点。默认展示第一个节点。</p>
      </aside>
      <div class="detail-body">
        <h3 id="detailTitle">横版预告分镜</h3>
        <p id="detailSummary">从完整故事资产里拆出最低成本的先行验证版本。</p>
        <ol id="detailSteps"></ol>
        <div class="detail-output" id="detailOutputs"></div>
      </div>
    </section>

    <details class="detail-graph">
      <summary>02 · 详细节点脑图</summary>
      <p class="caption" style="padding: 0 16px;">这部分用于展开细讲：每个节点有输入、工具、输出、确认点，呈现方式接近 ComfyUI 的生产节点。</p>
      <section class="board" aria-label="ComfyUI式工作流节点脑图">
      <div class="canvas">
        <svg class="links" viewBox="0 0 2070 525" preserveAspectRatio="none">
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M0,0 L8,4 L0,8 Z" fill="rgba(136,185,162,.72)"></path>
            </marker>
          </defs>
          {render_edges()}
        </svg>
        {render_nodes()}
      </div>
      </section>
    </details>

    <h2>03 · 面试讲解路径</h2>
    <section class="steps">{render_demo_steps()}</section>

    <div class="grid">
      <section>
        <h2>04 · 平台确认表</h2>
        <div class="panel"><div class="panel-inner">
          <table>
            <thead><tr><th>环节</th><th>平台/工具</th><th>确认方式</th><th>输出物</th></tr></thead>
            <tbody>{render_platform_rows()}</tbody>
          </table>
        </div></div>
      </section>
      <section>
        <h2>05 · 本地文件入口</h2>
        <div class="panel"><div class="panel-inner">
          <ul class="file-list">{render_file_entry(project)}</ul>
        </div></div>
      </section>
    </div>

    <h2>06 · 验收审核与自检</h2>
    <section class="panel"><div class="panel-inner">
      <table>
        <thead><tr><th>检查项</th><th>通过标准</th><th>失败处理</th></tr></thead>
        <tbody>{render_qa_rows()}</tbody>
      </table>
    </div></section>

    <div class="footer">{esc(project["name"])} 面试演示工作流看板 · ComfyUI式节点脑图 · 皮玺玉风格 · 本地离线 HTML</div>
  </main>
  {render_detail_script()}
</body>
</html>"""


def write_opener(output: Path) -> None:
    opener = output.with_name("open_workflow_dashboard.bat")
    opener.write_text(
        '@echo off\nset "DIR=%~dp0"\nstart "" "%DIR%workflow_dashboard.html"\n',
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an interview-ready manju workflow dashboard.")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    root = args.project_root.resolve()
    output = args.output or (root / "01_生产SOP" / "workflow_dashboard.html")
    output.parent.mkdir(parents=True, exist_ok=True)

    project = infer_project(root)
    title = args.title or f"{root.name} AI漫剧生产工作流"
    output.write_text(render_html(project, title), encoding="utf-8")
    write_opener(output)
    print(f"dashboard: {output}")


if __name__ == "__main__":
    main()
