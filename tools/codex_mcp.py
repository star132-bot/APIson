"""Install and diagnose APIson's MCP server in Codex Desktop/CLI."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SERVER_NAME = "agent-model-connect"
ROOT = Path(__file__).resolve().parent.parent
MCP_SCRIPT = ROOT / "mcp_server.py"


def codex_config_path() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "config.toml"


def preferred_python() -> Path:
    if os.name == "nt":
        candidates = [ROOT / ".venv" / "Scripts" / "python.exe"]
    else:
        candidates = [ROOT / ".venv" / "bin" / "python"]
    return next((p for p in candidates if p.exists()), Path(sys.executable))


def codex_toml_block(python: str | Path | None = None, script: str | Path | None = None) -> str:
    """Build valid TOML for POSIX and Windows paths."""
    python_path = json.dumps(str(python or preferred_python()))
    script_path = json.dumps(str(script or MCP_SCRIPT))
    return (
        f"[mcp_servers.{SERVER_NAME}]\n"
        f"command = {python_path}\n"
        f"args = [{script_path}]\n"
        "startup_timeout_sec = 30\n"
        "tool_timeout_sec = 300\n"
        "required = true\n"
    )


def get_codex_mcp_status() -> dict:
    config = codex_config_path()
    if not config.exists():
        return {"installed": False, "config": str(config), "platform": sys.platform,
                "message": "未找到 Codex 配置文件"}
    text = config.read_text(encoding="utf-8")
    match = re.search(rf"(?m)^\[mcp_servers\.{re.escape(SERVER_NAME)}\]\s*$", text)
    return {
        "installed": bool(match),
        "config": str(config),
        "platform": sys.platform,
        "python": str(preferred_python()),
        "python_exists": preferred_python().exists(),
        "message": "已安装" if match else "尚未安装",
    }


def install_codex_mcp() -> dict:
    config = codex_config_path()
    config.parent.mkdir(parents=True, exist_ok=True)
    current = config.read_text(encoding="utf-8") if config.exists() else ""
    backup = None
    if config.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = config.with_name(f"config.toml.apison-backup-{stamp}")
        shutil.copy2(config, backup)

    block = codex_toml_block()
    section = re.compile(
        rf"(?ms)^\[mcp_servers\.{re.escape(SERVER_NAME)}\]\s*$.*?(?=^\[|\Z)"
    )
    if section.search(current):
        updated = section.sub(block + "\n", current, count=1)
    else:
        updated = current.rstrip() + ("\n\n" if current.strip() else "") + block
    config.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return {
        "success": True,
        "config": str(config),
        "backup": str(backup) if backup else "",
        "platform": sys.platform,
        "python": str(preferred_python()),
        "message": "Codex MCP 已设为必需服务器，请在 Codex 的 MCP 设置中重新启动服务器。",
    }


def test_mcp_server(timeout: int = 10) -> dict:
    """Start the stdio server and verify initialize + tools/list without spending API credit."""
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    payload = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in requests)
    try:
        proc = subprocess.run(
            [str(preferred_python()), str(MCP_SCRIPT)], input=payload,
            capture_output=True, text=True, timeout=timeout, cwd=ROOT,
        )
        responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
        tools = []
        for response in responses:
            if response.get("id") == 2:
                tools = response.get("result", {}).get("tools", [])
        names = [tool.get("name") for tool in tools]
        required = {"delegate_task", "delegate_tasks", "review_results"}
        ok = proc.returncode == 0 and required.issubset(names)
        return {
            "success": ok,
            "tools": names,
            "error": proc.stderr.strip() if not ok else "",
            "message": "MCP Server 正常，单任务、并发委派和评分工具均已注册" if ok else "MCP Server 工具注册不完整",
        }
    except Exception as exc:
        return {"success": False, "tools": [], "error": str(exc), "message": "MCP Server 测试失败"}
