#!/usr/bin/env python3
"""Serve a local casting-look selection gallery from a manifest JSON.

This script is a reusable starter. Copy it into the project output folder or
run it directly with --manifest pointing at the project manifest.
"""

from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def iter_images(manifest: dict):
    for role in manifest.get("roles", []):
        for state in role.get("states", []):
            for group in state.get("groups", []):
                for image in group.get("images", []):
                    yield role, state, group, image


def render_html(manifest: dict) -> bytes:
    sections = []
    for role in manifest.get("roles", []):
        role_name = html.escape(role.get("name", "未命名角色"))
        state_html = []
        for state in role.get("states", []):
            state_name = html.escape(state.get("name", "默认场景"))
            group_html = []
            for group in state.get("groups", []):
                engine = html.escape(group.get("engine", "image2"))
                cards = []
                for image in group.get("images", []):
                    img_id = html.escape(image.get("id") or image.get("path", "image"))
                    path = html.escape(image.get("path", ""))
                    cards.append(f"""
                    <article class="card" data-id="{img_id}">
                      <button class="star" type="button" title="标心">☆</button>
                      <img src="/asset/{path}" alt="{img_id}">
                      <div class="id">{img_id}</div>
                    </article>
                    """)
                group_html.append(f"""
                <div class="group">
                  <h4>{engine}</h4>
                  <div class="cards">{''.join(cards)}</div>
                </div>
                """)
            state_html.append(f"""
            <section class="state">
              <h3>{state_name}</h3>
              {''.join(group_html)}
              <label>心仪的点<textarea data-field="likes" data-role="{role_name}" data-state="{state_name}"></textarea></label>
              <label>调整提示词<textarea data-field="adjustments" data-role="{role_name}" data-state="{state_name}"></textarea></label>
            </section>
            """)
        sections.append(f"<section class='role'><h2>{role_name}</h2>{''.join(state_html)}</section>")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>定妆造选择</title>
<style>
body{{margin:0;font-family:"Microsoft YaHei",sans-serif;background:#f3efe8;color:#202522}}
header{{position:sticky;top:0;background:#f3efe8cc;backdrop-filter:blur(10px);border-bottom:1px solid #d8d0c4;padding:14px 20px;display:flex;gap:12px;align-items:center;justify-content:space-between}}
main{{padding:20px;max-width:1440px;margin:auto}}
button{{height:34px;border:1px solid #cfc7ba;border-radius:6px;background:white;cursor:pointer}}
.primary{{background:#24695c;color:white;border-color:#24695c;padding:0 14px}}
.role{{margin-bottom:30px}}
.state{{background:white;border:1px solid #ddd6ca;border-radius:8px;padding:14px;margin-top:14px}}
.group h4{{margin:16px 0 10px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}}
.card{{position:relative;border:2px solid transparent;border-radius:8px;overflow:hidden;background:#eee}}
.card.selected{{border-color:#b35a32}}
.card img{{display:block;width:100%;aspect-ratio:1/1.25;object-fit:cover}}
.star{{position:absolute;right:8px;top:8px;z-index:2;width:34px;border-radius:50%;font-size:22px;line-height:1;background:#ffffffdd}}
.selected .star{{color:#b35a32}}
.id{{padding:8px;background:white;font-size:13px}}
label{{display:block;margin-top:12px;font-size:14px}}
textarea{{display:block;width:100%;min-height:64px;margin-top:6px;border:1px solid #d8d0c4;border-radius:6px;padding:8px;font:inherit}}
</style>
</head>
<body>
<header><strong>定妆造选择</strong><button id="save" class="primary" type="button">保存选择</button></header>
<main>{''.join(sections)}</main>
<script>
const state = JSON.parse(localStorage.getItem("castingState") || "{{\\"favorites\\":[],\\"notes\\":{{}}}}");
function sync(){{
  document.querySelectorAll(".card").forEach(card => card.classList.toggle("selected", state.favorites.includes(card.dataset.id)));
  localStorage.setItem("castingState", JSON.stringify(state));
}}
document.querySelectorAll(".card").forEach(card => {{
  card.addEventListener("click", () => {{
    const id = card.dataset.id;
    state.favorites = state.favorites.includes(id) ? state.favorites.filter(x => x !== id) : [...state.favorites, id];
    sync();
  }});
}});
document.querySelectorAll("textarea").forEach(area => {{
  const key = `${{area.dataset.role}}::${{area.dataset.state}}::${{area.dataset.field}}`;
  area.value = state.notes[key] || "";
  area.addEventListener("input", () => {{ state.notes[key] = area.value; sync(); }});
}});
document.getElementById("save").addEventListener("click", async () => {{
  sync();
  const res = await fetch("/api/save", {{method:"POST", headers:{{"Content-Type":"application/json"}}, body:JSON.stringify(state)}});
  alert(res.ok ? "已保存" : "保存失败");
}});
sync();
</script>
</body>
</html>""".encode("utf-8")


def make_handler(manifest_path: Path, output_path: Path):
    root = manifest_path.parent.resolve()
    manifest = load_manifest(manifest_path)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html"}:
                self._send(render_html(manifest), "text/html; charset=utf-8")
                return
            if parsed.path.startswith("/asset/"):
                rel = unquote(parsed.path.removeprefix("/asset/"))
                target = (root / rel).resolve()
                if not str(target).startswith(str(root)) or not target.exists():
                    self._send_json({"error": "not found"}, 404)
                    return
                self._send(target.read_bytes(), "image/png")
                return
            self._send_json({"error": "not found"}, 404)

        def do_POST(self):
            if urlparse(self.path).path != "/api/save":
                self._send_json({"error": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "path": str(output_path)})

        def _send(self, body: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: dict, status: int = 200):
            self._send(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", default="selection-state.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    output_path = (manifest_path.parent / args.out).resolve()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manifest_path, output_path))
    print(f"Gallery: http://{args.host}:{args.port}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
