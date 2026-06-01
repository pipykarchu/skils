#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人景合一 manifest 构建器 —— 解析既有分镜提示词 + 自动匹配锁定参考图。

第一铁律：不重写任何提示词。主提示词一律原样取自既有产物：
  首选 07_绘图提示词/第XX集_*.md 的「分镜生图提示词」表格 → 主提示词列
  兜底 06_分镜表/第XX集_*.md 的「画面内容提示词」列

自动匹配参考图：
  人物 → 08_生成图片/角色三视图/*.png（去序号去标点子串匹配 + 别名表）
  场景/道具 → 02_世界观/视觉定版/scene-anchors.json（aliases 包含匹配）

输出 shot-manifest.json 喂给 fuse_shots.py 和 fusion_gallery_server.py。
不联网、不调任何 API。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# ---- 角色别名表（可被 03_角色设定/角色固定提示词.md 校正）---------------------
# key 是三视图归一化后的候选名，value 是它在提示词里可能的别称。
ALIASES: dict[str, list[str]] = {
    "成年阿妮": ["阿妮", "母亲", "三十多岁母亲", "妈"],
    "少女妮儿": ["小妮儿", "少女小妮儿", "妮儿"],
    "小妮儿": ["婴儿小妮儿", "幼年", "幼年小妮儿"],
    "娃娃仙姐姐": ["娃娃仙", "姐姐", "辫子姐姐"],
    "五辫布娃娃": ["布娃娃", "粗布娃娃", "娃娃", "五辫娃娃"],
    "姥爷": ["姥爷", "外公", "中年农人"],
    "姥姥": ["姥姥", "外婆", "中年农妇"],
    "道士": ["道士", "修行者", "修行人"],
}

TURNAROUND_DIRS = [
    "08_生成图片/角色三视图",
    "03_角色设定/定妆造",
]
SCENE_ANCHORS = "02_世界观/视觉定版/scene-anchors.json"

PUNCT_RE = re.compile(r"[，,、_/（）()·。：:；;！!　\s]+")
SEQ_PREFIX_RE = re.compile(r"^\d+[_\-．.、]?")


# ---- markdown 表格解析 ----------------------------------------------------

def _cells(line: str) -> list[str]:
    line = line.rstrip("\n")
    if not line.strip().startswith("|"):
        return []
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells if c)


def parse_table(md: str) -> list[dict]:
    rows, header = [], None
    for raw in md.splitlines():
        cs = _cells(raw)
        if not cs:
            header = None
            continue
        if header is None:
            if any("镜号" in c for c in cs):
                header = cs
            continue
        if _is_sep(cs):
            continue
        rows.append({header[i] if i < len(header) else f"c{i}": (cs[i] if i < len(cs) else "")
                     for i in range(max(len(header), len(cs)))})
    return rows


def _col(row: dict, *names: str) -> str:
    for n in names:
        for k, v in row.items():
            if n in str(k):
                return v
    return ""


def _section_body(md: str, heading: str) -> str:
    """取 `## heading` 到下一个 `## ` 之间的正文（去表格行）。"""
    lines = md.splitlines()
    out, capture = [], False
    for ln in lines:
        if ln.strip().startswith("## "):
            if capture:
                break
            capture = heading in ln
            continue
        if capture and ln.strip() and not ln.strip().startswith("|") and not ln.strip().startswith("#"):
            out.append(ln.strip())
    return " ".join(out).strip()


# ---- 文件名归一化 & 匹配 --------------------------------------------------

def normalize(name: str) -> str:
    name = SEQ_PREFIX_RE.sub("", name)
    name = re.sub(r"\.(png|jpg|jpeg|webp)$", "", name, flags=re.I)
    name = PUNCT_RE.sub(" ", name)
    return name.strip()


def candidate_names(norm: str) -> list[str]:
    parts = [p for p in norm.split(" ") if len(p) >= 2]
    return parts or ([norm] if norm else [])


def find_turnarounds(root: Path) -> list[dict]:
    found = []
    for rel in TURNAROUND_DIRS:
        d = root / rel
        if not d.exists():
            continue
        for p in sorted(d.glob("*.png")):
            nm = p.name
            if any(x in nm for x in ("总览", "gallery", "log", "pid", ".err")):
                continue
            norm = normalize(nm)
            found.append({"file": p, "display": norm, "cands": candidate_names(norm)})
    return found


def match_roles(text: str, turnarounds: list[dict]) -> list[dict]:
    hits = []
    for t in turnarounds:
        conf = ""
        # high: 任一候选名整段是 text 子串
        for c in t["cands"]:
            if c in text:
                conf = "high"
                break
        # medium: 别名命中
        if not conf:
            for c in t["cands"]:
                for alias in ALIASES.get(c, []):
                    if alias in text:
                        conf = "medium"
                        break
                if conf:
                    break
        if conf:
            hits.append({"kind": "role", "name": t["display"], "file": t["file"], "confidence": conf})
    return hits


def load_anchors(root: Path) -> dict:
    p = root / SCENE_ANCHORS
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    # 锚点里的 path 相对 02_世界观/视觉定版/，补成绝对路径，供 relpath() 转项目根相对
    base = (root / "02_世界观" / "视觉定版").resolve()
    for group in ("scenes", "props"):
        for item in data.get(group, []):
            rp = item.get("path", "")
            if rp and not Path(rp).is_absolute():
                item["path"] = str((base / rp).resolve())
    return data


def match_scene_prop(text: str, shot_no: str, anchors: dict) -> list[dict]:
    hits = []
    for sc in anchors.get("scenes", []):
        aliases = sc.get("aliases", []) + [sc.get("subscene", ""), sc.get("module", "")]
        matched = [a for a in aliases if a and a in text]
        if matched:
            conf = "high" if shot_no in sc.get("usedByShots", []) else "medium"
            hits.append({"kind": "scene", "name": f"{sc.get('subscene','')}·{sc.get('variant','')}".strip("·"),
                         "file": sc.get("path", ""), "confidence": conf, "_alias_len": max(len(a) for a in matched)})
    for pr in anchors.get("props", []):
        aliases = pr.get("aliases", []) + [pr.get("name", "")]
        if any(a and a in text for a in aliases):
            conf = "high" if shot_no in pr.get("usedByShots", []) else "medium"
            hits.append({"kind": "prop", "name": pr.get("name", ""), "file": pr.get("path", ""), "confidence": conf})
    # 多个场景命中时，优先 high，再按 alias 长度
    scenes = sorted([h for h in hits if h["kind"] == "scene"],
                    key=lambda h: (h["confidence"] != "high", -h.get("_alias_len", 0)))
    props = [h for h in hits if h["kind"] == "prop"]
    if scenes:
        scenes = [scenes[0]]  # 一镜锁一个主场景
    for h in scenes + props:
        h.pop("_alias_len", None)
    return scenes + props


# ---- 提示词源加载 ---------------------------------------------------------

def find_prompt_file(root: Path, episode: str) -> Path | None:
    d = root / "07_绘图提示词"
    if d.exists():
        for p in sorted(d.glob(f"第{episode}*_*.md")):
            return p
    return None


def find_storyboard_file(root: Path, episode: str) -> Path | None:
    d = root / "06_分镜表"
    if d.exists():
        for p in sorted(d.glob(f"第{episode}*_*.md")):
            return p
    return None


def _shot_no(row: dict) -> str:
    m = re.search(r"\d+", _col(row, "镜号"))
    return m.group(0).zfill(2) if m else _col(row, "镜号").strip()


# ---- 主流程 ---------------------------------------------------------------

def build(root: Path, episode: str) -> dict:
    turnarounds = find_turnarounds(root)
    anchors = load_anchors(root)

    prompt_file = find_prompt_file(root, episode)
    sb_file = find_storyboard_file(root, episode)
    source_file = prompt_file or sb_file
    if not source_file:
        raise SystemExit(f"第{episode}集：07_绘图提示词 和 06_分镜表 都找不到对应 md")

    md = source_file.read_text(encoding="utf-8")
    rows = parse_table(md)
    from_07 = source_file == prompt_file

    style_anchor = _section_body(md, "全片风格锚点") if from_07 else ""
    global_neg = _section_body(md, "统一负面提示词") if from_07 else ""
    # 标题：从文件名取「第XX集_标题_…」里的标题段
    mtitle = re.search(rf"第{episode}\w*?_([^_]+)_", source_file.name)
    title = mtitle.group(1) if mtitle else ""

    manifest_dir = root / "10_镜头图"

    def relpath(target) -> str:
        """路径一律相对【项目根】，不用 ../，避免浏览器规范化掉 /asset/../ 导致取图失败。
        服务器的 /asset/ 根域也设为项目根，候选图(10_镜头图/...)和参考图(08_/02_...)都覆盖。"""
        if not target:
            return ""
        try:
            return Path(target).resolve().relative_to(root.resolve()).as_posix()
        except Exception:
            import os
            return os.path.relpath(str(Path(target).resolve()), str(root.resolve())).replace("\\", "/")

    shots = []
    for row in rows:
        no = _shot_no(row)
        if not no:
            continue
        prompt = _col(row, "主提示词", "画面内容提示词").strip()
        role_anchor_col = _col(row, "角色锚点")
        scene_col = _col(row, "场景/镜头", "场景")
        match_text = " ".join([role_anchor_col, prompt])
        scene_text = " ".join([scene_col, prompt])

        role_hits = match_roles(match_text, turnarounds)
        sp_hits = match_scene_prop(scene_text, no, anchors)

        refs = []
        for h in role_hits:
            refs.append({"kind": "role", "name": h["name"], "path": relpath(h["file"]), "confidence": h["confidence"]})
        for h in sp_hits:
            refs.append({"kind": h["kind"], "name": h["name"], "path": relpath(h["file"]) if h["file"] else "",
                         "confidence": h["confidence"]})

        # negative：07 写「统一负面提示词」时回填正文
        neg_col = _col(row, "负面提示词")
        negative = global_neg if (not neg_col or "统一" in neg_col) else neg_col

        # needsReview 判定
        review = []
        has_role_text = bool(role_anchor_col.strip()) or any(
            a in match_text for al in ALIASES.values() for a in al)
        if has_role_text and not any(r["kind"] == "role" for r in refs):
            review.append("疑似有角色但未匹配到三视图")
        if not anchors:
            review.append("场景未锁(无scene-anchors.json)，建议先跑 changjingmeishu")
        elif not any(r["kind"] == "scene" for r in refs) and scene_col.strip():
            review.append("场景列有内容但未匹配到锁定场景")
        dup_roles = [r["name"] for r in refs if r["kind"] == "role"]
        if len(dup_roles) >= 4:
            review.append(f"匹配到{len(dup_roles)}个角色，确认是否过匹配")

        shots.append({
            "no": no,
            "prompt": prompt,
            "negative": negative,
            "shot": {
                "画面目的": _col(row, "画面目的"),
                "景别": _col(row, "景别"),
                "运镜": _col(row, "运镜"),
                "时长": _col(row, "时长"),
                "台词": _col(row, "人物台词", "台词"),
                "场景": scene_col,
                "光影": _col(row, "光影色彩", "光影"),
            },
            "refs": refs,
            "candidates": [{"id": f"ep{episode}-s{no}-{i:02d}", "path": "", "note": f"融合候选{i}"}
                           for i in range(1, 5)],
            "needsReview": "；".join(review),
        })

    return {
        "project": root.name,
        "episode": episode,
        "title": title,
        "styleAnchor": style_anchor,
        "globalNegative": global_neg,
        "promptSource": source_file.name,
        "promptSourceType": "07_绘图提示词" if from_07 else "06_分镜表",
        "shots": shots,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="人景合一 shot-manifest 构建器")
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--episode", required=True, help="集号，如 01")
    ap.add_argument("--out", default="shot-manifest.json")
    ap.add_argument("--print", action="store_true", dest="do_print")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"项目根不存在: {root}")
    ep = args.episode.zfill(2) if args.episode.isdigit() else args.episode

    manifest = build(root, ep)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = root / "10_镜头图" / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    shots = manifest["shots"]
    role_hit = sum(1 for s in shots if any(r["kind"] == "role" for r in s["refs"]))
    scene_hit = sum(1 for s in shots if any(r["kind"] == "scene" for r in s["refs"]))
    review = [s for s in shots if s["needsReview"]]
    print(f"项目: {manifest['project']}  第{ep}集《{manifest['title']}》")
    print(f"提示词源: {manifest['promptSource']} ({manifest['promptSourceType']})")
    print(f"镜头: {len(shots)}  人物命中: {role_hit}  场景命中: {scene_hit}  needsReview: {len(review)}")
    print(f"shot-manifest -> {out_path}")
    if args.do_print:
        print("\n逐镜匹配:")
        for s in shots:
            refs = " ".join(f"{r['kind']}:{r['name']}({r['confidence']})" for r in s["refs"]) or "(无参考)"
            print(f"  [{s['no']}] {refs}")
            if s["needsReview"]:
                print(f"       ! {s['needsReview']}")


if __name__ == "__main__":
    main()
