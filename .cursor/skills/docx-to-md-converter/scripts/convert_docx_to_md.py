# -*- coding: utf-8 -*-
"""doc / docx -> Markdown 主入口。

设计：双引擎 + 老格式桥接 + 统一后处理
  - pandoc 引擎（默认，保真度最好）：pandoc -f docx -t gfm --wrap=none --extract-media
  - 内置引擎（无 pandoc 时自动兜底）：scripts/docx_reader.py 直接解析 OOXML
  - .doc/.wps/.rtf 先经 LibreOffice 或 Word COM 转成 .docx
  - 两条链路都走 md_postprocess，输出风格一致：去目录、去锚点噪声、图片相对路径

用法（PowerShell / CMD / Git Bash 均可）：
    python convert_docx_to_md.py "docs/某文档.docx"
    python convert_docx_to_md.py "docs/某文档.doc" --out-dir docs/md --front-matter
    python convert_docx_to_md.py docs --recursive --split-by-heading 2
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import md_postprocess  # noqa: E402
import office_to_docx  # noqa: E402
from docx_reader import DocxToMarkdown  # noqa: E402

# pandoc 可直接读的输入格式（odt 也支持，无需先转 docx）
PANDOC_DIRECT = {".docx": "docx", ".docm": "docx", ".odt": "odt"}
SCAN_SUFFIXES = (".docx", ".doc", ".docm", ".wps", ".rtf", ".odt")

LUA_BASE = r"""
-- 清理 Word 转换噪声：空锚点 span、空段落、自动书签 id、custom-style Div
function Span(el)
  if #el.content == 0 then
    return {}
  end
  return el
end

function Para(el)
  for _, item in ipairs(el.content) do
    local t = item.t
    if t ~= 'Space' and t ~= 'SoftBreak' and t ~= 'LineBreak' then
      return el
    end
  end
  return {}
end

function Header(el)
  if el.identifier:match('^_Toc') or el.identifier:match('^_Ref') or el.identifier:match('^_Hlk') then
    el.identifier = ''
  end
  -- 标题里的换行会让 pandoc 退化成 setext 标题（下面画 ==== 那种），压成空格
  local flat = {}
  for _, item in ipairs(el.content) do
    if item.t == 'LineBreak' or item.t == 'SoftBreak' then
      flat[#flat + 1] = pandoc.Space()
    else
      flat[#flat + 1] = item
    end
  end
  el.content = flat
  return el
end

"""

# +styles 会把每段包一层 custom-style Div/Span；不需要样式信息时直接拆掉包装
LUA_UNWRAP_STYLE_DIV = r"""
function Div(el)
  if el.attributes and el.attributes['custom-style'] then
    return el.content
  end
  return el
end
"""

# 带宽高属性的图片会被 gfm writer 写成 <img>，去掉属性才能得到 ![](path)
LUA_STRIP_IMAGE_ATTRS = r"""
function Image(el)
  el.attr = pandoc.Attr()
  return el
end
"""

# Word 的段落缩进常被读成 BlockQuote，留着会让表格单元格变多块内容而降级为 HTML 表
LUA_UNWRAP_BLOCKQUOTE = r"""
function BlockQuote(el)
  return el.content
end
"""


def build_lua_filter(args) -> str:
    parts = [LUA_BASE]
    if not args.keep_styles:
        parts.append(LUA_UNWRAP_STYLE_DIV)
    if not args.keep_image_size:
        parts.append(LUA_STRIP_IMAGE_ATTRS)
    if not args.keep_blockquotes:
        parts.append(LUA_UNWRAP_BLOCKQUOTE)
    return "\n".join(parts)


# ---------------------------------------------------------------- 工具


def resolve_pandoc():
    """按 PATH -> 环境变量 -> 常见安装位置 依次查找 pandoc。"""
    env = os.environ.get("PANDOC")
    if env and Path(env).exists():
        return env
    found = shutil.which("pandoc")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    candidates = []
    if local:
        candidates.append(str(Path(local) / "Pandoc" / "pandoc.exe"))
        winget = Path(local) / "Microsoft" / "WinGet" / "Packages"
        if winget.exists():
            candidates.extend(str(p) for p in winget.rglob("pandoc.exe"))
    candidates += [
        r"C:\Program Files\Pandoc\pandoc.exe",
        r"C:\Program Files (x86)\Pandoc\pandoc.exe",
        r"C:\ProgramData\chocolatey\bin\pandoc.exe",
        "/usr/local/bin/pandoc",
        "/usr/bin/pandoc",
        "/opt/homebrew/bin/pandoc",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def pandoc_version(binary):
    try:
        out = subprocess.run(
            [binary, "--version"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        ).stdout.decode("utf-8", "ignore")
        m = re.search(r"pandoc\s+([\d.]+)", out)
        return m.group(1) if m else "unknown"
    except OSError:
        return "unknown"


def unique_path(path: Path, overwrite: bool) -> Path:
    """默认不覆盖：已存在则追加 _01、_02 ……"""
    if overwrite or not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 1
    while True:
        candidate = parent / ("%s_%02d%s" % (stem, n, suffix))
        if not candidate.exists():
            return candidate
        n += 1


def flatten_media(media_dir: Path):
    """pandoc 会写成 <assets>/media/xxx.png，这里拉平一层并去重。"""
    if not media_dir.exists():
        return 0
    moved = 0
    for src in list(media_dir.rglob("*")):
        if src.is_dir() or src.parent == media_dir:
            continue
        dst = media_dir / src.name
        if dst.exists():
            if dst.stat().st_size == src.stat().st_size:
                src.unlink()
                continue
            stem, suffix = src.stem, src.suffix
            n = 1
            while (media_dir / ("%s_%d%s" % (stem, n, suffix))).exists():
                n += 1
            dst = media_dir / ("%s_%d%s" % (stem, n, suffix))
        shutil.move(str(src), str(dst))
        moved += 1
    for sub in sorted(
        (p for p in media_dir.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)
    ):
        try:
            sub.rmdir()
        except OSError:
            pass
    return moved


def summarize(text: str) -> dict:
    """从最终 md 统计产出规模，便于人工抽查。"""
    return {
        "行数": text.count("\n") + 1,
        "字符": len(text),
        "标题": len(re.findall(r"^#{1,6}\s+\S", text, flags=re.M)),
        "管道表": len(re.findall(r"^\|[^\n]*\|\s*$\n^\|[\s:|-]+\|\s*$", text, flags=re.M)),
        "HTML表": text.count("<table>"),
        "图片": len(re.findall(r"!\[[^\]]*\]\(", text)),
        "代码块": len(re.findall(r"^```", text, flags=re.M)) // 2,
    }


def build_front_matter(props: dict, source: Path, engine: str, title_fallback: str):
    def esc(value):
        value = str(value).replace('"', '\\"')
        return '"%s"' % value

    lines = ["---"]
    lines.append("title: %s" % esc(props.get("title") or title_fallback))
    lines.append("source: %s" % esc(source.name))
    if props.get("creator"):
        lines.append("author: %s" % esc(props["creator"]))
    if props.get("modified"):
        lines.append("doc_modified: %s" % esc(props["modified"]))
    lines.append("converted_at: %s" % esc(date.today().isoformat()))
    lines.append("converter: %s" % esc("docx-to-md-converter/%s" % engine))
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def read_core_props(docx_path: Path) -> dict:
    try:
        return DocxToMarkdown(docx_path, keep_media=False).core_properties()
    except Exception:
        return {}


# ---------------------------------------------------------------- 引擎


def run_pandoc(pandoc_bin, src_docx: Path, out_md: Path, media_rel: str, args):
    """在输出目录里执行 pandoc，保证 --extract-media 生成相对路径。"""
    fmt = PANDOC_DIRECT.get(src_docx.suffix.lower(), "docx")
    if args.keep_styles:
        fmt += "+styles"
    tmpdir = Path(tempfile.mkdtemp(prefix="d2m_"))
    lua = tmpdir / "clean.lua"
    lua.write_text(build_lua_filter(args), encoding="utf-8")
    cmd = [
        pandoc_bin,
        "-f",
        fmt,
        "-t",
        "gfm",
        "--wrap=none",
        "--markdown-headings=atx",
        "--lua-filter=%s" % lua,
        "-o",
        out_md.name,
        str(src_docx.resolve()),
    ]
    if args.shift_heading_level_by:
        cmd.insert(-1, "--shift-heading-level-by=%d" % args.shift_heading_level_by)
    if not args.no_media:
        cmd.insert(-1, "--extract-media=%s" % media_rel)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(out_md.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        shutil.rmtree(str(tmpdir), ignore_errors=True)
    stderr = proc.stderr.decode("utf-8", "ignore").strip()
    if proc.returncode != 0:
        raise RuntimeError("pandoc 转换失败（退出码 %d）：%s" % (proc.returncode, stderr))
    if stderr and args.verbose:
        print("[pandoc] %s" % stderr)
    return out_md.read_text(encoding="utf-8"), {}


def run_builtin(src_docx: Path, media_dir: Path, media_rel: str, args):
    if src_docx.suffix.lower() == ".odt":
        raise RuntimeError("内置引擎不支持 .odt，请安装 pandoc 或先转成 .docx")
    conv = DocxToMarkdown(
        src_docx,
        media_dir=media_dir,
        media_rel=media_rel,
        keep_media=not args.no_media,
    )
    text, stats = conv.convert(drop_toc=not args.keep_toc)
    return text, stats


# ---------------------------------------------------------------- 单文件流程


def convert_one(src: Path, args, pandoc_bin):
    src = src.resolve()
    if not src.exists():
        raise RuntimeError("输入文件不存在：%s" % src)

    out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 老格式先转 docx（临时目录，不污染业务目录）
    tmp_convert = None
    work = src
    if office_to_docx.needs_conversion(src) and src.suffix.lower() not in PANDOC_DIRECT:
        tmp_convert = Path(tempfile.mkdtemp(prefix="legacy_"))
        work = office_to_docx.convert_to_docx(
            src, tmp_convert, prefer=args.office_backend, verbose=args.verbose
        )

    try:
        # 2) 决定引擎
        engine = args.engine
        if engine == "auto":
            engine = "pandoc" if pandoc_bin else "builtin"
        if engine == "pandoc" and not pandoc_bin:
            raise RuntimeError("指定了 --engine pandoc，但未找到 pandoc 可执行文件")

        stem = args.name or src.stem
        out_md = unique_path(out_dir / ("%s.md" % stem), args.overwrite)
        media_rel = args.media_dir or ("%s.assets" % out_md.stem)
        media_dir = out_dir / media_rel

        # 3) 跑引擎
        if engine == "pandoc":
            text, engine_stats = run_pandoc(pandoc_bin, work, out_md, media_rel, args)
            flatten_media(media_dir)
        else:
            text, engine_stats = run_builtin(work, media_dir, media_rel, args)

        # 4) 统一后处理
        text, post_stats = md_postprocess.postprocess(
            text,
            media_dirname=media_rel,
            keep_toc=args.keep_toc,
            keep_image_size=args.keep_image_size,
            heading_mode=args.headings_from_numbers,
            keep_media=not args.no_media,
        )

        # 5) front matter：标题优先取正文第一个 H1，它比 docProps 里的历史标题更可信
        if args.front_matter:
            props = read_core_props(work)
            first_h1 = re.search(r"^#\s+(\S.*)$", text, flags=re.M)
            if first_h1:
                props["title"] = first_h1.group(1).strip()
            text = build_front_matter(props, src, engine, stem) + text

        out_md.write_text(text, encoding="utf-8")

        # 图片目录为空时删掉，避免留空壳
        if media_dir.exists() and not any(media_dir.iterdir()):
            media_dir.rmdir()

        # 6) 可选拆分
        extra = []
        if args.split_by_heading:
            extra = md_postprocess.split_by_heading(
                text, args.split_by_heading, out_dir, out_md.stem
            )

        stats = summarize(text)
        stats.update({k: v for k, v in post_stats.items() if v})
        if engine_stats.get("html_tables"):
            stats["HTML表(合并单元格)"] = engine_stats["html_tables"]
        return {
            "source": src,
            "output": out_md,
            "engine": engine,
            "media_dir": media_dir if media_dir.exists() else None,
            "split": extra,
            "stats": stats,
        }
    finally:
        if tmp_convert:
            shutil.rmtree(str(tmp_convert), ignore_errors=True)


def collect_inputs(raw_inputs, recursive: bool):
    """支持文件、目录、通配符混合传入。"""
    files = []
    for item in raw_inputs:
        path = Path(item)
        if path.is_dir():
            it = path.rglob("*") if recursive else path.glob("*")
            files.extend(
                p
                for p in sorted(it)
                if p.is_file()
                and p.suffix.lower() in SCAN_SUFFIXES
                and not p.name.startswith("~$")
            )
        elif path.exists():
            files.append(path)
        else:
            matches = sorted(Path().glob(item))
            if not matches:
                raise RuntimeError("找不到输入：%s" % item)
            files.extend(p for p in matches if p.is_file() and not p.name.startswith("~$"))
    # 去重且保持顺序
    seen, result = set(), []
    for f in files:
        key = str(f.resolve()).lower()
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result


def build_parser():
    ap = argparse.ArgumentParser(
        prog="convert_docx_to_md.py",
        description="把 .doc/.docx/.odt 等 Word 文档转成 Markdown（GFM）",
    )
    ap.add_argument("inputs", nargs="+", help="文件、目录或通配符")
    ap.add_argument("--out-dir", default=None, help="输出目录，默认与源文件同目录")
    ap.add_argument("--recursive", action="store_true", help="输入是目录时递归子目录")
    ap.add_argument("--name", default=None, help="输出文件名（不含 .md），仅单文件时有效")
    ap.add_argument(
        "--engine", choices=["auto", "pandoc", "builtin"], default="auto",
        help="auto：有 pandoc 用 pandoc，否则用内置引擎",
    )
    ap.add_argument("--media-dir", default=None, help="图片目录名，默认 <输出名>.assets")
    ap.add_argument("--no-media", action="store_true", help="不导出图片，正文留注释占位")
    ap.add_argument("--keep-toc", action="store_true", help="保留 Word 自动目录")
    ap.add_argument("--keep-image-size", action="store_true", help="保留图片宽高属性")
    ap.add_argument(
        "--keep-blockquotes", action="store_true",
        help="保留引用块；默认展开（Word 的段落缩进常被误读成引用）",
    )
    ap.add_argument("--keep-styles", action="store_true", help="pandoc：保留自定义样式信息")
    ap.add_argument(
        "--headings-from-numbers", choices=["auto", "on", "off"], default="auto",
        help="把「1.2 标题」段落提升为标题；auto 仅在原文几乎没有标题时生效",
    )
    ap.add_argument(
        "--shift-heading-level-by", type=int, default=0,
        help="整体升降标题级别，如 -1 把 H1 变成文档标题之外的正文结构",
    )
    ap.add_argument("--split-by-heading", type=int, default=0, help="按第 N 级标题拆分为多个文件")
    ap.add_argument("--front-matter", action="store_true", help="写入 YAML front matter")
    ap.add_argument("--overwrite", action="store_true", help="允许覆盖同名输出")
    ap.add_argument(
        "--office-backend", choices=["libreoffice", "word"], default=None,
        help="老格式转换优先使用的后端",
    )
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.quiet:
        args.verbose = False

    pandoc_bin = resolve_pandoc() if args.engine in ("auto", "pandoc") else None
    if args.verbose:
        print(
            "[engine] pandoc=%s"
            % ("%s (%s)" % (pandoc_bin, pandoc_version(pandoc_bin)) if pandoc_bin else "未安装")
        )

    files = collect_inputs(args.inputs, recursive=args.recursive)
    if not files:
        print("没有可转换的文档", file=sys.stderr)
        return 1
    if len(files) > 1:
        args.name = None  # 批量时忽略 --name，避免互相覆盖

    failures = []
    for src in files:
        try:
            result = convert_one(src, args, pandoc_bin)
        except Exception as exc:  # 批量场景下单个失败不阻断其余文件
            failures.append((src, exc))
            print("[FAIL] %s -> %s" % (src.name, exc), file=sys.stderr)
            continue
        if not args.quiet:
            stats = " ".join("%s=%s" % (k, v) for k, v in result["stats"].items())
            print("Generated: %s" % result["output"])
            print("  引擎=%s  %s" % (result["engine"], stats))
            if result["media_dir"]:
                count = len(list(result["media_dir"].iterdir()))
                print("  图片目录=%s（%d 个文件）" % (result["media_dir"].name, count))
            for extra in result["split"]:
                print("  拆分: %s" % extra.name)

    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
