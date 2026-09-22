"""Cross-platform environment bootstrap and launcher for APIson."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
STAMP = VENV_DIR / ".apison-requirements"


def venv_python(windowed: bool = False, platform_name: str | None = None) -> Path:
    platform_name = platform_name or os.name
    if platform_name == "nt":
        name = "pythonw.exe" if windowed else "python.exe"
        return VENV_DIR / "Scripts" / name
    return VENV_DIR / "bin" / "python"


def requirements_fingerprint() -> str:
    return REQUIREMENTS.read_text(encoding="utf-8").strip() if REQUIREMENTS.exists() else ""


def ensure_environment() -> Path:
    if sys.version_info < (3, 10):
        raise RuntimeError("需要 Python 3.10 或更高版本")
    python = venv_python()
    if not python.exists():
        print(f"[APIson] 正在创建虚拟环境: {VENV_DIR}", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    fingerprint = requirements_fingerprint()
    installed = STAMP.read_text(encoding="utf-8") if STAMP.exists() else ""
    if fingerprint != installed:
        print("[APIson] 正在安装或更新依赖...", flush=True)
        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            cwd=ROOT, check=True,
        )
        STAMP.write_text(fingerprint, encoding="utf-8")
    return python


def launch(target: str, extra_args: list[str], wait: bool = True) -> int:
    python = ensure_environment()
    script = ROOT / ("gui.py" if target == "gui" else "gateway.py")
    executable = python
    if target == "gui" and os.name == "nt" and venv_python(windowed=True).exists():
        executable = venv_python(windowed=True)
    command = [str(executable), str(script), *extra_args]
    if wait:
        return subprocess.run(command, cwd=ROOT).returncode
    subprocess.Popen(command, cwd=ROOT, start_new_session=(os.name != "nt"))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="准备并启动 APIson")
    parser.add_argument("target", choices=("gui", "gateway"), nargs="?", default="gui")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    try:
        return launch(options.target, options.args)
    except subprocess.CalledProcessError as exc:
        print(f"[APIson] 依赖安装失败，退出码: {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"[APIson] 启动失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
