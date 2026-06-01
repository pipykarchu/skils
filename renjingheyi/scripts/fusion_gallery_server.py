#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""人景合一 逐镜头融合评审 Gallery —— 集→镜号 三栏布局本地服务器。

左栏：集 -> 镜号列表（✓ 标记已确认）。
中栏：某镜的融合候选（❤️心仪多选）+ 该镜用到的参考图缩略图 + 只读原始主提示词
      + 心仪的点/调整提示词 + 进入下一版/确认此镜镜头图。
右栏：该镜 景别/运镜/时长/台词/场景说明。
底部：全部确认后「导出镜头图」（仅记录意图，真正导出由 agent 下一步执行）。

复用 dingzhuangzao casting_gallery_server 的全部后端机制：服务器从不调任何生图 API，
只 serve 页面、/api/manifest（热更新）、/asset/<relpath>（路径穿越防护）、POST /api/save。

用法：
  python fusion_gallery_server.py --manifest shot-manifest.json --out selection-state.json --port 8792
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>人景合一 · 逐镜评审</title>
<style>
:root{
  --bg:#f4f0e9; --panel:#fffdf9; --line:#ddd6ca; --ink:#26221c; --muted:#7c7264;
  --accent:#24695c; --accent-soft:#e2efe9; --warm:#b35a32; --heart:#e0395e;
  --shadow:0 1px 2px rgba(40,30,15,.06),0 8px 24px rgba(40,30,15,.06);
}
*{box-sizing:border-box}
body{margin:0;font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;
  gap:16px;padding:12px 22px;background:rgba(244,240,233,.86);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line)}
header .title{display:flex;align-items:baseline;gap:12px}
header h1{margin:0;font-size:18px;letter-spacing:.5px}
header .proj{font-size:13px;color:var(--muted)}
header .progress{font-size:13px;color:var(--muted)}
header .progress b{color:var(--accent)}
.btn{height:34px;padding:0 14px;border:1px solid var(--line);border-radius:7px;background:var(--panel);
  cursor:pointer;font:inherit;color:var(--ink);transition:.15s}
.btn:hover{border-color:#c3bbac}
.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.primary:hover{filter:brightness(1.05)}
.btn:disabled{opacity:.45;cursor:not-allowed}

.layout{display:grid;grid-template-columns:230px 1fr 300px;gap:0;height:calc(100vh - 59px)}
@media(max-width:1180px){.layout{grid-template-columns:200px 1fr}.aside-right{display:none}}

/* ---- 左栏：集→镜号 ---- */
.nav{border-right:1px solid var(--line);overflow:auto;padding:14px 8px 60px;background:#efe9e0}
.ep-title{position:sticky;top:0;z-index:5;font-size:12px;letter-spacing:1px;color:var(--muted);
  padding:6px 10px;background:#efe9e0;border-bottom:1px solid #e2dacd}
.shot-link{display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;
  padding:8px 10px;border:0;border-radius:7px;background:transparent;cursor:pointer;font:inherit;
  color:var(--ink);text-align:left;font-size:13px;margin-top:2px}
.shot-link:hover{background:#e7e0d4}
.shot-link.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.shot-link .sno{font-weight:600;min-width:30px}
.shot-link .purpose{flex:1;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.shot-link.active .purpose{color:var(--accent)}
.shot-link .tick{font-size:12px;color:var(--accent);opacity:0}
.shot-link.confirmed .tick{opacity:1}
.shot-link.review .sno::after{content:"!";color:var(--warm);margin-left:3px;font-weight:700}

/* ---- 中栏 ---- */
.stage{overflow:auto;padding:20px 24px 90px}
.stage .crumb{font-size:13px;color:var(--muted);margin-bottom:4px}
.stage h2{margin:0 0 2px;font-size:21px}
.stage .purpose-big{font-size:13px;color:var(--muted);margin-bottom:14px}
.refrow{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 6px}
.refchip{display:flex;flex-direction:column;align-items:center;gap:4px;width:78px}
.refchip .thumb{width:78px;height:104px;border-radius:8px;overflow:hidden;background:#ece5d8;
  border:1px solid var(--line);display:flex;align-items:center;justify-content:center}
.refchip .thumb img{width:100%;height:100%;object-fit:cover;cursor:zoom-in}
.refchip .ph{font-size:10px;color:#b3a892;text-align:center;padding:6px}
.refchip .lab{font-size:11px;color:var(--muted);text-align:center;line-height:1.3;
  max-width:78px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.refchip .kindtag{font-size:10px;padding:1px 6px;border-radius:5px;background:#eee5d6;color:#6b5d45}
.refchip .kindtag.scene{background:#d9ece5;color:#2c6356}
.refchip .kindtag.prop{background:#e7e0f2;color:#5a4a86}
.review-banner{background:#fbeee4;border:1px solid #e8c9a8;border-radius:8px;padding:8px 12px;
  font-size:12px;color:#8a5a2a;margin:8px 0}
.promptbox{background:#f7f3ec;border:1px solid var(--line);border-radius:10px;padding:10px 13px;
  margin:12px 0;font-size:13px;line-height:1.7;color:#4a4338;white-space:pre-wrap}
.promptbox .lab{font-size:11px;letter-spacing:1px;color:var(--muted);margin-bottom:5px;font-weight:600}
.promptbox .ro{font-size:11px;color:var(--warm);margin-left:8px;font-weight:400}
.cands-title{font-size:14px;color:var(--muted);margin:18px 0 10px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}
.card{position:relative;border:2px solid transparent;border-radius:12px;overflow:hidden;background:var(--panel);
  box-shadow:var(--shadow);cursor:pointer;transition:.15s}
.card:hover{transform:translateY(-2px)}
.card.liked{border-color:var(--heart)}
.card.final{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft),var(--shadow)}
.card .imgwrap{aspect-ratio:9/13;background:#ece5d8;display:flex;align-items:center;justify-content:center}
.card img{display:block;width:100%;height:100%;object-fit:cover}
.card .ph{color:#b3a892;font-size:12px;text-align:center;padding:14px;line-height:1.6}
.heart{position:absolute;top:8px;right:8px;z-index:3;width:34px;height:34px;border-radius:50%;border:0;
  background:rgba(255,255,255,.9);cursor:pointer;font-size:18px;line-height:34px;color:#c9bfb0;
  box-shadow:0 1px 4px rgba(0,0,0,.15);transition:.15s}
.heart:hover{transform:scale(1.1)}
.card.liked .heart{color:var(--heart)}
.card .meta{padding:8px 10px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:6px}
.card .finaltag{display:none;color:var(--accent);font-weight:600}
.card.final .finaltag{display:inline}
.notes{margin-top:22px;background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px;box-shadow:var(--shadow)}
.notes label{display:block;font-size:13px;color:var(--muted);margin-top:10px}
.notes label:first-child{margin-top:0}
.notes textarea{display:block;width:100%;min-height:50px;margin-top:6px;border:1px solid var(--line);
  border-radius:8px;padding:9px;font:inherit;resize:vertical}
.state-actions{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.empty{color:var(--muted);padding:60px 0;text-align:center}

/* ---- 右栏：镜头信息 ---- */
.aside-right{border-left:1px solid var(--line);background:var(--panel);overflow:auto;padding:16px 18px 60px}
.aside-right h3{margin:0 0 10px;font-size:13px;letter-spacing:1px;color:var(--muted)}
.aside-right .kv .k{font-size:12px;color:var(--muted);margin-top:13px}
.aside-right .kv .v{font-size:13px;line-height:1.6;margin-top:3px;color:#4a4338}
.aside-right .dia{background:var(--accent-soft);border:1px solid #cfe2da;border-radius:9px;
  padding:9px 11px;font-size:12px;line-height:1.6;color:#2c4a42;margin-top:6px;white-space:pre-wrap}

/* ---- 底部 ---- */
.footer-bar{position:fixed;left:230px;right:300px;bottom:0;z-index:20;display:flex;align-items:center;
  justify-content:space-between;gap:14px;padding:12px 24px;background:rgba(255,253,249,.92);
  backdrop-filter:blur(10px);border-top:1px solid var(--line)}
@media(max-width:1180px){.footer-bar{right:0;left:200px}}
.footer-bar .sum{font-size:13px;color:var(--muted)}
.footer-bar .sum b{color:var(--accent)}
.toast{position:fixed;bottom:70px;left:50%;transform:translateX(-50%);background:#26221c;color:#fff;
  padding:10px 18px;border-radius:8px;font-size:13px;opacity:0;transition:.25s;z-index:50;pointer-events:none}
.toast.show{opacity:1}
/* 放大预览 */
.lightbox{position:fixed;inset:0;background:rgba(20,16,10,.82);display:none;align-items:center;
  justify-content:center;z-index:90;cursor:zoom-out}
.lightbox.show{display:flex}
.lightbox img{max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 10px 40px rgba(0,0,0,.5)}
</style>
</head>
<body>
<header>
  <div class="title"><h1>人景合一 · 逐镜评审</h1><span class="proj" id="projName"></span></div>
  <div class="progress" id="progress"></div>
  <div><button class="btn primary" id="saveBtn">保存选择</button></div>
</header>

<div class="layout">
  <nav class="nav" id="nav"></nav>
  <main class="stage" id="stage"></main>
  <aside class="aside-right" id="aside"></aside>
</div>

<div class="footer-bar">
  <div class="sum" id="exportSum"></div>
  <button class="btn primary" id="exportBtn">导出镜头图</button>
</div>
<div class="toast" id="toast"></div>
<div class="lightbox" id="lightbox"><img id="lightboxImg" alt=""></div>

<script>
const STATE_KEY = "fusionState_v1";
let MANIFEST = null;
let STATE = loadState();
let CUR = null; // 当前镜号

function loadState(){
  try{ return JSON.parse(localStorage.getItem(STATE_KEY)) || blank(); }
  catch(e){ return blank(); }
}
function blank(){ return {likes:{}, finals:{}, notes:{}, exportRequested:false}; }
function persist(){ localStorage.setItem(STATE_KEY, JSON.stringify(STATE)); }

function esc(s){ return String(s??"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800); }

async function boot(){
  MANIFEST = await (await fetch("/api/manifest")).json();
  const ep = MANIFEST.episode ? ("第"+MANIFEST.episode+"集") : "";
  document.getElementById("projName").textContent =
    (MANIFEST.project? "· "+MANIFEST.project : "") + (MANIFEST.title? " 《"+MANIFEST.title+"》":"") + (ep? " "+ep:"");
  CUR = (MANIFEST.shots[0]||{}).no;
  renderNav(); renderStage(); renderAside(); renderProgress(); renderExport();
  document.getElementById("lightbox").onclick=()=>document.getElementById("lightbox").classList.remove("show");
}

function shots(){ return MANIFEST.shots||[]; }
function findShot(no){ return shots().find(s=>s.no===no); }
function totalShots(){ return shots().length; }
function confirmedCount(){ return Object.keys(STATE.finals).filter(k=>STATE.finals[k]).length; }
function shotImageIds(s){ return (s.candidates||[]).map(c=>c.id||c.path); }

/* ---- 左栏 ---- */
function renderNav(){
  const nav = document.getElementById("nav");
  const ep = MANIFEST.episode ? ("第"+MANIFEST.episode+"集") : "镜头列表";
  const links = shots().map(s=>{
    const active = s.no===CUR;
    const conf = !!STATE.finals[s.no];
    const review = !!(s.needsReview && s.needsReview.length);
    const purpose = (s.shot&&s.shot["画面目的"]) || "";
    return `<button class="shot-link ${active?'active':''} ${conf?'confirmed':''} ${review?'review':''}" data-no="${esc(s.no)}">
      <span class="sno">${esc(s.no)}</span><span class="purpose">${esc(purpose)}</span><span class="tick">✓</span></button>`;
  }).join("");
  nav.innerHTML = `<div class="ep-title">${esc(ep)} · ${totalShots()}镜</div>${links}`;
  nav.querySelectorAll(".shot-link").forEach(b=>b.onclick=()=>{
    CUR=b.dataset.no; renderNav(); renderStage(); renderAside();
  });
}

/* ---- 中栏 ---- */
function renderStage(){
  const stage = document.getElementById("stage");
  const s = findShot(CUR);
  if(!s){ stage.innerHTML = `<div class="empty">请选择左侧镜号</div>`; return; }
  const notes = STATE.notes[s.no] || {};
  const purpose = (s.shot&&s.shot["画面目的"])||"";

  // 参考图缩略图
  const refs = (s.refs||[]).map(r=>{
    const kindCls = r.kind==="scene"?"scene":r.kind==="prop"?"prop":"";
    const kindLab = r.kind==="role"?"人物":r.kind==="scene"?"场景":r.kind==="prop"?"道具":r.kind;
    const thumb = r.path
      ? `<img src="/asset/${encodeURI(r.path)}" alt="${esc(r.name)}" data-zoom="/asset/${encodeURI(r.path)}">`
      : `<div class="ph">未锁定<br>${esc(r.name)}</div>`;
    return `<div class="refchip"><div class="thumb">${thumb}</div>
      <span class="kindtag ${kindCls}">${esc(kindLab)}</span>
      <span class="lab" title="${esc(r.name)}">${esc(r.name)}</span></div>`;
  }).join("") || `<div class="empty" style="padding:10px 0">该镜暂无匹配参考图（可在 manifest 手动补 refs）</div>`;

  const reviewBanner = (s.needsReview && s.needsReview.length)
    ? `<div class="review-banner">⚠ 待校正：${esc(s.needsReview)}</div>` : "";

  const cands = (s.candidates||[]);
  const cardsHtml = cands.length
    ? `<div class="cards">${cands.map(c=>cardHtml(s,c)).join("")}</div>`
    : `<div class="empty">该镜暂无融合候选，先运行 fuse_shots.py 生成</div>`;

  stage.innerHTML = `
    <div class="crumb">第${esc(MANIFEST.episode||"")}集 / 镜 ${esc(s.no)}</div>
    <h2>镜 ${esc(s.no)}</h2>
    <div class="purpose-big">${esc(purpose)}</div>
    ${reviewBanner}
    <div class="refrow">${refs}</div>
    <div class="promptbox"><div class="lab">融合主提示词<span class="ro">只读 · 来自 07绘图提示词，本工具不改写</span></div>${esc(s.prompt)}</div>
    <div class="cands-title">融合候选（点图或 ❤️ 收藏，确认后心仪图即该镜镜头图）</div>
    ${cardsHtml}
    <div class="notes">
      <label>心仪的点 / 想保留的特征
        <textarea data-field="likes">${esc(notes.likes||"")}</textarea></label>
      <label>调整提示词（下一版方向，反馈给重出，不改原始提示词）
        <textarea data-field="adjustments">${esc(notes.adjustments||"")}</textarea></label>
      <div class="state-actions">
        <button class="btn" id="nextRound">进入下一版</button>
        <button class="btn primary" id="confirmShot">${STATE.finals[s.no]?"已确认 · 取消确认":"确认此镜镜头图"}</button>
      </div>
    </div>`;

  stage.querySelectorAll(".heart").forEach(h=>h.onclick=(e)=>{
    e.stopPropagation(); toggleLike(h.dataset.id); renderStage(); renderNav(); renderExport();
  });
  stage.querySelectorAll(".card").forEach(c=>c.onclick=()=>{
    toggleLike(c.dataset.id); renderStage(); renderNav(); renderExport();
  });
  stage.querySelectorAll("[data-zoom]").forEach(img=>img.onclick=(e)=>{
    e.stopPropagation();
    const lb=document.getElementById("lightbox"); document.getElementById("lightboxImg").src=img.dataset.zoom;
    lb.classList.add("show");
  });
  stage.querySelectorAll(".notes textarea").forEach(t=>t.oninput=()=>{
    STATE.notes[s.no]=STATE.notes[s.no]||{}; STATE.notes[s.no][t.dataset.field]=t.value; persist();
  });
  document.getElementById("confirmShot").onclick=()=>{
    if(!STATE.finals[s.no]){
      const ids = shotImageIds(s);
      const liked = ids.filter(id=>STATE.likes[id]).length;
      if(liked===0 && !confirm("该镜还没有 ❤️ 心仪候选，确认后将没有最终镜头图。仍要确认吗？")) return;
    }
    STATE.finals[s.no] = !STATE.finals[s.no]; persist();
    renderStage(); renderNav(); renderProgress(); renderExport();
    toast(STATE.finals[s.no]?"已确认该镜镜头图":"已取消确认");
  };
  document.getElementById("nextRound").onclick=()=>{
    STATE.notes[s.no]=STATE.notes[s.no]||{}; STATE.notes[s.no].nextRound=true; persist();
    toast("已标记『进入下一版』，保存后据此重出该镜");
  };
}

function cardHtml(s,c){
  const id = c.id || c.path;
  const liked = !!STATE.likes[id];
  const isFinal = !!STATE.finals[s.no] && liked;
  const inner = c.path
    ? `<img src="/asset/${encodeURI(c.path)}" alt="${esc(id)}" loading="lazy" data-zoom="/asset/${encodeURI(c.path)}">`
    : `<div class="ph">占位<br>${esc(c.note||id)}</div>`;
  return `<article class="card ${liked?'liked':''} ${isFinal?'final':''}" data-id="${esc(id)}">
    <button class="heart" data-id="${esc(id)}" title="心仪">${liked?'❤':'♡'}</button>
    <div class="imgwrap">${inner}</div>
    <div class="meta"><span>${esc(id)}</span><span class="finaltag">镜头图</span></div>
  </article>`;
}

function toggleLike(id){ STATE.likes[id]=!STATE.likes[id]; if(!STATE.likes[id]) delete STATE.likes[id]; persist(); }

/* ---- 右栏 ---- */
function renderAside(){
  const aside=document.getElementById("aside");
  const s=findShot(CUR);
  if(!s){ aside.innerHTML=""; return; }
  const sh=s.shot||{};
  const row=(k,v)=> v? `<div class="k">${esc(k)}</div><div class="v">${esc(v)}</div>`:"";
  const dia = sh["台词"] ? `<div class="k">台词</div><div class="dia">${esc(sh["台词"])}</div>` : "";
  aside.innerHTML = `
    <h3>镜头信息</h3>
    <div class="kv">
      ${row("景别", sh["景别"])}
      ${row("运镜", sh["运镜"])}
      ${row("时长", sh["时长"])}
      ${row("场景/镜头", sh["场景"])}
      ${row("光影色彩", sh["光影"])}
      ${dia}
    </div>`;
}

/* ---- 进度 & 导出 ---- */
function renderProgress(){
  document.getElementById("progress").innerHTML =
    `已确认 <b>${confirmedCount()}</b> / ${totalShots()} 镜`;
}
function renderExport(){
  const done=confirmedCount(), total=totalShots();
  const all=done===total && total>0;
  const btn=document.getElementById("exportBtn"); btn.disabled=!all;
  document.getElementById("exportSum").innerHTML = all
    ? `全部 <b>${total}</b> 镜已确认，可导出镜头图交接生视频`
    : `还差 ${total-done} 镜未确认（导出需全部确认）`;
}

/* ---- 保存 ---- */
function confirmedShots(){
  const out=[];
  for(const s of shots()){
    if(!STATE.finals[s.no]) continue;
    let fin=null;
    for(const c of (s.candidates||[])){
      if(STATE.likes[c.id||c.path]){ fin={id:c.id||c.path, path:c.path||""}; break; }
    }
    out.push({no:s.no, prompt:s.prompt, shot:s.shot||{}, refs:s.refs||[], finalCandidate:fin});
  }
  return out;
}
function buildPayload(extra){
  return Object.assign({
    project: MANIFEST.project||"", episode: MANIFEST.episode||"",
    likes:STATE.likes, finals:STATE.finals, notes:STATE.notes,
    exportRequested:STATE.exportRequested,
    confirmedShots:confirmedShots(),
    confirmedCount:confirmedCount(), totalShots:totalShots(),
  }, extra||{});
}
async function save(extra, okMsg){
  persist();
  const res=await fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify(buildPayload(extra))});
  toast(res.ok ? (okMsg||"已保存到 selection-state.json") : "保存失败");
  return res.ok;
}
document.getElementById("saveBtn").onclick=()=>save();
document.getElementById("exportBtn").onclick=async()=>{
  STATE.exportRequested=true; persist();
  const ok=await save({exportRequested:true}, "已记录『导出镜头图』意图，我会据此导出并交接生视频");
  if(ok) renderExport();
};

boot();
</script>
</body>
</html>"""


def make_handler(manifest_path: Path, output_path: Path, asset_root: Path):
    serve_root = asset_root.resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path in {"/", "/index.html"}:
                self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/manifest":
                self._send_json(load_manifest(manifest_path))
                return
            if path.startswith("/asset/"):
                rel = unquote(path[len("/asset/"):])
                # 路径相对【项目根】(serve_root)，无 ../，候选图(10_镜头图/...)与参考图(08_/02_...)都覆盖。
                target = (serve_root / rel).resolve()
                # 防护：必须落在项目根之内，拦截绝对路径或越界。
                try:
                    target.relative_to(serve_root)
                except ValueError:
                    self._send_json({"error": "forbidden", "path": rel}, 403)
                    return
                if not target.exists():
                    self._send_json({"error": "not found", "path": rel}, 404)
                    return
                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                self._send(target.read_bytes(), ctype)
                return
            self._send_json({"error": "not found"}, 404)

        def do_POST(self):
            if urlparse(self.path).path != "/api/save":
                self._send_json({"error": "not found"}, 404)
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "path": str(output_path)})

        def _send(self, body: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, data: dict, status: int = 200):
            self._send(json.dumps(data, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8", status)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="人景合一逐镜评审 Gallery 服务器")
    parser.add_argument("--manifest", required=True, help="shot-manifest.json 路径")
    parser.add_argument("--out", default="selection-state.json", help="保存选择状态的文件名")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8792)
    parser.add_argument("--asset-root", default="",
                        help="参考图允许的根目录，默认 manifest 目录的父级（项目根）。"
                             "参考图常在 08_生成图片/02_世界观 等兄弟目录，需放行而仍拦截项目外越界。")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    output_path = (manifest_path.parent / args.out).resolve()
    asset_root = Path(args.asset_root).resolve() if args.asset_root else manifest_path.parent.parent
    load_manifest(manifest_path)  # 启动即校验
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manifest_path, output_path, asset_root))
    print(f"人景合一 Gallery: http://{args.host}:{args.port}/")
    print(f"保存目标: {output_path}")
    print(f"参考图根域: {asset_root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
