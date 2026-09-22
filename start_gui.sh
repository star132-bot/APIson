#!/usr/bin/env bash
# 启动 APIson 桌面可视化管理面板；首次运行自动创建环境并安装依赖
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
    exec python3 bootstrap.py gui "$@"
elif command -v python >/dev/null 2>&1; then
    exec python bootstrap.py gui "$@"
else
    echo "APIson 需要 Python 3.10 或更高版本。" >&2
    exit 1
fi
