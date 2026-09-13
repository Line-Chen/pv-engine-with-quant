# -*- coding: utf-8 -*-
"""转换结果自检：图片是否落地、表格列数是否对齐、是否残留 Word 噪声。

    python check_md.py <out.md>

有 ERROR 时退出码 1，只有 WARN 时退出码 0（便于接入流水线）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from md_postprocess import split_code_blocks  # noqa: E402

# 残留噪声特征：Word 锚点、pandoc 尺寸属性、不可见字符
NOISE_PATTERNS = [
    (r'<span\s+id="[^"]*"\s*>\s*</span>', "残留空锚点 span"),
    (r"\{width=", "残留 pandoc 图片尺寸属性"),
    (r"\u00a0", "残留不换行空格 (U+00A0)"),
    (r"\ufffc", "残留对象替换符 (U+FFFC)"),
    (r"\{#_Toc", "残留 Word 目录书签"),
]


def count_columns(line: str) -> int:
    """统计管道表格列数：单元格内容里的 \\| 是转义竖线，不能算作分隔符。"""
    return len(re.findall(r"(?<!\\)\|", line)) - 1


def check(md_path: Path):
    errors, warns, infos = [], [], []
    text = md_path.read_text(encoding="utf-8")
    base = md_path.parent

    # 1) 图片链接必须能在磁盘上找到（兼容 <path with space> 尖括号写法）
    images = [
        m.group(1)[1:-1] if m.group(1).startswith("<") else m.group(1)
        for m in re.finditer(r"!\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)", text)
    ]
    for target in images:
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target) or target.startswith("data:"):
            continue
        if not (base / target).exists():
            errors.append("图片缺失：%s" % target)
    infos.append("图片链接 %d 个" % len(images))

    # 2) 管道表格列数一致性（表头与分隔行、数据行）
    table_count = 0
    for is_code, block in split_code_blocks(text):
        if is_code:
            continue
        lines = block.split("\n")
        i = 0
        while i < len(lines):
            if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(
                r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]
            ):
                table_count += 1
                width = count_columns(lines[i])
                j = i
                while j < len(lines) and lines[j].lstrip().startswith("|"):
                    got = count_columns(lines[j])
                    if got != width:
                        warns.append(
                            "表格列数不一致（表头 %d 列，该行 %d 列）：%s"
                            % (width, got, lines[j][:60])
                        )
                    j += 1
                i = j
                continue
            i += 1
    infos.append("管道表格 %d 个，HTML 表格 %d 个" % (table_count, text.count("<table>")))

    # 3) 噪声残留
    for pattern, desc in NOISE_PATTERNS:
        hits = len(re.findall(pattern, text))
        if hits:
            warns.append("%s（%d 处）" % (desc, hits))

    # 4) 标题层级跳级（H1 直接到 H3 之类，影响目录生成）
    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s+\S", text, flags=re.M)]
    jumps = sum(1 for a, b in zip(levels, levels[1:]) if b - a > 1)
    if jumps:
        warns.append("标题层级跳级 %d 处（可能是 Word 样式不规范）" % jumps)
    infos.append("标题 %d 个（最深 H%d）" % (len(levels), max(levels) if levels else 0))
    if not levels:
        warns.append("没有识别到任何标题，考虑 --headings-from-numbers on")

    return errors, warns, infos


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown 转换结果自检")
    ap.add_argument("inputs", nargs="+")
    args = ap.parse_args(argv)

    exit_code = 0
    for item in args.inputs:
        path = Path(item)
        print("== %s" % path)
        if not path.exists():
            print("  ERROR 文件不存在")
            exit_code = 1
            continue
        errors, warns, infos = check(path)
        for line in infos:
            print("  INFO  %s" % line)
        for line in warns:
            print("  WARN  %s" % line)
        for line in errors:
            print("  ERROR %s" % line)
        if errors:
            exit_code = 1
        elif not warns:
            print("  OK    未发现问题")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
