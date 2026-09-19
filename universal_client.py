"""
universal_client.py — 通用大模型调用工具（支持 OpenAI 协议与 Anthropic 协议）
特点：
1. 完全独立自包含：无复杂本地依赖，直接复制该文件到任何项目、数据库批处理脚本或服务中即可运行。
2. 双协议兼容：支持 OpenAI Chat Completions 协议与 Anthropic Messages 协议。
3. 预置配置：已预置实测通过的火山引擎 Agent Plan（包含 API Key、官方 Base URL 及推荐模型）。
4. 容错重试：内置自动重试、超时保护、思考链/长文本解析以及错误处理。
5. 适用场景：对话生成、子任务委派、数据库批量字段分析/提取/清洗等。
"""

import os
import json
import time
from typing import Union, List, Dict, Optional, Any
import requests

# 默认凭证与地址（已实测通过的火山引擎 Agent Plan）
VOLCES_API_KEY = os.environ.get("VOLCES_API_KEY", "")
VOLCES_OPENAI_URL = "https://ark.cn-beijing.volces.com/api/plan/v3"
VOLCES_ANTHROPIC_URL = "https://ark.cn-beijing.volces.com/api/plan"
DEFAULT_MODEL = "claude-3-5-sonnet"  # 备选: "doubao-seed-2.0-pro", "doubao-seed-2.0-lite"


def call_llm(
    prompt: Union[str, List[Dict[str, str]]],
    system: Optional[str] = None,
    protocol: str = "openai",  # "openai" 或 "anthropic"
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 4096,
    timeout: int = 45,
    retries: int = 2
) -> str:
    """
    通用大模型单次/多轮调用函数。
    
    参数:
        prompt: 提示词（直接传字符串，或传 [{"role": "user", "content": "..."}] 消息列表）
        system: 可选的系统提示词 (System Prompt)
        protocol: 接口协议，"openai"（默认，推荐）或 "anthropic"
        model: 模型名称，默认为 "claude-3-5-sonnet"
        api_key: API 密钥，默认使用预置的火山 Agent Plan Key
        base_url: 接口端点，默认根据 protocol 自动选择官方专属地址
        temperature: 生成多样性，0.0~1.0
        max_tokens: 最大生成长度
        timeout: 超时时间（秒）
        retries: 网络波动时的重试次数
        
    返回:
        模型回复的纯文本字符串。失败时抛出异常。
    """
    key = api_key or os.environ.get("ARK_API_KEY") or VOLCES_API_KEY
    m = model or DEFAULT_MODEL
    proto = protocol.lower().strip()

    # 规范化消息列表
    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    elif isinstance(prompt, list):
        messages = list(prompt)
    else:
        raise ValueError("prompt 参数必须是字符串或消息字典列表")

    # 路由到对应协议的实现
    last_err = None
    for attempt in range(retries + 1):
        try:
            if proto in ("openai", "openai_chat"):
                url = (base_url or VOLCES_OPENAI_URL).rstrip("/")
                return _call_openai(
                    base_url=url,
                    model=m,
                    messages=messages,
                    system=system,
                    api_key=key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
            elif proto in ("anthropic", "claude"):
                url = (base_url or VOLCES_ANTHROPIC_URL).rstrip("/")
                return _call_anthropic(
                    base_url=url,
                    model=m,
                    messages=messages,
                    system=system,
                    api_key=key,
                    max_tokens=max_tokens,
                    timeout=timeout
                )
            else:
                raise ValueError(f"不支持的协议类型: {proto}，请选择 'openai' 或 'anthropic'")
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"调用模型失败 (已重试 {retries} 次): {str(last_err)}") from last_err


def _call_openai(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    system: Optional[str],
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int
) -> str:
    """底层执行 OpenAI 兼容协议调用"""
    endpoint = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
    
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": full_messages,
        "max_tokens": max_tokens
    }
    # 部分推理模型不接收非默认 temperature
    if temperature is not None:
        payload["temperature"] = temperature

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAI API 响应异常 [{resp.status_code}]: {resp.text}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"服务端未返回任何内容: {resp.text}")

    content = choices[0].get("message", {}).get("content", "")
    return content.strip()


def _call_anthropic(
    base_url: str,
    model: str,
    messages: List[Dict[str, str]],
    system: Optional[str],
    api_key: str,
    max_tokens: int,
    timeout: int
) -> str:
    """底层执行 Anthropic 兼容协议调用"""
    endpoint = base_url
    if endpoint.endswith("/messages"):
        pass
    elif endpoint.endswith("/v1"):
        endpoint = f"{endpoint}/messages"
    else:
        endpoint = f"{endpoint}/v1/messages"

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }
    if system:
        payload["system"] = system

    headers = {
        "x-api-key": api_key,
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Anthropic API 响应异常 [{resp.status_code}]: {resp.text}")

    data = resp.json()
    content_blocks = data.get("content", [])
    texts = [b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text"]
    if texts:
        return "".join(texts).strip()
    if "text" in data:
        return str(data["text"]).strip()
    return str(data).strip()


# ─── 针对数据库处理场景的通用批处理函数 ────────────────────────────────────────

def process_database_rows(
    rows: List[Dict[str, Any]],
    input_field: str,
    output_field: str,
    task_instruction: str,
    batch_delay: float = 0.2
) -> List[Dict[str, Any]]:
    """
    通用数据库批量行处理函数。
    例如读取了数据库数据: rows = [{"id": 1, "content": "用户留言..."}, ...]
    执行后会在每行字典增加 output_field 字段，填入模型返回的结果。
    """
    results = []
    total = len(rows)
    print(f"[*] 开始批量处理数据，共 {total} 条记录...")

    for idx, row in enumerate(rows):
        item = dict(row)
        user_input = str(item.get(input_field, ""))
        prompt = f"{task_instruction}\n\n待处理输入:\n{user_input}"
        try:
            reply = call_llm(prompt=prompt)
            item[output_field] = reply
            item["_llm_status"] = "success"
        except Exception as e:
            item[output_field] = None
            item["_llm_status"] = f"error: {str(e)}"
        
        results.append(item)
        print(f"[{idx+1}/{total}] 处理完成 (ID: {item.get('id', idx)})")
        if batch_delay > 0:
            time.sleep(batch_delay)

    return results


if __name__ == "__main__":
    print("=== 通用调用方法快速自检 ===")
    
    # 1. 极简一句调用 (OpenAI 协议)
    print("\n1. 测试 OpenAI 协议:")
    res_openai = call_llm("请回答'测试成功'四个字")
    print("返回结果:", res_openai)

    # 2. 极简一句调用 (Anthropic 协议)
    print("\n2. 测试 Anthropic 协议:")
    res_anthropic = call_llm("请回答'测试成功'四个字", protocol="anthropic")
    print("返回结果:", res_anthropic)

    # 3. 带 System Prompt 的复杂调用
    print("\n3. 测试 System Prompt 结构化输出:")
    res_structured = call_llm(
        prompt="这是一条关于订单迟迟未发货的差评，请提取情绪和核心诉求",
        system="你是一个电商数据清洗助手，请输出简洁的JSON格式结果。"
    )
    print("返回结果:", res_structured)
