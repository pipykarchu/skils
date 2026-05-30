#!/usr/bin/env python3
"""Generate a Chinese storyboard script from screenplay-like input."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import textwrap
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


DEFAULT_BASE_URL = "https://api.tu-zi.com/v1"
DEFAULT_DRAFT_MODEL = "DeepSeek V4 Pro"
DEFAULT_REWRITE_MODEL = "Claude Sonnet 4.6"
FIELDS = [
    "镜号",
    "时长",
    "景别",
    "场景",
    "时间",
    "出场事物造型",
    "画面描述",
    "运镜",
    "对白",
    "音效",
    "AI生图提示词",
    "负面提示词",
    "备注",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned:
            self.parts.append(cleaned)

    def text(self) -> str:
        return "\n".join(self.parts)


def read_text(source: str) -> str:
    if re.match(r"^https?://", source, re.I):
        with urllib.request.urlopen(source, timeout=30) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return html_to_text(raw.decode(charset, errors="replace"))

    path = Path(source)
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    if suffix in {".html", ".htm"}:
        return html_to_text(path.read_text(encoding="utf-8-sig", errors="replace"))
    if suffix == ".docx":
        return docx_to_text(path)
    if suffix == ".pdf":
        return pdf_to_text(path)
    raise ValueError(f"暂不支持的输入格式：{suffix or source}")


def normalize_label(value: str) -> str:
    return re.sub(r"[\s#*_`：:，,。.\-—|【】\[\]()（）]+", "", value).lower()


def extract_named_segment(text: str, segment: str) -> str:
    target = normalize_label(segment)
    if not target:
        return text

    lines = text.splitlines()
    headings: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    for pos, (start, level, title) in enumerate(headings):
        label = normalize_label(title)
        if target in label or label in target:
            end = len(lines)
            for next_start, next_level, _ in headings[pos + 1 :]:
                if next_level <= level:
                    end = next_start
                    break
            selected = "\n".join(lines[start:end]).strip()
            if selected:
                return selected

    for index, line in enumerate(lines):
        if target in normalize_label(line):
            end = len(lines)
            for next_index in range(index + 1, len(lines)):
                if re.match(r"^#{1,6}\s+", lines[next_index]):
                    end = next_index
                    break
            selected = "\n".join(lines[index:end]).strip()
            if selected:
                return selected

    raise ValueError(f"没有在剧本中找到片段：{segment}")


def safe_filename_part(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value).strip(" ._")
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:60] or "片段"


def html_to_text(markup: str) -> str:
    parser = TextExtractor()
    parser.feed(markup)
    return html.unescape(parser.text())


def docx_to_text(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml")
    root = ET.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def pdf_to_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("读取 PDF 需要安装 pypdf：python -m pip install pypdf") from exc

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\n".join(page for page in pages if page)


def tuzi_chat(
    messages: list[dict[str, str]],
    model: str,
    api_key: str,
    base_url: str,
    temperature: float,
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def list_models(api_key: str, base_url: str) -> None:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    for item in data.get("data", []):
        model_id = item.get("id") or item.get("model") or str(item)
        print(model_id)


def build_draft_prompt(text: str) -> list[dict[str, str]]:
    schema = {field: "字符串" for field in FIELDS}
    return [
        {
            "role": "system",
            "content": (
                "你是漫剧分镜编剧。把剧本拆成连续分镜头脚本。"
                "只输出 JSON 数组，不输出解释、Markdown 或代码块。"
            ),
        },
        {
            "role": "user",
            "content": textwrap.dedent(
                f"""
                按下面字段输出，每个镜头必须字段完整：
                {json.dumps(schema, ensure_ascii=False)}

                要求：
                1. 全部中文。
                2. 每个镜头只描述一个明确画面或动作。
                3. 画面描述直观客观，避免华丽辞藻。
                4. 出场事物造型写清人物年龄段、服装、发型、关键道具、环境陈设。
                5. AI生图提示词包含主体、动作、场景、时间、光线、构图、画幅、质量要求。
                6. 不要在 AI生图提示词 中写对白、字幕、镜号或不可见心理活动。

                原始剧本：
                {text}
                """
            ).strip(),
        },
    ]


def build_rewrite_prompt(draft_json: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是短剧和漫剧导演。改对白、节奏和情绪，但保持分镜字段结构。"
                "只输出 JSON 数组，不输出解释、Markdown 或代码块。"
            ),
        },
        {
            "role": "user",
            "content": textwrap.dedent(
                f"""
                请基于下面初稿 JSON 润色：
                - 对白更口语，符合人物当下情绪。
                - 节奏更清楚，过长镜头可以拆分。
                - 情绪通过表情、动作、停顿和环境反应表现。
                - 保持画面描述直观客观，方便 AI 生图。
                - 每条记录必须保留这些字段：{", ".join(FIELDS)}

                初稿 JSON：
                {draft_json}
                """
            ).strip(),
        },
    ]


def extract_json_array(raw: str) -> list[dict[str, Any]]:
    cleaned = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S | re.I)
    if fenced:
        cleaned = fenced.group(1).strip()
    if not cleaned.startswith("["):
        match = re.search(r"\[.*\]", cleaned, re.S)
        if match:
            cleaned = match.group(0)
    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError("模型输出不是 JSON 数组")
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            continue
        item = {field: str(row.get(field, "")).strip() for field in FIELDS}
        item["镜号"] = item["镜号"] or f"{index:03d}"
        normalized.append(item)
    return normalized


def dry_run_rows(text: str) -> list[dict[str, str]]:
    summary = " ".join(line.strip() for line in text.splitlines() if line.strip())[:80]
    return [
        {
            "镜号": "001",
            "时长": "3秒",
            "景别": "全景",
            "场景": "示例场景",
            "时间": "白天",
            "出场事物造型": "主角，现代日常服装，站在室内，桌面有剧本道具",
            "画面描述": f"主角站在场景中央，画面交代环境。原文片段：{summary}",
            "运镜": "固定镜头",
            "对白": "",
            "音效": "环境底噪",
            "AI生图提示词": "主角站在室内，现代日常服装，白天自然光，全景，横版16:9，清晰构图，主体明确，细节完整，无文字水印",
            "负面提示词": "模糊，低清晰度，多余文字，水印，畸形手指，人物重复",
            "备注": "dry-run 示例镜头",
        },
        {
            "镜号": "002",
            "时长": "2秒",
            "景别": "中景",
            "场景": "示例场景",
            "时间": "白天",
            "出场事物造型": "主角保持同一服装，手里拿着关键道具",
            "画面描述": "主角看向道具，表情发生变化。",
            "运镜": "轻微推进",
            "对白": "这件事不对。",
            "音效": "轻微停顿",
            "AI生图提示词": "同一主角拿着道具，注视道具，中景，白天室内自然光，轻微紧张表情，横版16:9，电影感灯光，主体明确，无文字水印",
            "负面提示词": "模糊，文字，水印，夸张表情，过度变形",
            "备注": "dry-run 示例镜头",
        },
        {
            "镜号": "003",
            "时长": "2秒",
            "景别": "特写",
            "场景": "示例场景",
            "时间": "白天",
            "出场事物造型": "主角面部特写，服装和发型保持一致",
            "画面描述": "主角抬眼，准备做出决定。",
            "运镜": "固定特写",
            "对白": "我自己去查。",
            "音效": "低频气氛音",
            "AI生图提示词": "主角面部特写，抬眼，坚定表情，白天室内柔和光，浅景深，横版16:9，清晰面部细节，主体明确，无文字水印",
            "负面提示词": "模糊，水印，字幕，脸部变形，眼睛错位",
            "备注": "dry-run 示例镜头",
        },
    ]


def write_markdown(rows: list[dict[str, Any]], output: Path) -> None:
    lines = ["# 分镜头脚本", "", "|" + "|".join(FIELDS) + "|", "|" + "|".join(["---"] * len(FIELDS)) + "|"]
    for row in rows:
        values = [str(row.get(field, "")).replace("\n", "<br>").replace("|", "｜") for field in FIELDS]
        lines.append("|" + "|".join(values) + "|")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_xlsx(rows: list[dict[str, Any]], output: Path) -> None:
    try:
        from openpyxl import Workbook  # type: ignore
        from openpyxl.styles import Alignment, Font  # type: ignore
    except ImportError as exc:
        raise RuntimeError("导出 Excel 需要安装 openpyxl：python -m pip install openpyxl") from exc

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "分镜脚本"
    sheet.append(FIELDS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in rows:
        sheet.append([row.get(field, "") for field in FIELDS])
    widths = {
        "A": 8,
        "B": 10,
        "C": 12,
        "D": 18,
        "E": 12,
        "F": 32,
        "G": 36,
        "H": 16,
        "I": 28,
        "J": 18,
        "K": 48,
        "L": 28,
        "M": 20,
    }
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    workbook.save(output)


def generate_rows(args: argparse.Namespace, text: str) -> list[dict[str, Any]]:
    if args.dry_run:
        return dry_run_rows(text)

    api_key = args.api_key or os.getenv("TUZI_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 TUZI_API_KEY。先设置环境变量，或使用 --api-key / --dry-run。")

    draft_raw = tuzi_chat(
        build_draft_prompt(text),
        args.draft_model,
        api_key,
        args.base_url,
        temperature=0.35,
    )
    draft_rows = extract_json_array(draft_raw)
    rewrite_raw = tuzi_chat(
        build_rewrite_prompt(json.dumps(draft_rows, ensure_ascii=False)),
        args.rewrite_model,
        api_key,
        args.base_url,
        temperature=0.25,
    )
    return extract_json_array(rewrite_raw)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把剧本生成中文分镜头脚本。")
    parser.add_argument("input", nargs="?", help="输入文件路径或网页 URL，支持 md/txt/docx/pdf/html/url")
    parser.add_argument("--segment", help="只生成指定片段，例如：片段 01：妈妈病了、妈妈病了")
    parser.add_argument("--out", default="storyboard_out", help="输出目录")
    parser.add_argument("--formats", default="md,xlsx", help="输出格式：md,xlsx")
    parser.add_argument("--dry-run", action="store_true", help="不访问 API，生成示例结构用于验证")
    parser.add_argument("--api-key", help="Tuzi API Key；也可用 TUZI_API_KEY")
    parser.add_argument("--base-url", default=os.getenv("TUZI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--draft-model", default=os.getenv("TUZI_DRAFT_MODEL", DEFAULT_DRAFT_MODEL))
    parser.add_argument("--rewrite-model", default=os.getenv("TUZI_REWRITE_MODEL", DEFAULT_REWRITE_MODEL))
    parser.add_argument("--list-models", action="store_true", help="列出 Tuzi 可用模型，需要 API Key")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = args.api_key or os.getenv("TUZI_API_KEY")
    if args.list_models:
        if not api_key:
            raise RuntimeError("列模型需要 TUZI_API_KEY 或 --api-key。")
        list_models(api_key, args.base_url)
        return 0
    if not args.input:
        raise RuntimeError("请提供输入文件或 URL。")

    text = read_text(args.input).strip()
    if args.segment:
        text = extract_named_segment(text, args.segment)
    if not text:
        raise RuntimeError("输入内容为空，无法生成分镜。")
    rows = generate_rows(args, text)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.input).stem if not re.match(r"^https?://", args.input, re.I) else "webpage"
    if args.segment:
        stem = f"{stem}_{safe_filename_part(args.segment)}"
    selected = {item.strip().lower() for item in args.formats.split(",") if item.strip()}
    if "md" in selected:
        write_markdown(rows, out_dir / f"{stem}_分镜脚本.md")
    if "xlsx" in selected:
        write_xlsx(rows, out_dir / f"{stem}_分镜脚本.xlsx")
    print(f"完成：{len(rows)} 个镜头，输出目录：{out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1)
