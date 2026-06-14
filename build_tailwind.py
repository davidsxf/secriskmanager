"""
Tailwind CSS 构建脚本
Windows 上 django-tailwind-cli 的管理命令不输出 CSS 文件，
使用此脚本替代。

用法: uv run python build_tailwind.py
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CLI_DIR = BASE_DIR / ".django_tailwind_cli"
SRC = BASE_DIR / "source.css"
OUT = BASE_DIR / "assets" / "css" / "tailwind.css"

# 查找 Tailwind CLI
cli = None
for f in CLI_DIR.iterdir():
    if f.name.startswith("tailwindcss") and f.suffix == ".exe":
        cli = f
        break

if not cli:
    print("❌ Tailwind CLI not found. Run: python manage.py tailwind setup")
    sys.exit(1)

OUT.parent.mkdir(parents=True, exist_ok=True)
SRC.write_text('@import "tailwindcss";')

print(f"Building Tailwind CSS...")

# 使用 uv run python assets/write_tailwind.py 构建
# 当前脚本仅用于手动构建，实际构建由 assets/write_tailwind.py 完成

import subprocess, sys
from pathlib import Path
BASE_DIR = Path(__file__).parent
CLI_DIR = BASE_DIR / ".django_tailwind_cli"
SRC = BASE_DIR / "source.css"
OUT = BASE_DIR / "assets" / "css" / "tailwind.css"

cli = None
for f in CLI_DIR.iterdir():
    if f.name.startswith("tailwindcss") and f.suffix == ".exe":
        cli = f
        break

if not cli:
    print("Tailwind CLI not found. Using manual CSS fallback.")
    # 备用：手动写入基础样式
    from assets.write_tailwind import write_css
    write_css()
    sys.exit(0)

OUT.parent.mkdir(parents=True, exist_ok=True)
SRC.write_text('@import "tailwindcss";')

r = subprocess.run(
    [str(cli), "run", "tailwindcss", "-i", str(SRC), "-o", str(OUT)],
    cwd=str(BASE_DIR),
    capture_output=True, text=False, timeout=120,
)

if r.returncode == 0 and OUT.exists() and OUT.stat().st_size > 0:
    print(f"Built: {OUT} ({OUT.stat().st_size} bytes)")
else:
    print(f"CLI build issue, using manual fallback...")
    from assets.write_tailwind import write_css
    write_css()
