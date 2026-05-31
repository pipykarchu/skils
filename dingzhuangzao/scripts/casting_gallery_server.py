#!/usr/bin/env python3
"""定妆造选择 Gallery —— 三栏布局本地评审服务器。

左栏：角色按模块分组，可展开 -> 不同时期。
中栏：某时期角色，上下两行（Image2 / MJ），右上角整体基调风格，图片右上角 ❤️ 心仪标记，
      每个时期有「确认造型」按钮。
右栏：该时期角色的世界观/场景背景说明。
底部：所有角色确认后可「生成总览图」（仅记录意图，真正出图由 Codex/Claude 下一步执行）。

这是可复用的起点脚本。把它拷进项目输出目录，或用 --manifest 指向项目 manifest 运行。
本脚本本身不调用任何出图 API；它只负责评审、收藏、确认与意图记录。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>定妆造选择</title>
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

.layout{display:grid;grid-template-columns:268px 1fr 320px;gap:0;height:calc(100vh - 59px)}
@media(max-width:1180px){.layout{grid-template-columns:240px 1fr}.aside-right{display:none}}

/* ---- 左栏：角色导航 ---- */
.nav{border-right:1px solid var(--line);overflow:auto;padding:14px 10px 60px;background:#efe9e0}
.module{margin-bottom:14px}
.module-title{font-size:12px;letter-spacing:1px;color:var(--muted);padding:4px 10px;text-transform:none}
.role-item>button.role-toggle{width:100%;display:flex;align-items:center;justify-content:space-between;
  gap:8px;padding:9px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;font:inherit;
  color:var(--ink);text-align:left}
.role-item>button.role-toggle:hover{background:#e7e0d4}
.role-item .caret{transition:.2s;color:var(--muted);font-size:11px}
.role-item.open .caret{transform:rotate(90deg)}
.role-item .role-name{font-weight:600;font-size:14px}
.role-item .role-dot{width:8px;height:8px;border-radius:50%;background:#cbc3b4;flex:none}
.role-item.has-confirm .role-dot{background:var(--accent)}
.states{display:none;padding:2px 0 6px 12px}
.role-item.open .states{display:block}
.state-link{display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;
  padding:7px 10px;border:0;border-radius:7px;background:transparent;cursor:pointer;font:inherit;
  color:var(--muted);text-align:left;font-size:13px}
.state-link:hover{background:#e7e0d4;color:var(--ink)}
.state-link.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.state-link .tick{font-size:12px;color:var(--accent);opacity:0}
.state-link.confirmed .tick{opacity:1}

/* ---- 中栏：候选评审 ---- */
.stage{overflow:auto;padding:22px 26px 90px;position:relative}
.stage .crumb{font-size:13px;color:var(--muted);margin-bottom:4px}
.stage .head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:6px}
.stage h2{margin:0;font-size:22px}
.stage .age{font-size:13px;color:var(--muted);margin-top:4px}
.tone{flex:none;max-width:300px;text-align:right;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:10px 13px;box-shadow:var(--shadow)}
.tone .lab{font-size:11px;letter-spacing:1px;color:var(--muted);margin-bottom:3px}
.tone .val{font-size:13px;line-height:1.5}
.row{margin-top:22px}
.row-title{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--muted);margin-bottom:10px}
.row-title .eng{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:6px;
  font-size:12px;font-weight:600;background:#eee5d6;color:#6b5d45}
.row-title .eng.mj{background:#e7e0f2;color:#5a4a86}
.row-title .eng.image2{background:#d9ece5;color:#2c6356}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}
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
.notes{margin-top:24px;background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:14px 16px;box-shadow:var(--shadow)}
.notes label{display:block;font-size:13px;color:var(--muted);margin-top:10px}
.notes label:first-child{margin-top:0}
.notes textarea{display:block;width:100%;min-height:56px;margin-top:6px;border:1px solid var(--line);
  border-radius:8px;padding:9px;font:inherit;resize:vertical}
.state-actions{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
.empty{color:var(--muted);padding:60px 0;text-align:center}

/* ---- 右栏：世界观场景 ---- */
.aside-right{border-left:1px solid var(--line);background:var(--panel);overflow:auto;padding:20px 18px 60px}
.aside-right h3{margin:0 0 6px;font-size:13px;letter-spacing:1px;color:var(--muted)}
.aside-right .era{font-size:15px;font-weight:600;margin:0 0 10px}
.aside-right .wv{font-size:13px;line-height:1.75;color:#4a4338;white-space:pre-wrap}
.aside-right .kv{margin-top:16px}
.aside-right .kv .k{font-size:12px;color:var(--muted);margin-top:12px}
.aside-right .kv .v{font-size:13px;line-height:1.6;margin-top:3px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.tag{font-size:12px;padding:3px 9px;border-radius:999px;background:#f0ebe1;color:#6b6052;border:1px solid var(--line)}

/* ---- 底部总览栏 ---- */
.footer-bar{position:fixed;left:268px;right:320px;bottom:0;z-index:20;display:flex;align-items:center;
  justify-content:space-between;gap:14px;padding:12px 26px;background:rgba(255,253,249,.92);
  backdrop-filter:blur(10px);border-top:1px solid var(--line)}
@media(max-width:1180px){.footer-bar{right:0;left:240px}}
.footer-bar .sum{font-size:13px;color:var(--muted)}
.footer-bar .sum b{color:var(--accent)}
.toast{position:fixed;bottom:70px;left:50%;transform:translateX(-50%);background:#26221c;color:#fff;
  padding:10px 18px;border-radius:8px;font-size:13px;opacity:0;transition:.25s;z-index:50;pointer-events:none}
.toast.show{opacity:1}
</style>
</head>
<body>
<header>
  <div class="title"><h1>定妆造选择</h1><span class="proj" id="projName"></span></div>
  <div class="progress" id="progress"></div>
  <div><button class="btn primary" id="saveBtn">保存选择</button></div>
</header>

<div class="layout">
  <nav class="nav" id="nav"></nav>
  <main class="stage" id="stage"></main>
  <aside class="aside-right" id="aside"></aside>
</div>

<div class="footer-bar">
  <div class="sum" id="overviewSum"></div>
  <button class="btn primary" id="overviewBtn">生成总览图</button>
</div>
<div class="toast" id="toast"></div>

<script>
const STATE_KEY = "castingState_v2";
let MANIFEST = null;
let STATE = loadState();
let CUR = {role:null, state:null};

function loadState(){
  try{ return JSON.parse(localStorage.getItem(STATE_KEY)) || blank(); }
  catch(e){ return blank(); }
}
function blank(){ return {likes:{}, finals:{}, notes:{}, overviewRequested:false}; }
function persist(){ localStorage.setItem(STATE_KEY, JSON.stringify(STATE)); }

function keyOf(role, state){ return role + "::" + state; }
function esc(s){ return String(s??"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800); }

async function boot(){
  MANIFEST = await (await fetch("/api/manifest")).json();
  document.getElementById("projName").textContent = MANIFEST.project ? "· " + MANIFEST.project : "";
  // 默认选第一个角色第一时期
  const firstRole = (firstModuleRole());
  if(firstRole){ CUR.role = firstRole.role.name; CUR.state = (firstRole.role.states[0]||{}).name; }
  renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
}

function* iterRoles(){
  for(const mod of (MANIFEST.modules||[{name:"", roles:MANIFEST.roles||[]}]))
    for(const role of (mod.roles||[])) yield {mod, role};
}
function firstModuleRole(){ for(const r of iterRoles()) return r; return null; }
function findRole(name){ for(const {role} of iterRoles()) if(role.name===name) return role; return null; }
function findState(role, sname){ return (role.states||[]).find(s=>s.name===sname); }

function totalStates(){ let n=0; for(const {role} of iterRoles()) n += (role.states||[]).length; return n; }
function confirmedCount(){ return Object.keys(STATE.finals).filter(k=>STATE.finals[k]).length; }

/* ---------- 左栏 ---------- */
function renderNav(){
  const nav = document.getElementById("nav");
  const mods = MANIFEST.modules || [{name:"", roles:MANIFEST.roles||[]}];
  nav.innerHTML = mods.map(mod=>{
    const roles = (mod.roles||[]).map(role=>{
      const open = role.name===CUR.role;
      const hasConfirm = (role.states||[]).some(s=>STATE.finals[keyOf(role.name,s.name)]);
      const states = (role.states||[]).map(s=>{
        const k = keyOf(role.name, s.name);
        const active = role.name===CUR.role && s.name===CUR.state;
        const conf = !!STATE.finals[k];
        return `<button class="state-link ${active?'active':''} ${conf?'confirmed':''}"
                   data-role="${esc(role.name)}" data-state="${esc(s.name)}">
                  <span>${esc(s.name)}</span><span class="tick">✓</span></button>`;
      }).join("");
      return `<div class="role-item ${open?'open':''} ${hasConfirm?'has-confirm':''}" data-role="${esc(role.name)}">
        <button class="role-toggle" data-role="${esc(role.name)}">
          <span style="display:flex;align-items:center;gap:8px">
            <span class="role-dot"></span><span class="role-name">${esc(role.name)}</span>
          </span><span class="caret">▶</span>
        </button>
        <div class="states">${states}</div>
      </div>`;
    }).join("");
    const title = mod.name ? `<div class="module-title">${esc(mod.name)}</div>` : "";
    return `<div class="module">${title}${roles}</div>`;
  }).join("");

  nav.querySelectorAll(".role-toggle").forEach(b=>b.onclick=()=>{
    const r = b.dataset.role;
    if(CUR.role===r){ // 折叠当前
      const item = b.closest(".role-item"); item.classList.toggle("open");
      return;
    }
    const role = findRole(r); CUR.role = r; CUR.state = (role.states[0]||{}).name;
    renderNav(); renderStage(); renderAside();
  });
  nav.querySelectorAll(".state-link").forEach(b=>b.onclick=()=>{
    CUR.role = b.dataset.role; CUR.state = b.dataset.state;
    renderNav(); renderStage(); renderAside();
  });
}

/* ---------- 中栏 ---------- */
function renderStage(){
  const stage = document.getElementById("stage");
  const role = findRole(CUR.role); const st = role && findState(role, CUR.state);
  if(!role || !st){ stage.innerHTML = `<div class="empty">请选择左侧角色与时期</div>`; return; }
  const tone = st.styleTone || role.styleTone || MANIFEST.styleTone || "（未设定整体基调）";
  const groups = normalizeGroups(st);
  const k = keyOf(role.name, st.name);
  const notes = STATE.notes[k] || {};

  const rowsHtml = groups.map(g=>{
    const engClass = (g.engine||"").toLowerCase().includes("mj") ? "mj" : "image2";
    const cards = (g.images||[]).map(img=>cardHtml(role, st, g, img)).join("");
    const inner = (g.images&&g.images.length) ? `<div class="cards">${cards}</div>`
      : `<div class="empty">该行暂无候选图，待生成</div>`;
    return `<div class="row">
      <div class="row-title"><span class="eng ${engClass}">${esc(g.engine||"")}</span>
        <span>${esc(g.label||"候选")}</span></div>${inner}</div>`;
  }).join("");

  stage.innerHTML = `
    <div class="crumb">${esc(findModuleName(role.name))} / ${esc(role.name)}</div>
    <div class="head">
      <div><h2>${esc(role.name)} · ${esc(st.name)}</h2>
        <div class="age">${esc(st.age||role.age||"")}</div></div>
      <div class="tone"><div class="lab">整体基调风格</div><div class="val">${esc(tone)}</div></div>
    </div>
    ${rowsHtml}
    <div class="notes">
      <label>心仪的点 / 想保留的特征
        <textarea data-field="likes">${esc(notes.likes||"")}</textarea></label>
      <label>调整提示词（下一版方向）
        <textarea data-field="adjustments">${esc(notes.adjustments||"")}</textarea></label>
      <div class="state-actions">
        <button class="btn" id="nextRound">进入下一版</button>
        <button class="btn primary" id="confirmLook">${STATE.finals[k]?"已确认 · 取消确认":"确认此时期造型"}</button>
      </div>
    </div>`;

  stage.querySelectorAll(".heart").forEach(h=>h.onclick=(e)=>{
    e.stopPropagation();
    toggleLike(h.dataset.id); renderStage(); renderNav(); renderOverview();
  });
  stage.querySelectorAll(".card").forEach(c=>c.onclick=()=>{
    toggleLike(c.dataset.id); renderStage(); renderNav(); renderOverview();
  });
  stage.querySelectorAll(".notes textarea").forEach(t=>t.oninput=()=>{
    STATE.notes[k] = STATE.notes[k]||{}; STATE.notes[k][t.dataset.field]=t.value; persist();
  });
  document.getElementById("confirmLook").onclick=()=>{
    if(!STATE.finals[k]){
      // 确认前检查该时期是否有心仪图作为最终参考
      const ids = stateImageIds(role, st);
      const likedHere = ids.filter(id=>STATE.likes[id]).length;
      if(likedHere===0 && !confirm("该时期还没有 ❤️ 心仪图，确认后将没有最终参考图。仍要确认吗？")) return;
    }
    STATE.finals[k] = !STATE.finals[k]; persist();
    renderStage(); renderNav(); renderProgress(); renderOverview();
    toast(STATE.finals[k]?"已确认该时期造型":"已取消确认");
  };
  document.getElementById("nextRound").onclick=()=>{
    STATE.notes[k]=STATE.notes[k]||{}; STATE.notes[k].nextRound=true; persist();
    toast("已标记『进入下一版』，保存后我会据此生成新一轮");
  };
}

function cardHtml(role, st, group, img){
  const id = img.id || img.path;
  const liked = !!STATE.likes[id];
  const k = keyOf(role.name, st.name);
  // 已确认时期里，被心仪的图即为该时期的最终参考图
  const isFinal = !!STATE.finals[k] && liked;
  const inner = img.path
    ? `<img src="/asset/${encodeURI(img.path)}" alt="${esc(id)}" loading="lazy">`
    : `<div class="ph">占位<br>${esc(img.note||id)}</div>`;
  return `<article class="card ${liked?'liked':''} ${isFinal?'final':''}" data-id="${esc(id)}">
    <button class="heart" data-id="${esc(id)}" title="心仪">${liked?'❤':'♡'}</button>
    <div class="imgwrap">${inner}</div>
    <div class="meta"><span>${esc(id)}</span><span class="finaltag">最终</span></div>
  </article>`;
}

function toggleLike(id){ STATE.likes[id] = !STATE.likes[id]; if(!STATE.likes[id]) delete STATE.likes[id]; persist(); }

function normalizeGroups(st){
  // 保证顺序：Image2 在上，MJ 在下；缺失则补空行
  const gs = st.groups || [];
  const find = (frag)=>gs.find(g=>(g.engine||"").toLowerCase().includes(frag));
  const i2 = find("image2") || {engine:"Image2", label:"候选", images:[]};
  const mj = find("mj") || {engine:"MJ", label:"候选", images:[]};
  const rest = gs.filter(g=>g!==i2 && g!==mj);
  return [i2, mj, ...rest];
}
function stateImageIds(role, st){
  const ids=[];
  for(const g of (st.groups||[])) for(const im of (g.images||[])) ids.push(im.id||im.path);
  return ids;
}
function findModuleName(roleName){
  for(const {mod, role} of iterRoles()) if(role.name===roleName) return mod.name||"";
  return "";
}

/* ---------- 右栏 ---------- */
function renderAside(){
  const aside = document.getElementById("aside");
  const role = findRole(CUR.role); const st = role && findState(role, CUR.state);
  if(!role || !st){ aside.innerHTML=""; return; }
  const wv = st.worldview || {};
  const tags = (wv.keywords||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join("");
  aside.innerHTML = `
    <h3>世界观 · 场景背景</h3>
    <div class="era">${esc(wv.era || st.name)}</div>
    <div class="wv">${esc(wv.scene || "（该时期暂无场景说明，可在 manifest 的 state.worldview 补充）")}</div>
    ${tags?`<div class="tags">${tags}</div>`:""}
    <div class="kv">
      ${wv.space?`<div class="k">空间</div><div class="v">${esc(wv.space)}</div>`:""}
      ${wv.props?`<div class="k">道具</div><div class="v">${esc(wv.props)}</div>`:""}
      ${wv.costume?`<div class="k">服装</div><div class="v">${esc(wv.costume)}</div>`:""}
      ${wv.light?`<div class="k">光线</div><div class="v">${esc(wv.light)}</div>`:""}
      ${wv.forbid?`<div class="k">禁止</div><div class="v">${esc(wv.forbid)}</div>`:""}
    </div>`;
}

/* ---------- 进度 & 总览 ---------- */
function renderProgress(){
  document.getElementById("progress").innerHTML =
    `已确认 <b>${confirmedCount()}</b> / ${totalStates()} 个时期造型`;
}
function renderOverview(){
  const done = confirmedCount(), total = totalStates();
  const all = done===total && total>0;
  const btn = document.getElementById("overviewBtn");
  btn.disabled = !all;
  document.getElementById("overviewSum").innerHTML = all
    ? `全部 <b>${total}</b> 个时期造型已确认，可生成总览图`
    : `还差 ${total-done} 个时期未确认（总览图需全部确认后生成）`;
}

/* ---------- 保存 ---------- */
function imgById(id){
  for(const {role} of iterRoles())
    for(const st of (role.states||[]))
      for(const g of (st.groups||[]))
        for(const im of (g.images||[]))
          if((im.id||im.path)===id) return {role, st, g, im};
  return null;
}
function confirmedLooks(){
  // 供下一步出图：每个已确认时期的最终参考图（= 该时期被心仪的图）
  const out=[];
  for(const {mod, role} of iterRoles())
    for(const st of (role.states||[])){
      const k = keyOf(role.name, st.name);
      if(!STATE.finals[k]) continue;
      const refs=[];
      for(const g of (st.groups||[]))
        for(const im of (g.images||[]))
          if(STATE.likes[im.id||im.path])
            refs.push({engine:g.engine, id:im.id||im.path, path:im.path||""});
      out.push({module:mod.name||"", role:role.name, state:st.name,
                era:(st.worldview||{}).era||"", styleTone: st.styleTone||role.styleTone||MANIFEST.styleTone||"",
                refs});
    }
  return out;
}
function buildPayload(extra){
  return Object.assign({
    project: MANIFEST.project || "",
    round: MANIFEST.round || 1,
    likes: STATE.likes, finals: STATE.finals, notes: STATE.notes,
    overviewRequested: STATE.overviewRequested,
    confirmedLooks: confirmedLooks(),
    confirmedCount: confirmedCount(), totalStates: totalStates(),
  }, extra||{});
}
async function save(extra, okMsg){
  persist();
  const res = await fetch("/api/save", {method:"POST",
    headers:{"Content-Type":"application/json"}, body:JSON.stringify(buildPayload(extra))});
  toast(res.ok ? (okMsg||"已保存到 selection-state.json") : "保存失败");
  return res.ok;
}
document.getElementById("saveBtn").onclick=()=>save();
document.getElementById("overviewBtn").onclick=async ()=>{
  STATE.overviewRequested = true; persist();
  const ok = await save({overviewRequested:true}, "已记录『生成总览图』意图，保存成功，我会据此出图");
  if(ok) renderOverview();
};

boot();
</script>
</body>
</html>"""


def make_handler(manifest_path: Path, output_path: Path):
    root = manifest_path.parent.resolve()
    manifest = load_manifest(manifest_path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # 静音默认日志
            pass

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            if path in {"/", "/index.html"}:
                self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/manifest":
                # 每次重新读盘，便于热更新 manifest
                data = load_manifest(manifest_path)
                self._send_json(data)
                return
            if path.startswith("/asset/"):
                rel = unquote(path[len("/asset/"):])
                target = (root / rel).resolve()
                if not str(target).startswith(str(root)) or not target.exists():
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
    parser = argparse.ArgumentParser(description="定妆造选择 Gallery 服务器")
    parser.add_argument("--manifest", required=True, help="manifest.json 路径")
    parser.add_argument("--out", default="selection-state.json", help="保存选择状态的文件名")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    output_path = (manifest_path.parent / args.out).resolve()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manifest_path, output_path))
    print(f"定妆造 Gallery: http://{args.host}:{args.port}/")
    print(f"保存目标: {output_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
