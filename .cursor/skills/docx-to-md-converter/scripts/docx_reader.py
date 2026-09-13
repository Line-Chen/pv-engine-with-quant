# -*- coding: utf-8 -*-
"""内置 docx -> Markdown 引擎（纯 Python + 标准库，无需 pandoc）。

直接解析 OOXML：
  - 标题：w:pStyle 对应样式名（heading N / 标题 N）或 w:outlineLvl
  - 列表：w:numPr + numbering.xml 判断有序 / 无序与层级
  - 表格：能用 GFM 管道表就用；出现合并单元格或单元格内多块内容时降级为 HTML 表
  - 图片：a:blip / v:imagedata 从 word/media 抽到资源目录
  - 代码块：等宽字体或代码类样式的连续段落合并为围栏代码块
  - 脚注：正文写 [^n]，文末补定义

单独调用：
    python docx_reader.py <in.docx> [out.md] [--media-dir DIR] [--media-rel NAME]
"""

from __future__ import annotations

import argparse
import posixpath
import re
import string
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "v": "urn:schemas-microsoft-com:vml",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}


def w(tag: str) -> str:
    return "{%s}%s" % (NS["w"], tag)


def r_(tag: str) -> str:
    return "{%s}%s" % (NS["r"], tag)


W_VAL = w("val")

# 等宽字体：命中即认为该段是代码
MONO_FONTS = {
    "consolas",
    "courier",
    "courier new",
    "monaco",
    "menlo",
    "lucida console",
    "dejavu sans mono",
    "source code pro",
    "jetbrains mono",
    "cascadia code",
    "cascadia mono",
    "sf mono",
    "fira code",
}
# 代码类样式名
CODE_STYLE_RE = re.compile(
    r"^(?:html\s*preformatted|plain\s*text|source\s*code|code|codeblock|preformatted.*|代码.*|程序.*)$"
)
HEADING_NAME_RE = re.compile(r"^(?:heading|标题|head)\s*([1-9])$", re.I)
TOC_STYLE_RE = re.compile(r"^(?:toc\s*\d*|目\s*录\s*\d*)", re.I)

_ESC_ALWAYS = re.compile(r"([\\`|<>\[\]])")
# 只把 ASCII 字母数字算作「词内部」：中文的 isalnum() 也为真，会漏掉该转义的位置
_ASCII_WORD = frozenset(string.ascii_letters + string.digits)
# 行首这些写法会被 md 解析成标题/列表/引用/分隔线，需要转义。
# 注意必须要求后面跟空白，否则会把 **加粗** 的星号也转义掉。
_LINE_START_RISK = re.compile(r"^(\s*)(#{1,6}(?=\s)|[-+*](?=\s)|>|\d+[.)](?=\s))")

# Wingdings / Symbol 字体的私用码位（U+F000~U+F0FF）在 Unicode 下不可显示，
# 按常见项目符号映射成等价字符，其余统一退化为 ·
SYMBOL_CHAR_MAP = {
    0xF020: " ",
    0xF04A: "☺",
    0xF06C: "●",
    0xF06E: "■",
    0xF071: "◆",
    0xF075: "◆",
    0xF07F: "□",
    0xF09F: "•",
    0xF0A1: "✁",
    0xF0A4: "◆",
    0xF0A7: "▪",
    0xF0A8: "▫",
    0xF0B7: "•",
    0xF0D8: "➢",
    0xF0E0: "➔",
    0xF0E8: "⇨",
    0xF0FB: "✗",
    0xF0FC: "✓",
    0xF0FE: "☑",
}


def map_symbol_text(text: str) -> str:
    """把符号字体的私用码位换成可显示字符。"""
    if not text:
        return text
    out = []
    for ch in text:
        code = ord(ch)
        if 0xF000 <= code <= 0xF0FF:
            out.append(SYMBOL_CHAR_MAP.get(code, "·"))
        else:
            out.append(ch)
    return "".join(out)


def escape_md(text: str) -> str:
    """转义 Markdown 元字符。

    `*` `_` 只在可能被解析成强调的位置转义：夹在 ASCII 字母数字之间（如 `get_price`）
    时保持原样，避免中文正文满屏反斜杠。必须一次遍历完成，分两次 sub 会把
    `MRM0609_*` 这类文本重复转义成 `\\_\\\\*`。
    """
    if not text:
        return ""
    text = _ESC_ALWAYS.sub(r"\\\1", text)

    def repl(m):
        start = m.start()
        prev = text[start - 1] if start > 0 else ""
        nxt = text[m.end()] if m.end() < len(text) else ""
        if prev in _ASCII_WORD and nxt in _ASCII_WORD:
            return m.group(0)
        return "\\" + m.group(0)

    return re.sub(r"[*_]", repl, text)


def escape_line_start(line: str) -> str:
    """段落开头可能被误读成标题 / 列表 / 引用 / 有序列表时加转义。"""
    m = _LINE_START_RISK.match(line)
    if not m:
        return line
    indent, token, rest = m.group(1), m.group(2), line[m.end() :]
    if token[0].isdigit():
        # 1. -> 1\.  转义的是分隔符而不是数字
        return "%s%s\\%s%s" % (indent, token[:-1], token[-1], rest)
    return "%s\\%s%s" % (indent, token, rest)


def html_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def _on(el) -> bool:
    """w:b / w:i 这类开关元素：存在且 val 不是 0/false 即为开启。"""
    if el is None:
        return False
    val = el.get(W_VAL)
    return val not in ("0", "false", "off")


class DocxToMarkdown:
    """把单个 .docx 转成 Markdown 文本。"""

    def __init__(self, docx_path, media_dir=None, media_rel="assets", keep_media=True):
        self.path = Path(docx_path)
        self.zip = zipfile.ZipFile(str(self.path))
        self.media_dir = Path(media_dir) if media_dir else None
        self.media_rel = media_rel.replace("\\", "/").rstrip("/")
        self.keep_media = keep_media
        self.stats = {
            "headings": 0,
            "tables": 0,
            "html_tables": 0,
            "images": 0,
            "code_blocks": 0,
            "footnotes": 0,
        }
        self._saved_media = {}
        self._footnotes = []
        self._fn_index = {}
        self._styles = self._load_styles()
        self._numbering = self._load_numbering()
        self._rels = self._load_rels("word/_rels/document.xml.rels")
        self._footnote_xml = self._read_xml("word/footnotes.xml")

    # ------------------------------------------------------------ 载入辅助

    def _read_xml(self, name):
        try:
            data = self.zip.read(name)
        except KeyError:
            return None
        return ET.fromstring(data)

    def _load_styles(self):
        """styleId -> {name, outline, basedOn}"""
        root = self._read_xml("word/styles.xml")
        styles = {}
        if root is None:
            return styles
        for st in root.findall(w("style")):
            sid = st.get(w("styleId"))
            if not sid:
                continue
            name_el = st.find(w("name"))
            based = st.find(w("basedOn"))
            outline = st.find("./%s/%s" % (w("pPr"), w("outlineLvl")))
            styles[sid] = {
                "name": (name_el.get(W_VAL) if name_el is not None else "") or "",
                "outline": int(outline.get(W_VAL)) if outline is not None else None,
                "basedOn": based.get(W_VAL) if based is not None else None,
            }
        return styles

    def _load_numbering(self):
        """numId -> {ilvl: 'bullet'|'decimal'|...}"""
        root = self._read_xml("word/numbering.xml")
        if root is None:
            return {}
        abstract = {}
        for an in root.findall(w("abstractNum")):
            aid = an.get(w("abstractNumId"))
            levels = {}
            for lvl in an.findall(w("lvl")):
                ilvl = int(lvl.get(w("ilvl")) or 0)
                fmt = lvl.find(w("numFmt"))
                levels[ilvl] = (fmt.get(W_VAL) if fmt is not None else "decimal") or "decimal"
            abstract[aid] = levels
        nums = {}
        for num in root.findall(w("num")):
            nid = num.get(w("numId"))
            aid_el = num.find(w("abstractNumId"))
            if nid and aid_el is not None:
                nums[nid] = abstract.get(aid_el.get(W_VAL), {})
        return nums

    def _load_rels(self, name):
        root = self._read_xml(name)
        rels = {}
        if root is None:
            return rels
        for rel in root:
            rid = rel.get("Id")
            target = rel.get("Target")
            if rid and target:
                rels[rid] = target
        return rels

    def _style_chain(self, style_id):
        """沿 basedOn 向上遍历，最多 10 层防环。"""
        seen = set()
        cur = style_id
        depth = 0
        while cur and cur in self._styles and cur not in seen and depth < 10:
            seen.add(cur)
            yield self._styles[cur]
            cur = self._styles[cur]["basedOn"]
            depth += 1

    def _style_name(self, style_id):
        info = self._styles.get(style_id)
        return (info["name"] if info else "") or ""

    def _heading_level(self, style_id, pPr):
        """返回 1..6 或 None。样式名优先，其次 outlineLvl。"""
        for info in self._style_chain(style_id):
            m = HEADING_NAME_RE.match(info["name"].strip())
            if m:
                return min(6, int(m.group(1)))
        if pPr is not None:
            direct = pPr.find(w("outlineLvl"))
            if direct is not None and direct.get(W_VAL) is not None:
                lvl = int(direct.get(W_VAL))
                if 0 <= lvl <= 5:
                    return lvl + 1
        for info in self._style_chain(style_id):
            if info["outline"] is not None and 0 <= info["outline"] <= 5:
                # TOC Heading 之类样式带 outlineLvl=9，已被范围过滤
                return info["outline"] + 1
        return None

    def _is_code_style(self, style_id):
        for info in self._style_chain(style_id):
            if CODE_STYLE_RE.match(info["name"].strip().lower()):
                return True
        return False

    def _is_toc_style(self, style_id):
        name = self._style_name(style_id).strip()
        return bool(TOC_STYLE_RE.match(name)) and not HEADING_NAME_RE.match(name)

    # ------------------------------------------------------------ 图片

    def _save_media(self, rid, rels=None):
        """按 rId 抽取图片，返回 Markdown 里用的相对路径。"""
        rels = rels or self._rels
        target = rels.get(rid)
        if not target:
            return None
        if target in self._saved_media:
            return self._saved_media[target]
        zip_name = posixpath.normpath(posixpath.join("word", target.replace("\\", "/")))
        if zip_name not in self.zip.namelist():
            alt = posixpath.normpath(target.replace("\\", "/").lstrip("/"))
            if alt in self.zip.namelist():
                zip_name = alt
            else:
                return None
        base = posixpath.basename(zip_name)
        rel = "%s/%s" % (self.media_rel, base)
        if self.keep_media and self.media_dir is not None:
            self.media_dir.mkdir(parents=True, exist_ok=True)
            out = self.media_dir / base
            if not out.exists():
                out.write_bytes(self.zip.read(zip_name))
        self._saved_media[target] = rel
        self.stats["images"] += 1
        return rel

    def _drawing_images(self, el, rels=None):
        """从 w:drawing / w:pict 中取出所有图片，返回 [(alt, rel_path)]。"""
        found = []
        for blip in el.iter("{%s}blip" % NS["a"]):
            rid = blip.get(r_("embed")) or blip.get(r_("link"))
            rel = self._save_media(rid, rels) if rid else None
            if rel:
                found.append((self._nearest_alt(el), rel))
        for imgdata in el.iter("{%s}imagedata" % NS["v"]):
            rid = imgdata.get(r_("id")) or imgdata.get(r_("href"))
            rel = self._save_media(rid, rels) if rid else None
            if rel:
                found.append((imgdata.get(w("title")) or "", rel))
        return found

    @staticmethod
    def _nearest_alt(el):
        for docpr in el.iter("{%s}docPr" % NS["wp"]):
            alt = (docpr.get("descr") or "").strip()
            if alt:
                return alt
        return ""

    # ------------------------------------------------------------ 行内内容

    def _run_props(self, run):
        rPr = run.find(w("rPr"))
        if rPr is None:
            return {"bold": False, "italic": False, "strike": False, "mono": False, "sub": None}
        fonts = rPr.find(w("rFonts"))
        mono = False
        if fonts is not None:
            for attr in ("ascii", "hAnsi", "cs"):
                name = (fonts.get(w(attr)) or "").strip().lower()
                if name in MONO_FONTS:
                    mono = True
                    break
        if not mono:
            rstyle = rPr.find(w("rStyle"))
            if rstyle is not None and self._is_code_style(rstyle.get(W_VAL)):
                mono = True
        vert = rPr.find(w("vertAlign"))
        # 只认 w:b / w:i：w:bCs / w:iCs 仅对复杂文字生效，Word 常在非加粗文本上留 bCs，
        # 误判会凭空多出一堆 ** 。
        return {
            "bold": _on(rPr.find(w("b"))),
            "italic": _on(rPr.find(w("i"))),
            "strike": _on(rPr.find(w("strike"))) or _on(rPr.find(w("dstrike"))),
            "mono": mono,
            "sub": vert.get(W_VAL) if vert is not None else None,
        }

    def _run_items(self, run, rels=None):
        """把一个 w:r 拆成 [('text', s, props) / ('image', ...) / ('break',) / ('fn', n)]。"""
        props = self._run_props(run)
        items = []
        buf = []
        for child in run:
            tag = child.tag
            if tag == w("t"):
                buf.append(map_symbol_text(child.text or ""))
            elif tag == w("tab"):
                buf.append(" ")
            elif tag in (w("br"), w("cr")):
                if buf:
                    items.append(("text", "".join(buf), props))
                    buf = []
                items.append(("break",))
            elif tag == w("noBreakHyphen"):
                buf.append("-")
            elif tag == w("softHyphen"):
                continue
            elif tag == w("sym"):
                buf.append(self._sym_char(child))
            elif tag in (w("drawing"), w("pict"), w("object")):
                if buf:
                    items.append(("text", "".join(buf), props))
                    buf = []
                for alt, rel in self._drawing_images(child, rels):
                    items.append(("image", alt, rel))
            elif tag in (w("footnoteReference"), w("endnoteReference")):
                num = self._footnote(child.get(w("id")))
                if num:
                    if buf:
                        items.append(("text", "".join(buf), props))
                        buf = []
                    items.append(("fn", num))
            # w:instrText / w:delText 等域指令与删除内容一律丢弃
        if buf:
            items.append(("text", "".join(buf), props))
        return items

    @staticmethod
    def _sym_char(sym):
        """w:sym 符号：按符号字体映射表转换，未收录的退化为 · 。"""
        code = sym.get(w("char")) or ""
        try:
            value = int(code, 16)
        except ValueError:
            return ""
        try:
            return map_symbol_text(chr(value))
        except ValueError:
            return ""

    def _footnote(self, fid):
        """把脚注正文收集起来，返回正文中使用的编号。"""
        if self._footnote_xml is None or fid is None or int(fid) < 1:
            return None
        if fid in self._fn_index:
            return self._fn_index[fid]
        target = None
        for fn in self._footnote_xml.findall(w("footnote")):
            if fn.get(w("id")) == fid:
                target = fn
                break
        if target is None:
            return None
        num = len(self._fn_index) + 1
        self._fn_index[fid] = num
        parts = []
        for p in target.findall(w("p")):
            items = self._inline_items(p)
            text = self._render_inline(items).strip()
            if text:
                parts.append(text)
        self._footnotes.append((num, " ".join(parts)))
        self.stats["footnotes"] += 1
        return num

    def _inline_items(self, container, rels=None):
        """遍历段落级容器，收集行内元素（处理超链接 / 修订 / 域 / 嵌套 sdt）。"""
        items = []
        for child in container:
            tag = child.tag
            if tag == w("r"):
                items.extend(self._run_items(child, rels))
            elif tag == w("hyperlink"):
                inner = self._inline_items(child, rels)
                rid = child.get(r_("id"))
                href = (rels or self._rels).get(rid) if rid else None
                anchor = child.get(w("anchor"))
                if href:
                    items.append(("link", inner, href))
                elif anchor:
                    items.extend(inner)  # 文档内跳转在 md 里没有对应目标，退化为纯文本
                else:
                    items.extend(inner)
            elif tag in (w("ins"), w("smartTag"), w("fldSimple"), w("bdo"), w("dir")):
                items.extend(self._inline_items(child, rels))
            elif tag == w("sdt"):
                content = child.find(w("sdtContent"))
                if content is not None:
                    items.extend(self._inline_items(content, rels))
            elif tag == w("subDoc") or tag == w("del"):
                continue
            elif tag == w("pPr"):
                continue
            elif tag == "{%s}AlternateContent" % NS["mc"]:
                fallback = child.find("{%s}Fallback" % NS["mc"])
                choice = child.find("{%s}Choice" % NS["mc"])
                node = choice if choice is not None else fallback
                if node is not None:
                    for alt, rel in self._drawing_images(node, rels):
                        items.append(("image", alt, rel))
        return items

    def _render_inline(self, items, html=False):
        """把行内元素渲染成 Markdown（html=True 时渲染成 HTML，供 HTML 表格用）。"""
        out = []
        for item in items:
            kind = item[0]
            if kind == "text":
                _, raw, props = item
                if not raw:
                    continue
                text = html_escape(raw) if html else escape_md(raw)
                if props.get("mono") and not html:
                    text = "`%s`" % raw.replace("`", "'")
                if props.get("bold"):
                    text = ("<strong>%s</strong>" if html else "**%s**") % text
                if props.get("italic"):
                    text = ("<em>%s</em>" if html else "*%s*") % text
                if props.get("strike"):
                    text = ("<s>%s</s>" if html else "~~%s~~") % text
                if props.get("sub") == "superscript":
                    text = "<sup>%s</sup>" % text
                elif props.get("sub") == "subscript":
                    text = "<sub>%s</sub>" % text
                out.append(text)
            elif kind == "image":
                _, alt, rel = item
                out.append(
                    '<img src="%s" alt="%s" />' % (rel, html_escape(alt))
                    if html
                    else "![%s](%s)" % (alt.replace("]", ""), rel)
                )
            elif kind == "link":
                _, inner, href = item
                label = self._render_inline(inner, html).strip() or href
                out.append(
                    '<a href="%s">%s</a>' % (html_escape(href), label)
                    if html
                    else "[%s](%s)" % (label, href)
                )
            elif kind == "fn":
                out.append("[^%d]" % item[1])
            elif kind == "break":
                out.append("<br>" if html else "\n")
        text = "".join(out)
        # 合并多余空白，但保留换行标记
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text

    # ------------------------------------------------------------ 块级内容

    def _paragraph(self, p, rels=None):
        pPr = p.find(w("pPr"))
        style_id = None
        if pPr is not None:
            ps = pPr.find(w("pStyle"))
            style_id = ps.get(W_VAL) if ps is not None else None

        items = self._inline_items(p, rels)
        text_md = self._render_inline(items).strip()
        images = [it for it in items if it[0] == "image"]
        if not text_md and not images:
            return None

        if self._is_toc_style(style_id):
            return {"kind": "toc", "text": text_md}

        level = self._heading_level(style_id, pPr)
        if level:
            self.stats["headings"] += 1
            flat = re.sub(r"\s*\n\s*", " ", text_md).strip()
            flat = re.sub(r"^#+\s*", "", flat)
            return {"kind": "heading", "level": level, "text": flat}

        # 代码段：整段等宽字体或代码样式
        text_props = [it[2] for it in items if it[0] == "text" and it[1].strip()]
        all_mono = bool(text_props) and all(pr.get("mono") for pr in text_props)
        if not images and (self._is_code_style(style_id) or all_mono):
            raw = "".join(
                it[1] if it[0] == "text" else ("\n" if it[0] == "break" else "")
                for it in items
            )
            return {"kind": "code", "text": raw.rstrip()}

        numPr = pPr.find(w("numPr")) if pPr is not None else None
        if numPr is not None:
            num_el = numPr.find(w("numId"))
            ilvl_el = numPr.find(w("ilvl"))
            num_id = num_el.get(W_VAL) if num_el is not None else None
            ilvl = int(ilvl_el.get(W_VAL)) if ilvl_el is not None else 0
            fmt = self._numbering.get(num_id, {}).get(ilvl, "decimal")
            if num_id and num_id != "0":
                return {
                    "kind": "li",
                    "level": min(ilvl, 5),
                    "ordered": fmt not in ("bullet", "none"),
                    "text": re.sub(r"\s*\n\s*", " ", text_md).strip(),
                }

        return {"kind": "p", "text": text_md}

    def _cell_blocks(self, tc, rels=None):
        blocks = []
        self._walk(tc, blocks, rels)
        return blocks

    def _table(self, tbl, rels=None):
        """解析表格。返回块 dict，含 rows 结构与是否需要 HTML 降级。"""
        rows = []
        for tr in tbl.findall(w("tr")):
            cells = []
            col = 0
            for tc in tr.findall(w("tc")):
                tcPr = tc.find(w("tcPr"))
                span = 1
                vmerge = None
                if tcPr is not None:
                    gs = tcPr.find(w("gridSpan"))
                    if gs is not None and gs.get(W_VAL):
                        span = max(1, int(gs.get(W_VAL)))
                    vm = tcPr.find(w("vMerge"))
                    if vm is not None:
                        vmerge = "restart" if (vm.get(W_VAL) or "continue") == "restart" else "continue"
                cells.append(
                    {
                        "blocks": self._cell_blocks(tc, rels),
                        "colspan": span,
                        "rowspan": 1,
                        "vmerge": vmerge,
                        "col": col,
                        "skip": False,
                    }
                )
                col += span
            if cells:
                rows.append(cells)

        if not rows:
            return None
        self.stats["tables"] += 1

        # 纵向合并：continue 单元格并到上方 restart 单元格
        open_spans = {}
        for row in rows:
            for cell in row:
                if cell["vmerge"] == "restart":
                    open_spans[cell["col"]] = cell
                elif cell["vmerge"] == "continue":
                    owner = open_spans.get(cell["col"])
                    if owner is not None:
                        owner["rowspan"] += 1
                        cell["skip"] = True

        complex_cell = False
        for row in rows:
            for cell in row:
                if cell["colspan"] > 1 or cell["rowspan"] > 1 or cell["vmerge"]:
                    complex_cell = True
                kinds = [b["kind"] for b in cell["blocks"]]
                if any(k in ("table", "li", "code", "heading") for k in kinds):
                    complex_cell = True
                if len([k for k in kinds if k != "toc"]) > 1:
                    complex_cell = True
        widths = {sum(c["colspan"] for c in row) for row in rows}
        if len(widths) > 1:
            complex_cell = True

        if complex_cell:
            self.stats["html_tables"] += 1
        return {"kind": "table", "rows": rows, "html": complex_cell}

    def _walk(self, container, blocks, rels=None):
        for child in container:
            tag = child.tag
            if tag == w("p"):
                block = self._paragraph(child, rels)
                if block:
                    blocks.append(block)
            elif tag == w("tbl"):
                block = self._table(child, rels)
                if block:
                    blocks.append(block)
            elif tag == w("sdt"):
                content = child.find(w("sdtContent"))
                if content is not None:
                    self._walk(content, blocks, rels)
            elif tag == w("tc"):
                self._walk(child, blocks, rels)

    # ------------------------------------------------------------ 序列化

    def _render_cell_md(self, cell):
        parts = []
        for block in cell["blocks"]:
            if block["kind"] in ("p", "heading", "li", "toc"):
                parts.append(block["text"])
            elif block["kind"] == "code":
                parts.append("`%s`" % block["text"].replace("`", "'").replace("\n", " "))
        text = " ".join(x for x in parts if x)
        text = text.replace("\n", "<br>")
        # escape_md 已经转义过竖线，这里只补漏，避免出现 \\| 双重转义
        text = re.sub(r"(?<!\\)\|", r"\\|", text)
        return re.sub(r"\s{2,}", " ", text).strip()

    def _render_cell_html(self, cell):
        parts = []
        for block in cell["blocks"]:
            kind = block["kind"]
            if kind == "table":
                parts.append(self._render_table_html(block, nested=True))
            elif kind == "code":
                parts.append("<pre>%s</pre>" % html_escape(block["text"]))
            elif kind == "li":
                parts.append("• " + html_escape_inline_md(block["text"]))
            elif kind in ("p", "heading", "toc"):
                parts.append(html_escape_inline_md(block["text"]))
        return "<br>".join(x for x in parts if x).strip() or "&nbsp;"

    def _render_table_html(self, block, nested=False):
        lines = ["<table>"]
        for idx, row in enumerate(block["rows"]):
            lines.append("<tr>")
            tag = "th" if idx == 0 and not nested else "td"
            for cell in row:
                if cell["skip"]:
                    continue
                attrs = ""
                if cell["colspan"] > 1:
                    attrs += ' colspan="%d"' % cell["colspan"]
                if cell["rowspan"] > 1:
                    attrs += ' rowspan="%d"' % cell["rowspan"]
                lines.append(
                    "<%s%s>%s</%s>" % (tag, attrs, self._render_cell_html(cell), tag)
                )
            lines.append("</tr>")
        lines.append("</table>")
        return "".join(lines) if nested else "\n".join(lines)

    def _render_table_md(self, block):
        rows = block["rows"]
        width = max(sum(c["colspan"] for c in row) for row in rows)
        out = []
        for idx, row in enumerate(rows):
            cells = [self._render_cell_md(c) for c in row if not c["skip"]]
            cells += [""] * (width - len(cells))
            out.append("| " + " | ".join(cells[:width]) + " |")
            if idx == 0:
                out.append("|" + "|".join([" --- "] * width) + "|")
        if len(rows) == 1:
            # 只有一行时补一行空数据行，保证是合法 GFM 表格
            out.append("|" + "|".join(["  "] * width) + "|")
        return "\n".join(out)

    def _serialize(self, blocks, drop_toc=True):
        out = []
        code_buf = []
        counters = {}

        def flush_code():
            if code_buf:
                self.stats["code_blocks"] += 1
                out.append("```\n" + "\n".join(code_buf).strip("\n") + "\n```")
                del code_buf[:]

        for block in blocks:
            kind = block["kind"]
            if kind == "code":
                code_buf.append(block["text"])
                continue
            flush_code()
            if kind == "toc":
                if not drop_toc and block["text"]:
                    out.append(escape_line_start(block["text"]))
                continue
            if kind == "heading":
                counters.clear()
                out.append("%s %s" % ("#" * block["level"], block["text"]))
            elif kind == "li":
                level = block["level"]
                indent = "  " * level
                if block["ordered"]:
                    counters[level] = counters.get(level, 0) + 1
                    for deeper in [k for k in counters if k > level]:
                        counters.pop(deeper)
                    marker = "%d." % counters[level]
                else:
                    marker = "-"
                text = block["text"].replace("\n", " ")
                out.append("%s%s %s" % (indent, marker, text))
            elif kind == "table":
                counters.clear()
                out.append(
                    self._render_table_html(block)
                    if block["html"]
                    else self._render_table_md(block)
                )
            else:
                counters.clear()
                text = block["text"]
                lines = [escape_line_start(ln) for ln in text.split("\n")]
                out.append("\n".join(lines))
        flush_code()

        if self._footnotes:
            out.append("")
            for num, text in self._footnotes:
                out.append("[^%d]: %s" % (num, text or ""))
        return "\n\n".join(x for x in out if x is not None)

    def core_properties(self):
        """docProps/core.xml 里的标题 / 作者 / 时间，用于 YAML front matter。"""
        root = self._read_xml("docProps/core.xml")
        props = {}
        if root is None:
            return props
        for child in root:
            tag = child.tag.rsplit("}", 1)[-1]
            if child.text and tag in ("title", "creator", "lastModifiedBy", "created", "modified", "subject"):
                props[tag] = child.text.strip()
        return props

    def convert(self, drop_toc=True):
        root = self._read_xml("word/document.xml")
        if root is None:
            raise ValueError("不是有效的 docx：缺少 word/document.xml")
        body = root.find(w("body"))
        if body is None:
            raise ValueError("不是有效的 docx：缺少 w:body")
        blocks = []
        self._walk(body, blocks)
        return self._serialize(blocks, drop_toc=drop_toc), dict(self.stats)


def html_escape_inline_md(text: str) -> str:
    """HTML 表格单元格里把 md 强调还原成标签，其余转义。"""
    text = text.replace("\\", "")
    parts = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append("<strong>%s</strong>" % html_escape(part[2:-2]))
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append("<code>%s</code>" % html_escape(part[1:-1]))
        else:
            out.append(html_escape(part))
    return "".join(out).replace("&lt;br&gt;", "<br>")


def main(argv=None):
    ap = argparse.ArgumentParser(description="内置 docx -> Markdown 引擎")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--media-dir", default=None, help="图片输出目录（绝对或相对路径）")
    ap.add_argument("--media-rel", default="assets", help="写进 md 的图片目录名")
    ap.add_argument("--keep-toc", action="store_true")
    args = ap.parse_args(argv)

    conv = DocxToMarkdown(args.input, media_dir=args.media_dir, media_rel=args.media_rel)
    text, stats = conv.convert(drop_toc=not args.keep_toc)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print("Generated: %s %s" % (args.output, stats))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
