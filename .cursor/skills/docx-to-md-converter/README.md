# docx-to-md-converter

把 Word 文档转成干净的 Markdown（GFM）。`.doc` 老格式会先自动转 `.docx`；图片抽到 `<输出名>.assets/`；表格能用管道表就用管道表，有合并单元格才降级成 HTML 表；Word 自动目录、书签锚点、图片尺寸属性这些噪声默认清掉。

姊妹技能 [pandoc-docx-converter](../pandoc-docx-converter/README.md) 负责反向的 `md → Word`，两者可以配合做「Word 进来改完再出去」的往返。

## 安装（单独拿走时）

解压后放到 Cursor 技能目录，目录名保持 `docx-to-md-converter`：

| 范围 | 路径 |
|------|------|
| 个人（所有项目） | `~/.cursor/skills/docx-to-md-converter/` |
| 仅当前仓库 | `<repo>/.cursor/skills/docx-to-md-converter/` |

本技能设为**仅显式调用**（`disable-model-invocation: true`，与姊妹技能一致）：在对话里点名 `docx-to-md-converter`，或者直接按下面的命令自己跑脚本。

## 依赖

| 工具 | 用途 | 必需？ |
|------|------|--------|
| Python 3 | 跑脚本本体 | 必需 |
| [pandoc](https://pandoc.org/installing.html) | 首选转换引擎，保真度最好 | 可选，没有则自动用内置引擎 |
| LibreOffice 或 Microsoft Word | `.doc`/`.wps`/`.rtf` 先转 `.docx` | 仅老格式需要 |

内置引擎只用 Python 标准库，**不需要 pandoc、不需要 python-docx、不需要 lxml**。

Windows 可先 `winget install JohnMacFarlane.Pandoc`；pandoc 不在 PATH 上也没关系，脚本会自己去 `%LOCALAPPDATA%\Pandoc`、WinGet 目录、Program Files 里找。

## 怎么转

```powershell
$S = ".cursor\skills\docx-to-md-converter\scripts"

# 1) 最简：输出到源文件同目录的同名 .md
python $S\convert_docx_to_md.py "docs\接口文档.docx"

# 2) 输出到指定目录 + 写 YAML front matter
python $S\convert_docx_to_md.py "docs\接口文档.docx" --out-dir docs\md --front-matter

# 3) .doc 老格式（自动经 LibreOffice / Word 转一次）
python $S\convert_docx_to_md.py "docs\旧文档.doc"

# 4) 批量：整个目录（--recursive 含子目录）
python $S\convert_docx_to_md.py docs --recursive --out-dir docs\md

# 5) 长文档按二级标题拆成多个文件 + 索引
python $S\convert_docx_to_md.py "docs\接口文档.docx" --split-by-heading 2

# 6) 只要文字不要图
python $S\convert_docx_to_md.py "docs\接口文档.docx" --no-media

# 7) 转完自检
python $S\check_md.py "docs\md\接口文档.md"
```

Git Bash / Linux / macOS：

```bash
bash scripts/convert_docx_to_md.sh "docs/接口文档.docx" --out-dir docs/md
```

不写 `--out-dir` 时输出到源文件同目录；同名文件已存在会写 `_01`、`_02`，**不会覆盖**，除非显式加 `--overwrite`。

## 输出长什么样

```
docs/md/
  接口文档.md                 # 正文
  接口文档.assets/            # 图片，md 里用相对路径引用
    image3.jpeg
    image4.png
```

加 `--front-matter` 会在开头写：

```yaml
---
title: "星耀QUANT SDK接口说明"
source: "星耀QUANT SDK接口文档.docx"
author: "项目组"
converted_at: "2026-09-10"
converter: "docx-to-md-converter/pandoc"
---
```

`title` 优先取正文第一个 `#` 标题，因为 Word 文档属性里的标题经常是模板遗留的旧值。

## 两个引擎的差异

| | pandoc 引擎 | 内置引擎 |
|---|---|---|
| 依赖 | 需要 pandoc | 仅 Python 标准库 |
| 保真度 | 更高（列表嵌套、复杂行内格式） | 覆盖标题/列表/表格/图片/脚注/代码块 |
| 表格 | 单元格稍复杂就降级 HTML 表 | 更倾向输出管道表，更干净 |
| 适用 | 日常首选 | 无法装 pandoc 的环境、需要更干净表格时 |

`--engine auto`（默认）= 有 pandoc 用 pandoc，没有就用内置。拿不准哪个好，两个都转一次对比：

```powershell
python $S\convert_docx_to_md.py "a.docx" --name a_pandoc  --engine pandoc
python $S\convert_docx_to_md.py "a.docx" --name a_builtin --engine builtin
```

## 默认清掉哪些噪声

- Word 自动目录（md 里没页码，纯噪声）——`--keep-toc` 可保留
- 书签锚点残留：空 `<span id="...">`、`[]{#_Toc123}`、标题尾部 `{#...}`
- 图片尺寸属性 `{width="5in" height="2in"}`——留着 pandoc 会输出 `<img>` 而不是 `![]()`
- 哈希串 / `imageN` 这类无信息量的图片 alt
- Word 段落缩进被误读成的引用块（顺带让封面表从 HTML 表回落成管道表）——`--keep-blockquotes` 可保留
- 标题里多余的 `**` / `*`
- `U+00A0`、零宽字符、行首全角空格、连续空行
- Wingdings/Symbol 私用码位映射成可显示字符（`U+F075` → `◆`），未收录的退化为 `·`

## 自检脚本

```powershell
python $S\check_md.py "docs\md\接口文档.md"
# INFO  图片链接 3 个
# INFO  管道表格 19 个，HTML 表格 3 个
# INFO  标题 45 个（最深 H4）
# OK    未发现问题
```

检查项：图片链接能否在磁盘上找到（ERROR，退出码 1）、管道表格列数是否对齐、是否残留 Word 噪声、标题是否跳级、是否一个标题都没有。

## 目录结构

```
docx-to-md-converter/
  SKILL.md                  # 给 Cursor Agent 看的说明
  README.md                 # 本文件
  scripts/
    convert_docx_to_md.py   # 主入口：引擎选择 + 老格式桥接 + 后处理 + 拆分
    convert_docx_to_md.sh   # Git Bash 包装器
    docx_reader.py          # 内置 OOXML -> Markdown 引擎
    office_to_docx.py       # .doc/.wps/.rtf -> .docx（LibreOffice / Word COM）
    md_postprocess.py       # 两引擎共用的清理与拆分
    check_md.py             # 结果自检
```

## 常见问题

- **图片显示不出来**：`.assets` 目录要和 md 放在一起；单独搬走 md 会断链，重转一次即可。
- **表格变成一坨 HTML**：该表有合并单元格，或单元格里有列表/多段落。这是有意的无损降级，管道表表达不了这些结构。
- **一个标题都没识别到**：原文靠手工敲编号而不是标题样式，加 `--headings-from-numbers on`。
- **`.doc` 转换失败**：装 LibreOffice，或确认当前会话能起 Word COM（无桌面会话的远程环境起不来，用 `--office-backend libreoffice`）。
- **公式 / 文本框 / SmartArt 丢了**：OOXML 里这些不是普通段落，两个引擎都不保证；转完人工复核。
- **想保留原样不做清理**：`--keep-toc --keep-image-size --keep-blockquotes --headings-from-numbers off` 一起加上。
