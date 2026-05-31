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
    "运镜",
    "画面内容提示词",
    "人物台词",
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
                "你是经验丰富的导演和编剧。根据剧本拆成可执行的连续分镜头脚本。"
                "严格按照剧本已有内容客观编写，不添油加醋，不新增剧情、人物、道具或情绪。"
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
                2. 严格按剧本已有信息拆分镜头，不补写剧本没有的情节、人物、道具、背景设定。
                3. 每个镜头只对应一个适合生成单张分镜图片的明确画面或动作。
                4. 画面内容提示词要直观客观，写清主体、动作、场景、时间、可见道具、光线、构图、画幅；不要使用华丽辞藻。
                5. 人物台词只写剧本中已有台词；没有台词则留空。
                6. 时长要合理：普通画面 2-4 秒，动作或转场 1-3 秒，较长台词镜头 4-6 秒；不要让一个镜头承载过多动作或过长台词。
                7. 运镜必须可实现，优先使用固定镜头、轻微推进、轻微后拉、平移、跟拍、切到特写；不要写复杂或无法稳定生成的运镜。

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
                "你是短剧和漫剧导演，负责审查分镜是否能用于 AI 短片图片生成。"
                "只能基于剧本已有内容修正节奏、镜头拆分和客观表达，不能添油加醋。"
                "只输出 JSON 数组，不输出解释、Markdown 或代码块。"
            ),
        },
        {
            "role": "user",
            "content": textwrap.dedent(
                f"""
                请基于下面初稿 JSON 审查并修正：
                - 严格保持剧本事实，不新增剧情、人物、道具、台词或华丽修饰。
                - 画面合理性：每个镜头必须能生成一张单独分镜图，画面主体明确，动作不超过一个重点。
                - 时长合理性：普通画面 2-4 秒，动作/转场 1-3 秒，较长台词 4-6 秒；如果台词太长，拆成多个镜头。
                - 对话覆盖合理性：人物台词必须能在该镜头时长内说完；不要让无关画面承载台词。
                - 运镜实现合理性：运镜要简单可执行，避免复杂调度、快速旋转、连续多机位。
                - 画面内容提示词保持直观客观，适合 AI 生图，不写字幕、镜号、水印、不可见心理活动。
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
            "运镜": "固定镜头",
            "画面内容提示词": f"按原剧本内容建立场景，主体站在画面中央，交代环境和人物位置，横版16:9，清晰构图。原文片段：{summary}",
            "人物台词": "",
            "备注": "dry-run 示例镜头；单张图片可生成，时长用于环境交代",
        },
        {
            "镜号": "002",
            "时长": "2秒",
            "景别": "中景",
            "运镜": "轻微推进",
            "画面内容提示词": "同一主体看向剧本中已有的关键物件，中景，主体明确，动作单一，横版16:9，清晰构图。",
            "人物台词": "这件事不对。",
            "备注": "dry-run 示例镜头；短句台词可在 2 秒内覆盖",
        },
        {
            "镜号": "003",
            "时长": "2秒",
            "景别": "特写",
            "运镜": "固定特写",
            "画面内容提示词": "同一主体面部特写，抬眼，表情根据剧本情境保持克制，横版16:9，面部清晰，背景简洁。",
            "人物台词": "我自己去查。",
            "备注": "dry-run 示例镜头；固定特写适合单张分镜图片",
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
        "D": 16,
        "E": 58,
        "F": 32,
        "G": 30,
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
