#!/usr/bin/env bash
# 启动 APIson 桌面可视化管理面板
cd "$(dirname "$0")"
if [ -f "./.venv/bin/python" ]; then
    exec ./.venv/bin/python gui.py "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 gui.py "$@"
else
    exec python gui.py "$@"
fi
