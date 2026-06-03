#!/usr/bin/env python3
"""视觉定版 Gallery —— 三栏布局本地评审服务器。

左栏：按模块分组，可展开 -> 条目 -> 状态/变体。
中栏：导入 / Gemini Image / Image2 / MJ 等候选行，人物定妆默认为三视图候选，图片右上角 ❤️ 心仪标记，
      左上角可锁脸/身体/衣服等局部参考，每个状态有「确认造型」按钮。
右栏：该状态的世界观/场景背景说明和可复制提示词。
底部：全部确认后可「生成总览图」（仅记录意图，真正出图由 Codex/Claude 下一步执行）。

这是人物定妆、场景美术、道具定版共用的本地评审脚本。把它拷进项目输出目录，
或用 --manifest 指向项目 manifest 运行。
本脚本默认只负责评审、收藏、确认与意图记录；用户双击空白候选卡片并确认额度后，
才会调用本机环境变量中的出图 API key 生成候选图。
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.request
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
header .center-tools{display:flex;align-items:center;gap:12px;min-width:240px;justify-content:center}
header .progress{font-size:13px;color:var(--muted);white-space:nowrap}
header .progress b{color:var(--accent)}
header .head-right{display:flex;align-items:center;gap:12px}
.mode-tabs{display:inline-flex;align-items:center;padding:3px;border:1px solid var(--line);border-radius:9px;background:var(--panel);box-shadow:var(--shadow)}
.mode-tab{height:30px;padding:0 14px;border:0;border-radius:7px;background:transparent;color:var(--muted);font:inherit;font-size:13px;cursor:pointer}
.mode-tab:hover{color:var(--ink);background:var(--nav-hover)}
.mode-tab.active{background:var(--accent);color:#fff}
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
@media(max-width:860px){
  header{flex-wrap:wrap}
  header .center-tools{order:3;width:100%;min-width:0;justify-content:center}
}

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
.shot-link{display:flex;align-items:center;justify-content:space-between;gap:6px;width:100%;
  padding:8px 10px;border:0;border-radius:7px;background:transparent;cursor:pointer;font:inherit;
  color:var(--ink);text-align:left;font-size:13px;margin-top:2px}
.shot-link:hover{background:var(--nav-hover)}
.shot-link.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.shot-link .sno{font-weight:600;min-width:30px}
.shot-link .purpose{flex:1;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.shot-link.active .purpose{color:var(--accent)}
.shot-link .tick{font-size:12px;color:var(--accent);opacity:0}
.shot-link.confirmed .tick{opacity:1}
.key-panel{margin:18px 2px 0;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--panel);box-shadow:var(--shadow)}
.key-toggle{width:100%;height:30px;border:0;background:transparent;color:var(--ink);display:flex;align-items:center;justify-content:space-between;font:inherit;font-size:13px;font-weight:600;cursor:pointer}
.key-body{display:none;margin-top:8px}
.key-panel.open .key-body{display:block}
.key-panel.open .caret{transform:rotate(90deg)}
.key-note{font-size:11px;line-height:1.5;color:var(--muted);margin-bottom:8px}
.key-grid{display:grid;gap:7px}
.key-field label{display:block;font-size:11px;color:var(--muted);margin-bottom:3px}
.key-field input{width:100%;height:30px;border:1px solid var(--line);border-radius:7px;background:var(--slot-bg);color:var(--ink);padding:0 8px;font:inherit;font-size:12px}
.key-actions{display:flex;gap:7px;margin-top:9px}
.key-actions .btn{height:30px;padding:0 10px;font-size:12px}

/* ---- 中栏：候选评审 ---- */
.stage{overflow:auto;padding:22px 26px 90px;position:relative}
.stage .crumb{font-size:13px;color:var(--muted);margin-bottom:4px}
.stage .head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:6px}
.stage h2{margin:0;font-size:22px}
.stage .age{font-size:13px;color:var(--muted);margin-top:4px}
.head-actions{flex:none}
.format-toggle{display:inline-flex;align-items:center;gap:4px;padding:3px;border:1px solid var(--line);
  border-radius:8px;background:var(--panel);box-shadow:var(--shadow)}
.format-toggle .btn{height:28px;padding:0 12px;font-size:12px;border-color:transparent;box-shadow:none}
.format-toggle .btn.active{background:var(--accent);border-color:var(--accent);color:white}
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
.gen-card{position:relative;border:1.5px dashed var(--line);border-radius:12px;overflow:hidden;background:var(--panel);
  padding:0;text-align:left;
  box-shadow:var(--shadow);cursor:pointer;transition:.15s}
.gen-card:hover{transform:translateY(-2px);border-color:var(--accent);color:var(--accent)}
.gen-card.marked{border-color:var(--accent);border-style:solid;color:var(--accent);background:var(--accent-soft)}
.gen-card .imgwrap{aspect-ratio:9/13;background:var(--imgwrap);display:flex;align-items:center;justify-content:center}
.stage.landscape .gen-card .imgwrap{aspect-ratio:16/9}
.gen-card .ph{color:var(--muted);font-size:12px;text-align:center;padding:14px;line-height:1.6;opacity:.8}
.gen-card.marked .ph{color:var(--accent);opacity:1}
.gen-card .meta{padding:8px 10px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}
.card{position:relative;border:2px solid transparent;border-radius:12px;overflow:hidden;background:var(--panel);
  box-shadow:var(--shadow);cursor:pointer;transition:.15s}
.card:hover{transform:translateY(-2px)}
.card.liked{border-color:var(--heart)}
.card.final{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft),var(--shadow)}
.card.pickable{outline:2px dashed var(--accent);outline-offset:2px}
.card .imgwrap{aspect-ratio:9/13;background:var(--imgwrap);display:flex;align-items:center;justify-content:center}
.stage.landscape .card .imgwrap{aspect-ratio:16/9}
.card img{display:block;width:100%;height:100%;object-fit:cover}
.card .ph{color:var(--muted);font-size:12px;text-align:center;padding:14px;line-height:1.6;opacity:.8}
.heart{position:absolute;top:8px;right:8px;z-index:3;width:34px;height:34px;border-radius:50%;border:0;
  background:rgba(255,255,255,.9);cursor:pointer;font-size:18px;line-height:34px;color:#c9bfb0;
  box-shadow:0 1px 4px rgba(0,0,0,.15);transition:.15s}
[data-theme="dark"] .heart{background:rgba(20,22,26,.85);color:#6a7079}
.heart:hover{transform:scale(1.1)}
.card.liked .heart{color:var(--heart)}
.locks{position:absolute;top:8px;left:8px;right:42px;z-index:4;display:flex;gap:5px;flex-wrap:wrap}
.lockbtn{height:26px;min-width:30px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.92);
  color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.12)}
[data-theme="dark"] .lockbtn{background:rgba(20,22,26,.86)}
.lockbtn.active{border-color:var(--accent);background:var(--accent);color:#fff}
.card .meta{padding:8px 10px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:6px}
.card .finaltag{display:none;color:var(--accent);font-weight:600}
.card.final .finaltag{display:inline}
.fusion-section{margin-top:18px}
.fusion-section:first-child{margin-top:0}
.fusion-title{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;color:var(--muted);font-size:14px}
.fusion-title b{color:var(--ink);font-size:15px}
.fusion-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px}
.fusion-card{position:relative;border:1px solid var(--line);border-radius:8px;background:var(--panel);overflow:hidden;box-shadow:var(--shadow)}
.fusion-card .imgwrap{aspect-ratio:9/13;background:var(--imgwrap);display:flex;align-items:center;justify-content:center}
.fusion-card.scene .imgwrap{aspect-ratio:16/9}
.fusion-card img{display:block;width:100%;height:100%;object-fit:cover;cursor:zoom-in}
.fusion-card .ph{font-size:12px;line-height:1.6;text-align:center;color:var(--muted);padding:14px}
.fusion-card .meta{padding:8px 10px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);display:grid;gap:6px}
.fusion-card .meta b{color:var(--ink);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mini-btn{height:28px;padding:0 9px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink);font:inherit;font-size:12px;cursor:pointer}
.mini-btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.fusion-mode{display:grid;grid-template-columns:minmax(160px,240px) 1fr;gap:12px;align-items:start;margin:12px 0;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--slot-bg)}
.fusion-mode label{font-size:12px;color:var(--muted)}
.fusion-mode select{width:100%;height:34px;margin-top:5px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink);font:inherit}
.fusion-mode .hint{font-size:12px;line-height:1.6;color:var(--muted)}
.format-picker{display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 10px;border:1px solid var(--line);border-radius:7px;background:var(--panel);font-size:12px;color:var(--muted)}
.format-picker select{height:26px;border:1px solid var(--line);border-radius:6px;background:var(--slot-bg);color:var(--ink);font:inherit;font-size:12px}
.fusion-prompt{margin-top:14px;background:var(--slot-bg);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.65;white-space:pre-wrap;word-break:break-word;color:var(--ink)}
.clip-list{display:grid;gap:8px;max-height:360px;overflow:auto;padding-right:2px}
.clip-item{border:1px solid var(--line);border-radius:8px;padding:8px 9px;background:var(--slot-bg)}
.clip-item.active{border-color:var(--accent);background:var(--accent-soft)}
.clip-top{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--muted);margin-bottom:4px}
.clip-top b{color:var(--ink)}
.clip-img{font-size:12px;line-height:1.55;color:var(--ink)}
.clip-sub{margin-top:4px;font-size:11px;line-height:1.45;color:var(--muted)}
.shot-link.review .sno::after{content:"!";color:var(--warm);margin-left:3px;font-weight:700}
.delete-img{position:absolute;right:8px;bottom:34px;z-index:4;height:26px;padding:0 8px;border:1px solid rgba(0,0,0,.12);
  border-radius:999px;background:rgba(255,255,255,.92);color:#9a2d25;font-size:12px;font-weight:600;cursor:pointer;
  box-shadow:0 1px 4px rgba(0,0,0,.14);opacity:0;transform:translateY(4px);transition:.15s}
.card:hover .delete-img{opacity:1;transform:translateY(0)}
[data-theme="dark"] .delete-img{background:rgba(20,22,26,.9);border-color:var(--line);color:#ff9a8f}
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
.lightbox{position:fixed;inset:0;z-index:80;display:none;align-items:center;justify-content:center;
  padding:30px;background:rgba(0,0,0,.76)}
.lightbox.open{display:flex}
.lightbox-inner{position:relative;max-width:min(1200px,94vw);max-height:92vh;background:#111;border-radius:12px;
  box-shadow:0 18px 80px rgba(0,0,0,.5);overflow:hidden}
.lightbox img{display:block;max-width:94vw;max-height:86vh;object-fit:contain;background:#111}
.lightbox-title{position:absolute;left:0;right:0;bottom:0;padding:10px 14px;background:linear-gradient(transparent,rgba(0,0,0,.78));
  color:#fff;font-size:12px;line-height:1.5;word-break:break-all}
.lightbox-close{position:absolute;top:10px;right:10px;z-index:2;width:34px;height:34px;border:1px solid rgba(255,255,255,.35);
  border-radius:50%;background:rgba(0,0,0,.45);color:#fff;font-size:20px;line-height:1;cursor:pointer}
</style>
</head>
<body>
<header>
  <div class="title"><h1 id="pageTitle">视觉定版评审</h1><span class="proj" id="projName"></span></div>
  <div class="center-tools">
    <div class="mode-tabs" id="modeTabs">
      <button class="mode-tab active" data-mode="casting">定妆造</button>
      <button class="mode-tab" data-mode="scene">场景美术</button>
      <button class="mode-tab" data-mode="fusion">人景合一</button>
    </div>
  </div>
  <div class="head-right">
    <div class="progress" id="progress"></div>
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
<div class="lightbox" id="lightbox" aria-hidden="true">
  <div class="lightbox-inner">
    <button class="lightbox-close" id="lightboxClose" type="button" title="关闭">×</button>
    <img id="lightboxImg" alt="">
    <div class="lightbox-title" id="lightboxTitle"></div>
  </div>
</div>

<script>
const STATE_KEY = "castingState_v2";
const CARD_FORMAT_KEY = "visualReviewCardFormat";
let MANIFEST = null;
let FUSION = null;
let PREVIEW = null;
let STATE = loadState();
let FUSION_STATE = loadFusionState();
let CUR = {role:null, state:null};
let FUSION_CUR = null;
let FUSION_SOURCE = "preview";
let ACTIVE_MODE = localStorage.getItem("visualReviewMode") || "casting";
if(!["casting","scene","fusion"].includes(ACTIVE_MODE)) ACTIVE_MODE = "casting";
let CARD_FORMAT = localStorage.getItem(CARD_FORMAT_KEY) || "portrait";
let PICK_FINAL = null;   // 正在为哪个时期点选最终（key 或 null）
let CARD_CLICK_TIMER = null;

function loadState(){
  try{ const s = JSON.parse(localStorage.getItem(STATE_KEY)) || blank();
    return Object.assign(blank(), s); }
  catch(e){ return blank(); }
}
function blank(){ return {likes:{}, locks:{}, finals:{}, notes:{}, gen:{}, deleted:{}, overviewRequested:false}; }
function persist(){ localStorage.setItem(STATE_KEY, JSON.stringify(STATE)); }
function loadFusionState(){
  try{ return Object.assign(blankFusion(), JSON.parse(localStorage.getItem("fusionState_v2")) || {}); }
  catch(e){ return blankFusion(); }
}
function blankFusion(){ return {likes:{}, finals:{}, notes:{}, uploadedRefs:{}, sceneInputs:{}, genRequests:{}, exportRequested:false}; }
function persistFusion(){ localStorage.setItem("fusionState_v2", JSON.stringify(FUSION_STATE)); }
// 关键操作自动保存：写本地 + 后台落盘，无需手动点「保存选择」
function autosave(){ persist(); save(null, null, true); }

function keyOf(role, state){ return role + "::" + state; }
function esc(s){ return String(s??"").replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function toast(msg){ const t=document.getElementById("toast"); t.textContent=msg; t.classList.add("show");
  clearTimeout(t._t); t._t=setTimeout(()=>t.classList.remove("show"),1800); }

async function boot(){
  MANIFEST = await (await fetch("/api/manifest")).json();
  try{ FUSION = await (await fetch("/api/fusion-manifest")).json(); }
  catch(e){ FUSION = {project:MANIFEST.project||"", shots:[]}; }
  try{ PREVIEW = await (await fetch("/api/preview-candidates")).json(); }
  catch(e){ PREVIEW = {shots:[]}; }
  document.getElementById("pageTitle").textContent = MANIFEST.pageTitle || "视觉定版评审";
  document.title = MANIFEST.pageTitle || "视觉定版评审";
  document.getElementById("projName").textContent = MANIFEST.project ? "· " + MANIFEST.project : "";
  if(!FUSION_CUR && findPreviewShot("01")) FUSION_CUR = "01";
  if(!FUSION_CUR && fusionShots()[0]) { FUSION_CUR = fusionShots()[0].no; FUSION_SOURCE = "episode"; }
  initModeTabs();
  if(ACTIVE_MODE!=="fusion") ensureCurrentInMode();
  renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
}

function modeLabel(mode){ return mode==="fusion" ? "人景合一" : (mode==="scene" ? "场景美术" : "定妆造"); }
function moduleMatchesMode(mod, mode){
  const name = mod.name || "";
  if(mode==="scene") return name.includes("场景美术") || name.includes("道具定版") || name.includes("关键道具");
  return name.includes("人物定妆") || (!name.includes("场景美术") && !name.includes("道具定版") && !name.includes("关键道具"));
}
function* iterRoles(mode=ACTIVE_MODE){
  for(const mod of (MANIFEST.modules||[{name:"", roles:MANIFEST.roles||[]}]))
    if(mode==="all" || moduleMatchesMode(mod, mode))
    for(const role of (mod.roles||[])) yield {mod, role};
}
function firstModuleRole(){ for(const r of iterRoles()) return r; return null; }
function findRole(name, mode=ACTIVE_MODE){ for(const {role} of iterRoles(mode)) if(role.name===name) return role; return null; }
function findState(role, sname){ return (role.states||[]).find(s=>s.name===sname); }
function ensureCurrentInMode(){
  const current = CUR.role && findRole(CUR.role);
  if(current) return;
  const firstRole = firstModuleRole();
  if(firstRole){ CUR.role = firstRole.role.name; CUR.state = (firstRole.role.states[0]||{}).name; }
}
function initModeTabs(){
  document.querySelectorAll(".mode-tab").forEach(btn=>{
    btn.classList.toggle("active", btn.dataset.mode===ACTIVE_MODE);
    btn.onclick=()=>{
      ACTIVE_MODE = btn.dataset.mode;
      localStorage.setItem("visualReviewMode", ACTIVE_MODE);
      document.querySelectorAll(".mode-tab").forEach(b=>b.classList.toggle("active", b.dataset.mode===ACTIVE_MODE));
      if(ACTIVE_MODE==="fusion"){
        if(!FUSION_CUR && findPreviewShot("01")) { FUSION_CUR = "01"; FUSION_SOURCE = "preview"; }
        if(!FUSION_CUR && fusionShots()[0]) { FUSION_CUR = fusionShots()[0].no; FUSION_SOURCE = "episode"; }
      } else {
        const firstRole = firstModuleRole();
        if(firstRole){ CUR.role = firstRole.role.name; CUR.state = (firstRole.role.states[0]||{}).name; }
      }
      renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
    };
  });
}

function fusionShots(){ return (FUSION&&FUSION.shots)||[]; }
function findFusionShot(no){ return fusionShots().find(s=>s.no===no); }
function findPreviewShot(no){ return ((PREVIEW&&PREVIEW.shots)||[]).find(s=>String(s.shot).padStart(2,"0")===String(no).padStart(2,"0")); }
function previewAsFusionShot(no){
  const p = findPreviewShot(no);
  if(!p) return null;
  const shotNo = String(p.shot||no).padStart(2,"0");
  return {
    no: shotNo,
    prompt: p.image || "",
    negative: "",
    shot: {
      "画面目的": p.shot_type || "剪辑版分镜",
      "景别": "",
      "运镜": p.motion || "",
      "时长": p.duration ? `${p.duration}秒` : "",
      "台词": p.subtitle || "",
      "场景": p.image || "",
      "光影": ""
    },
    refs: [],
    replaceMode: {default:"compose", options:["compose","replace_face","replace_pose","replace_face_and_pose"]},
    candidates: Array.from({length:4}, (_,i)=>({id:`preview-s${shotNo}-${i+1}`, path:"", note:`剪辑版镜头候选${i+1}`})),
    needsReview: "剪辑版镜头尚未匹配角色三视图和锁定场景，可先手动上传参考图"
  };
}
function currentFusionShot(){
  if(FUSION_SOURCE === "preview"){
    return previewAsFusionShot(FUSION_CUR) || findFusionShot(FUSION_CUR);
  }
  return findFusionShot(FUSION_CUR) || previewAsFusionShot(FUSION_CUR);
}
function totalStates(mode=ACTIVE_MODE){
  if(mode==="fusion") return fusionShots().length;
  let n=0; for(const {role} of iterRoles(mode)) n += (role.states||[]).length; return n;
}
function confirmedCount(mode=ACTIVE_MODE){
  if(mode==="fusion") return Object.keys(FUSION_STATE.finals||{}).filter(k=>FUSION_STATE.finals[k]).length;
  let n=0;
  for(const {role} of iterRoles(mode))
    for(const s of (role.states||[]))
      if(STATE.finals[keyOf(role.name, s.name)]) n++;
  return n;
}

/* ---------- 左栏 ---------- */
function renderNav(){
  if(ACTIVE_MODE==="fusion"){ renderFusionNav(); return; }
  const nav = document.getElementById("nav");
  const mods = (MANIFEST.modules || [{name:"", roles:MANIFEST.roles||[]}]).filter(mod=>moduleMatchesMode(mod, ACTIVE_MODE));
  const moduleHtml = mods.map(mod=>{
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
  nav.innerHTML = moduleHtml + keyPanelHtml();

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
  bindKeyPanel(nav);
}

function renderFusionNav(){
  const nav = document.getElementById("nav");
  const ep = FUSION&&FUSION.episode ? `第${esc(FUSION.episode)}集` : "镜头列表";
  const preview = ((PREVIEW&&PREVIEW.shots)||[]);
  const previewLinks = preview.map(p=>{
    const no = String(p.shot||"").padStart(2,"0");
    const active = FUSION_SOURCE==="preview" && String(FUSION_CUR).padStart(2,"0")===no;
    return `<button class="shot-link ${active?'active':''}" data-preview-no="${esc(no)}" title="${esc(p.image||"")}">
      <span class="sno">剪${esc(no)}</span><span class="purpose">${esc(p.image||"")}</span><span class="tick">✓</span></button>`;
  }).join("");
  const links = fusionShots().map(s=>{
    const active = FUSION_SOURCE==="episode" && s.no===FUSION_CUR;
    const conf = !!(FUSION_STATE.finals||{})[s.no];
    const review = !!s.needsReview;
    const purpose = (s.shot&&s.shot["画面目的"]) || "";
    return `<button class="shot-link ${active?'active':''} ${conf?'confirmed':''} ${review?'review':''}" data-no="${esc(s.no)}">
      <span class="sno">${esc(s.no)}</span><span class="purpose">${esc(purpose)}</span><span class="tick">✓</span></button>`;
  }).join("");
  nav.innerHTML = `
    <div class="module">
      <div class="module-title">剪辑版分镜 · ${preview.length}镜</div>
      ${previewLinks || `<div class="empty" style="padding:20px 8px">未读取到剪辑版分镜</div>`}
    </div>
    <div class="module">
      <div class="module-title">${esc(ep)} · ${fusionShots().length}镜</div>
      ${links || `<div class="empty" style="padding:20px 8px">还没有 shot-manifest.json</div>`}
    </div>`;
  nav.querySelectorAll("[data-preview-no]").forEach(b=>b.onclick=()=>{
    const no = b.dataset.previewNo;
    FUSION_SOURCE = "preview";
    if(findFusionShot(no)){
      FUSION_CUR = no;
      renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
    } else {
      FUSION_CUR = no;
      renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
      toast(`剪辑版镜 ${no} 暂无对应合成清单`);
    }
  });
  nav.querySelectorAll("[data-no]").forEach(b=>b.onclick=()=>{
    FUSION_SOURCE = "episode";
    FUSION_CUR = b.dataset.no;
    renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
  });
}

const KEY_STORE = "visualReviewProviderKeys";
const KEY_FIELDS = [
  ["nanoBananaPro", "Nano Banana Pro"],
  ["seedream5", "Seedream 5"],
  ["midjourney", "Midjourney"],
  ["image2", "Image2 / Tuzi"],
  ["kling", "可灵"],
  ["jimeng", "即梦"],
  ["seedance", "Seedance"]
];
function loadProviderKeys(){
  try{ return JSON.parse(localStorage.getItem(KEY_STORE)) || {}; }
  catch(e){ return {}; }
}
function saveProviderKeys(keys){ localStorage.setItem(KEY_STORE, JSON.stringify(keys)); }
function keyPanelHtml(){
  const keys = loadProviderKeys();
  const open = localStorage.getItem("visualReviewKeyPanelOpen")==="1";
  const fields = KEY_FIELDS.map(([id,label])=>`
    <div class="key-field">
      <label>${esc(label)}</label>
      <input type="password" data-key-id="${esc(id)}" value="${esc(keys[id]||"")}" autocomplete="off" placeholder="粘贴 ${esc(label)} Key">
    </div>`).join("");
  return `<section class="key-panel ${open?'open':''}" id="keyPanel">
    <button class="key-toggle" type="button"><span>平台 Key</span><span class="caret">▶</span></button>
    <div class="key-body">
      <div class="key-note">仅保存在本浏览器 localStorage，不写入项目文件；清缓存或换浏览器后需重填。</div>
      <div class="key-grid">${fields}</div>
      <div class="key-actions">
        <button class="btn primary" id="saveKeysBtn" type="button">保存Key</button>
        <button class="btn" id="clearKeysBtn" type="button">清空</button>
      </div>
    </div>
  </section>`;
}
function bindKeyPanel(nav){
  const panel = nav.querySelector("#keyPanel");
  if(!panel) return;
  const toggle = panel.querySelector(".key-toggle");
  toggle.onclick=()=>{
    panel.classList.toggle("open");
    localStorage.setItem("visualReviewKeyPanelOpen", panel.classList.contains("open") ? "1" : "0");
  };
  panel.querySelector("#saveKeysBtn").onclick=()=>{
    const keys = {};
    panel.querySelectorAll("input[data-key-id]").forEach(input=>{ keys[input.dataset.keyId] = input.value.trim(); });
    saveProviderKeys(keys);
    toast("平台 Key 已保存到本浏览器");
  };
  panel.querySelector("#clearKeysBtn").onclick=()=>{
    localStorage.removeItem(KEY_STORE);
    panel.querySelectorAll("input[data-key-id]").forEach(input=>input.value="");
    toast("已清空本浏览器保存的 Key");
  };
}

/* ---------- 人景合一：中栏/右栏/保存 ---------- */
const FUSION_ASPECTS = [
  {id:"portrait", label:"竖版 9:16"},
  {id:"landscape", label:"横版 16:9"}
];
const FUSION_MODE_LABELS = {
  compose:"人物三视图 + 场景合成",
  replace_face:"场景图已有身体，只换脸",
  replace_pose:"保留人物身份，换动作",
  replace_face_and_pose:"场景中已有占位人物，换脸+换动作"
};
function fusionNote(no){ FUSION_STATE.notes[no]=FUSION_STATE.notes[no]||{}; return FUSION_STATE.notes[no]; }
function fusionUpload(no, name){ return (((FUSION_STATE.uploadedRefs||{})[no]||{})[name]) || null; }
function fusionSceneInput(no, slot){ return (((FUSION_STATE.sceneInputs||{})[no]||{})[slot]) || null; }
function refAsset(path){ return path ? `/asset/${encodeURI(path)}` : ""; }
function fusionRoles(s){ return (s.refs||[]).filter(r=>r.kind==="role"); }
function fusionSceneRefs(s){ return (s.refs||[]).filter(r=>r.kind==="scene"); }
function fusionModeOptions(s, selected){
  return ((s.replaceMode&&s.replaceMode.options)||Object.keys(FUSION_MODE_LABELS))
    .map(m=>`<option value="${esc(m)}" ${m===selected?'selected':''}>${esc(FUSION_MODE_LABELS[m]||m)}</option>`).join("");
}
function fusionUploadCard(s, ref){
  const uploaded = fusionUpload(s.no, ref.name);
  const path = uploaded&&uploaded.path ? uploaded.path : ref.path;
  const title = ref.name || "角色";
  const folder = path ? path.split("/").slice(0,-1).join("/") : "08_生成图片/角色三视图";
  const img = path ? `<img src="${refAsset(path)}" alt="${esc(title)}" data-lightbox-src="${refAsset(path)}" data-lightbox-title="${esc(title)}">`
    : `<div class="ph">上传人物三视图<br>${esc(title)}</div>`;
  return `<article class="fusion-card" data-upload-kind="role" data-upload-name="${esc(title)}">
    <div class="imgwrap">${img}</div>
    <div class="meta"><b title="${esc(title)}">${esc(title)}</b>
      <button class="mini-btn" data-open-folder="${esc(folder)}">打开三视图文件夹</button>
      <button class="mini-btn" data-upload-trigger="role::${esc(title)}">上传/替换三视图</button>
      <input type="file" accept="image/*" hidden data-upload-input="role::${esc(title)}">
    </div>
  </article>`;
}
function fusionSceneCard(s, idx){
  const slot = `scene_${idx+1}`;
  const uploaded = fusionSceneInput(s.no, slot);
  const locked = fusionSceneRefs(s)[idx] || fusionSceneRefs(s)[0] || {};
  const path = uploaded&&uploaded.path ? uploaded.path : locked.path;
  const title = uploaded&&uploaded.name ? uploaded.name : (locked.name || `场景图候选 ${idx+1}`);
  const folder = path ? path.split("/").slice(0,-1).join("/") : "08_生成图片/场景美术";
  const img = path ? `<img src="${refAsset(path)}" alt="${esc(title)}" data-lightbox-src="${refAsset(path)}" data-lightbox-title="${esc(title)}">`
    : `<div class="ph">上传场景图候选 ${idx+1}<br>作为镜头合成环境</div>`;
  return `<article class="fusion-card scene" data-upload-kind="scene" data-upload-name="${esc(slot)}">
    <div class="imgwrap">${img}</div>
    <div class="meta"><b>场景图候选 ${idx+1}</b>
      <span>${esc(title)}</span>
      <button class="mini-btn" data-open-folder="${esc(folder)}">打开场景图文件夹</button>
      <button class="mini-btn" data-upload-trigger="scene::${esc(slot)}">上传/替换场景图</button>
      <input type="file" accept="image/*" hidden data-upload-input="scene::${esc(slot)}">
    </div>
  </article>`;
}
function fusionCandidateCard(s, c){
  const id = c.id || c.path;
  const liked = !!FUSION_STATE.likes[id];
  const final = !!FUSION_STATE.finals[s.no] && FUSION_STATE.finals[s.no]===id;
  const img = c.path ? `<img src="${refAsset(c.path)}" alt="${esc(id)}" data-lightbox-src="${refAsset(c.path)}" data-lightbox-title="${esc(id)}">`
    : `<div class="ph">待生成镜头图<br>${esc(c.note||id)}</div>`;
  return `<article class="card ${liked?'liked':''} ${final?'final':''}" data-fusion-candidate="${esc(id)}">
    <button class="heart" data-fusion-like="${esc(id)}" title="心仪">${liked?'❤':'♡'}</button>
    <div class="imgwrap">${img}</div>
    <div class="meta"><span>${esc(id)}</span><span class="finaltag">镜头图</span></div>
  </article>`;
}
function renderFusionStage(){
  const stage = document.getElementById("stage");
  const s = currentFusionShot();
  if(!s){ stage.innerHTML = `<div class="empty">请选择左侧镜号，或先生成 shot-manifest.json</div>`; return; }
  const note = fusionNote(s.no);
  const selectedMode = note.replaceMode || (s.replaceMode&&s.replaceMode.default) || "compose";
  const selectedAspect = note.generationAspect || "portrait";
  stage.classList.toggle("landscape", selectedAspect==="landscape");
  stage.classList.toggle("portrait", selectedAspect!=="landscape");
  const aspectOptions = FUSION_ASPECTS.map(a=>`<option value="${esc(a.id)}" ${a.id===selectedAspect?'selected':''}>${esc(a.label)}</option>`).join("");
  const roleRefs = fusionRoles(s);
  const roleCards = (roleRefs.length ? roleRefs : Array.from({length:3}, (_,i)=>({
    kind:"role", name:`人物三视图候选 ${i+1}`, path:"", confidence:"manual"
  }))).map(r=>fusionUploadCard(s,r)).join("");
  const sceneCount = Math.max(3, fusionSceneRefs(s).length || 1);
  const sceneCards = Array.from({length:sceneCount}, (_,i)=>fusionSceneCard(s,i)).join("");
  const cands = (s.candidates||[]).map(c=>fusionCandidateCard(s,c)).join("");
  stage.innerHTML = `
    <div class="crumb">人景合一 / ${FUSION_SOURCE==="preview"?"剪辑版分镜":`第${esc((FUSION&&FUSION.episode)||"")}集`} / 镜 ${esc(s.no)}</div>
    <div class="head"><div><h2>镜 ${esc(s.no)} · 合并生成镜头图片</h2>
      <div class="age">${esc((s.shot&&s.shot["画面目的"])||"")}</div></div></div>
    ${s.needsReview?`<div class="pickbar">待校正：${esc(s.needsReview)}</div>`:""}
    <section class="fusion-section">
      <div class="fusion-title"><b>人物三视图</b><span>根据本镜出现角色自动给上传框</span></div>
      <div class="fusion-grid">${roleCards}</div>
    </section>
    <section class="fusion-section">
      <div class="fusion-title"><b>场景图</b><span>只放场景候选，不标模型</span></div>
      <div class="fusion-grid">${sceneCards}</div>
    </section>
    <div class="fusion-mode">
      <label>合成方式
        <select id="fusionReplaceMode">${fusionModeOptions(s, selectedMode)}</select>
      </label>
      <div class="hint">按右侧分镜故事和原始主提示词合成；如果场景图里已经有人物，可选择换脸、换动作或换脸+换动作。</div>
    </div>
    <section class="fusion-section">
      <div class="fusion-title">
        <b>镜头图片候选</b>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end">
          <label class="format-picker">画幅
            <select id="fusionGenerationAspect">${aspectOptions}</select>
          </label>
          <button class="btn primary" id="fusionGenerateBtn">根据分镜生成镜头图候选</button>
        </div>
      </div>
      <div class="cards">${cands}</div>
      <div class="notes">
        <label>心仪的点 / 要保留的画面
          <textarea data-fusion-note="likes">${esc(note.likes||"")}</textarea></label>
        <label>调整方向 / 下一版要求
          <textarea data-fusion-note="adjustments">${esc(note.adjustments||"")}</textarea></label>
        <div class="state-actions">
          <button class="btn" id="fusionNextRound">进入下一版</button>
          <button class="btn primary" id="fusionConfirmShot">${FUSION_STATE.finals[s.no]?'已确认 · 取消确认':'确认此镜镜头图'}</button>
        </div>
      </div>
    </section>`;
  bindFusionStage(stage, s);
}
function bindFusionStage(stage, s){
  stage.querySelectorAll("[data-upload-trigger]").forEach(btn=>btn.onclick=()=>{
    const input = stage.querySelector(`[data-upload-input="${btn.dataset.uploadTrigger}"]`);
    if(input) input.click();
  });
  stage.querySelectorAll("[data-open-folder]").forEach(btn=>btn.onclick=()=>openProjectFolder(btn.dataset.openFolder));
  stage.querySelectorAll("[data-upload-input]").forEach(input=>input.onchange=()=>handleFusionUpload(input, s));
  stage.querySelectorAll("[data-lightbox-src]").forEach(img=>img.ondblclick=()=>openLightbox(img.dataset.lightboxSrc, img.dataset.lightboxTitle||""));
  stage.querySelectorAll("[data-fusion-like]").forEach(btn=>btn.onclick=(e)=>{
    e.stopPropagation();
    const id=btn.dataset.fusionLike;
    FUSION_STATE.likes[id]=!FUSION_STATE.likes[id];
    if(!FUSION_STATE.likes[id]) delete FUSION_STATE.likes[id];
    persistFusion(); renderStage();
  });
  stage.querySelectorAll("[data-fusion-note]").forEach(t=>t.oninput=()=>{
    fusionNote(s.no)[t.dataset.fusionNote]=t.value; persistFusion();
  });
  const mode = stage.querySelector("#fusionReplaceMode");
  if(mode) mode.onchange=()=>{ fusionNote(s.no).replaceMode=mode.value; persistFusion(); renderAside(); };
  const aspect = stage.querySelector("#fusionGenerationAspect");
  if(aspect) aspect.onchange=()=>{ fusionNote(s.no).generationAspect=aspect.value; persistFusion(); renderStage(); };
  stage.querySelector("#fusionGenerateBtn").onclick=()=>{
    FUSION_STATE.genRequests[s.no]={shotNo:s.no, aspect:fusionNote(s.no).generationAspect || "portrait", replacementMode:fusionNote(s.no).replaceMode || (s.replaceMode&&s.replaceMode.default) || "compose", requestedAt:new Date().toISOString()};
    persistFusion(); fusionSave(null, "已记录生成镜头图请求；真正调用生图前还需要你确认额度和上传风险");
  };
  stage.querySelector("#fusionNextRound").onclick=()=>{ fusionNote(s.no).nextRound=true; persistFusion(); fusionSave(null, "已记录进入下一版"); };
  stage.querySelector("#fusionConfirmShot").onclick=()=>{
    if(FUSION_STATE.finals[s.no]) delete FUSION_STATE.finals[s.no];
    else {
      const liked = (s.candidates||[]).map(c=>c.id||c.path).find(id=>FUSION_STATE.likes[id]);
      FUSION_STATE.finals[s.no]=liked || "__confirmed_without_candidate__";
    }
    persistFusion(); renderNav(); renderStage(); renderProgress(); renderOverview(); fusionSave(null, "人景合一状态已保存");
  };
}
async function handleFusionUpload(input, shot){
  const file = input.files && input.files[0];
  if(!file) return;
  const [kind, name] = input.dataset.uploadInput.split("::");
  const dataUrl = await new Promise((resolve,reject)=>{ const r=new FileReader(); r.onload=()=>resolve(r.result); r.onerror=reject; r.readAsDataURL(file); });
  const res = await fetch("/api/fusion-upload",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({shotNo:shot.no, episode:(FUSION&&FUSION.episode)||"", kind, name, file:{name:file.name, dataUrl}})});
  const out = await res.json();
  if(!res.ok){ toast(out.error||"上传失败"); return; }
  if(kind==="role"){
    FUSION_STATE.uploadedRefs[shot.no]=FUSION_STATE.uploadedRefs[shot.no]||{};
    FUSION_STATE.uploadedRefs[shot.no][name]={path:out.path, name:file.name};
  } else {
    FUSION_STATE.sceneInputs[shot.no]=FUSION_STATE.sceneInputs[shot.no]||{};
    FUSION_STATE.sceneInputs[shot.no][name]={path:out.path, name:file.name};
  }
  persistFusion(); renderStage(); fusionSave(null, "已上传并保存到本地");
}
async function openProjectFolder(folder){
  const res = await fetch("/api/open-folder",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({path:folder})});
  const out = await res.json().catch(()=>({}));
  toast(res.ok ? "已打开本地文件夹" : (out.error||"打开文件夹失败"));
}

/* ---------- 中栏 ---------- */
function renderStage(){
  if(ACTIVE_MODE==="fusion"){ renderFusionStage(); return; }
  const stage = document.getElementById("stage");
  stage.classList.toggle("landscape", CARD_FORMAT==="landscape");
  stage.classList.toggle("portrait", CARD_FORMAT!=="landscape");
  const role = findRole(CUR.role); const st = role && findState(role, CUR.state);
  if(!role || !st){ stage.innerHTML = `<div class="empty">请选择左侧角色与时期</div>`; return; }
  const groups = normalizeGroups(st);
  const k = keyOf(role.name, st.name);
  const notes = STATE.notes[k] || {};
  const characterMode = isCharacterRole(role.name);
  const candidateLabel = characterMode ? "三视图候选" : "候选";
  const markedText = characterMode ? "已标记待生成 ✓（默认 Gemini Image，保存后由 AI 生成三视图）" : "已标记待生成 ✓（默认 Gemini Image，保存后由 AI 出图）";

  const rowsHtml = groups.map(g=>{
    const eng = (g.engine||"");
    const lowEng = eng.toLowerCase();
    const engClass = (lowEng.includes("midjourney") || lowEng==="mj") ? "mj" : (lowEng.includes("gemini") ? "gemini" : (eng==="导入" ? "imp" : "image2"));
    const hasImg = g.images && g.images.length;
    const cards = (g.images||[]).map((img,idx)=>cardHtml(role, st, g, img, idx+1)).join("");
    let inner;
    if(hasImg){
      inner = `<div class="cards">${cards}</div>`;
    } else if(eng==="导入"){
      inner = `<div class="empty">点右上角「导入图」上传</div>`;
    } else {
      // 空的 Image2/MJ 行：默认展示 4 个候选小卡，点击记录待生成意图
      const marked = (STATE.gen&&STATE.gen[`${k}::${eng}`]);
      const slots = [1,2,3,4].map(n=>`<article class="gen-slot gen-card ${marked?'marked':''}" data-gen-engine="${esc(eng)}" data-gen-slot="${n}">
        <div class="imgwrap"><div class="ph">${marked?markedText:'＋ 单击标记 / 双击生成'}<br>${esc(eng)} ${candidateLabel} ${n}</div></div>
        <div class="meta">${esc((eng||'candidate').toLowerCase().replace(/\s+/g,'-'))}-${characterMode?'threeview':'candidate'}-${n}</div>
      </article>`).join("");
      inner = `<div class="cards">${slots}</div>`;
    }
    return `<div class="row">
      <div class="row-title"><span class="eng ${engClass}">${esc(eng)}</span>
        <span>${esc(g.label||candidateLabel)}</span></div>${inner}</div>`;
  }).join("");

  const picking = (PICK_FINAL===k);
  stage.innerHTML = `
    <div class="crumb">${esc(findModuleName(role.name))} / ${esc(role.name)}</div>
    <div class="head">
      <div><h2>${esc(role.name)} · ${esc(st.name)}</h2>
        <div class="age">${esc(st.age||role.age||"")}</div></div>
      <div class="head-actions">
        <div class="format-toggle" aria-label="候选图画幅">
          <button class="btn ${CARD_FORMAT!=="landscape"?'active':''}" type="button" data-card-format="portrait">竖版</button>
          <button class="btn ${CARD_FORMAT==="landscape"?'active':''}" type="button" data-card-format="landscape">横版</button>
        </div>
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
        <button class="btn" id="nextRound">${characterMode?"进入下一版（三视图）":"进入下一版"}</button>
        <button class="btn primary" id="confirmLook">${STATE.finals[k]?"已确认（取消）":(picking?"点选最终中…":"确认此时期造型")}</button>
      </div>
    </div>`;

  // 爱心按钮负责心仪；卡片本体只在“点选最终”模式下参与选择
  stage.querySelectorAll(".heart").forEach(h=>h.onclick=(e)=>{ e.stopPropagation(); onCardClick(role,st,k,h.dataset.id); });
  stage.querySelectorAll(".delete-img").forEach(b=>b.onclick=(e)=>{
    e.stopPropagation();
    deleteImage(role, st, k, b.dataset.id);
  });
  stage.querySelectorAll(".lockbtn").forEach(b=>b.onclick=(e)=>{
    e.stopPropagation(); toggleLock(k, b.dataset.kind, b.dataset.id);
    renderStage(); renderNav(); renderOverview();
  });
  stage.querySelectorAll("[data-upload-slot]").forEach(c=>{
    c.onclick=(e)=>{
      e.preventDefault();
      if(PICK_FINAL===k) return;
      uploadImageToImageSlot(c, role, st);
    };
  });
  stage.querySelectorAll(".card").forEach(c=>{
    if(c.classList.contains("gen-slot")) return;
    if(c.dataset.uploadSlot) return;
    c.onclick=()=>{
      if(PICK_FINAL!==k) return;
      clearTimeout(CARD_CLICK_TIMER);
      CARD_CLICK_TIMER = setTimeout(()=>onCardClick(role,st,k,c.dataset.id), 220);
    };
    c.ondblclick=(e)=>{
      e.preventDefault();
      clearTimeout(CARD_CLICK_TIMER);
      openLightbox(c.dataset.src, c.dataset.id);
    };
  });
  // 空行：单击记录生成意图，双击真实调用接口生成该槽位
  stage.querySelectorAll(".gen-slot").forEach(el=>{
    el.onclick=()=>{
      clearTimeout(CARD_CLICK_TIMER);
      CARD_CLICK_TIMER = setTimeout(()=>{
        const gk = `${k}::${el.dataset.genEngine}`;
        STATE.gen = STATE.gen||{}; STATE.gen[gk] = !STATE.gen[gk];
        if(!STATE.gen[gk]) delete STATE.gen[gk];
        autosave(); renderStage();
        toast(STATE.gen[gk]?"已标记待生成，默认 Gemini Image 补图":"已取消标记");
      }, 220);
    };
    el.ondblclick=(e)=>{
      e.preventDefault();
      clearTimeout(CARD_CLICK_TIMER);
      generateSlot(el, role, st, k);
    };
  });
  stage.querySelectorAll("[data-card-format]").forEach(btn=>btn.onclick=()=>{
    CARD_FORMAT = btn.dataset.cardFormat==="landscape" ? "landscape" : "portrait";
    localStorage.setItem(CARD_FORMAT_KEY, CARD_FORMAT);
    renderStage();
    toast(CARD_FORMAT==="landscape" ? "已切换为横版候选" : "已切换为竖版候选");
  });
  stage.querySelectorAll(".notes textarea").forEach(t=>t.oninput=()=>{
    STATE.notes[k] = STATE.notes[k]||{}; STATE.notes[k][t.dataset.field]=t.value; persist();
  });
  document.getElementById("confirmLook").onclick=()=>onConfirm(role,st,k);
  document.getElementById("nextRound").onclick=()=>{
    STATE.notes[k]=STATE.notes[k]||{};
    STATE.notes[k].nextRound=true;
    STATE.notes[k].nextEngine="Gemini Image";
    STATE.notes[k].nextOutputType=characterMode ? "character_turnaround_3view" : "visual_candidate";
    autosave();
    toast(characterMode ? "已标记『进入下一版』：默认 Gemini Image 生成三视图" : "已标记『进入下一版』：默认 Gemini Image 生成 4 张");
  };
}

function isImageToImageEngine(engine){
  const text = String(engine||"").toLowerCase();
  return String(engine||"").includes("图生图") || text.includes("img2img") || text.includes("image-to-image");
}

async function refreshManifestAndRender(){
  MANIFEST = await (await fetch("/api/manifest")).json();
  renderNav(); renderStage(); renderAside(); renderProgress(); renderOverview();
}

function chooseLocalImage(){
  return new Promise(resolve=>{
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/png,image/jpeg,image/webp";
    input.onchange = ()=>resolve(input.files && input.files[0] ? input.files[0] : null);
    input.click();
  });
}

function fileToDataUrl(file){
  return new Promise((resolve,reject)=>{
    const reader = new FileReader();
    reader.onload = ()=>resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function uploadImageToImageSlot(card, role, st){
  const slot = Number(card.dataset.uploadSlot || 1);
  const engine = card.dataset.uploadEngine || "图生图";
  const file = await chooseLocalImage();
  if(!file) return;
  if(!/^image\/(png|jpeg|webp)$/.test(file.type)){
    toast("请选择 PNG / JPG / WebP 图片");
    return;
  }
  toast("正在上传到图生图卡片...");
  try{
    const dataUrl = await fileToDataUrl(file);
    const res = await fetch("/api/upload-slot", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({role:role.name, state:st.name, engine, slot, file:{name:file.name, dataUrl}})
    });
    const out = await res.json();
    if(!res.ok) throw new Error(out.error || "上传失败");
    await refreshManifestAndRender();
    toast("已上传到图生图卡片");
  }catch(err){
    toast(err.message || "上传失败");
  }
}

async function generateSlot(el, role, st, k){
  const engine = el.dataset.genEngine || "";
  const slot = Number(el.dataset.genSlot || 1);
  const low = engine.toLowerCase();
  if(low.includes("midjourney") || low==="mj"){
    toast("Midjourney 当前作为手动渠道，请复制提示词生成");
    return;
  }
  const ok = confirm(`双击会真实调用出图接口并消耗额度。\n\n生成：${role.name} / ${st.name}\n渠道：${engine} 第 ${slot} 张\n\n继续吗？`);
  if(!ok) return;
  el.classList.add("marked");
  toast("生成中，可能需要几十秒...");
  try{
    const res = await fetch("/api/generate-slot", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({role:role.name, state:st.name, engine, slot})
    });
    const out = await res.json();
    if(!res.ok) throw new Error(out.error || "生成失败");
    await refreshManifestAndRender();
    toast("已生成并写入当前卡片");
  }catch(err){
    toast(err.message || "生成失败");
    el.classList.remove("marked");
  }
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

function lockOptionsForRole(roleName){
  const modName = findModuleName(roleName);
  if(modName.includes("场景美术") || modName.includes("道具定版") || modName.includes("关键道具")){
    return [
      {kind:"atmosphere", label:"氛围", title:"锁氛围气质"},
      {kind:"color", label:"色调", title:"锁色调与光影"},
      {kind:"composition", label:"构图", title:"锁镜头构图"},
      {kind:"architecture", label:"建筑", title:"锁建筑/空间结构"}
    ];
  }
  return [
    {kind:"face", label:"脸", title:"锁脸"},
    {kind:"body", label:"身体", title:"锁身体比例和姿态"},
    {kind:"clothes", label:"衣服", title:"锁衣服材质和配饰"},
    {kind:"hair", label:"发型", title:"锁发型和发量"}
  ];
}

function lockLabel(kind){
  const all = [
    ...lockOptionsForRole("__default__"),
    {kind:"atmosphere", label:"氛围"},
    {kind:"color", label:"色调"},
    {kind:"composition", label:"构图"},
    {kind:"architecture", label:"建筑"}
  ];
  const hit = all.find(x=>x.kind===kind);
  return hit ? hit.label : kind;
}

function cardHtml(role, st, group, img, slot){
  const id = img.id || img.path;
  if(isDeleted(id)) return "";
  const liked = !!STATE.likes[id];
  const k = keyOf(role.name, st.name);
  const locks = (STATE.locks||{})[k] || {};
  const uploadable = !img.path && isImageToImageEngine(group.engine);
  // 单选最终：finals[k] 存被选中的那张 id
  const isFinal = STATE.finals[k] === id;
  const pickable = (PICK_FINAL===k && liked);
  const inner = img.path
    ? `<img src="/asset/${encodeURI(img.path)}" alt="${esc(id)}" loading="lazy">`
    : `<div class="ph">${uploadable?'＋ 点击上传图生图参考':'占位'}<br>${esc(img.note||id)}</div>`;
  const lockButtons = uploadable ? "" : lockOptionsForRole(role.name).map(opt =>
    `<button class="lockbtn ${locks[opt.kind]===id?'active':''}" data-kind="${esc(opt.kind)}" data-id="${esc(id)}" title="${esc(opt.title)}">${esc(opt.label)}</button>`
  ).join("");
  return `<article class="card ${liked?'liked':''} ${isFinal?'final':''} ${pickable?'pickable':''}" data-id="${esc(id)}" data-src="${img.path?('/asset/'+encodeURI(img.path)):''}" ${uploadable?`data-upload-slot="${slot||1}" data-upload-engine="${esc(group.engine||'图生图')}"`:''}>
    <div class="locks">${lockButtons}</div>
    ${uploadable?'':`<button class="heart" data-id="${esc(id)}" title="心仪">${liked?'❤':'♡'}</button>`}
    <div class="imgwrap">${inner}</div>
    ${uploadable?'':`<button class="delete-img" data-id="${esc(id)}" type="button" title="从评审中移除">删除</button>`}
    <div class="meta"><span>${esc(id)}</span><span class="finaltag">最终</span></div>
  </article>`;
}

function toggleLike(id){ STATE.likes[id] = !STATE.likes[id]; if(!STATE.likes[id]) delete STATE.likes[id]; persist(); }
function isDeleted(id){ return !!(STATE.deleted && STATE.deleted[id]); }
function deleteImage(role, st, k, id){
  if(!id) return;
  if(!confirm("从当前评审页移除这张图？\\n只会软删除并保存状态，不会删除硬盘图片文件。")) return;
  STATE.deleted = STATE.deleted || {};
  STATE.deleted[id] = {role:role.name, state:st.name, deletedAt:new Date().toISOString()};
  delete STATE.likes[id];
  if(STATE.finals[k]===id) delete STATE.finals[k];
  const locks = (STATE.locks||{})[k] || {};
  for(const kind of Object.keys(locks)) if(locks[kind]===id) delete locks[kind];
  if(Object.keys(locks).length===0 && STATE.locks) delete STATE.locks[k];
  autosave();
  renderStage(); renderNav(); renderProgress(); renderOverview();
  toast("已从评审中移除，原图文件未删除");
}
function toggleLock(k, kind, id){
  STATE.locks = STATE.locks || {};
  STATE.locks[k] = STATE.locks[k] || {};
  const current = STATE.locks[k][kind];
  if(current === id) delete STATE.locks[k][kind];
  else STATE.locks[k][kind] = id;
  if(Object.keys(STATE.locks[k]).length===0) delete STATE.locks[k];
  autosave();
  const label = lockLabel(kind);
  toast(current === id ? `已取消锁${label}` : `已锁${label}参考`);
}

function normalizeGroups(st){
  // 顺序：导入（若有）→ Gemini Image → Image2 → Midjourney → 其余；MJ 只作为 Midjourney 别名，不单独补行
  const gs = st.groups || [];
  const find = (frag)=>gs.find(g=>(g.engine||"").toLowerCase().includes(frag));
  const findMidjourney = ()=>gs.find(g=>{
    const e=(g.engine||"").toLowerCase();
    return e==="mj" || e.includes("midjourney");
  });
  const imp = gs.find(g=>(g.engine||"")==="导入");
  const characterMode = isCharacterRole(CUR.role);
  const defaultLabel = characterMode ? "三视图候选" : "候选";
  const gemini = find("gemini") || {engine:"Gemini Image", label:characterMode ? "下一版/图生图默认三视图" : "下一版/图生图默认候选", images:[]};
  const i2 = find("image2") || {engine:"Image2", label:defaultLabel, images:[]};
  const mj = findMidjourney() || {engine:"Midjourney", label:defaultLabel, images:[]};
  const rest = gs.filter(g=>g!==i2 && g!==mj && g!==imp && g!==gemini);
  return [...(imp?[imp]:[]), gemini, i2, mj, ...rest];
}
function stateImageIds(role, st){
  const ids=[];
  for(const g of (st.groups||[])) for(const im of (g.images||[])){
    const id = im.id||im.path;
    if(id && !isDeleted(id)) ids.push(id);
  }
  return ids;
}
function findModuleName(roleName){
  for(const {mod, role} of iterRoles("all")) if(role.name===roleName) return mod.name||"";
  return "";
}
function isCharacterRole(roleName){
  const modName = findModuleName(roleName);
  return /人物|定妆/.test(modName) && !/场景|道具/.test(modName);
}

/* ---------- 右栏 ---------- */
function renderAside(){
  if(ACTIVE_MODE==="fusion"){ renderFusionAside(); return; }
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
        <div class="phead"><span class="eng mj">Midjourney</span><button class="copy" data-copy="mj">复制</button></div>
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

function renderFusionAside(){
  const aside = document.getElementById("aside");
  const s = currentFusionShot();
  if(!s){ aside.innerHTML = ""; return; }
  const sh = s.shot || {};
  const note = fusionNote(s.no);
  const preview = findPreviewShot(s.no);
  const mode = note.replaceMode || (s.replaceMode&&s.replaceMode.default) || "compose";
  const storyTitle = FUSION_SOURCE==="preview" ? "剪辑版分镜故事" : "分镜故事";
  const promptTitle = FUSION_SOURCE==="preview" ? "剪辑版提示词 / 画面描述" : "分镜提示词";
  const promptSource = FUSION_SOURCE==="preview" ? "只读，来自剪辑版分镜" : "只读，来自 07_绘图提示词";
  const row=(k,v)=> v ? `<div class="k">${esc(k)}</div><div class="v">${esc(v)}</div>` : "";
  const previewDetailBlock = preview ? `
    <div class="prompt-block">
      <h3>当前同号剪辑镜头</h3>
      <div class="kv">
        ${row("时间", `${preview.start||""}${preview.duration?` · ${preview.duration}秒`:""}`)}
        ${row("类型", preview.shot_type)}
        ${row("画面", preview.image)}
        ${row("动效/生成方式", preview.motion)}
        ${row("旁白/字幕", preview.subtitle)}
        ${row("音效", preview.sound)}
        ${row("平台", preview.platform)}
        ${row("优先级", preview.priority)}
      </div>
    </div>` : `
    <div class="prompt-block">
      <h3>当前同号剪辑镜头</h3>
      <div class="pempty">剪辑版分镜里没有匹配到镜 ${esc(s.no)}。</div>
    </div>`;
  aside.innerHTML = `
    <div class="tone"><div class="lab">人景合一方式</div><div class="val">${esc(FUSION_MODE_LABELS[mode]||mode)}</div></div>
    <div class="wv-block">
      <h3>${storyTitle}</h3>
      <div class="era">镜 ${esc(s.no)} · ${esc(sh["画面目的"]||"")}</div>
      <div class="kv">
        ${row("景别", sh["景别"])}
        ${row("运镜", sh["运镜"])}
        ${row("时长", sh["时长"])}
        ${row("场景/镜头", sh["场景"])}
        ${row("光影色彩", sh["光影"])}
        ${sh["台词"]?`<div class="k">台词</div><div class="v">${esc(sh["台词"])}</div>`:""}
      </div>
    </div>
    ${previewDetailBlock}
    <div class="prompt-block">
      <h3>${promptTitle} <span class="pmuted">${promptSource}</span></h3>
      <pre class="fusion-prompt">${esc(s.prompt||"")}</pre>
      ${s.negative?`<h3 style="margin-top:14px">负面提示词</h3><pre class="fusion-prompt">${esc(s.negative)}</pre>`:""}
    </div>`;
}

/* ---------- 进度 & 总览 ---------- */
function renderProgress(){
  document.getElementById("progress").innerHTML =
    `${modeLabel(ACTIVE_MODE)} 已确认 <b>${confirmedCount(ACTIVE_MODE)}</b> / ${totalStates(ACTIVE_MODE)} ${ACTIVE_MODE==="fusion"?"镜":"个"}`;
}
function renderOverview(){
  if(ACTIVE_MODE==="fusion"){
    const done = confirmedCount("fusion"), total = totalStates("fusion");
    const btn = document.getElementById("overviewBtn");
    btn.disabled = total===0;
    btn.textContent = "保存人景合一";
    document.getElementById("overviewSum").innerHTML = total
      ? `镜头图确认 <b>${done}</b> / ${total}，生成请求会保存到 10_镜头图/selection-state.json`
      : `还没有可评审镜头，请先生成 shot-manifest.json`;
    return;
  }
  const done = confirmedCount("all"), total = totalStates("all");
  const all = done===total && total>0;
  const btn = document.getElementById("overviewBtn");
  btn.disabled = !all;
  btn.textContent = "生成总览图";
  document.getElementById("overviewSum").innerHTML = all
    ? `全部 <b>${total}</b> 个时期造型已确认，可生成总览图`
    : `还差 ${total-done} 个时期未确认（总览图需全部确认后生成）`;
}

/* ---------- 保存 ---------- */
function imgById(id){
  for(const {role} of iterRoles("all"))
    for(const st of (role.states||[]))
      for(const g of (st.groups||[]))
        for(const im of (g.images||[]))
          if((im.id||im.path)===id) return {role, st, g, im};
  return null;
}
function confirmedLooks(){
  // 供下一步出图：每个已确认时期的「最终单张」+ 心仪备选
  const out=[];
  for(const {mod, role} of iterRoles("all"))
    for(const st of (role.states||[])){
      const k = keyOf(role.name, st.name);
      const finalId = STATE.finals[k];
      if(!finalId) continue;
      let finalRef=null; const alts=[];
      for(const g of (st.groups||[]))
        for(const im of (g.images||[])){
          const id = im.id||im.path;
          if(isDeleted(id)) continue;
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
    if(parts.length>=3){
      const role = parts[0], state = parts[1], engine = parts.slice(2).join("::");
      out.push({role, state, engine, outputType: isCharacterRole(role) ? "character_turnaround_3view" : "visual_candidate"});
    }
  }
  return out;
}
function nextRoundRequests(){
  const out=[];
  for(const key in (STATE.notes||{})){
    const note = STATE.notes[key] || {};
    if(!note.nextRound) continue;
    const parts = key.split("::");
    if(parts.length<2) continue;
    const role = parts[0], state = parts.slice(1).join("::");
    out.push({
      role, state,
      engine: note.nextEngine || "Gemini Image",
      outputType: note.nextOutputType || (isCharacterRole(role) ? "character_turnaround_3view" : "visual_candidate"),
      locks: (STATE.locks||{})[key] || {},
      likedNote: note.likes || "",
      adjustments: note.adjustments || ""
    });
  }
  return out;
}
function buildPayload(extra){
  return Object.assign({
    project: MANIFEST.project || "",
    round: MANIFEST.round || 1,
    likes: STATE.likes, locks: STATE.locks||{}, finals: STATE.finals, notes: STATE.notes, gen: STATE.gen||{}, deleted: STATE.deleted||{},
    overviewRequested: STATE.overviewRequested,
    confirmedLooks: confirmedLooks(), genRequests: genRequests(), nextRoundRequests: nextRoundRequests(),
    confirmedCount: confirmedCount("all"), totalStates: totalStates("all"),
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
function fusionConfirmedShots(){
  const out=[];
  for(const s of fusionShots()){
    const finalId = FUSION_STATE.finals[s.no] || "";
    let finalCandidate = null;
    for(const c of (s.candidates||[])){
      const id = c.id || c.path;
      if(id === finalId) finalCandidate = {id, path:c.path||""};
    }
    out.push({no:s.no, prompt:s.prompt, shot:s.shot||{}, refs:s.refs||[],
      replacementMode:fusionNote(s.no).replaceMode || (s.replaceMode&&s.replaceMode.default) || "compose",
      uploadedRefs:((FUSION_STATE.uploadedRefs||{})[s.no]||{}),
      sceneInputs:((FUSION_STATE.sceneInputs||{})[s.no]||{}),
      finalCandidate});
  }
  return out;
}
function fusionPayload(extra){
  return Object.assign({
    project:(FUSION&&FUSION.project)||MANIFEST.project||"",
    episode:(FUSION&&FUSION.episode)||"",
    likes:FUSION_STATE.likes, finals:FUSION_STATE.finals, notes:FUSION_STATE.notes,
    uploadedRefs:FUSION_STATE.uploadedRefs, sceneInputs:FUSION_STATE.sceneInputs,
    genRequests:FUSION_STATE.genRequests, exportRequested:FUSION_STATE.exportRequested,
    confirmedShots:fusionConfirmedShots(),
    confirmedCount:confirmedCount("fusion"), totalShots:totalStates("fusion")
  }, extra||{});
}
async function fusionSave(extra, okMsg, silent){
  persistFusion();
  try{
    const res = await fetch("/api/fusion-save", {method:"POST",
      headers:{"Content-Type":"application/json"}, body:JSON.stringify(fusionPayload(extra))});
    if(!silent) toast(res.ok ? (okMsg||"已保存到 10_镜头图/selection-state.json") : "保存失败");
    return res.ok;
  }catch(e){ if(!silent) toast("保存失败"); return false; }
}
document.getElementById("saveBtn").onclick=()=> ACTIVE_MODE==="fusion" ? fusionSave() : save();
document.getElementById("overviewBtn").onclick=async ()=>{
  if(ACTIVE_MODE==="fusion"){
    FUSION_STATE.exportRequested = true; persistFusion();
    const ok = await fusionSave({exportRequested:true}, "已保存人景合一状态");
    if(ok) renderOverview();
    return;
  }
  STATE.overviewRequested = true; persist();
  const ok = await save({overviewRequested:true}, "已记录『生成总览图』意图，保存成功，我会据此出图");
  if(ok) renderOverview();
};

/* ---------- 大图预览 ---------- */
function openLightbox(src, title){
  if(!src){ toast("这张还没有图片文件"); return; }
  const box = document.getElementById("lightbox");
  document.getElementById("lightboxImg").src = src;
  document.getElementById("lightboxImg").alt = title || "";
  document.getElementById("lightboxTitle").textContent = title || "";
  box.classList.add("open");
  box.setAttribute("aria-hidden","false");
}
function closeLightbox(){
  const box = document.getElementById("lightbox");
  box.classList.remove("open");
  box.setAttribute("aria-hidden","true");
  document.getElementById("lightboxImg").src = "";
}
document.getElementById("lightboxClose").onclick=closeLightbox;
document.getElementById("lightbox").onclick=(e)=>{ if(e.target.id==="lightbox") closeLightbox(); };
document.addEventListener("keydown",(e)=>{ if(e.key==="Escape") closeLightbox(); });

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

PREVIEW_PAGE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>娃娃仙剪辑版静帧候选</title>
<style>
:root{--bg:#f4f0e9;--panel:#fffdf9;--line:#ddd6ca;--ink:#26221c;--muted:#7c7264;--accent:#24695c;--warm:#b35a32}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei",system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 22px;background:rgba(244,240,233,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
h1{margin:0;font-size:18px}.meta{font-size:13px;color:var(--muted)}a{color:var(--accent);text-decoration:none}
.wrap{display:grid;grid-template-columns:260px minmax(0,1fr);height:calc(100vh - 58px)}
nav{overflow:auto;border-right:1px solid var(--line);background:#efe9e0;padding:12px}
.shotbtn{width:100%;border:1px solid transparent;background:transparent;text-align:left;padding:9px 10px;border-radius:8px;cursor:pointer;color:var(--ink)}
.shotbtn:hover,.shotbtn.active{background:#fffaf1;border-color:var(--line)}
.shotbtn b{font-size:14px}.shotbtn span{display:block;font-size:12px;color:var(--muted);margin-top:3px}
main{overflow:auto;padding:18px 22px 32px}
.head{display:flex;justify-content:space-between;gap:16px;margin-bottom:14px}.head h2{margin:0 0 5px;font-size:22px}.desc{color:var(--muted);font-size:14px;line-height:1.6}
.channel{margin:18px 0 26px}.channel h3{margin:0 0 10px;font-size:15px;color:var(--warm);display:flex;align-items:center;gap:8px}.channel h3 small{font-weight:400;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden;box-shadow:0 8px 22px rgba(68,52,29,.08)}
.imgbox{aspect-ratio:16/9;background:#e7dfd2;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:13px}
.imgbox img{width:100%;height:100%;object-fit:cover;display:block;cursor:zoom-in}
.cap{display:flex;justify-content:space-between;gap:8px;padding:8px 10px;font-size:12px;color:var(--muted)}.cap b{color:var(--ink)}
.missing{border:1px dashed #c9bda9;background:#f7f1e8;color:#8b7a62;padding:20px;border-radius:8px;text-align:center}
.lightbox{position:fixed;inset:0;background:rgba(0,0,0,.82);display:none;align-items:center;justify-content:center;z-index:20;padding:20px}.lightbox.open{display:flex}.lightbox img{max-width:96vw;max-height:90vh;object-fit:contain;background:#111}.close{position:fixed;right:18px;top:14px;border:1px solid rgba(255,255,255,.35);background:rgba(0,0,0,.4);color:white;border-radius:999px;width:38px;height:38px;font-size:24px;cursor:pointer}
@media(max-width:980px){.wrap{grid-template-columns:1fr;height:auto}nav{display:flex;overflow:auto;border-right:0;border-bottom:1px solid var(--line)}.shotbtn{min-width:150px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
</head>
<body>
<header>
  <div><h1>《娃娃仙》剪辑版静帧候选</h1><div class="meta" id="summary">加载中...</div></div>
  <div class="meta"><a href="/">返回视觉定版评审</a></div>
</header>
<div class="wrap"><nav id="nav"></nav><main id="main"></main></div>
<div class="lightbox" id="lightbox"><button class="close" id="close">×</button><img id="big" alt=""></div>
<script>
let DATA=[], CUR=0;
const CHANNELS=["Image2","即梦_Seedream","Nano_Banana_Pro","Midjourney"];
fetch("/api/preview-candidates").then(r=>r.json()).then(data=>{
  DATA=data.shots||[]; renderNav(); renderMain();
  document.getElementById("summary").textContent=`${data.generated}/${data.total} 张已生成；Midjourney 当前为手动渠道`;
});
function esc(s){return String(s||"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]));}
function renderNav(){
  document.getElementById("nav").innerHTML=DATA.map((s,i)=>`<button class="shotbtn ${i===CUR?'active':''}" data-i="${i}"><b>镜头 ${esc(s.shot)}</b><span>${esc(s.priority)} · ${s.generated}/16 已生成</span></button>`).join("");
  document.querySelectorAll(".shotbtn").forEach(b=>b.onclick=()=>{CUR=Number(b.dataset.i);renderNav();renderMain();});
}
function renderMain(){
  const s=DATA[CUR]; if(!s){document.getElementById("main").innerHTML="<div class='missing'>没有候选图数据</div>";return;}
  const rows=CHANNELS.map(ch=>{
    const imgs=(s.channels&&s.channels[ch])||[];
    const cards=[1,2,3,4].map(n=>{
      const img=imgs.find(x=>x.variant===n);
      if(!img)return `<article class="card"><div class="imgbox">未生成</div><div class="cap"><b>${ch}</b><span>#${n}</span></div></article>`;
      return `<article class="card"><div class="imgbox"><img src="${img.url}" alt="${esc(img.name)}" data-src="${img.url}"></div><div class="cap"><b>${ch}</b><span>#${n}</span></div></article>`;
    }).join("");
    return `<section class="channel"><h3>${esc(ch)} <small>${imgs.length}/4</small></h3><div class="grid">${cards}</div></section>`;
  }).join("");
  document.getElementById("main").innerHTML=`<div class="head"><div><h2>镜头 ${esc(s.shot)}</h2><div class="desc">${esc(s.image)}</div></div><div class="meta">${esc(s.priority)} · ${esc(s.subtitle)}</div></div>${rows}`;
  document.querySelectorAll("img[data-src]").forEach(img=>img.ondblclick=()=>openBig(img.dataset.src));
}
function openBig(src){document.getElementById("big").src=src;document.getElementById("lightbox").classList.add("open");}
function closeBig(){document.getElementById("lightbox").classList.remove("open");document.getElementById("big").src="";}
document.getElementById("close").onclick=closeBig;document.getElementById("lightbox").onclick=e=>{if(e.target.id==="lightbox")closeBig();};document.addEventListener("keydown",e=>{if(e.key==="Escape")closeBig();});
</script>
</body>
</html>"""


def make_handler(manifest_path: Path, output_path: Path):
    root = manifest_path.parent.resolve()
    project_root = root.parent.parent.resolve()
    preview_dir = project_root / "09_素材与参考" / "预告剪辑版"
    preview_candidates = preview_dir / "images_candidates"
    preview_shots = preview_dir / "manifests" / "preview_shots.json"
    fusion_dir = project_root / "10_镜头图"
    fusion_manifest = fusion_dir / "shot-manifest.json"
    fusion_state = fusion_dir / "selection-state.json"
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
            if path == "/preview-candidates":
                self._send(PREVIEW_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/manifest":
                # 每次重新读盘，便于热更新 manifest
                data = load_manifest(manifest_path)
                self._send_json(data)
                return
            if path == "/api/preview-candidates":
                self._send_json(self._preview_payload())
                return
            if path == "/api/fusion-manifest":
                if fusion_manifest.exists():
                    self._send_json(load_manifest(fusion_manifest))
                else:
                    self._send_json({"project": manifest.get("project", ""), "shots": [], "missing": str(fusion_manifest)})
                return
            if path.startswith("/asset/"):
                rel = unquote(path[len("/asset/"):])
                target = self._resolve_asset(rel)
                if not target:
                    self._send_json({"error": "not found", "path": rel}, 404)
                    return
                ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                self._send(target.read_bytes(), ctype)
                return
            if path.startswith("/preview-asset/"):
                rel = unquote(path[len("/preview-asset/"):])
                target = (preview_candidates / rel).resolve()
                if not str(target).startswith(str(preview_candidates.resolve())) or not target.exists():
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
            if path == "/api/fusion-save":
                length = int(self.headers.get("Content-Length", "0") or "0")
                data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
                fusion_dir.mkdir(parents=True, exist_ok=True)
                fusion_state.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                self._send_json({"ok": True, "path": str(fusion_state)})
                return
            if path == "/api/fusion-upload":
                self._handle_fusion_upload()
                return
            if path == "/api/open-folder":
                self._handle_open_folder()
                return
            if path == "/api/import":
                self._handle_import()
                return
            if path == "/api/upload-slot":
                self._handle_upload_slot()
                return
            if path == "/api/generate-slot":
                self._handle_generate_slot()
                return
            self._send_json({"error": "not found"}, 404)

        def _resolve_asset(self, rel: str):
            candidates = [(root / rel).resolve(), (project_root / rel).resolve()]
            for target in candidates:
                try:
                    if target.exists() and (target.is_relative_to(root) or target.is_relative_to(project_root)):
                        return target
                except AttributeError:
                    if target.exists() and (str(target).startswith(str(root)) or str(target).startswith(str(project_root))):
                        return target
            return None

        def _handle_upload_slot(self):
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                self._send_json({"error": "empty body"}, 400)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as exc:
                self._send_json({"error": f"bad json: {exc}"}, 400)
                return

            role_name = (payload.get("role") or "").strip()
            state_name = (payload.get("state") or "").strip()
            engine = (payload.get("engine") or "图生图").strip()
            file = payload.get("file") or {}
            try:
                slot = max(1, min(4, int(payload.get("slot") or 1)))
            except Exception:
                slot = 1
            if not role_name or not state_name or not file:
                self._send_json({"error": "missing role/state/file"}, 400)
                return
            data_url = file.get("dataUrl", "")
            m = re.match(r"data:image/(png|jpeg|jpg|webp);base64,(.+)", data_url, re.I | re.S)
            if not m:
                self._send_json({"error": "只支持 PNG / JPG / WebP 图片"}, 400)
                return
            ext = "jpg" if m.group(1).lower() in {"jpeg", "jpg"} else m.group(1).lower()
            try:
                image_bytes = base64.b64decode(m.group(2))
            except Exception:
                self._send_json({"error": "bad image base64"}, 400)
                return

            current = load_manifest(manifest_path)
            found = self._find_role_state(current, role_name, state_name)
            if not found:
                self._send_json({"error": "manifest 中找不到该角色/时期"}, 404)
                return
            module, role, state = found
            rel_path, image_id = self._save_uploaded_slot(module, role, state, engine, slot, image_bytes, ext, file.get("name"))
            group = self._ensure_group(state, engine)
            images = group.setdefault("images", [])
            while len(images) < slot:
                idx = len(images) + 1
                images.append({
                    "id": f"{self._safe_name(role.get('name'))}-{self._safe_name(state.get('name'))}-{self._safe_name(engine)}-{idx:02d}",
                    "path": "",
                    "note": f"{engine} 候选 {idx}",
                })
            images[slot - 1] = {
                **(images[slot - 1] or {}),
                "id": image_id,
                "path": rel_path,
                "note": f"{engine} 上传参考图 {slot}",
            }
            manifest_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "path": rel_path, "id": image_id, "engine": engine, "slot": slot})

        def _handle_generate_slot(self):
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0:
                self._send_json({"error": "empty body"}, 400)
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as exc:
                self._send_json({"error": f"bad json: {exc}"}, 400)
                return

            role_name = (payload.get("role") or "").strip()
            state_name = (payload.get("state") or "").strip()
            engine = (payload.get("engine") or "Image2").strip()
            try:
                slot = max(1, min(4, int(payload.get("slot") or 1)))
            except Exception:
                slot = 1
            if not role_name or not state_name:
                self._send_json({"error": "missing role/state"}, 400)
                return
            if self._is_midjourney(engine):
                self._send_json({"error": "Midjourney 当前接口不可自动生成，请复制提示词手动生成"}, 400)
                return

            api_key = self._read_tuzi_key()
            if not api_key:
                self._send_json({"error": "未找到 TUZI_API_KEY。请先写入系统环境变量，再重启本地服务。"}, 400)
                return

            current = load_manifest(manifest_path)
            found = self._find_role_state(current, role_name, state_name)
            if not found:
                self._send_json({"error": "manifest 中找不到该角色/时期"}, 404)
                return
            module, role, state = found

            prompt = self._build_generation_prompt(current, module, role, state, engine, slot)
            try:
                image_bytes = self._request_image_generation(api_key, prompt)
            except Exception as exc:
                self._send_json({"error": f"生成失败: {exc}"}, 502)
                return

            rel_path, image_id = self._save_generated_image(module, role, state, engine, slot, image_bytes)
            group = self._ensure_group(state, engine)
            images = group.setdefault("images", [])
            while len(images) < slot:
                idx = len(images) + 1
                images.append({
                    "id": f"{self._safe_name(role.get('name'))}-{self._safe_name(state.get('name'))}-{self._safe_name(engine)}-{idx:02d}",
                    "path": "",
                    "note": f"{engine} 候选 {idx}",
                })
            images[slot - 1] = {
                **(images[slot - 1] or {}),
                "id": image_id,
                "path": rel_path,
                "note": f"{engine} 双击生成候选 {slot}",
            }
            manifest_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "path": rel_path, "id": image_id, "engine": engine, "slot": slot})

        def _find_role_state(self, data: dict, role_name: str, state_name: str):
            role_key = role_name.split(" / ")[0].strip()
            for module in data.get("modules", [{"name": "", "roles": data.get("roles", [])}]):
                for role in module.get("roles", []):
                    name = (role.get("name") or "").strip()
                    if name != role_name and name.split(" / ")[0].strip() != role_key:
                        continue
                    for state in role.get("states", []):
                        if (state.get("name") or "").strip() == state_name:
                            return module, role, state
            return None

        def _safe_name(self, value) -> str:
            text = str(value or "item").strip() or "item"
            text = re.sub(r"[\\/:*?\"<>|\s]+", "_", text)
            text = re.sub(r"_+", "_", text).strip("_")
            return text[:80] or "item"

        def _is_midjourney(self, engine: str) -> bool:
            low = (engine or "").lower()
            return low == "mj" or "midjourney" in low

        def _is_character_module(self, module_name: str) -> bool:
            return bool(re.search(r"人物|定妆", module_name or "")) and not bool(re.search(r"场景|道具", module_name or ""))

        def _category_for_module(self, module_name: str) -> str:
            if re.search(r"场景", module_name or ""):
                return "场景"
            if re.search(r"道具", module_name or ""):
                return "道具"
            if self._is_character_module(module_name):
                return "人物"
            return "候选"

        def _ensure_group(self, state: dict, engine: str) -> dict:
            groups = state.setdefault("groups", [])
            for group in groups:
                existing = group.get("engine") or ""
                if existing == engine or (self._is_midjourney(existing) and self._is_midjourney(engine)):
                    return group
            label = "三视图候选" if engine in {"Image2", "Gemini Image"} else "候选"
            group = {"engine": engine, "label": label, "images": []}
            groups.append(group)
            return group

        def _build_generation_prompt(self, data: dict, module: dict, role: dict, state: dict, engine: str, slot: int) -> str:
            module_name = module.get("name") or ""
            worldview = state.get("worldview") or {}
            prompts = state.get("prompts") or {}
            source_prompt = prompts.get("image2") or prompts.get("gemini") or prompts.get("base") or ""
            tone = state.get("styleTone") or role.get("styleTone") or data.get("styleTone") or ""
            details = [
                f"项目: {data.get('project') or '漫剧项目'}",
                f"模块: {module_name}",
                f"对象: {role.get('name')}",
                f"时期/状态: {state.get('name')}",
                f"年龄/阶段: {state.get('age') or role.get('age') or ''}",
                f"整体质感: {tone}",
                f"时代空间: {worldview.get('era') or ''} {worldview.get('space') or ''}",
                f"服装道具: {worldview.get('costume') or ''} {worldview.get('props') or ''}",
                f"光线氛围: {worldview.get('light') or ''}",
                f"禁止项: {worldview.get('forbid') or ''}",
                f"原始提示词参考: {source_prompt}",
                f"候选编号: {slot}",
            ]
            if self._is_character_module(module_name):
                task = (
                    "生成一张横版16:9人物三视图设定图。画面中同一位虚构演员角色正面、侧面、背面并排，全身，"
                    "五官身份一致，身高体态一致，服装材质和发型一致，站姿自然，背景干净中性，适合后续锁脸、身体、衣服、发型。"
                )
            else:
                task = (
                    "生成一张横版16:9影视概念候选图。突出空间结构、氛围色调、构图和可复用美术细节，"
                    "真实质感，适合后续锁定场景/道具参考。"
                )
            prompt = task + "\n" + "\n".join(x for x in details if x.strip())
            replacements = {
                "恐怖": "民俗悬疑",
                "鬼": "异象",
                "旱魃": "古老异象",
                "尸": "旧物",
                "死": "消逝",
                "血": "暗红痕迹",
                "深坑": "竹林低洼处",
                "斩": "对抗",
                "蛇": "草丛危险动物",
            }
            for bad, safe in replacements.items():
                prompt = prompt.replace(bad, safe)
            return prompt + "\n不要文字，不要水印，不要现代物件，不要明星脸，不要二次元。"

        def _read_tuzi_key(self) -> str:
            key = os.getenv("TUZI_API_KEY", "").strip()
            if key:
                return key
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env_key:
                    value, _ = winreg.QueryValueEx(env_key, "TUZI_API_KEY")
                    return str(value or "").strip()
            except Exception:
                return ""

        def _request_image_generation(self, api_key: str, prompt: str) -> bytes:
            body = json.dumps({
                "model": "seedream-5.0",
                "prompt": prompt,
                "n": 1,
                "size": "1536x864",
                "quality": "medium",
            }, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                "https://api.tu-zi.com/v1/images/generations",
                data=body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
            item = (data.get("data") or [{}])[0]
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                return self._download_image(item["url"])
            raise RuntimeError("接口未返回图片 url 或 b64_json")

        def _download_image(self, url: str) -> bytes:
            last_exc = None
            for attempt in range(1, 6):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        return resp.read()
                except (urllib.error.URLError, http.client.RemoteDisconnected, http.client.IncompleteRead, TimeoutError) as exc:
                    last_exc = exc
                    time.sleep(min(2 * attempt, 8))
            raise RuntimeError(f"下载生成图失败: {last_exc}")

        def _save_generated_image(self, module: dict, role: dict, state: dict, engine: str, slot: int, image_bytes: bytes):
            category = self._category_for_module(module.get("name") or "")
            role_dir = self._safe_name(role.get("name"))
            state_dir = self._safe_name(state.get("imageDir") or state.get("name"))
            engine_dir = self._safe_name(engine)
            target_dir = (root / "candidates" / category / role_dir / state_dir / engine_dir / "round-01").resolve()
            try:
                target_dir.relative_to(root)
            except ValueError:
                raise RuntimeError("path escape")
            target_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{slot:02d}_{engine_dir}_双击生成.png"
            target = target_dir / filename
            target.write_bytes(image_bytes)
            rel_path = target.relative_to(root).as_posix()
            image_id = f"{role_dir}-{state_dir}-{engine_dir}-{slot:02d}"
            return rel_path, image_id

        def _save_uploaded_slot(self, module: dict, role: dict, state: dict, engine: str, slot: int, image_bytes: bytes, ext: str, original_name=None):
            category = self._category_for_module(module.get("name") or "")
            role_dir = self._safe_name(role.get("name"))
            state_dir = self._safe_name(state.get("imageDir") or state.get("name"))
            engine_dir = self._safe_name(engine)
            target_dir = (root / "candidates" / category / role_dir / state_dir / engine_dir / "round-01").resolve()
            try:
                target_dir.relative_to(root)
            except ValueError:
                raise RuntimeError("path escape")
            target_dir.mkdir(parents=True, exist_ok=True)
            stem = self._safe_name(Path(str(original_name or "")).stem) or "upload"
            filename = f"{slot:02d}_上传_{stem}.{ext}"
            target = target_dir / filename
            target.write_bytes(image_bytes)
            rel_path = target.relative_to(root).as_posix()
            image_id = f"{role_dir}-{state_dir}-{engine_dir}-{slot:02d}"
            return rel_path, image_id

        def _handle_fusion_upload(self):
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
            file = payload.get("file") or {}
            data_url = file.get("dataUrl", "")
            m = _re.match(r"data:image/(\w+);base64,(.+)", data_url, _re.S)
            if not m:
                self._send_json({"error": "missing image data"}, 400)
                return
            ext = "jpg" if m.group(1).lower() in {"jpeg", "jpg"} else m.group(1).lower()
            try:
                blob = base64.b64decode(m.group(2))
            except Exception:
                self._send_json({"error": "bad image base64"}, 400)
                return
            def _safe(value):
                value = str(value or "").strip() or "item"
                for ch in '\\/:*?"<>|':
                    value = value.replace(ch, "_")
                return value[:80]
            episode = _safe(payload.get("episode") or "XX")
            shot_no = _safe(payload.get("shotNo") or "00")
            kind = _safe(payload.get("kind") or "ref")
            name = _safe(payload.get("name") or "ref")
            target_dir = (fusion_dir / "uploads" / f"第{episode}集" / shot_no / kind / name).resolve()
            try:
                target_dir.relative_to(project_root)
            except ValueError:
                self._send_json({"error": "path escape"}, 400)
                return
            target_dir.mkdir(parents=True, exist_ok=True)
            fname = _safe(file.get("name") or f"{kind}.{ext}")
            if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                fname = f"{fname}.{ext}"
            target = target_dir / fname
            target.write_bytes(blob)
            rel = target.resolve().relative_to(project_root.resolve()).as_posix()
            self._send_json({"ok": True, "path": rel, "file": fname})

        def _handle_open_folder(self):
            import os
            import subprocess
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            except Exception as exc:
                self._send_json({"error": f"bad json: {exc}"}, 400)
                return
            rel = str(payload.get("path") or "").strip()
            if not rel:
                self._send_json({"error": "missing path"}, 400)
                return
            target = (project_root / rel).resolve()
            try:
                target.relative_to(project_root.resolve())
            except ValueError:
                self._send_json({"error": "只能打开项目目录内的文件夹"}, 403)
                return
            if target.is_file():
                target = target.parent
            if not target.exists():
                target.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                subprocess.Popen(["explorer", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
            self._send_json({"ok": True, "path": str(target)})

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

        def _preview_payload(self):
            try:
                shots = json.loads(preview_shots.read_text(encoding="utf-8"))
            except Exception:
                shots = []
            channels = ["Image2", "即梦_Seedream", "Nano_Banana_Pro", "Midjourney"]
            out = []
            generated = 0
            total = len(shots) * len(channels) * 4
            base = preview_candidates.resolve()
            for shot in shots:
                shot_no = str(shot.get("shot", "")).zfill(2)
                shot_dir = preview_candidates / f"shot_{shot_no}"
                item = {
                    "shot": shot_no,
                    "priority": shot.get("priority", ""),
                    "image": shot.get("image", ""),
                    "subtitle": shot.get("subtitle", ""),
                    "channels": {},
                    "generated": 0,
                }
                for channel in channels:
                    imgs = []
                    folder = shot_dir / channel
                    if folder.exists():
                        for p in sorted(folder.glob("*.png")):
                            variant = 0
                            try:
                                variant = int(p.stem.rsplit("_", 1)[-1])
                            except Exception:
                                pass
                            rel = p.resolve().relative_to(base).as_posix()
                            imgs.append({"name": p.name, "variant": variant, "url": "/preview-asset/" + rel})
                    item["channels"][channel] = imgs
                    item["generated"] += len(imgs)
                    generated += len(imgs)
                out.append(item)
            return {"shots": out, "generated": generated, "total": total}

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
