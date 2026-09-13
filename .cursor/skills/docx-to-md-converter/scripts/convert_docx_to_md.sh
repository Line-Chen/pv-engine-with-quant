#!/usr/bin/env bash
# Git Bash / Linux / macOS 下的薄包装：解析 python 后原样转发参数。
# Windows PowerShell 直接用 `python scripts/convert_docx_to_md.py ...` 即可。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_PY="${SCRIPT_DIR}/convert_docx_to_md.py"

python_works() {
  local bin="${1:-}"
  [[ -n "$bin" ]] || return 1
  # Windows 上 WindowsApps/python3 是微软商店的占位程序，不是真解释器：
  # 它不输出任何内容就以非 0 退出，必须排除掉，否则脚本会莫名失败。
  case "$bin" in
  */WindowsApps/*) return 1 ;;
  esac
  "$bin" -c 'import sys' >/dev/null 2>&1
}

resolve_python() {
  local name bin
  for name in python3 python py; do
    bin="$(command -v "$name" 2>/dev/null || true)"
    if python_works "$bin"; then
      echo "$bin"
      return
    fi
  done
  # PATH 上没有可用解释器时，扫一遍 Windows / Unix 常见安装位置
  for bin in \
    /c/Python3*/python.exe \
    "/c/Program Files/Python3"*/python.exe \
    "/c/Program Files (x86)/Python3"*/python.exe \
    "/c/Program Files (x86)/python/python.exe" \
    "/d/Program Files (x86)/python/python.exe" \
    "$HOME/AppData/Local/Programs/Python/Python3"*/python.exe \
    /usr/local/bin/python3 \
    /usr/bin/python3; do
    if python_works "$bin"; then
      echo "$bin"
      return
    fi
  done
  return 1
}

PYTHON_BIN="$(resolve_python || true)"
if [[ -z "${PYTHON_BIN}" ]]; then
  echo "找不到可用的 Python 3 解释器，请先安装 Python 3 并加入 PATH。" >&2
  echo "提示：Git Bash 里的 WindowsApps/python3 是商店占位程序，不能用。" >&2
  exit 1
fi

exec "$PYTHON_BIN" "$MAIN_PY" "$@"
