#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Package per-state casting prompts into per-role Markdown files.

Run from a project's ``08_生成图片/定妆造`` directory, or pass ``--root``.
Reads ``manifest.json`` plus ``prompts/*.md`` and writes:
``03_角色设定/定妆提示词/<角色>_定妆提示词合集.md``.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path


def safe_name(name: str) -> str:
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip() or "未命名"


def role_slug(name: str) -> str:
    return safe_name(re.split(r"\s*/\s*|、|，|,", name)[0])


def read_prompt(path: Path) -> str | None:
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    body = [ln for i, ln in enumerate(lines) if not (i == 0 and ln.startswith("# "))]
    return "\n".join(body).strip()


def load_merge_map(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    if not path.exists():
        raise SystemExit(f"未找到 merge map: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("merge map 必须是 JSON object，例如 {\"阿妮\": \"小妮儿（阿妮）\"}")
    return {str(k): str(v) for k, v in data.items()}


def infer_prompt_base(role: str, state: dict) -> str:
    prompts = state.get("prompts") or {}
    if isinstance(prompts, dict):
        for key in ("base", "prompt_base"):
            if prompts.get(key):
                return str(prompts[key])
    return f"{role_slug(role)}_{safe_name(str(state.get('name', '未命名时期')))}"


def collect(manifest: dict, prompts_dir: Path, merge_map: dict[str, str]):
    packages: "OrderedDict[str, list[dict]]" = OrderedDict()
    for module in manifest.get("modules", []):
        for role in module.get("roles", []):
            role_name = str(role.get("name", "未命名角色"))
            package_name = merge_map.get(role_name, role_name)
            package_name = merge_map.get(role_slug(role_name), package_name)
            packages.setdefault(package_name, [])
            for state in role.get("states", []):
                state_name = str(state.get("name", "未命名时期"))
                base = infer_prompt_base(role_name, state)
                item = {
                    "module": module.get("name", ""),
                    "role": role_name,
                    "state": state_name,
                    "base": base,
                    "prompts": OrderedDict(),
                }
                for engine in ("Gemini Image", "Image2", "MJ"):
                    filename_engine = engine.replace(" ", "_")
                    candidates = [
                        prompts_dir / f"{base}_{engine}_round01.md",
                        prompts_dir / f"{base}_{filename_engine}_round01.md",
                    ]
                    body = next((read_prompt(p) for p in candidates if p.exists()), None)
                    if body:
                        item["prompts"][engine] = body
                packages[package_name].append(item)
    return packages


def write_packages(packages, out_dir: Path, project: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for package_name, items in packages.items():
        parts = [
            f"# 《{project}》{package_name} 定妆提示词合集\n",
            "> 由定妆造 skill 按 manifest 自动打包。Gemini/Image2 为整句约束版，MJ 为紧凑标签版。\n",
        ]
        for item in items:
            parts.append(f"\n## {item['role']} · {item['state']}\n")
            if item.get("module"):
                parts.append(f"\n- 模块：{item['module']}\n")
            if not item["prompts"]:
                parts.append("\n（该时期暂无提示词文件）\n")
                continue
            for engine, body in item["prompts"].items():
                parts.append(f"\n### {engine} 版\n\n{body}\n")
        out = out_dir / f"{safe_name(package_name)}_定妆提示词合集.md"
        out.write_text("\n".join(parts).strip() + "\n", encoding="utf-8")
        written.append(out)
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="项目 08_生成图片/定妆造 目录")
    parser.add_argument("--manifest", default="manifest.json")
    parser.add_argument("--prompts", default="prompts")
    parser.add_argument("--out", default=None, help="默认输出到 ../../03_角色设定/定妆提示词")
    parser.add_argument("--merge-map", default=None, help="可选 JSON：把跨时期别名合并到同一角色合集")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / args.manifest
    if not manifest_path.exists():
        raise SystemExit(f"未找到 manifest: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out_dir = Path(args.out).resolve() if args.out else root.parent.parent / "03_角色设定" / "定妆提示词"
    packages = collect(manifest, root / args.prompts, load_merge_map(Path(args.merge_map).resolve() if args.merge_map else None))
    written = write_packages(packages, out_dir, str(manifest.get("project", "项目")))

    print(f"已输出 {len(written)} 个角色提示词合集到 {out_dir}")
    for path in written:
        print("  -", path.name)


if __name__ == "__main__":
    main()
