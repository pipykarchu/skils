#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人景合一融合编排器 —— 读 shot-manifest，逐镜调 generate.js 多图融合。

融合提示词 = 07 主提示词（原样） + 固定融合约束（见 references/fusion-prompt-rules.md）。
不改写主提示词。把每镜 refs 的 PNG 逐个作 --image 传给 gpt-image-2 的 edits 端点。

--dry-run：不调任何 API，只打印每镜将执行的完整命令 + 参考图清单。
           （未设 TUZI_API_KEY 时自动进入 dry-run，绝不误调 API。）

用法：
  # 干跑（默认安全，不花钱）
  python fuse_shots.py --manifest shot-manifest.json --dry-run

  # 实跑（需用户授权，消耗额度，上传素材到第三方）
  export TUZI_API_KEY=sk-...
  python fuse_shots.py --manifest shot-manifest.json \
      --tool "<.../short-comic-storyboard/tools/gpt-image-2/generate.js>" \
      --n 2 --size 1024x1536
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

# 运镜 → 静帧取景（与 references/fusion-prompt-rules.md 一致）
MOVE_TO_FRAMING = {
    "固定": "稳定居中构图", "推进": "主体略大、前景强调", "推": "主体略大、前景强调",
    "后拉": "环境更多入画", "拉": "环境更多入画", "平移": "主体偏画面一侧，留出运动方向空间",
    "跟拍": "主体偏画面一侧，留出运动方向空间", "跟随": "主体偏画面一侧，留出运动方向空间",
    "特写": "主体面部或道具占主导", "俯拍": "高角度俯视", "仰拍": "低角度仰视",
}


def framing_for(move: str, shot_size: str) -> str:
    parts = []
    for key, val in MOVE_TO_FRAMING.items():
        if key in (move or ""):
            parts.append(val)
            break
    if shot_size:
        parts.append(shot_size)
    return "，".join(parts) if parts else "按分镜景别构图"


def build_fusion_prompt(shot: dict) -> str:
    base = shot["prompt"].strip()
    sd = shot.get("shot", {})
    jingbie = sd.get("景别", "")
    yunjing = sd.get("运镜", "")
    framing = framing_for(yunjing, jingbie)
    # 07 提示词表无独立景别/运镜列时，回退用「场景/镜头」列作取景提示
    if framing == "按分镜景别构图":
        scene_framing = sd.get("场景", "").strip()
        if scene_framing:
            framing = scene_framing
    # 按 refs 顺序点明每张参考图角色
    refs = shot.get("refs", [])
    ref_lines = []
    idx = 1
    for r in refs:
        if not r.get("path"):
            continue
        kind = {"role": "人物", "scene": "场景", "prop": "道具"}.get(r["kind"], r["kind"])
        ref_lines.append(f"第{idx}张参考图为{kind}（{r['name']}）")
        idx += 1
    ref_note = "；".join(ref_lines)

    constraint = f"""

【多图融合约束】
- 以参考图中的人物为身份基准：保持五官、脸型、发型、年龄段、服装、配饰与人物三视图参考完全一致，不改变识别特征。
- 以参考图中的场景为环境基准：保持空间布局、墙体门窗、家具陈设、材质与场景定版参考一致，只按本镜光线/时段/天气呈现。
- 以参考图中的道具为道具基准：关键道具外形、材质、年代与道具定版参考一致。
- 按本镜景别构图：{framing}。
- 画面只呈现可见内容，不画台词、字幕、镜号、心理活动。
- 竖屏 9:16，真实人物画风，民俗年代质感，低饱和，电影感光影。
- 无文字，无水印，无logo，不使用明星脸，不使用真实人物肖像。"""
    if ref_note:
        constraint += f"\n- 参考图顺序：{ref_note}。"
    neg = shot.get("negative", "")
    if neg:
        constraint += f"\n- 避免：{neg}"
    return base + constraint


def resolve_ref_paths(shot: dict, project_root: Path) -> list[Path]:
    out = []
    for r in shot.get("refs", []):
        p = r.get("path", "")
        if not p:
            continue
        full = (project_root / p).resolve()
        out.append(full)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="人景合一融合编排器")
    ap.add_argument("--manifest", required=True, help="shot-manifest.json 路径")
    ap.add_argument("--tool", default="", help="generate.js 路径（实跑必填）")
    ap.add_argument("--n", default="2", help="每镜候选数")
    ap.add_argument("--size", default="1024x1536", help="画幅，竖屏漫剧默认 1024x1536")
    ap.add_argument("--quality", default="auto")
    ap.add_argument("--only", default="", help="只跑指定镜号，逗号分隔，如 01,05,09")
    ap.add_argument("--dry-run", action="store_true", help="不调 API，只打印命令")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        raise SystemExit(f"manifest 不存在: {manifest_path}")
    manifest_dir = manifest_path.parent
    # manifest 默认在 <项目根>/10_镜头图/ 下；路径(refs/candidates)一律相对项目根。
    project_root = manifest_dir.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 安全闸门：未授权一律 dry-run
    has_key = bool(os.environ.get("TUZI_API_KEY"))
    dry = args.dry_run or not has_key or not args.tool
    if dry and not args.dry_run:
        print("[安全] 未检测到 TUZI_API_KEY 或未指定 --tool，自动进入 --dry-run，不调用任何 API。\n")

    episode = manifest.get("episode", "XX")
    only = {s.strip().zfill(2) for s in args.only.split(",") if s.strip()} if args.only else None

    shots = manifest["shots"]
    if only:
        shots = [s for s in shots if s["no"] in only]

    total_calls = 0
    changed = False
    for shot in shots:
        no = shot["no"]
        fusion_prompt = build_fusion_prompt(shot)
        ref_paths = resolve_ref_paths(shot, project_root)
        out_dir = manifest_dir / "candidates" / f"第{episode}集" / no

        missing = [str(p) for p in ref_paths if not p.exists()]
        ref_desc = "  ".join(f"[{r['kind']}]{r['name']}" for r in shot.get("refs", []) if r.get("path")) or "(无参考图)"

        print(f"=== 镜 {no} ===")
        print(f"  参考图: {ref_desc}")
        if missing:
            print(f"  ! 缺失参考图(跳过实跑): {missing}")
        if shot.get("needsReview"):
            print(f"  ! needsReview: {shot['needsReview']}")

        # 组装命令
        cmd = ["node", args.tool or "<generate.js>", "--prompt", fusion_prompt]
        for p in ref_paths:
            cmd += ["--image", str(p)]
        cmd += ["--size", args.size, "--n", args.n, "--quality", args.quality, "--out", str(out_dir)]

        if dry:
            # 打印可读命令（prompt 截断显示，参考图全列）
            printable = ["node", Path(args.tool).name if args.tool else "<generate.js>",
                         "--prompt", f'"{shot["prompt"][:40]}…+融合约束"']
            for p in ref_paths:
                printable += ["--image", p.name]
            printable += ["--size", args.size, "--n", args.n, "--out",
                          str(out_dir.relative_to(manifest_dir)) if out_dir.is_relative_to(manifest_dir) else str(out_dir)]
            print("  命令:", " ".join(printable))
            total_calls += 1
            print()
            continue

        if not ref_paths:
            print("  (无参考图，跳过——人景合一至少需要1张参考图，请先校正 refs 或先锁定素材)\n")
            continue
        if missing:
            print("  跳过：参考图缺失\n")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"  调用 generate.js -> {out_dir}")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        except FileNotFoundError:
            raise SystemExit("找不到 node，确认已安装 Node 18+ 并在 PATH 中")
        if res.returncode != 0:
            print(f"  失败: {res.stderr.strip()[:300]}\n")
            continue
        saved = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
        print(f"  生成 {len(saved)} 张")
        # 回填 manifest candidates（路径相对项目根，与 refs 一致）
        for i, sp in enumerate(saved):
            try:
                rel = Path(sp).resolve().relative_to(project_root.resolve()).as_posix()
            except Exception:
                rel = sp
            if i < len(shot["candidates"]):
                shot["candidates"][i]["path"] = rel
            else:
                shot["candidates"].append({"id": f"ep{episode}-s{no}-{i+1:02d}", "path": rel, "note": "融合候选"})
        changed = True
        total_calls += 1
        print()

    if changed and not dry:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已回填候选路径 -> {manifest_path}")

    if dry:
        n = int(args.n) if args.n.isdigit() else 1
        print(f"[干跑汇总] {total_calls} 个镜头将各出 {args.n} 候选，约 {total_calls * n} 次 API 调用。")
        print("实跑前请：① 确认 refs 匹配正确、needsReview 已校正；② 估算额度并获用户授权；")
        print("          ③ 设 TUZI_API_KEY 并传 --tool <generate.js路径>。")


if __name__ == "__main__":
    main()
