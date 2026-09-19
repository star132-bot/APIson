"""
mcp_server.py — Agent Model Connect 的标准 MCP (Model Context Protocol) 服务端
基于标准输入输出 (stdio) 实现 JSON-RPC 2.0 协议。
支持同时兼容：
1. 换行符分隔的 JSON-RPC（NDJSON / JSON Lines）
2. 带 Content-Length 请求头的标准传输
使 Cursor, Antigravity, Claude Desktop, Roo Code, Windsurf 都能即插即用。
"""

import sys
import os
import json
import traceback
from pathlib import Path

# 添加 agent 目录到 sys.path
_AGENT_DIR = Path(__file__).parent
if str(_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENT_DIR))

from tools.delegate import delegate_task, _load_state

SERVER_INFO = {
    "name": "agent-model-connect",
    "version": "1.0.0"
}

TOOL_DEFINITION = {
    "name": "delegate_task",
    "description": (
        "将明确的子任务或耗费大量推理、重复性高的任务委派给外部高性能模型助手（例如 Grok-4.6, Gemini 等）。"
        "主 Agent 可以继续专注于架构设计与总体编排，将子任务的执行结果拿回后审查整合。"
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "需要委派的具体子任务内容，尽量清晰详尽"
            },
            "provider": {
                "type": "string",
                "description": "模型厂商标识，例如 'grok'。可选，留空则使用默认配置"
            },
            "model": {
                "type": "string",
                "description": "具体的模型名称，例如 'grok-4.6'。可选，留空使用该厂商默认模型"
            },
            "system_prompt": {
                "type": "string",
                "description": "可选。传递给助手模型的系统角色提示词"
            }
        },
        "required": ["task"]
    }
}

USE_CONTENT_LENGTH = False

def send_response(response_obj):
    body = json.dumps(response_obj, ensure_ascii=False)
    if USE_CONTENT_LENGTH:
        encoded = body.encode("utf-8")
        sys.stdout.write(f"Content-Length: {len(encoded)}\r\n\r\n{body}")
    else:
        sys.stdout.write(body + "\n")
    sys.stdout.flush()

def send_error(req_id, code, message):
    send_response({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": code,
            "message": message
        }
    })

def handle_request(req):
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": SERVER_INFO
            }
        })
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [TOOL_DEFINITION]
            }
        })
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "delegate_task":
            task = args.get("task", "")
            provider = args.get("provider")
            model = args.get("model")
            system_prompt = args.get("system_prompt")
            try:
                res = delegate_task(
                    task=task,
                    provider=provider,
                    model=model,
                    system_prompt=system_prompt
                )
                content_text = json.dumps(res, ensure_ascii=False, indent=2)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": content_text
                            }
                        ],
                        "isError": not res.get("success", False)
                    }
                })
            except Exception as e:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"调用异常: {str(e)}\n{traceback.format_exc()}"
                            }
                        ],
                        "isError": True
                    }
                })
        else:
            send_error(req_id, -32601, f"未找到工具: {tool_name}")
    elif method == "ping":
        send_response({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        })
    else:
        if req_id is not None:
            send_error(req_id, -32601, f"不支持的方法: {method}")

def main():
    global USE_CONTENT_LENGTH
    import io
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        raw_line = line.strip()
        if not raw_line:
            continue

        if raw_line.lower().startswith("content-length:"):
            USE_CONTENT_LENGTH = True
            try:
                content_length = int(raw_line.split(":")[1].strip())
            except ValueError:
                continue
            # 读取空行
            while True:
                empty = sys.stdin.readline()
                if not empty or empty.strip() == "":
                    break
            body_text = sys.stdin.read(content_length)
        else:
            body_text = raw_line

        try:
            req = json.loads(body_text)
            handle_request(req)
        except json.JSONDecodeError:
            pass
        except Exception:
            pass

if __name__ == "__main__":
    main()
