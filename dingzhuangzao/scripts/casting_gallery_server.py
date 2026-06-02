#!/usr/bin/env python3
"""视觉定版 Gallery —— 三栏布局本地评审服务器。

左栏：按模块分组，可展开 -> 条目 -> 状态/变体。
中栏：导入 / Gemini Image / Image2 / MJ 等候选行，图片右上角 ❤️ 心仪标记，
      左上角可锁脸/身体/衣服等局部参考，每个状态有「确认造型」按钮。
右栏：该状态的世界观/场景背景说明和可复制提示词。
底部：全部确认后可「生成总览图」（仅记录意图，真正出图由 Codex/Claude 下一步执行）。

这是人物定妆、场景美术、道具定版共用的本地评审脚本。把它拷进项目输出目录，
或用 --manifest 指向项目 manifest 运行。
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
<title>视觉定版评审</title>
<style>
:root{
  --bg:#f4f0e9; --panel:#fffdf9; --line:#ddd6ca; --ink:#26221c; --muted:#7c7264;
  --accent:#24695c; --accent-soft:#e2efe9; --warm:#b35a32; --heart:#e0395e;
  --nav-bg:#efe9e0; --nav-hover:#e7e0d4; --header-bg:rgba(244,240,233,.86);
  --slot-bg:#faf7f1; --imgwrap:#ece5d8;
  --shadow:0 1px 2px rgba(40,30,15,.06),0 8px 24px rgba(40,30,15,.06);
}
[data-theme="dark"]{
  --bg:#16181c; --panel:#1f2329; --line:#343a42; --ink:#e6e1d8; --muted:#9aa0a8;
  --accent:#4fb39d; --accent-soft:#1d3a35; --warm:#d3805a; --heart:#ff5f7e;
  --nav-bg:#1a1d22; --nav-hover:#262b32; --header-bg:rgba(22,24,28,.86);
  --slot-bg:#23272e; --imgwrap:#2a2f37;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
body{margin:0;font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);transition:background .2s,color .2s}
header{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;
  gap:16px;padding:12px 22px;background:var(--header-bg);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--line)}
header .title{display:flex;align-items:baseline;gap:12px}
header h1{margin:0;font-size:18px;letter-spacing:.5px}
header .proj{font-size:13px;color:var(--muted)}
header .progress{font-size:13px;color:var(--muted)}
header .progress b{color:var(--accent)}
header .head-right{display:flex;align-items:center;gap:10px}
.theme-toggle{width:34px;height:34px;border:1px solid var(--line);border-radius:7px;background:var(--panel);
  cursor:pointer;font-size:16px;line-height:1;color:var(--ink)}
.theme-toggle:hover{border-color:var(--accent)}
.btn{height:34px;padding:0 14px;border:1px solid var(--line);border-radius:7px;background:var(--panel);
  cursor:pointer;font:inherit;color:var(--ink);transition:.15s}
.btn:hover{border-color:#c3bbac}
.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.primary:hover{filter:brightness(1.05)}
.btn:disabled{opacity:.45;cursor:not-allowed}

.layout{display:grid;grid-template-columns:268px 1fr 320px;gap:0;height:calc(100vh - 59px)}
@media(max-width:1180px){.layout{grid-template-columns:240px 1fr}.aside-right{display:none}}

/* ---- 左栏：角色导航 ---- */
.nav{border-right:1px solid var(--line);overflow:auto;padding:14px 10px 60px;background:var(--nav-bg)}
.module{margin-bottom:14px}
.module-title{position:sticky;top:0;z-index:5;font-size:12px;letter-spacing:1px;color:var(--muted);
  padding:6px 10px;background:var(--nav-bg);border-bottom:1px solid var(--line)}
.role-item>button.role-toggle{width:100%;display:flex;align-items:center;justify-content:space-between;
  gap:8px;padding:9px 10px;border:0;border-radius:8px;background:transparent;cursor:pointer;font:inherit;
  color:var(--ink);text-align:left}
.role-item>button.role-toggle:hover{background:var(--nav-hover)}
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
.state-link:hover{background:var(--nav-hover);color:var(--ink)}
.state-link.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.state-link .tick{font-size:12px;color:var(--accent);opacity:0}
.state-link.confirmed .tick{opacity:1}

/* ---- 中栏：候选评审 ---- */
.stage{overflow:auto;padding:22px 26px 90px;position:relative}
.stage .crumb{font-size:13px;color:var(--muted);margin-bottom:4px}
.stage .head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:6px}
.stage h2{margin:0;font-size:22px}
.stage .age{font-size:13px;color:var(--muted);margin-top:4px}
.head-actions{flex:none}
.pickbar{margin:10px 0;padding:9px 13px;background:var(--accent-soft);border:1px solid var(--accent);
  border-radius:8px;font-size:13px;color:var(--accent)}
.row{margin-top:22px}
.row-title{display:flex;align-items:center;gap:8px;font-size:14px;color:var(--muted);margin-bottom:10px}
.row-title .eng{display:inline-flex;align-items:center;height:22px;padding:0 9px;border-radius:6px;
  font-size:12px;font-weight:600;background:#eee5d6;color:#6b5d45}
.row-title .eng.mj{background:#e7e0f2;color:#5a4a86}
.row-title .eng.image2{background:#d9ece5;color:#2c6356}
.row-title .eng.gemini{background:#dce8ff;color:#315f9f}
.row-title .eng.imp{background:#fbe7cf;color:#9a6322}
[data-theme="dark"] .row-title .eng.image2{background:#1d3a35;color:#7fd3bf}
[data-theme="dark"] .row-title .eng.mj{background:#312a4a;color:#b9a8e6}
[data-theme="dark"] .row-title .eng.gemini{background:#223452;color:#9fc2ff}
[data-theme="dark"] .row-title .eng.imp{background:#3a2c19;color:#e0a86a}
.gen-slot{border:1.5px dashed var(--line);border-radius:12px;padding:26px;text-align:center;
  color:var(--muted);cursor:pointer;font-size:13px;transition:.15s;background:var(--slot-bg)}
.gen-slot:hover{border-color:var(--accent);color:var(--accent)}
.gen-slot.marked{border-color:var(--accent);border-style:solid;color:var(--accent);background:var(--accent-soft)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}
.card{position:relative;border:2px solid transparent;border-radius:12px;overflow:hidden;background:var(--panel);
  box-shadow:var(--shadow);cursor:pointer;transition:.15s}
.card:hover{transform:translateY(-2px)}
.card.liked{border-color:var(--heart)}
.card.final{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft),var(--shadow)}
.card.pickable{outline:2px dashed var(--accent);outline-offset:2px}
.card .imgwrap{aspect-ratio:9/13;background:var(--imgwrap);display:flex;align-items:center;justify-content:center}
.card img{display:block;width:100%;height:100%;object-fit:cover}
.card .ph{color:var(--muted);font-size:12px;text-align:center;padding:14px;line-height:1.6;opacity:.8}
.heart{position:absolute;top:8px;right:8px;z-index:3;width:34px;height:34px;border-radius:50%;border:0;
  background:rgba(255,255,255,.9);cursor:pointer;font-size:18px;line-height:34px;color:#c9bfb0;
  box-shadow:0 1px 4px rgba(0,0,0,.15);transition:.15s}
[data-theme="dark"] .heart{background:rgba(20,22,26,.85);color:#6a7079}
.heart:hover{transform:scale(1.1)}
.card.liked .heart{color:var(--heart)}
.locks{position:absolute;top:8px;left:8px;z-index:4;display:flex;gap:5px}
.lockbtn{height:26px;min-width:30px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.92);
  color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.12)}
[data-theme="dark"] .lockbtn{background:rgba(20,22,26,.86)}
.lockbtn.active{border-color:var(--accent);background:var(--accent);color:#fff}
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
.aside-right{border-left:1px solid var(--line);background:var(--panel);overflow:auto;padding:16px 18px 60px}
.tone{background:var(--accent-soft);border:1px solid var(--line);border-radius:10px;padding:9px 12px;margin-bottom:16px}
.tone .lab{font-size:11px;letter-spacing:1px;color:var(--accent);margin-bottom:3px;font-weight:600}
.tone .val{font-size:12px;line-height:1.55;color:var(--ink);opacity:.85}
.aside-right h3{margin:0 0 6px;font-size:13px;letter-spacing:1px;color:var(--muted)}
.aside-right .era{font-size:15px;font-weight:600;margin:0 0 10px}
.aside-right .wv{font-size:13px;line-height:1.75;color:var(--ink);opacity:.85;white-space:pre-wrap}
.aside-right .kv{margin-top:16px}
.aside-right .kv .k{font-size:12px;color:var(--muted);margin-top:12px}
.aside-right .kv .v{font-size:13px;line-height:1.6;margin-top:3px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.tag{font-size:12px;padding:3px 9px;border-radius:999px;background:var(--nav-bg);color:var(--muted);border:1px solid var(--line)}
/* 定妆提示词区块 */
.prompt-block{margin-top:20px;border-top:1px solid var(--line);padding-top:14px}
.prompt-block h3{margin:0 0 10px}
.prompt-block .pmuted{font-size:11px;color:var(--muted);font-weight:400;letter-spacing:0}
.pgroup{margin-bottom:12px}
.phead{display:flex;align-items:center;justify-content:space-between;margin-bottom:5px}
.phead .eng{display:inline-flex;align-items:center;height:20px;padding:0 8px;border-radius:5px;font-size:11px;font-weight:600}
.phead .eng.image2{background:#d9ece5;color:#2c6356}
.phead .eng.gemini{background:#dce8ff;color:#315f9f}
.phead .eng.mj{background:#e7e0f2;color:#5a4a86}
[data-theme="dark"] .phead .eng.image2{background:#1d3a35;color:#7fd3bf}
[data-theme="dark"] .phead .eng.gemini{background:#223452;color:#9fc2ff}
[data-theme="dark"] .phead .eng.mj{background:#312a4a;color:#b9a8e6}
.copy{height:22px;padding:0 9px;font-size:12px;border:1px solid var(--line);border-radius:5px;background:var(--panel);cursor:pointer;color:var(--ink)}
.copy:hover{border-color:var(--accent)}
.ptext{margin:0;max-height:220px;overflow:auto;background:var(--slot-bg);border:1px solid var(--line);border-radius:8px;
  padding:9px 10px;font-size:11.5px;line-height:1.6;white-space:pre-wrap;word-break:break-word;
  font-family:"Microsoft YaHei",monospace;color:var(--ink);opacity:.9}
.pempty{font-size:12px;color:var(--muted);line-height:1.6}

/* ---- 底部总览栏 ---- */
.footer-bar{position:fixed;left:268px;right:320px;bottom:0;z-index:20;display:flex;align-items:center;
  justify-content:space-between;gap:14px;padding:12px 26px;background:var(--header-bg);
  backdrop-filter:blur(10px);border-top:1px solid var(--line)}
@media(max-width:1180px){.footer-bar{right:0;left:240px}}
.footer-bar .sum{font-size:13px;color:var(--muted)}
.footer-bar .sum b{color:var(--accent)}
.toast{position:fixed;bottom:70px;left:50%;transform:translateX(-50%);background:var(--ink);color:var(--bg);
  padding:10px 18px;border-radius:8px;font-size:13px;opacity:0;transition:.25s;z-index:50;pointer-events:none}
.toast.show{opacity:1}
</style>
</head>
<body>
<header>
  <div class="title"><h1 id="pageTitle">视觉定版评审</h1><span class="proj" id="projName"></span></div>
  <div class="progress" id="progress"></div>
  <div class="head-right">
    <button class="theme-toggle" id="themeToggle" title="切换深色/浅色">🌙</button>
    <button class="btn primary" id="saveBtn">保存选择</button>
  </div>
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
let PICK_FINAL = null;   // 正在为哪个时期点选最终（key 或 null）

function loadState(){
  try{ const s = JSON.parse(localStorage.getItem(STATE_KEY)) || blank();
    return Object.assign(blank(), s); }
  catch(e){ return blank(); }
}
function blank(){ return {likes:{}, locks:{}, finals:{}, notes:{}, gen:{}, overviewRequested:false}; }
function persist(){ localStorage.setItem(STATE_KEY, JSON.stringify(STATE)); }
// 关键操作自动保存：写本地 + 后台落盘，无需手动点「保存选择」
function autosave(){ persist(); save(null, null, true); }

function keyOf(role, state){ return role + "::" + state; }
function esc(s){ return String(s??"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800); }

async function boot(){
  MANIFEST = await (await fetch("/api/manifest")).json();
  document.getElementById("pageTitle").textContent = MANIFEST.pageTitle || "视觉定版评审";
  document.title = MANIFEST.pageTitle || "视觉定版评审";
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
  const groups = normalizeGroups(st);
  const k = keyOf(role.name, st.name);
  const notes = STATE.notes[k] || {};

  const rowsHtml = groups.map(g=>{
    const eng = (g.engine||"");
    const lowEng = eng.toLowerCase();
    const engClass = lowEng.includes("mj") ? "mj" : (lowEng.includes("gemini") ? "gemini" : (eng==="导入" ? "imp" : "image2"));
    const hasImg = g.images && g.images.length;
    const cards = (g.images||[]).map(img=>cardHtml(role, st, g, img)).join("");
    let inner;
    if(hasImg){
      inner = `<div class="cards">${cards}</div>`;
    } else if(eng==="导入"){
      inner = `<div class="empty">点右上角「导入图」上传</div>`;
    } else {
      // 空的 Image2/MJ 行：点击记录待生成意图
      const marked = (STATE.gen&&STATE.gen[`${k}::${eng}`]);
      inner = `<div class="gen-slot ${marked?'marked':''}" data-gen-engine="${esc(eng)}">
        ${marked?'已标记待生成 ✓（默认 Gemini Image，保存后由 AI 出图）':'＋ 点此生成/标记「'+esc(eng)+' 候选」'}</div>`;
    }
    return `<div class="row">
      <div class="row-title"><span class="eng ${engClass}">${esc(eng)}</span>
        <span>${esc(g.label||"候选")}</span></div>${inner}</div>`;
  }).join("");

  const picking = (PICK_FINAL===k);
  stage.innerHTML = `
    <div class="crumb">${esc(findModuleName(role.name))} / ${esc(role.name)}</div>
    <div class="head">
      <div><h2>${esc(role.name)} · ${esc(st.name)}</h2>
        <div class="age">${esc(st.age||role.age||"")}</div></div>
      <div class="head-actions">
        <button class="btn" id="importBtn">导入图（≤4张）</button>
        <input type="file" id="importInput" accept="image/*" multiple hidden>
      </div>
    </div>
    ${picking?`<div class="pickbar">从 ❤️ 心仪图中点选一张作为该时期最终造型（再次点「确认」可取消）</div>`:""}
    ${rowsHtml}
    <div class="notes">
      <label>心仪的点 / 想保留的特征
        <textarea data-field="likes">${esc(notes.likes||"")}</textarea></label>
      <label>调整提示词（下一版方向）
        <textarea data-field="adjustments">${esc(notes.adjustments||"")}</textarea></label>
      <div class="state-actions">
        <button class="btn" id="nextRound">进入下一版</button>
        <button class="btn primary" id="confirmLook">${STATE.finals[k]?"已确认（取消）":(picking?"点选最终中…":"确认此时期造型")}</button>
      </div>
    </div>`;

  // 卡片：点选最终模式 -> 设为最终；否则切换心仪
  stage.querySelectorAll(".heart").forEach(h=>h.onclick=(e)=>{ e.stopPropagation(); onCardClick(role,st,k,h.dataset.id); });
  stage.querySelectorAll(".lockbtn").forEach(b=>b.onclick=(e)=>{
    e.stopPropagation(); toggleLock(k, b.dataset.kind, b.dataset.id);
    renderStage(); renderNav(); renderOverview();
  });
  stage.querySelectorAll(".card").forEach(c=>c.onclick=()=>onCardClick(role,st,k,c.dataset.id));
  // 空行点击 -> 记录生成意图
  stage.querySelectorAll(".gen-slot").forEach(el=>el.onclick=()=>{
    const gk = `${k}::${el.dataset.genEngine}`;
    STATE.gen = STATE.gen||{}; STATE.gen[gk] = !STATE.gen[gk];
    if(!STATE.gen[gk]) delete STATE.gen[gk];
    autosave(); renderStage();
    toast(STATE.gen[gk]?"已标记待生成，默认 Gemini Image 补图":"已取消标记");
  });
  stage.querySelectorAll(".notes textarea").forEach(t=>t.oninput=()=>{
    STATE.notes[k] = STATE.notes[k]||{}; STATE.notes[k][t.dataset.field]=t.value; persist();
  });
  document.getElementById("confirmLook").onclick=()=>onConfirm(role,st,k);
  document.getElementById("nextRound").onclick=()=>{
    STATE.notes[k]=STATE.notes[k]||{}; STATE.notes[k].nextRound=true; STATE.notes[k].nextEngine="Gemini Image"; autosave();
    toast("已标记『进入下一版』：默认 Gemini Image 生成 4 张");
  };
  // 导入图：单按钮 -> 选≤4张 -> POST /api/import -> 重建刷新（导入行出现在 Image2 上方）
  const impBtn = document.getElementById("importBtn"), impInput = document.getElementById("importInput");
  impBtn.onclick = ()=> impInput.click();
  impInput.onchange = async ()=>{
    const fileList = Array.from(impInput.files||[]).slice(0,4);
    if(!fileList.length) return;
    toast(`读取 ${fileList.length} 张...`);
    const files = await Promise.all(fileList.map(f=>new Promise(res=>{
      const rd=new FileReader(); rd.onload=()=>res({name:f.name, dataUrl:rd.result}); rd.readAsDataURL(f);
    })));
    const res = await fetch("/api/import",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({role:CUR.role, state:CUR.state, files})});
    const j = await res.json().catch(()=>({}));
    if(res.ok && j.ok){
      toast(`已导入 ${(j.saved||[]).length} 张`);
      MANIFEST = await (await fetch("/api/manifest")).json();
      renderStage(); renderAside();
    } else { toast("导入失败" + (j.error?("："+j.error):"")); }
    impInput.value = "";
  };
}

// 卡片点击统一处理：点选最终模式 vs 心仪切换
function onCardClick(role, st, k, id){
  if(PICK_FINAL===k){
    if(!STATE.likes[id]){ toast("请点选 ❤️ 心仪过的图作为最终"); return; }
    STATE.finals[k] = id; PICK_FINAL = null; autosave();
    renderStage(); renderNav(); renderProgress(); renderOverview();
    toast("已确认该时期最终造型");
    return;
  }
  toggleLike(id); persist(); renderStage(); renderNav(); renderOverview();
}

// 确认此时期造型（单选）
function onConfirm(role, st, k){
  if(STATE.finals[k]){ // 已确认 -> 取消
    STATE.finals[k] = null; delete STATE.finals[k]; PICK_FINAL=null; autosave();
    renderStage(); renderNav(); renderProgress(); renderOverview(); toast("已取消确认"); return;
  }
  const liked = stateImageIds(role, st).filter(id=>STATE.likes[id]);
  if(liked.length===0){ toast("请先 ❤️ 心仪至少一张图，再确认"); return; }
  if(liked.length===1){
    STATE.finals[k] = liked[0]; autosave();
    renderStage(); renderNav(); renderProgress(); renderOverview(); toast("已确认该时期最终造型"); return;
  }
  // 多张心仪 -> 进入点选模式
  PICK_FINAL = k; renderStage(); toast("有多张心仪图，请点选其中一张作为最终");
}

function cardHtml(role, st, group, img){
  const id = img.id || img.path;
  const liked = !!STATE.likes[id];
  const k = keyOf(role.name, st.name);
  const locks = (STATE.locks||{})[k] || {};
  // 单选最终：finals[k] 存被选中的那张 id
  const isFinal = STATE.finals[k] === id;
  const pickable = (PICK_FINAL===k && liked);
  const inner = img.path
    ? `<img src="/asset/${encodeURI(img.path)}" alt="${esc(id)}" loading="lazy">`
    : `<div class="ph">占位<br>${esc(img.note||id)}</div>`;
  return `<article class="card ${liked?'liked':''} ${isFinal?'final':''} ${pickable?'pickable':''}" data-id="${esc(id)}">
    <div class="locks">
      <button class="lockbtn ${locks.face===id?'active':''}" data-kind="face" data-id="${esc(id)}" title="锁脸">脸</button>
      <button class="lockbtn ${locks.body===id?'active':''}" data-kind="body" data-id="${esc(id)}" title="锁身体比例和姿态">身体</button>
      <button class="lockbtn ${locks.clothes===id?'active':''}" data-kind="clothes" data-id="${esc(id)}" title="锁衣服材质和配饰">衣服</button>
    </div>
    <button class="heart" data-id="${esc(id)}" title="心仪">${liked?'❤':'♡'}</button>
    <div class="imgwrap">${inner}</div>
    <div class="meta"><span>${esc(id)}</span><span class="finaltag">最终</span></div>
  </article>`;
}

function toggleLike(id){ STATE.likes[id] = !STATE.likes[id]; if(!STATE.likes[id]) delete STATE.likes[id]; persist(); }
function toggleLock(k, kind, id){
  STATE.locks = STATE.locks || {};
  STATE.locks[k] = STATE.locks[k] || {};
  const current = STATE.locks[k][kind];
  if(current === id) delete STATE.locks[k][kind];
  else STATE.locks[k][kind] = id;
  if(Object.keys(STATE.locks[k]).length===0) delete STATE.locks[k];
  autosave();
  const label = kind==="face" ? "脸" : (kind==="body" ? "身体" : "衣服");
  toast(current === id ? `已取消锁${label}` : `已锁${label}参考`);
}

function normalizeGroups(st){
  // 顺序：导入（若有）→ Gemini Image → Image2 → MJ → 其余
  const gs = st.groups || [];
  const find = (frag)=>gs.find(g=>(g.engine||"").toLowerCase().includes(frag));
  const imp = gs.find(g=>(g.engine||"")==="导入");
  const gemini = find("gemini") || {engine:"Gemini Image", label:"下一版/图生图默认候选", images:[]};
  const i2 = find("image2") || {engine:"Image2", label:"候选", images:[]};
  const mj = find("mj") || {engine:"MJ", label:"候选", images:[]};
  const rest = gs.filter(g=>g!==i2 && g!==mj && g!==imp && g!==gemini);
  return [...(imp?[imp]:[]), gemini, i2, mj, ...rest];
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
  const tone = st.styleTone || role.styleTone || MANIFEST.styleTone || "（未设定整体基调）";
  const wv = st.worldview || {};
  const tags = (wv.keywords||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join("");
  const pr = st.prompts;
  const promptBlock = pr ? `
    <div class="prompt-block">
      <h3>定妆提示词 <span class="pmuted">（Claude 生成，可复制去出图）</span></h3>
      ${pr.image2?`<div class="pgroup">
        <div class="phead"><span class="eng image2">Image2</span><button class="copy" data-copy="i2">复制</button></div>
        <pre class="ptext" data-pt="i2">${esc(pr.image2)}</pre></div>`:""}
      ${pr.gemini?`<div class="pgroup">
        <div class="phead"><span class="eng gemini">Gemini Image</span><button class="copy" data-copy="gemini">复制</button></div>
        <pre class="ptext" data-pt="gemini">${esc(pr.gemini)}</pre></div>`:""}
      ${pr.mj?`<div class="pgroup">
        <div class="phead"><span class="eng mj">MJ</span><button class="copy" data-copy="mj">复制</button></div>
        <pre class="ptext" data-pt="mj">${esc(pr.mj)}</pre></div>`:""}
    </div>` : `
    <div class="prompt-block"><h3>定妆提示词</h3>
      <div class="pempty">该时期暂无提示词（放入 prompts/${esc(role.name.split(" / ")[0])}_${esc(st.name)}_Image2_round01.md 后重建 manifest）</div></div>`;
  aside.innerHTML = `
    <div class="tone"><div class="lab">整体基调风格</div><div class="val">${esc(tone)}</div></div>
    <div class="wv-block">
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
      </div>
    </div>
    ${promptBlock}`;
  aside.querySelectorAll(".copy").forEach(b=>b.onclick=()=>{
    const pre = aside.querySelector(`.ptext[data-pt="${b.dataset.copy}"]`);
    if(!pre) return;
    navigator.clipboard.writeText(pre.textContent).then(()=>toast("已复制提示词"),()=>toast("复制失败"));
  });
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
  // 供下一步出图：每个已确认时期的「最终单张」+ 心仪备选
  const out=[];
  for(const {mod, role} of iterRoles())
    for(const st of (role.states||[])){
      const k = keyOf(role.name, st.name);
      const finalId = STATE.finals[k];
      if(!finalId) continue;
      let finalRef=null; const alts=[];
      for(const g of (st.groups||[]))
        for(const im of (g.images||[])){
          const id = im.id||im.path;
          if(id===finalId) finalRef={engine:g.engine, id, path:im.path||""};
          else if(STATE.likes[id]) alts.push({engine:g.engine, id, path:im.path||""});
        }
      out.push({module:mod.name||"", role:role.name, state:st.name,
                era:(st.worldview||{}).era||"", styleTone: st.styleTone||role.styleTone||MANIFEST.styleTone||"",
                final: finalRef, alternates: alts, locks:(STATE.locks||{})[k]||{}});
    }
  return out;
}
function genRequests(){
  // 需生成的空行意图：[{role,state,engine}]，gen key = role::state::engine
  const out=[];
  for(const key in (STATE.gen||{})){
    if(!STATE.gen[key]) continue;
    const parts = key.split("::");
    if(parts.length>=3) out.push({role:parts[0], state:parts[1], engine:parts.slice(2).join("::")});
  }
  return out;
}
function buildPayload(extra){
  return Object.assign({
    project: MANIFEST.project || "",
    round: MANIFEST.round || 1,
    likes: STATE.likes, locks: STATE.locks||{}, finals: STATE.finals, notes: STATE.notes, gen: STATE.gen||{},
    overviewRequested: STATE.overviewRequested,
    confirmedLooks: confirmedLooks(), genRequests: genRequests(),
    confirmedCount: confirmedCount(), totalStates: totalStates(),
  }, extra||{});
}
async function save(extra, okMsg, silent){
  persist();
  try{
    const res = await fetch("/api/save", {method:"POST",
      headers:{"Content-Type":"application/json"}, body:JSON.stringify(buildPayload(extra))});
    if(!silent) toast(res.ok ? (okMsg||"已保存到 selection-state.json") : "保存失败");
    return res.ok;
  }catch(e){ if(!silent) toast("保存失败"); return false; }
}
document.getElementById("saveBtn").onclick=()=>save();
document.getElementById("overviewBtn").onclick=async ()=>{
  STATE.overviewRequested = true; persist();
  const ok = await save({overviewRequested:true}, "已记录『生成总览图』意图，保存成功，我会据此出图");
  if(ok) renderOverview();
};

/* ---------- 主题（深色/浅色） ---------- */
const THEME_KEY = "castingTheme";
function applyTheme(t){
  if(t==="dark") document.documentElement.setAttribute("data-theme","dark");
  else document.documentElement.removeAttribute("data-theme");
  const btn = document.getElementById("themeToggle");
  if(btn) btn.textContent = (t==="dark") ? "☀" : "🌙";
}
function initTheme(){
  let t = localStorage.getItem(THEME_KEY);
  if(!t) t = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  applyTheme(t);
}
document.getElementById("themeToggle").onclick=()=>{
  const cur = document.documentElement.getAttribute("data-theme")==="dark" ? "dark" : "light";
  const next = cur==="dark" ? "light" : "dark";
  localStorage.setItem(THEME_KEY, next); applyTheme(next);
};
initTheme();
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
            path = urlparse(self.path).path
            if path == "/api/save":
                length = int(self.headers.get("Content-Length", "0") or "0")
                data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send_json({"ok": True, "path": str(output_path)})
                return
            if path == "/api/import":
                self._handle_import()
                return
            self._send_json({"error": "not found"}, 404)

        def _handle_import(self):
            """接收 base64 图片，存进 candidates/<角色>/<时期目录>/导入/round-01/，再重建 manifest。

            请求体 JSON: {role, state, files:[{name, dataUrl}]}
            导入图统一作为「导入」行显示在 Image2 上方。
            """
            import base64
            import re as _re
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                self._send_json({"error": "empty body"}, 400)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as exc:
                self._send_json({"error": f"bad json: {exc}"}, 400)
                return
            role = (payload.get("role") or "").split(" / ")[0].strip()
            state_name = (payload.get("state") or "").strip()
            files = payload.get("files") or []
            if not role or not state_name or not files:
                self._send_json({"error": "missing role/state/files"}, 400)
                return

            # 解析该 state 的图片目录名（imageDir，兼容历史别名）
            current = load_manifest(manifest_path)
            folder = state_name
            for mod in current.get("modules", [{"roles": current.get("roles", [])}]):
                for r in mod.get("roles", []):
                    if (r.get("name") or "").split(" / ")[0].strip() == role:
                        for s in r.get("states", []):
                            if s.get("name") == state_name:
                                folder = s.get("imageDir") or state_name

            def _safe(name):
                for ch in '\\/:*?"<>|':
                    name = name.replace(ch, "_")
                return name.strip()

            target_dir = (root / "candidates" / _safe(role) / _safe(folder) / "导入" / "round-01").resolve()
            if not str(target_dir).startswith(str(root)):
                self._send_json({"error": "path escape"}, 400)
                return
            target_dir.mkdir(parents=True, exist_ok=True)

            existing = len([p for p in target_dir.iterdir() if p.is_file()]) if target_dir.exists() else 0
            saved = []
            for i, f in enumerate(files[:4], start=1):
                data_url = f.get("dataUrl", "")
                m = _re.match(r"data:image/(\w+);base64,(.+)", data_url, _re.S)
                if not m:
                    continue
                ext = "jpg" if m.group(1).lower() in {"jpeg", "jpg"} else m.group(1).lower()
                try:
                    blob = base64.b64decode(m.group(2))
                except Exception:
                    continue
                idx = existing + i
                fname = f"{idx:02d}_导入{_safe(f.get('name','')) or 'img'}"
                if not fname.lower().endswith(("." + ext, ".png", ".jpg", ".jpeg", ".webp")):
                    fname = f"{idx:02d}_导入.{ext}"
                (target_dir / fname).write_bytes(blob)
                saved.append(fname)

            # 重建 manifest（优先用项目 build_manifest.py，否则只回报已存路径）
            rebuilt = self._rebuild_manifest()
            self._send_json({"ok": True, "saved": saved, "dir": str(target_dir), "rebuilt": rebuilt})

        def _rebuild_manifest(self):
            """若同目录有 build_manifest.py 则跑它刷新 manifest.json。"""
            import subprocess
            import sys
            bm = manifest_path.parent / "build_manifest.py"
            if not bm.exists():
                return False
            try:
                subprocess.run([sys.executable, str(bm)], cwd=str(manifest_path.parent),
                               capture_output=True, timeout=60)
                return True
            except Exception:
                return False

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
    print(f"视觉定版 Gallery: http://{args.host}:{args.port}/")
    print(f"保存目标: {output_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
