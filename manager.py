"""
manager.py — Agent Model Connect 命令行管理器
用于管理 Agent 可以调用的外部模型厂商。

使用方法:
    python manager.py list
    python manager.py add
    python manager.py test <provider>
    python manager.py enable <provider>
    python manager.py disable <provider>
    python manager.py set-default <provider>
    python manager.py remove <provider>
    python manager.py set-key <provider>
    python manager.py show-key <provider>
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ─── ANSI 颜色 ────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def c(text, color): return f"{color}{text}{RESET}"

# ─── 路径 ─────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent
_STATE = _ROOT / "models" / "state.json"
_PROVIDERS_DIR = _ROOT / "models" / "providers"

def _load() -> dict:
    if not _STATE.exists():
        return {"version": "1.0", "default_provider": None, "providers": {}}
    with open(_STATE, encoding="utf-8") as f:
        return json.load(f)

def _save(state: dict):
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(c(f"✓ 已保存到 {_STATE}", GREEN))

def _save_provider(name: str, data: dict):
    _PROVIDERS_DIR.mkdir(parents=True, exist_ok=True)
    p = _PROVIDERS_DIR / f"{name}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_provider(name: str) -> dict:
    p = _PROVIDERS_DIR / f"{name}.json"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)

# ─── 命令：list ───────────────────────────────────────────────────────────────
def cmd_list(args):
    state = _load()
    providers = state.get("providers", {})
    default = state.get("default_provider", "")

    if not providers:
        print(c("暂无注册的模型厂商。运行 python manager.py add 添加。", YELLOW))
        return

    print(f"\n{c('已注册的模型厂商', BOLD)}\n")
    print(f"{'名称':<12} {'模型':<20} {'协议':<18} {'状态':<8} {'默认'}")
    print("─" * 70)

    for name, cfg in providers.items():
        status = c("[启用]", GREEN) if cfg.get("enabled", True) else c("[禁用]", RED)
        is_default = c("[默认]", CYAN) if name == default else ""
        model = cfg.get("model", "-")
        protocol = cfg.get("protocol", "openai_chat")
        print(f"{name:<12} {model:<20} {protocol:<18} {status:<16} {is_default}")

    print(f"\n{c('共 ' + str(len(providers)) + ' 个厂商', DIM)}")

# ─── 命令：add ────────────────────────────────────────────────────────────────
def cmd_add(args):
    state = _load()
    print(f"\n{c('添加新模型厂商', BOLD)}\n")

    name = input("厂商标识符（小写，如 grok / gemini / claude）: ").strip()
    if not name:
        print(c("错误：名称不能为空", RED)); return
    if name in state.get("providers", {}):
        print(c(f"错误：'{name}' 已存在，使用 remove 删除后重新添加", RED)); return

    display_name = input(f"显示名称（如 Grok xAI）: ").strip() or name
    base_url = input("API Base URL（如 https://api.x.ai/v1）: ").strip()
    model = input("默认模型 ID（如 grok-4）: ").strip()

    print("协议类型:")
    print("  1. openai_chat（OpenAI Chat Completions，兼容 Grok/Claude/本地模型）")
    print("  2. gemini（Google Gemini 原生 API）")
    proto_choice = input("选择 [1/2，默认 1]: ").strip() or "1"
    protocol = "gemini" if proto_choice == "2" else "openai_chat"

    env_var = input(f"API Key 环境变量名（如 XAI_API_KEY，回车跳过）: ").strip()
    if not env_var:
        env_var = f"{name.upper()}_API_KEY"
        print(f"  → 默认使用: {env_var}")

    provider_cfg = {
        "name": display_name,
        "base_url": base_url,
        "model": model,
        "protocol": protocol,
        "enabled": True,
        "api_key_env": env_var,
        "description": input("简短描述（可选）: ").strip(),
    }

    state.setdefault("providers", {})[name] = provider_cfg
    if not state.get("default_provider"):
        state["default_provider"] = name
        print(c(f"→ 已自动设为默认厂商", CYAN))

    _save(state)
    _save_provider(name, provider_cfg)
    print(c(f"✓ 已添加厂商 '{name}'", GREEN))
    print(f"\n{c('设置 API Key:', YELLOW)}")
    print(f"  Windows: set {env_var}=你的密钥")
    print(f"  测试: python manager.py test {name}")

# ─── 命令：test ───────────────────────────────────────────────────────────────
def cmd_test(args):
    name = args.provider
    state = _load()
    providers = state.get("providers", {})

    if name not in providers:
        print(c(f"错误：未找到厂商 '{name}'", RED))
        print(f"已注册: {list(providers.keys())}"); return

    cfg = {**providers[name], **_load_provider(name)}
    display = cfg.get("name", name)
    print(f"\n{c('测试连接: ' + display, BOLD)}")
    print(f"  端点: {cfg.get('base_url')}")
    print(f"  模型: {cfg.get('model')}")

    # 检查 API Key
    env_var = cfg.get("api_key_env", "")
    api_key = os.environ.get(env_var, "") if env_var else ""
    if not api_key:
        api_key = cfg.get("api_key", "")
    if not api_key:
        print(c(f"\n❌ 未找到 API Key", RED))
        print(f"  请先设置: set {env_var}=你的密钥"); return

    print(f"  API Key: {api_key[:8]}{'*' * max(0, len(api_key)-8)}")
    print(f"\n→ 发送测试请求...")

    try:
        import requests
    except ImportError:
        print(c("❌ 缺少 requests 库。请运行: pip install requests", RED)); return

    try:
        from tools.delegate import delegate_task
        result = delegate_task(
            task="请回复'连接成功'这四个字，不要其他内容。",
            provider=name,
            timeout=30,
        )
        if result["success"]:
            elapsed = result['elapsed_ms']
            print(c(f"\n[OK] 连接成功！耗时 {elapsed}ms", GREEN))
            print(f"   模型回复: {result['result'][:100]}")
        else:
            print(c(f"\n[FAIL] 连接失败: {result['error']}", RED))
    except Exception as e:
        print(c(f"\n[ERROR] {e}", RED))

# ─── 命令：enable / disable ────────────────────────────────────────────────────
def cmd_enable(args):
    _toggle(args.provider, True)

def cmd_disable(args):
    _toggle(args.provider, False)

def _toggle(name: str, enabled: bool):
    state = _load()
    if name not in state.get("providers", {}):
        print(c(f"错误：未找到 '{name}'", RED)); return
    state["providers"][name]["enabled"] = enabled
    _save(state)
    status = c("启用", GREEN) if enabled else c("禁用", RED)
    print(c(f"✓ '{name}' 已{status}", GREEN if enabled else RED))

# ─── 命令：set-default ────────────────────────────────────────────────────────
def cmd_set_default(args):
    state = _load()
    if args.provider not in state.get("providers", {}):
        print(c(f"错误：未找到 '{args.provider}'", RED)); return
    state["default_provider"] = args.provider
    _save(state)
    print(c(f"✓ 已将 '{args.provider}' 设为默认厂商", CYAN))

# ─── 命令：remove ─────────────────────────────────────────────────────────────
def cmd_remove(args):
    state = _load()
    name = args.provider
    if name not in state.get("providers", {}):
        print(c(f"错误：未找到 '{name}'", RED)); return
    confirm = input(c(f"确认删除 '{name}'？[y/N]: ", YELLOW))
    if confirm.lower() != "y":
        print("已取消"); return
    del state["providers"][name]
    if state.get("default_provider") == name:
        remaining = list(state["providers"].keys())
        state["default_provider"] = remaining[0] if remaining else None
    _save(state)
    p = _PROVIDERS_DIR / f"{name}.json"
    if p.exists():
        p.unlink()
    print(c(f"✓ 已删除 '{name}'", GREEN))

# ─── 命令：set-key ────────────────────────────────────────────────────────────
def cmd_set_key(args):
    state = _load()
    name = args.provider
    if name not in state.get("providers", {}):
        print(c(f"错误：未找到 '{name}'", RED)); return
    env_var = state["providers"][name].get("api_key_env", f"{name.upper()}_API_KEY")
    print(f"\n{c(f'设置 {name} 的 API Key', BOLD)}")
    print(f"环境变量名: {c(env_var, CYAN)}")
    print(f"\n请在你的终端中运行以下命令（API Key 不会保存到文件）：\n")
    cmd_cmd = f"set {env_var}=你的密钥"
    ps_cmd = f'$env:{env_var}="你的密钥"'
    test_cmd = f"python manager.py test {name}"
    print(f"  {c(cmd_cmd, YELLOW)}   <- Windows CMD")
    print(f"  {c(ps_cmd, YELLOW)} <- PowerShell")
    print(f"\n设置后使用 {c(test_cmd, CYAN)} 验证连接")

# ─── 命令：show-key ───────────────────────────────────────────────────────────
def cmd_show_key(args):
    state = _load()
    name = args.provider
    if name not in state.get("providers", {}):
        print(c(f"错误：未找到 '{name}'", RED)); return
    cfg = state["providers"][name]
    env_var = cfg.get("api_key_env", "")
    key = os.environ.get(env_var, "") if env_var else ""
    print(f"\n{c(f'{name} API Key 状态', BOLD)}")
    print(f"  环境变量: {env_var}")
    if key:
        print(f"  当前值:   {c(key[:8] + '*' * max(0, len(key)-8), GREEN)}")
        print(f"  状态:     {c('[已配置]', GREEN)}")
    else:
        print(f"  状态:     {c('[未配置]', RED)}")
        print(f"  提示:     set {env_var}=你的密钥")

# ─── 命令：balance ────────────────────────────────────────────────────────────
def cmd_balance(args):
    """查询模型余额/额度"""
    state = _load()
    providers = state.get("providers", {})
    target = getattr(args, "provider", None)

    if target:
        if target not in providers:
            print(c(f"错误：未找到厂商 '{target}'", RED))
            return
        targets = [target]
    else:
        targets = list(providers.keys())

    if not targets:
        print(c("当前未注册任何模型厂商", YELLOW))
        return

    from tools.balance import query_balance

    print(f"\n{c('API 账户余额与额度查询', BOLD)}")
    print("─" * 55)

    for p_id in targets:
        cfg = {**providers[p_id], **_load_provider(p_id)}
        name = cfg.get("name", p_id)
        url = cfg.get("base_url", "")
        key = cfg.get("api_key") or (os.environ.get(cfg.get("api_key_env", "")) if cfg.get("api_key_env") else "")

        print(f"\n[•] 厂商: {c(name, CYAN)} ({p_id})")
        print(f"    Base URL: {url}")

        res = query_balance(url, key, p_id, name)
        if res.get("success"):
            bal = res.get("balance", "")
            details = res.get("details", "")
            print(c(f"    💰 账户余额: {bal}", GREEN))
            if details:
                print(f"    📊 额度明细: {details}")
        elif not res.get("supported"):
            print(c(f"    ℹ️  平台提示: {res.get('message')}", YELLOW))
        else:
            print(c(f"    ❌ 查询失败: {res.get('message')}", RED))

    print("\n" + "─" * 55)

# ─── 命令：mcp-config ─────────────────────────────────────────────────────────
def cmd_mcp_config(args):
    mcp_path = str(_ROOT / "mcp_server.py")
    python_exe = sys.executable
    print(f"\n{c('=== MCP (Model Context Protocol) 接入配置 ===', BOLD)}\n")
    cfg = {
        "mcpServers": {
            "agent-model-connect": {
                "command": python_exe,
                "args": [mcp_path]
            }
        }
    }
    json_str = json.dumps(cfg, indent=2, ensure_ascii=False)
    print(c("将以下配置复制到支持 MCP 的 Agent（Cursor / Antigravity / Claude Desktop 等）配置文件中：", YELLOW))
    print(f"\n{c(json_str, CYAN)}\n")
    print("配置完成后，你的 Agent 会自动获得工具: delegate_task")

# ─── 命令：serve ──────────────────────────────────────────────────────────────
def cmd_serve(args):
    from gateway import app
    port = getattr(args, "port", 8765)
    host = getattr(args, "host", "127.0.0.1")
    print(f"\n{c('🚀 启动本地 OpenAI 兼容网关服务...', BOLD)}")
    print(f"  地址: {c(f'http://{host}:{port}/v1', CYAN)}")
    print(f"  可用端点:")
    print(f"    - GET  http://{host}:{port}/v1/models")
    print(f"    - POST http://{host}:{port}/v1/chat/completions")
    print(f"\n{c('提示: 任何仅支持 OpenAI API 的 Agent/软件填入此 Base URL 即可直接调用 Grok-4.6！', YELLOW)}")
    app.run(host=host, port=port, debug=False)

# ─── 命令：gui ───────────────────────────────────────────────────────────────
def cmd_gui(args):
    print(c("正在启动图形化工具窗口...", CYAN))
    from gui import launch
    launch()

# ─── 入口 ─────────────────────────────────────────────────────────────────────
def main():
    # Windows 控制台强制 UTF-8 输出
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        os.system("")  # 启用 ANSI 颜色

    parser = argparse.ArgumentParser(
        prog="manager.py",
        description=f"{c('Agent Model Connect', BOLD)} — 管理 Agent 可调用的外部模型",
    )
    sub = parser.add_subparsers(dest="cmd", metavar="命令")

    sub.add_parser("list", help="列出所有已注册的模型厂商")
    sub.add_parser("add",  help="交互式添加新厂商")

    p_test = sub.add_parser("test", help="测试厂商连通性")
    p_test.add_argument("provider", help="厂商标识符")

    p_en = sub.add_parser("enable", help="启用厂商")
    p_en.add_argument("provider")

    p_dis = sub.add_parser("disable", help="禁用厂商")
    p_dis.add_argument("provider")

    p_def = sub.add_parser("set-default", help="设置默认厂商")
    p_def.add_argument("provider")

    p_rm = sub.add_parser("remove", help="删除厂商")
    p_rm.add_argument("provider")

    p_sk = sub.add_parser("set-key", help="显示如何设置 API Key")
    p_sk.add_argument("provider")

    p_sh = sub.add_parser("show-key", help="查看 API Key 配置状态")
    p_sh.add_argument("provider")

    p_bal = sub.add_parser("balance", help="查询 API 余额与额度")
    p_bal.add_argument("provider", nargs="?", default=None, help="厂商标识（留空则查询所有）")

    sub.add_parser("mcp-config", help="导出适用于 Agent 的 MCP 客户端配置")
    sub.add_parser("gui", help="弹出桌面可视化模型管理与导出窗口")

    p_srv = sub.add_parser("serve", help="启动本地 OpenAI 兼容网关服务")
    p_srv.add_argument("--port", type=int, default=8765, help="端口 (默认: 8765)")
    p_srv.add_argument("--host", default="127.0.0.1", help="主机 (默认: 127.0.0.1)")

    args = parser.parse_args()

    dispatch = {
        "list": cmd_list,
        "add": cmd_add,
        "test": cmd_test,
        "balance": cmd_balance,
        "enable": cmd_enable,
        "disable": cmd_disable,
        "set-default": cmd_set_default,
        "remove": cmd_remove,
        "set-key": cmd_set_key,
        "show-key": cmd_show_key,
        "mcp-config": cmd_mcp_config,
        "serve": cmd_serve,
        "gui": cmd_gui,
    }

    if not args.cmd:
        parser.print_help()
        print(f"\n{c('快速开始:', BOLD)}")
        print(f"  python manager.py gui               # 弹出图形化操作窗口")
        print(f"  python manager.py list              # 查看已注册模型")
        print(f"  python manager.py balance           # 查询模型余额与额度")
        print(f"  python manager.py test grok         # 测试 Grok 连通性")
        print(f"  python manager.py mcp-config        # 导出 MCP 配置文件")
        print(f"  python manager.py serve             # 启动本地代理网关")
        print(f"  python manager.py add               # 添加新厂商")
        return

    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
