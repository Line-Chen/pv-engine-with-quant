# -*- coding: utf-8 -*-
"""老格式 Office 文档 -> .docx 的桥接层。

pandoc 与内置引擎都只认 OOXML（.docx/.docm），所以 .doc/.wps/.rtf 必须先转一次。
后端按可用性依次尝试：
  1. LibreOffice（soffice，跨平台、无需装 Office）
  2. Word COM（Windows + 已装 Word，通过 PowerShell 调用，不依赖 pywin32）

单独调用：
    python office_to_docx.py <in.doc> [out_dir]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 需要先转成 docx 的扩展名
LEGACY_SUFFIXES = {".doc", ".wps", ".rtf", ".dot", ".docm", ".dotx", ".dotm"}
# 内置/pandoc 引擎可直接读的扩展名
NATIVE_SUFFIXES = {".docx"}


def needs_conversion(path) -> bool:
    return Path(path).suffix.lower() in LEGACY_SUFFIXES


def find_soffice():
    """定位 LibreOffice 可执行文件。"""
    env = os.environ.get("SOFFICE_BIN")
    if env and Path(env).exists():
        return env
    for name in ("soffice", "soffice.exe", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def find_powershell():
    if os.name != "nt":
        return None
    for name in ("powershell.exe", "pwsh.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _convert_with_soffice(src: Path, out_dir: Path, timeout=300):
    soffice = find_soffice()
    if not soffice:
        return None, "未找到 LibreOffice(soffice)"
    # 用独立 user profile，避免和用户正在开的 LibreOffice 抢实例
    profile = tempfile.mkdtemp(prefix="lo_profile_")
    uri = Path(profile).as_uri()
    cmd = [
        soffice,
        "-env:UserInstallation=%s" % uri,
        "--headless",
        "--norestore",
        "--convert-to",
        "docx:MS Word 2007 XML",
        "--outdir",
        str(out_dir),
        str(src),
    ]
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        shutil.rmtree(profile, ignore_errors=True)
        return None, "LibreOffice 调用失败：%s" % exc
    shutil.rmtree(profile, ignore_errors=True)
    target = out_dir / (src.stem + ".docx")
    if target.exists():
        return target, None
    output = (proc.stdout or b"").decode("utf-8", "ignore").strip()
    return None, "LibreOffice 未产出 docx：%s" % (output or "无输出")


_PS_TEMPLATE = r"""
$ErrorActionPreference = 'Stop'
$src = $args[0]
$dst = $args[1]
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    # ConfirmConversions=$false 防止弹「文件转换」对话框；ReadOnly=$true 避免改动源文件
    $doc = $word.Documents.Open($src, $false, $true)
    # 16 = wdFormatDocumentDefault (.docx)
    $doc.SaveAs2($dst, 16)
    Write-Output "OK"
}
finally {
    if ($doc -ne $null) { $doc.Close(0) | Out-Null }
    if ($word -ne $null) { $word.Quit() | Out-Null }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) 2>$null | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) 2>$null | Out-Null
}
"""


def _convert_with_word_com(src: Path, out_dir: Path, timeout=300):
    ps = find_powershell()
    if not ps:
        return None, "非 Windows 或未找到 PowerShell"
    target = out_dir / (src.stem + ".docx")
    script = Path(tempfile.mkdtemp(prefix="w2d_")) / "convert.ps1"
    script.write_text(_PS_TEMPLATE, encoding="utf-8")
    cmd = [
        ps,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        str(src.resolve()),
        str(target.resolve()),
    ]
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        shutil.rmtree(script.parent, ignore_errors=True)
        return None, "Word COM 调用失败：%s" % exc
    shutil.rmtree(script.parent, ignore_errors=True)
    if target.exists():
        return target, None
    output = (proc.stdout or b"").decode("utf-8", "ignore").strip()
    return None, "Word COM 未产出 docx：%s" % (output or "无输出")


def convert_to_docx(src, out_dir=None, prefer=None, verbose=True):
    """把老格式文档转成 docx，返回新文件路径。失败抛 RuntimeError。"""
    src = Path(src)
    if not src.exists():
        raise RuntimeError("输入文件不存在：%s" % src)
    out_dir = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="docx_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    backends = [("libreoffice", _convert_with_soffice), ("word", _convert_with_word_com)]
    if prefer == "word":
        backends.reverse()
    elif prefer == "libreoffice":
        pass

    errors = []
    for name, func in backends:
        result, err = func(src, out_dir)
        if result is not None:
            if verbose:
                print("[office_to_docx] %s -> %s（后端：%s）" % (src.name, result.name, name))
            return result
        errors.append("%s: %s" % (name, err))
    raise RuntimeError(
        "无法把 %s 转成 docx。\n  %s\n请安装 LibreOffice 或 Microsoft Word 后重试。"
        % (src.name, "\n  ".join(errors))
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="老格式 Office 文档转 docx")
    ap.add_argument("input")
    ap.add_argument("out_dir", nargs="?")
    ap.add_argument("--prefer", choices=["libreoffice", "word"], default=None)
    args = ap.parse_args(argv)
    print(convert_to_docx(args.input, args.out_dir, prefer=args.prefer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
