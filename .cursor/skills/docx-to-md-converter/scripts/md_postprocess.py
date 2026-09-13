# -*- coding: utf-8 -*-
"""Markdown 后处理：清理 Word/pandoc 转换残留、规范图片路径、按标题拆分。

pandoc 引擎与内置引擎都会走这里，保证两条链路输出风格一致。

单独调用：
    python md_postprocess.py <in.md> [out.md] [--media-dir NAME] [--keep-toc]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 基础工具

# 围栏代码块起止（``` 或 ~~~），后处理规则不能进代码块乱改
_FENCE_RE = re.compile(r"^\s*(?:`{3,}|~{3,})")

# Word 常见不可见字符：不换行空格、零宽、软连字符、对象替换符
_INVISIBLE_MAP = {
    "\u00a0": " ",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\u00ad": "",
    "\ufffc": "",
    "\ufeff": "",
    "\u2028": "\n",
    "\u2029": "\n",
}


def split_code_blocks(text: str):
    """把文本切成 [(是否代码块, 段落文本)]，正文规则只作用在非代码段上。"""
    blocks = []
    buf = []
    in_code = False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            # 围栏行归属当前块，切换状态
            buf.append(line)
            if in_code:
                blocks.append((True, "\n".join(buf)))
                buf = []
                in_code = False
            else:
                # 前面攒的正文先收尾（不含当前围栏行）
                head = buf[:-1]
                if head:
                    blocks.append((False, "\n".join(head)))
                buf = [line]
                in_code = True
            continue
        buf.append(line)
    if buf:
        blocks.append((in_code, "\n".join(buf)))
    return blocks


def apply_to_prose(text: str, func):
    """只对非代码块部分应用 func。"""
    out = []
    for is_code, block in split_code_blocks(text):
        out.append(block if is_code else func(block))
    return "\n".join(out)


def is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|")


# ---------------------------------------------------------------- 各清理步骤


def normalize_invisibles(text: str) -> str:
    """统一不可见字符，并把行尾空白、全角空格缩进清掉。"""
    for src, dst in _INVISIBLE_MAP.items():
        text = text.replace(src, dst)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        # 行首全角空格（Word 首行缩进的产物）在 md 里没有意义
        line = re.sub(r"^[\u3000]+", "", line)
        lines.append(line.rstrip())
    return "\n".join(lines)


def strip_anchor_noise(block: str) -> str:
    """去掉书签锚点残留：空 span、空 a、[]{#id}、标题尾部 {#_Toc123}。"""
    block = re.sub(r'<span\s+id="[^"]*"\s*>\s*</span>', "", block)
    block = re.sub(r'<a\s+id="[^"]*"\s*>\s*</a>', "", block)
    block = re.sub(r'<a\s+name="[^"]*"\s*>\s*</a>', "", block)
    block = re.sub(r"\[\]\{#[^}]*\}", "", block)
    # 标题行尾的 pandoc 属性块
    block = re.sub(r"^(#{1,6}\s+.*?)\s*\{#[^}]*\}\s*$", r"\1", block, flags=re.M)
    # 独立成行的锚点段落
    block = re.sub(r"^\s*\{#[^}]*\}\s*$", "", block, flags=re.M)
    return block


def strip_image_attrs(block: str) -> str:
    """去掉 pandoc 输出的 ![](x.png){width="5in" height="2in"} 尺寸属性。"""
    return re.sub(r"(!\[[^\]]*\]\([^)]*\))\{[^}]*\}", r"\1", block)


def strip_empty_emphasis(block: str) -> str:
    """去掉空强调、空链接等噪声：**  **、__ __、[]()。"""
    block = re.sub(r"\*\*\s*\*\*", "", block)
    block = re.sub(r"(?<!\w)__\s*__(?!\w)", "", block)
    block = re.sub(r"(?<!!)\[\s*\]\(\s*\)", "", block)
    # 只有一个反斜杠的行是 pandoc 的硬换行残留
    block = re.sub(r"^\\\s*$", "", block, flags=re.M)
    return block


def unbold_headings(block: str) -> str:
    """标题本身就是强调，Word 里的加粗/斜体在 md 标题里只是噪声，全部去掉。"""

    def repl(m):
        prefix, text = m.group(1), m.group(2)
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        return "%s %s" % (prefix, text.strip())

    return re.sub(r"^(#{1,6})\s+(.+?)\s*$", repl, block, flags=re.M)


# 「目录」既可能是 md 标题，也可能只是一行普通文字（Word 里靠样式排版）
_TOC_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*"
    r"(?:目\s*录|目\s*次|Table\s+of\s+Contents|Contents)"
    r"\s*(?:\*\*)?\s*$",
    re.I,
)
# 目录条目：链接式（可能嵌套页码链接）、点线+页码、制表符+页码、末尾裸页码
_TOC_LINK_RE = re.compile(r"^\s*(?:\*\*)?\[.+\]\(#[^)]*\)\s*(?:\*\*)?\s*$")
_TOC_ENTRY_RE = re.compile(
    r"^\s*(?:\*\*)?(?:"
    r"\[.+\]\(#[^)]*\)"
    r"|.{0,90}?[.\u2026\u3002]{3,}\s*\d{1,4}"
    r"|.{0,90}?\t+\d{1,4}"
    r"|(?:\d+(?:\.\d+)*\s+)?\S.{0,88}?\s+\d{1,4}"
    r")(?:\*\*)?\s*$"
)


def _looks_like_toc(lines) -> bool:
    """区域内非空行里目录条目占比过半才认定是目录，避免误删正文。"""
    body = [ln for ln in lines if ln.strip()]
    if len(body) < 3:
        return False
    hits = sum(1 for ln in body if _TOC_ENTRY_RE.match(ln))
    return hits / len(body) >= 0.6


def drop_toc(text: str):
    """删掉 Word 自动目录（md 里没有页码，留着只是噪声）。返回 (文本, 删除行数)。"""
    lines = text.split("\n")
    removed = 0

    # 情况一：出现「目录」行（md 标题或纯文本），往后吃掉连续的目录条目
    out = []
    i = 0
    while i < len(lines):
        if _TOC_HEADING_RE.match(lines[i]):
            j = i + 1
            entries = 0
            while j < len(lines):
                line = lines[j]
                if not line.strip():
                    j += 1
                    continue
                if line.lstrip().startswith("#") or not _TOC_ENTRY_RE.match(line):
                    break
                entries += 1
                j += 1
            if entries >= 3 and _looks_like_toc(lines[i + 1 : j]):
                removed += j - i
                i = j
                continue
            if entries == 0:
                # 条目已被引擎按样式剔除，只剩一个孤立的「目录」行；
                # 后面紧跟标题或到文末，说明它不承载任何正文内容
                nxt = next((ln for ln in lines[i + 1 :] if ln.strip()), None)
                if nxt is None or nxt.lstrip().startswith("#"):
                    removed += 1
                    i += 1
                    continue
        out.append(lines[i])
        i += 1
    lines = out

    # 情况二：没有「目录」字样，正文开头直接是一长串锚点链接行
    out = []
    i = 0
    while i < len(lines):
        if _TOC_LINK_RE.match(lines[i]):
            j, run = i, 0
            while j < len(lines):
                if not lines[j].strip():
                    j += 1
                    continue
                if _TOC_LINK_RE.match(lines[j]):
                    run += 1
                    j += 1
                    continue
                break
            if run >= 5:
                removed += j - i
                i = j
                continue
        out.append(lines[i])
        i += 1

    return "\n".join(out), removed


_NUM_HEADING_RE = re.compile(
    r"^(?P<num>\d{1,2}(?:\\?\.\d{1,2}){0,5})\\?\.?[ \t\u3000]+(?P<title>\S.*)$"
)
_END_PUNCT = "。；，、：,;:.!?！？"


def headings_from_numbers(text: str, mode: str):
    """把「1.2.3 标题」形式的普通段落提升为 ATX 标题。

    mode=auto 时只在原文几乎没有标题、且编号行足够多的情况下才动手，
    避免把正文里的编号列表误判成标题。
    """
    if mode == "off":
        return text, 0

    existing = len(re.findall(r"^#{1,6}\s+\S", text, flags=re.M))

    def candidates(block: str):
        found = []
        for idx, line in enumerate(block.split("\n")):
            if line.startswith("#") or is_table_line(line):
                continue
            m = _NUM_HEADING_RE.match(line)
            if not m:
                continue
            title = m.group("title").strip()
            if len(title) > 60 or title[-1] in _END_PUNCT:
                continue
            found.append(idx)
        return found

    prose = "\n".join(b for c, b in split_code_blocks(text) if not c)
    if mode == "auto" and (existing >= 3 or len(candidates(prose)) < 5):
        return text, 0

    count = [0]

    def convert(block: str) -> str:
        lines = block.split("\n")
        for idx, line in enumerate(lines):
            if line.startswith("#") or is_table_line(line):
                continue
            m = _NUM_HEADING_RE.match(line)
            if not m:
                continue
            title = m.group("title").strip()
            if len(title) > 60 or title[-1] in _END_PUNCT:
                continue
            num = m.group("num").replace("\\", "")
            level = min(6, num.count(".") + 1)
            lines[idx] = "%s %s %s" % ("#" * level, num, title)
            count[0] += 1
        return "\n".join(lines)

    return apply_to_prose(text, convert), count[0]


def _rebase(target: str, name: str):
    """把任意形式的图片路径压成 `<media_dir>/<文件名>`；外链原样返回 None。

    目标可能是 `<path with space>`、`path%20x.png`、或 `path "标题"`。
    注意不能按空格切分：文件名本身就可能带空格。
    """
    raw = target.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    else:
        # 只剥掉引号形式的 title 后缀
        raw = re.sub(r"""\s+["'][^"']*["']\s*$""", "", raw).strip()
    norm = raw.replace("\\", "/")
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", norm) or norm.startswith("data:"):
        return None
    base = norm.rsplit("/", 1)[-1]
    if not base:
        return None
    return "%s/%s" % (name, base)


def normalize_media_links(text: str, media_dirname: str):
    """把图片链接统一成 `<stem>.assets/xxx.png`，去掉 pandoc 的 media/ 中间层。

    要同时覆盖 Markdown 图片和 pandoc 带尺寸时输出的 <img src="...">，
    否则拉平 media 目录后链接会失效。
    """
    changed = [0]
    name = media_dirname.replace("\\", "/").rstrip("/")

    def repl_md(m):
        rebased = _rebase(m.group(2), name)
        if rebased is None:
            return m.group(0)
        changed[0] += 1
        # 路径含空格或括号时必须用尖括号包裹，否则链接会在空格处被截断
        if re.search(r"[\s()]", rebased):
            return "%s(<%s>)" % (m.group(1), rebased)
        return "%s(%s)" % (m.group(1), rebased)

    def repl_html(m):
        rebased = _rebase(m.group(2), name)
        if rebased is None:
            return m.group(0)
        changed[0] += 1
        return '%s"%s"' % (m.group(1), rebased)

    text = re.sub(r"(!\[[^\]]*\])\(([^)]+)\)", repl_md, text)
    text = re.sub(r"(<img\s[^>]*?src=)\"([^\"]+)\"", repl_html, text)
    return text, changed[0]


def strip_junk_image_alt(block: str) -> str:
    """Word 的图片描述常是哈希串或 imageN，这种 alt 没有信息量，清掉。"""

    def repl(m):
        alt, target = m.group(1), m.group(2)
        base = target.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        junk = (
            re.match(r"^[0-9a-fA-F]{16,}$", alt)
            or re.match(r"^(?:image|图片|Picture|图\s*\d+)[\s_-]*\d*$", alt, re.I)
            or alt == base
        )
        return "![](%s)" % target if junk else m.group(0)

    return re.sub(r"!\[([^\]]+)\]\(([^)]+)\)", repl, block)


def clean_html_tables(block: str) -> str:
    """pandoc 降级成 HTML 表时会带 colgroup 和百分比宽度，这些在 md 里没用。"""
    block = re.sub(r"<colgroup>[\s\S]*?</colgroup>\s*", "", block)
    block = re.sub(
        r"(<(?:table|thead|tbody|tr|td|th|col)\b[^>]*?)\s+style=\"[^\"]*\"",
        r"\1",
        block,
    )
    block = re.sub(r"<(table|thead|tbody|tr|td|th)\s+>", r"<\1>", block)
    return block


def drop_images(text: str) -> str:
    """--no-media 模式：图片替换为可检索的注释占位。"""

    def repl(m):
        alt = m.group(1).strip()
        target = m.group(2).rsplit("/", 1)[-1]
        return "<!-- 图片已跳过：%s -->" % (alt or target)

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, text)


def ensure_block_spacing(block: str) -> str:
    """标题、表格、围栏前后补空行，保证任何 md 渲染器都能正确解析。"""
    lines = block.split("\n")
    out = []
    for idx, line in enumerate(lines):
        stripped = line.strip()
        is_head = bool(re.match(r"^#{1,6}\s+\S", stripped))
        is_tbl = is_table_line(line)
        prev = out[-1] if out else ""
        prev_tbl = is_table_line(prev) if prev else False
        if is_head and prev.strip():
            out.append("")
        elif is_tbl and prev.strip() and not prev_tbl:
            out.append("")
        elif prev_tbl and not is_tbl and stripped:
            out.append("")
        out.append(line)
    return "\n".join(out)


def collapse_blank_lines(text: str) -> str:
    """连续空行压成一行，首尾空行去掉。"""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n") + "\n"


# ---------------------------------------------------------------- 主入口


def postprocess(
    text: str,
    media_dirname: str = None,
    keep_toc: bool = False,
    keep_image_size: bool = False,
    heading_mode: str = "auto",
    keep_media: bool = True,
):
    """统一后处理。返回 (文本, 统计字典)。"""
    stats = {"toc_lines_removed": 0, "headings_promoted": 0, "images_relinked": 0}

    text = normalize_invisibles(text)
    text = apply_to_prose(text, strip_anchor_noise)
    if not keep_image_size:
        text = apply_to_prose(text, strip_image_attrs)
    text = apply_to_prose(text, strip_empty_emphasis)
    text = apply_to_prose(text, unbold_headings)
    text = apply_to_prose(text, strip_junk_image_alt)
    text = apply_to_prose(text, clean_html_tables)

    if not keep_toc:
        text, stats["toc_lines_removed"] = drop_toc(text)

    text, stats["headings_promoted"] = headings_from_numbers(text, heading_mode)

    if not keep_media:
        text = drop_images(text)
    elif media_dirname:
        text, stats["images_relinked"] = normalize_media_links(text, media_dirname)

    text = apply_to_prose(text, ensure_block_spacing)
    text = collapse_blank_lines(text)
    return text, stats


def split_by_heading(text: str, level: int, out_dir: Path, stem: str):
    """按第 level 级标题拆成多个文件，返回写出的文件列表（含索引文件）。"""
    lines = text.split("\n")
    marker = re.compile(r"^#{%d}\s+(\S.*)$" % level)
    sections = []  # [(标题, [行])]
    preamble = []
    current = None
    in_code = False
    for line in lines:
        if _FENCE_RE.match(line):
            in_code = not in_code
        if not in_code:
            m = marker.match(line)
            if m:
                current = [m.group(1).strip(), [line]]
                sections.append(current)
                continue
        (current[1] if current else preamble).append(line)

    if not sections:
        return []

    def safe(name: str) -> str:
        name = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip(" ._")
        return (name or "section")[:60]

    written = []
    index = ["# %s" % stem, "", "本目录由 docx-to-md-converter 按 H%d 拆分。" % level, ""]
    if "".join(preamble).strip():
        head = out_dir / ("%s_00_前言.md" % stem)
        head.write_text(collapse_blank_lines("\n".join(preamble)), encoding="utf-8")
        written.append(head)
        index.append("- [前言](%s)" % head.name)
    for i, (title, body) in enumerate(sections, start=1):
        path = out_dir / ("%s_%02d_%s.md" % (stem, i, safe(title)))
        path.write_text(collapse_blank_lines("\n".join(body)), encoding="utf-8")
        written.append(path)
        index.append("- [%s](%s)" % (title, path.name))
    idx_path = out_dir / ("%s_index.md" % stem)
    idx_path.write_text("\n".join(index) + "\n", encoding="utf-8")
    written.append(idx_path)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown 后处理")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--media-dir", default=None, help="图片目录名，用于规范链接")
    ap.add_argument("--keep-toc", action="store_true")
    ap.add_argument("--keep-image-size", action="store_true")
    ap.add_argument(
        "--headings-from-numbers", choices=["auto", "on", "off"], default="auto"
    )
    args = ap.parse_args(argv)

    src = Path(args.input)
    text, stats = postprocess(
        src.read_text(encoding="utf-8"),
        media_dirname=args.media_dir,
        keep_toc=args.keep_toc,
        keep_image_size=args.keep_image_size,
        heading_mode=args.headings_from_numbers,
    )
    dst = Path(args.output) if args.output else src
    dst.write_text(text, encoding="utf-8")
    print("postprocessed -> %s %s" % (dst, stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
