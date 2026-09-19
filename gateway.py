"""
gateway.py — Agent Model Connect 的本地 OpenAI 兼容网关 (HTTP Proxy)
让任何仅支持标准 OpenAI API 格式的 Agent、客户端或工具（如 Codex、Dify、Chatbox 等）
都可以将 Base URL 指向本服务，自动调用已配置的 Grok-4.6 等外部模型！

启动命令:
    python gateway.py --port 8765
"""

import sys
import os
import json
import time
from pathlib import Path
from flask import Flask, request, jsonify, Response

# 将 agent 目录加入 sys.path
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.delegate import delegate_task, _load_state, _load_provider

app = Flask(__name__)

@app.route("/v1/models", methods=["GET"])
def list_models():
    """返回当前已注册的所有可用模型列表"""
    try:
        state = _load_state()
        providers = state.get("providers", {})
        model_list = []
        for name, p_cfg in providers.items():
            if not p_cfg.get("enabled", True):
                continue
            model_id = p_cfg.get("model", name)
            model_list.append({
                "id": model_id,
                "object": "model",
                "created": int(time.time()),
                "owned_by": name,
                "permission": [],
                "root": model_id,
                "parent": None
            })
            # 同时把 provider 别名注册为一个模型名，方便直接用模型名呼叫
            if name != model_id:
                model_list.append({
                    "id": name,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": name,
                })
        return jsonify({"object": "list", "data": model_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """处理聊天补全请求"""
    data = request.get_json(force=True, silent=True) or {}
    messages = data.get("messages", [])
    model_req = data.get("model", "")
    stream = data.get("stream", False)

    # 提取系统提示词和最后一条用户提问
    sys_prompts = [m.get("content", "") for m in messages if m.get("role") == "system"]
    system_prompt = "\n".join(sys_prompts) if sys_prompts else None

    # 将用户上下文或最后一条消息转换为 task
    user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return jsonify({"error": {"message": "缺少 user 角色消息", "type": "invalid_request_error"}}), 400

    task = user_msgs[-1]

    # 根据请求的模型名称匹配 provider
    state = _load_state()
    providers = state.get("providers", {})

    target_provider = None
    target_model = None

    # 检查是否直接命中了 provider 名称
    if model_req in providers:
        target_provider = model_req
        target_model = providers[model_req].get("model")
    else:
        # 遍历查找匹配 model 的 provider
        for p_name, p_cfg in providers.items():
            if p_cfg.get("model") == model_req:
                target_provider = p_name
                target_model = model_req
                break
        if not target_provider:
            # 默认使用 default_provider
            target_provider = state.get("default_provider")
            target_model = model_req if model_req else providers.get(target_provider, {}).get("model")

    res = delegate_task(
        task=task,
        provider=target_provider,
        model=target_model,
        system_prompt=system_prompt
    )

    if not res.get("success"):
        return jsonify({
            "error": {
                "message": res.get("error", "未知错误"),
                "type": "api_error"
            }
        }), 502

    reply_content = res.get("result", "")
    response_payload = {
        "id": f"chatcmpl-{int(time.time()*1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": res.get("model", model_req),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": reply_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": res.get("usage", {
            "prompt_tokens": len(task),
            "completion_tokens": len(reply_content),
            "total_tokens": len(task) + len(reply_content)
        })
    }

    return jsonify(response_payload)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent Model Connect 本地网关")
    parser.add_argument("--port", type=int, default=8765, help="监听端口 (默认: 8765)")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址 (默认: 127.0.0.1)")
    args = parser.parse_args()

    print(f"🚀 本地 OpenAI 网关已就绪: http://{args.host}:{args.port}/v1")
    print(f"👉 任何 Agent 均可将 API Base URL 设为: http://{args.host}:{args.port}/v1")
    app.run(host=args.host, port=args.port, debug=False)
