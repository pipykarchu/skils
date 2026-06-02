#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export confirmed and liked casting references from selection-state.json.

Run from a project's ``08_生成图片/定妆造`` directory, or pass ``--root``.
Copies files only; it never deletes source images.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def safe_name(name: str) -> str:
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip() or "未命名"


def image_refs(look: dict) -> list[tuple[str, dict]]:
    refs: list[tuple[str, dict]] = []
    final = look.get("final")
    if isinstance(final, dict):
        refs.append(("final", final))
    for alt in look.get("alternates", []) or []:
        if isinstance(alt, dict):
            refs.append(("liked", alt))
    # Backward compatibility with older project states.
    for ref in look.get("refs", []) or []:
        if isinstance(ref, dict):
            refs.append(("ref", ref))
    seen = set()
    unique = []
    for kind, ref in refs:
        key = ref.get("id") or ref.get("path")
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append((kind, ref))
    return unique


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目 08_生成图片/定妆造 目录")
    parser.add_argument("--state", default="selection-state.json")
    parser.add_argument("--out", default=None, help="默认输出到 ../角色妆造敲定合集")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    state_path = root / args.state
    if not state_path.exists():
        raise SystemExit(f"未找到状态文件 {state_path}（先在网页里保存选择）")

    out_dir = Path(args.out).resolve() if args.out else root.parent / "角色妆造敲定合集"
    data = json.loads(state_path.read_text(encoding="utf-8"))
    looks = data.get("confirmedLooks", [])
    if not looks:
        print("confirmedLooks 为空。先在网页里心仪 + 确认此时期造型，再保存。")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    copied, missing = 0, []
    for look in looks:
        role = safe_name(str(look.get("role", "未知角色")).split(" / ")[0])
        state = safe_name(str(look.get("state", "未知时期")))
        for kind, ref in image_refs(look):
            rel = ref.get("path", "")
            if not rel:
                continue
            src = (root / rel).resolve()
            if not src.exists():
                missing.append(rel)
                continue
            engine = safe_name(str(ref.get("engine", "")))
            dst = out_dir / f"{role}_{state}_{kind}_{engine}_{safe_name(src.name)}"
            shutil.copy2(src, dst)
            copied += 1

    print(f"已收集 {copied} 张到 {out_dir}")
    if missing:
        print(f"找不到源图 {len(missing)} 张：")
        for rel in missing[:12]:
            print("  -", rel)


if __name__ == "__main__":
    main()
