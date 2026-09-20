#!/usr/bin/env bash
# 启动 APIson 本地 OpenAI 兼容网关服务 (默认端口 8765)
cd "$(dirname "$0")"
if [ -f "./.venv/bin/python" ]; then
    exec ./.venv/bin/python gateway.py "$@"
elif command -v python3 >/dev/null 2>&1; then
    exec python3 gateway.py "$@"
else
    exec python gateway.py "$@"
fi
