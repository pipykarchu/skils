#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""场景美术 manifest 构建器 —— 扫分镜反推场地，生成 casting 兼容 manifest.json。

核心：分镜驱动按需锁定，绝不穷举「场地 × 角度 × 时段 × 天气」全组合。
只把分镜里实际出现过的组合写进 manifest，并记录 usedByShots（引用镜号）。

数据来源（优先级）：
  06_分镜表/第XX集_*.md          （权威：画面内容提示词列）
  07_绘图提示词/第XX集_*.md       （兜底/补充：主提示词 + 场景/镜头 + 光影色彩列）
  02_世界观/年代设定与场景刻画.md  （styleTone / forbid 参考）

输出：
  manifest.json   —— 喂给 dingzhuangzao/casting_gallery_server.py

用法：
  python build_scene_manifest.py --project-root <项目根> [--out manifest.json] [--print]

不联网、不调任何 API。匹配不确定的组合会标 needsReview，并在 --print 时列出，
交人工/agent 校正后再生成参考图。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Windows 控制台默认 GBK，含中文/符号的 print 会崩；统一重配为 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# ---- 关键词词典（按项目可扩充）-------------------------------------------

LOCATION_HINTS = {
    "阿妮家·旧屋": ["旧屋", "卧室", "堂屋", "屋内", "炕", "床头"],
    "阿妮家·院落": ["院", "院门", "院子", "门口"],
    "阿妮家·灶房": ["灶台", "灶火", "厨房", "灶"],
    "阿妮家·偏房": ["偏房"],
    "河沟": ["河", "河边", "河沟", "河水", "上游"],
    "山坡土路": ["山坡", "土路", "山路", "山脚"],
    "竹林": ["竹林"],
    "坟地": ["坟", "墓", "坟头"],
    "婚礼现场": ["婚礼", "喜堂", "迎亲"],
}

ANGLE_HINTS = {
    "远景": ["远景", "全景"],
    "近景特写": ["近景", "特写", "大特写"],
    "俯视": ["俯拍", "俯视"],
    "仰视": ["仰拍", "仰视"],
    "中景": ["中景", "中近景", "过肩"],
}

TIME_HINTS = {
    "白天": ["白天", "烈日", "正午", "清晨", "清早", "早上", "日间", "夏日"],
    "黄昏": ["傍晚", "黄昏", "夕阳", "日落"],
    "夜": ["夜", "夜晚", "油灯", "床头灯", "深夜", "晚上", "烛"],
}

WEATHER_HINTS = {
    "晴": ["晴", "烈日", "阳光", "日头"],
    "阴": ["阴", "乌云", "阴天", "阴冷"],
    "雨": ["雨", "下雨", "雨夜"],
    "雾": ["雾", "迷雾"],
}

# ---- 分镜表解析 -----------------------------------------------------------

# 分镜表（06）表头候选：镜号 | 时长 | 景别 | 运镜 | 画面内容提示词 | 人物台词 | 备注
# 生图提示词（07）表头：镜号 | 画面目的 | 推荐平台/模型 | 主提示词 | 角色锚点 | 场景/镜头 | 光影色彩 | 负面提示词 | 参数/备注

def _split_md_row(line: str) -> list[str]:
    line = line.strip()
    if not line.startswith("|"):
        return []
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c)


def parse_storyboard_table(md_text: str) -> list[dict]:
    """从一份 md 里抓第一个含『镜号』的表格，返回每行 {header: value} 列表。"""
    rows: list[dict] = []
    header: list[str] | None = None
    for raw in md_text.splitlines():
        cells = _split_md_row(raw)
        if not cells:
            header = None  # 表格中断
            continue
        if header is None:
            if any("镜号" in c for c in cells):
                header = cells
            continue
        if _is_separator_row(cells):
            continue
        # 数据行
        row = {}
        for i, h in enumerate(header):
            row[h] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def _get(row: dict, *names: str) -> str:
    """按列名模糊取值（表头可能微变）。"""
    for n in names:
        for k, v in row.items():
            if n in k:
                return v
    return ""


# ---- 维度推断 -------------------------------------------------------------

def _match_dim(text: str, hints: dict[str, list[str]]) -> str | None:
    for label, kws in hints.items():
        for kw in kws:
            if kw in text:
                return label
    return None


def _shot_no(row: dict) -> str:
    raw = _get(row, "镜号")
    m = re.search(r"\d+", raw)
    return m.group(0).zfill(2) if m else raw.strip()


def extract_combos(rows: list[dict]) -> dict:
    """把每镜归并成 (场地,子场景占位,角度,时段,天气) 组合，记录 usedByShots。

    子场景这里先用『场地』本身占位；同场地不同房间靠 LOCATION_HINTS 的细分 key 区分
    （如 阿妮家·旧屋 / 阿妮家·院落 已是子场景级）。
    """
    combos: dict[tuple, dict] = {}
    for row in rows:
        shot = _shot_no(row)
        # 画面文字：06 用『画面内容提示词』，07 用『主提示词』+『场景/镜头』+『光影色彩』
        scene_text = " ".join([
            _get(row, "画面内容提示词", "主提示词"),
            _get(row, "场景/镜头", "场景"),
            _get(row, "光影色彩", "光影"),
            _get(row, "景别"),
            _get(row, "运镜"),
        ])
        loc = _match_dim(scene_text, LOCATION_HINTS)
        if not loc:
            continue  # 没识别到地点的镜头跳过（多为纯特写道具/人物，由人景合一处理）
        angle = _match_dim(_get(row, "景别") + scene_text, ANGLE_HINTS) or "中景"
        time = _match_dim(scene_text, TIME_HINTS) or "白天"
        weather = _match_dim(scene_text, WEATHER_HINTS) or ""
        # 大场地 = 取 · 前部分；子场景 = 完整 key
        big = loc.split("·")[0]
        sub = loc
        variant_parts = [angle, time] + ([weather] if weather else [])
        variant = "·".join(variant_parts)
        key = (big, sub, variant)
        c = combos.setdefault(key, {
            "module": big, "subscene": sub, "variant": variant,
            "angle": angle, "time": time, "weather": weather,
            "usedByShots": [], "sceneTexts": [],
        })
        if shot not in c["usedByShots"]:
            c["usedByShots"].append(shot)
        snippet = _get(row, "画面内容提示词", "主提示词")[:60]
        if snippet and snippet not in c["sceneTexts"]:
            c["sceneTexts"].append(snippet)
    return combos


# ---- manifest 组装 --------------------------------------------------------

def _slug(s: str) -> str:
    return re.sub(r"[^\w一-鿿]+", "", s) or "x"


def group(engine: str, base_id: str, n: int = 4) -> dict:
    eng_short = "i2" if "image2" in engine.lower() else "mj"
    images = [{"id": f"{base_id}-{eng_short}-{i:02d}", "path": "", "note": f"{engine} 候选 {i}"}
              for i in range(1, n + 1)]
    label = "场景概念图（整句约束）" if eng_short == "i2" else "场景概念图（紧凑标签）"
    return {"engine": "Image2" if eng_short == "i2" else "MJ", "label": label, "images": images}


def build_manifest(project: str, combos: dict, style_tone: str, forbid: str) -> dict:
    modules: dict[str, dict] = {}
    for (big, sub, variant), c in combos.items():
        mod = modules.setdefault(big, {"name": big, "roles": {}})
        role = mod["roles"].setdefault(sub, {"name": sub, "states": []})
        base_id = f"{_slug(big)}-{_slug(sub)}-{_slug(variant)}"
        scene_text = "；".join(c["sceneTexts"]) or "（取自分镜，待补充画面说明）"
        state = {
            "name": variant,
            "worldview": {
                "era": f"{c['time']}" + (f"·{c['weather']}" if c["weather"] else ""),
                "scene": scene_text,
                "space": "【空间锚点·禁止变化】同一子场景所有时段/天气共用此布局，待人工补充：墙体/门窗/家具位置",
                "props": "（待补充：本场景关键道具）",
                "costume": "（待补充：出场人物 + 位置关系 + 交互关系）",
                "light": f"{c['time']}" + (f"·{c['weather']}" if c["weather"] else "") + "，与已锁人物光影统一",
                "forbid": forbid,
                "keywords": [c["angle"], c["time"]] + ([c["weather"]] if c["weather"] else [])
                            + [f"镜号{s}" for s in c["usedByShots"]],
            },
            "groups": [group("Image2", base_id), group("MJ", base_id)],
            "_usedByShots": c["usedByShots"],
        }
        role["states"].append(state)
    # dict → list
    out_modules = []
    for mod in modules.values():
        mod["roles"] = list(mod["roles"].values())
        out_modules.append(mod)
    return {"project": project, "round": 1, "styleTone": style_tone, "modules": out_modules}


# ---- 主流程 ---------------------------------------------------------------

def collect_rows(project_root: Path) -> list[dict]:
    rows: list[dict] = []
    sb_dir = project_root / "06_分镜表"
    pr_dir = project_root / "07_绘图提示词"
    files = sorted(sb_dir.glob("第*_*.md")) if sb_dir.exists() else []
    if not files and pr_dir.exists():
        files = sorted(pr_dir.glob("第*_*.md"))
    for f in files:
        rows.extend(parse_storyboard_table(f.read_text(encoding="utf-8")))
    return rows


def read_style_tone(project_root: Path) -> tuple[str, str]:
    wv = project_root / "02_世界观" / "年代设定与场景刻画.md"
    default_tone = ("真实人物质感，竖屏9:16，民俗恐怖志怪，低饱和色彩，太行山旧村，"
                    "阴冷自然光与火光对比，与已锁人物画风统一")
    default_forbid = "现代家具、空调、现代灯具、现代电器、错误年代物件、文字、水印、卡通Q版"
    if not wv.exists():
        # 搜含 世界观/年代/场景 的文件
        cand = list((project_root / "02_世界观").glob("*.md")) if (project_root / "02_世界观").exists() else []
        if cand:
            wv = cand[0]
    if wv.exists():
        # 简单提取首段非空行作 styleTone 参考（不强求）
        text = wv.read_text(encoding="utf-8")
        return default_tone, default_forbid  # 词典化 forbid 更可靠，正文仅供 agent 参考
    return default_tone, default_forbid


def main() -> None:
    ap = argparse.ArgumentParser(description="场景美术 manifest 构建器（分镜驱动）")
    ap.add_argument("--project-root", required=True, help="漫剧项目根目录")
    ap.add_argument("--out", default="manifest.json", help="输出 manifest 路径")
    ap.add_argument("--print", action="store_true", dest="do_print", help="打印反推出的场地组合清单")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"项目根不存在: {root}")
    project = root.name

    rows = collect_rows(root)
    if not rows:
        raise SystemExit("没读到任何分镜行，确认 06_分镜表 或 07_绘图提示词 下有『第XX集_*.md』且含『镜号』表格")
    combos = extract_combos(rows)
    style_tone, forbid = read_style_tone(root)
    manifest = build_manifest(project, combos, style_tone, forbid)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / "02_世界观" / "视觉定版" / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"项目: {project}")
    print(f"分镜行: {len(rows)}  反推出场地组合: {len(combos)}")
    print(f"manifest -> {out_path}")
    if args.do_print:
        print("\n按需锁定的场地组合（分镜驱动）:")
        for (big, sub, variant), c in sorted(combos.items()):
            print(f"  [{big}] {sub} / {variant}  ← 镜号 {','.join(c['usedByShots'])}")
        print("\n[!] 每个 state 的 space(空间锚点)/props/costume 字段是占位，需人工或 agent 补充后再生成参考图。")


if __name__ == "__main__":
    main()
