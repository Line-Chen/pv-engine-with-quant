---
name: docx-to-md-converter
description: Convert Word documents (.doc/.docx/.docm/.wps/.rtf/.odt) to clean GFM Markdown, extracting images, tables and headings. Use when the user asks to convert doc/docx/Word to md/markdown, to extract text or tables from a Word file, or mentions docx2md / word 转 markdown.
disable-model-invocation: true
---

# Docx To Md Converter

`.md -> .docx` 是姊妹技能 [pandoc-docx-converter](../pandoc-docx-converter/SKILL.md)，本技能负责反向的 `Word -> Markdown`。

## Quick Start

1. 确认输入文件存在（`.docx` / `.doc` / `.docm` / `.wps` / `.rtf` / `.odt`）。
2. 直接跑主脚本（PowerShell / CMD / Git Bash 都可以）：

```powershell
python scripts/convert_docx_to_md.py "<input.docx>"
```

3. 指定输出目录、写入 YAML front matter：

```powershell
python scripts/convert_docx_to_md.py "<input.docx>" --out-dir "docs/md" --front-matter
```

4. 老格式 `.doc`：无需额外参数，脚本自动先转 `.docx` 再转 md。

```powershell
python scripts/convert_docx_to_md.py "<input.doc>"
```

5. 批量 / 拆分 / 自检：

```powershell
python scripts/convert_docx_to_md.py docs --recursive --out-dir docs/md
python scripts/convert_docx_to_md.py "<input.docx>" --split-by-heading 2
python scripts/check_md.py "<out.md>"
```

Git Bash 下可用包装器：`bash scripts/convert_docx_to_md.sh "<input.docx>"`。人读说明见同目录 [README.md](README.md)。

## Defaults

- 输出：与源文件**同目录**的 `<同名>.md`；已存在则写 `<同名>_01.md`，**默认不覆盖**（`--overwrite` 才覆盖）。
- 图片：抽到 `<输出名>.assets/`，正文用相对路径 `![](<输出名>.assets/imageN.png)`；无图时不留空目录。
- 引擎：`--engine auto`
  - **pandoc 引擎**（首选）：`-f docx -t gfm --wrap=none --markdown-headings=atx --extract-media`，保真度最好。
  - **内置引擎**（无 pandoc 时自动兜底）：`scripts/docx_reader.py` 纯标准库解析 OOXML，零外部依赖。
- pandoc 查找顺序：`$PANDOC` → PATH → `%LOCALAPPDATA%\Pandoc` → WinGet Packages → Program Files → `/usr/bin`、`/opt/homebrew`。**不在 PATH 上也能用**。
- 老格式转换后端：LibreOffice(`soffice`) 优先，其次 Windows 上的 Word COM（走 PowerShell，不需要 pywin32），`--office-backend` 可指定。
- `--wrap=none`：**不硬换行**，中文段落保持整行，避免 diff 噪声。
- 默认清理项（两个引擎一致）：
  - 删除 Word 自动目录（md 里没有页码，留着只是噪声），`--keep-toc` 保留
  - 删除书签锚点残留（空 `<span id>`、`[]{#_Toc123}`、标题尾部 `{#...}`）
  - 图片去掉 `{width= height=}` 尺寸属性（否则 pandoc 会输出 `<img>` 而不是 `![]()`），`--keep-image-size` 保留
  - 图片 alt 是哈希串 / `imageN` 时清空，只留路径
  - 展开 Word 段落缩进被误读成的 blockquote（`--keep-blockquotes` 保留）；这一步还能让封面表从臃肿 HTML 表回落成管道表
  - 标题内的 `**` / `*` 去掉（标题本身即强调）
  - `U+00A0`、零宽字符、行首全角空格、连续空行统一
  - Wingdings/Symbol 私用码位（`U+F000`~`U+F0FF`）映射为可显示字符（如 `U+F075` → `◆`）
- 表格：能表达成 GFM 管道表就用管道表；**出现合并单元格（gridSpan/vMerge）或单元格内多块内容时降级为 HTML 表**，保证不丢数据。
- `--headings-from-numbers auto`：原文几乎没有标题样式、又存在大量「1.2.3 标题」段落时，自动提升为 ATX 标题；`on` 强制、`off` 关闭。

## Options

| 参数 | 作用 |
|------|------|
| `--out-dir DIR` | 输出目录，默认与源文件同目录 |
| `--name NAME` | 输出文件名（不含 `.md`），批量时忽略 |
| `--engine auto\|pandoc\|builtin` | 选择引擎 |
| `--media-dir NAME` | 图片目录名，默认 `<输出名>.assets` |
| `--no-media` | 不导出图片，正文留 `<!-- 图片已跳过：xxx -->` |
| `--keep-toc` / `--keep-image-size` / `--keep-blockquotes` / `--keep-styles` | 关闭对应清理 |
| `--headings-from-numbers auto\|on\|off` | 编号段落提升为标题 |
| `--shift-heading-level-by N` | 整体升降标题级别 |
| `--split-by-heading N` | 按第 N 级标题拆成多文件，并生成 `<名>_index.md` |
| `--front-matter` | 写 YAML front matter（标题优先取正文第一个 H1，其次 docProps） |
| `--recursive` | 输入是目录时递归子目录 |
| `--overwrite` | 允许覆盖同名输出 |
| `--office-backend libreoffice\|word` | 老格式转换后端 |
| `-v` / `-q` | 打印引擎信息 / 静默 |

## Rules

- 生成的 `.md` 默认与源文档放在同一业务目录，图片目录跟着 md 一起走，整体可直接搬迁。
- 批量转换时单个文件失败不阻断其余文件，最后以非 0 退出码汇总。
- 用户明确要求覆盖已有文件时才加 `--overwrite`。
- 转换后建议跑 `python scripts/check_md.py <out.md>`：校验图片是否落地、表格列数是否对齐、是否残留 Word 噪声、标题是否跳级。
- 转换结果是**结构化文本**，公式（OMML）、文本框、SmartArt、修订批注不保证保留；这些内容需要人工复核。

## Troubleshooting

- **图片链接失效**：确认 `<输出名>.assets/` 与 md 在同一目录；被移动过就重转一次。
- **表格变成 HTML**：说明该表有合并单元格或单元格内含列表/多段落，属预期的无损降级；确实想要管道表就手工拆表。
- **没有识别到任何标题**：原文用手工编号而非标题样式，加 `--headings-from-numbers on`。
- **正文出现 `·`**：原文是 Wingdings 符号且未收录到映射表，属可接受退化；需要精确字符时手工替换。
- **`.doc` 转换失败**：装 LibreOffice 或 Microsoft Word；Word 后端要求当前会话能启动 Word COM（远程无桌面会话时会失败，改用 LibreOffice）。
- **pandoc 找不到**：`winget install JohnMacFarlane.Pandoc`，或直接用 `--engine builtin`（无外部依赖）。
- **两个引擎结果不一致**：pandoc 保真度更高但更容易输出 HTML 表；内置引擎输出更干净的管道表。分别转一次对比取优即可。
