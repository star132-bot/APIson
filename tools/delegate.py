"""
tools/delegate.py
将子任务委派给外部模型（Grok、Gemini、Claude 等）的核心工具。
Agent 可以通过调用 delegate_task() 把任务交给指定的助手模型。
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# ─── 路径解析 ─────────────────────────────────────────────────────────────────

_TOOLS_DIR = Path(__file__).parent
_AGENT_DIR = _TOOLS_DIR.parent
_STATE_FILE = _AGENT_DIR / "models" / "state.json"
_PROVIDERS_DIR = _AGENT_DIR / "models" / "providers"


def _load_state() -> dict:
    """读取 models/state.json 注册表"""
    if not _STATE_FILE.exists():
        raise FileNotFoundError(
            f"模型注册表不存在: {_STATE_FILE}\n"
            "请先运行 python manager.py list 确认配置。"
        )
    with open(_STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _load_provider(provider_name: str) -> dict:
    """读取指定厂商的详细配置"""
    p = _PROVIDERS_DIR / f"{provider_name}.json"
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _get_api_key(provider_cfg: dict, override_key: Optional[str] = None) -> str:
    """
    获取 API Key，优先级：
    1. 直接传入的 override_key
    2. 环境变量（api_key_env 指定的变量名）
    3. 配置中的 api_key 字段（不推荐，仅兼容）
    """
    if override_key:
        return override_key

    env_var = provider_cfg.get("api_key_env", "")
    if env_var:
        key = os.environ.get(env_var, "")
        if key:
            return key

    # 兼容直接在配置里写 key 的情况
    key = provider_cfg.get("api_key", "")
    if key:
        return key

    raise EnvironmentError(
        f"未找到 API Key。\n"
        f"请设置环境变量: set {env_var}=你的API密钥\n"
        f"或运行: python manager.py set-key {provider_cfg.get('name', 'provider')}"
    )


def delegate_task(
    task: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: int = 60,
    stream: bool = False,
) -> dict:
    """
    将任务委派给外部模型。

    参数:
        task: 要委派的任务描述（自然语言）
        provider: 厂商名称，如 'grok'、'gemini'。None 时使用默认厂商
        model: 具体模型版本，如 'grok-4'。None 时使用厂商默认模型
        system_prompt: 可选的系统提示，定义助手角色
        api_key: 直接传入 API Key（优先级最高，不推荐硬编码）
        timeout: 请求超时秒数，默认 60s
        stream: 是否使用流式输出（当前返回完整结果）

    返回:
        {
            "success": bool,
            "provider": str,
            "model": str,
            "result": str,      # 成功时的回复内容
            "error": str,       # 失败时的错误信息
            "usage": dict,      # token 用量（如有）
            "elapsed_ms": int   # 耗时毫秒
        }
    """
    start = time.monotonic()
    result_base = {"success": False, "provider": provider or "?", "model": model or "?",
                   "result": "", "error": "", "usage": {}, "elapsed_ms": 0}

    try:
        # 1. 加载注册表
        state = _load_state()
        provider = provider or state.get("default_provider")
        if not provider:
            raise ValueError("未指定 provider 且注册表中没有 default_provider")

        provider_state = state.get("providers", {}).get(provider)
        if not provider_state:
            available = list(state.get("providers", {}).keys())
            raise ValueError(
                f"未找到厂商 '{provider}'。\n"
                f"已注册的厂商: {available}\n"
                f"运行 python manager.py add 可添加新厂商。"
            )

        if not provider_state.get("enabled", True):
            raise ValueError(f"厂商 '{provider}' 已被禁用。运行 python manager.py enable {provider} 启用。")

        # 2. 加载厂商详细配置
        provider_detail = _load_provider(provider)
        merged_cfg = {**provider_state, **provider_detail}

        # 3. 确定模型和基础 URL
        model = model or merged_cfg.get("model") or merged_cfg.get("default_model", "")
        base_url = merged_cfg.get("base_url", "").rstrip("/")
        protocol = merged_cfg.get("protocol", "openai_chat")

        result_base["provider"] = provider
        result_base["model"] = model

        # 4. 获取 API Key
        key = _get_api_key(merged_cfg, api_key)

        # 5. 构造请求
        content = _call_api(
            protocol=protocol,
            base_url=base_url,
            model=model,
            task=task,
            system_prompt=system_prompt,
            api_key=key,
            timeout=timeout,
            result_base=result_base,
        )

        elapsed = int((time.monotonic() - start) * 1000)
        result_base.update({"success": True, "result": content, "elapsed_ms": elapsed})
        return result_base

    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        result_base.update({"success": False, "error": str(e), "elapsed_ms": elapsed})
        return result_base


def _call_api(
    protocol: str,
    base_url: str,
    model: str,
    task: str,
    system_prompt: Optional[str],
    api_key: str,
    timeout: int,
    result_base: dict,
) -> str:
    """根据协议类型调用对应的 API"""
    try:
        import requests
    except ImportError:
        raise ImportError("缺少 requests 库。请运行: pip install requests")

    if protocol == "openai_chat":
        return _call_openai_chat(base_url, model, task, system_prompt, api_key, timeout, requests, result_base)
    elif protocol == "anthropic":
        return _call_anthropic(base_url, model, task, system_prompt, api_key, timeout, requests, result_base)
    elif protocol == "gemini":
        return _call_gemini(base_url, model, task, system_prompt, api_key, timeout, requests, result_base)
    else:
        raise ValueError(f"不支持的协议: {protocol}。支持: openai_chat, anthropic, gemini")


def _call_openai_chat(base_url, model, task, system_prompt, api_key, timeout, requests, result_base) -> str:
    """调用 OpenAI Chat Completions 兼容接口（Grok、Claude、本地模型等）"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": task})

    payload = {
        "model": model,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/chat/completions"
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)

    if resp.status_code != 200:
        raise RuntimeError(
            f"API 请求失败 [{resp.status_code}]: {resp.text[:500]}"
        )

    data = resp.json()
    result_base["usage"] = data.get("usage", {})
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content")
    if not content:
        content = msg.get("reasoning_content") or choice.get("text") or ""
    return content


def _call_gemini(base_url, model, task, system_prompt, api_key, timeout, requests, result_base) -> str:
    """调用 Gemini API"""
    parts = []
    if system_prompt:
        parts.append({"text": f"[System]: {system_prompt}\n\n[User]: {task}"})
    else:
        parts.append({"text": task})

    payload = {
        "contents": [{"parts": parts}]
    }

    url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    resp = requests.post(url, json=payload, timeout=timeout)

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API 请求失败 [{resp.status_code}]: {resp.text[:500]}")

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        return str(data)
    cand_parts = candidates[0].get("content", {}).get("parts", [])
    texts = [p.get("text", "") for p in cand_parts if isinstance(p, dict) and "text" in p]
    return "".join(texts) or str(data)


def _call_anthropic(base_url, model, task, system_prompt, api_key, timeout, requests, result_base) -> str:
    """调用 Anthropic Messages 兼容接口（适用于 Claude Code、火山引擎等）"""
    base_url = base_url.rstrip("/")
    if base_url.endswith("/messages"):
        url = base_url
    elif base_url.endswith("/v1"):
        url = f"{base_url}/messages"
    else:
        url = f"{base_url}/v1/messages"

    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": task}
        ]
    }
    if system_prompt:
        payload["system"] = system_prompt

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Anthropic API 请求失败 [{resp.status_code}]: {resp.text[:500]}"
        )

    data = resp.json()
    result_base["usage"] = data.get("usage", {})

    content_blocks = data.get("content", [])
    texts = [b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text"]
    if texts:
        return "".join(texts)

    if "text" in data:
        return data["text"]
    return str(data)


# ─── 命令行快速测试 ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="快速测试 delegate_task")
    parser.add_argument("task", nargs="?", default="你好，请用一句话介绍自己。")
    parser.add_argument("--provider", "-p", default=None)
    parser.add_argument("--model", "-m", default=None)
    args = parser.parse_args()

    print(f"📤 委派任务给: {args.provider or '默认模型'}")
    print(f"📝 任务内容: {args.task}\n")

    res = delegate_task(args.task, provider=args.provider, model=args.model)

    if res["success"]:
        print(f"[OK] | 模型: {res['provider']}/{res['model']} | 耗时: {res['elapsed_ms']}ms")
        print(f"\n{res['result']}")
        if res["usage"]:
            u = res["usage"]
            print(f"\n[Token] 输入 {u.get('prompt_tokens','-')} / 输出 {u.get('completion_tokens','-')}")
    else:
        print(f"[FAIL] {res['error']}")
        sys.exit(1)
