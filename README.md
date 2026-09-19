# Agent Model Connect (多模型调度与助手委派工具)

用于给你的各类 AI Agent（Antigravity、Cursor、Claude Code、Codex、Dify 等）接入外部助手模型池（例如 **Grok-4.6**、Gemini、Claude、开源本地模型等）。

主 Agent 保持原有能力和上下文不变，遇到耗时、重复性高或需要重度推理的任务时，可将子任务**安全委派**给外部助手执行。

---

## 🖥️ 可视化管理窗口 (新增)

你可以直接弹出一个直观的桌面管理窗口：

### 启动方式：
1. **双击启动**：在目录直接双击 [`启动模型管理器.bat`](file:///D:/newzm/assets/AntigravityPro/agent/启动模型管理器.bat)
2. **命令行启动**：
   ```powershell
   python manager.py gui
   # 或者
   python gui.py
   ```

### 窗口核心功能：
- **左侧模型库**：直观查看当前已配置模型、状态及默认项，支持一键切换与删除。
- **添加与编辑**：填入 Base URL 和 Key 后，点击 **“🔄 从服务端拉取可用模型”** 即可自动获取厂商全部可用模型。
- **一键测试**：点击 **“⚡ 开始连通性与生成测试”**，实时查看真实请求耗时与模型回复。
- **一键导出**：测试成功后，下方自动生成 3 种格式配置：
  - 🧩 **MCP 插件配置**（一键复制，粘贴到 Cursor / Antigravity 等设置）
  - 💬 **Agent 提示词片段**（一键复制，直接发到主 Agent 对话框）
  - 🐍 **Python 代码片段**（一键复制，供编写脚本或开发 Agent 调用）
- **网关一键启动**：窗口右上角一键启动本地 OpenAI 兼容网关服务。

---

## ⚡ 当前已接入与预设厂商

1. **Grok (xAI 中转)**:
   - 端点: `https://194834.xyz/v1`
   - 模型: `grok-4.6`
   - 协议: `openai_chat` (兼容 OpenAI)
   - 状态: ✅ **已通过真实测试**

2. **火山引擎 Ark - 兼容 Anthropic 接口协议 (新增)**:
   - 端点: `https://ark.cn-beijing.volces.com/api/plan`
   - 适用工具: **Claude Code**
   - 协议: `anthropic` (Messages 协议)
   - 模型: 火山方舟接入点 ID (如 `ep-xxxxxx`)

3. **火山引擎 Ark - 兼容 OpenAI 接口协议 (新增)**:
   - 端点: `https://ark.cn-beijing.volces.com/api/plan/v3`
   - 适用工具: **OpenCode、OpenClaw、TraeCode、Hermes Agent、Codex CLI、Cline、Cursor、Kilo Code、Roo Code 等**
   - 协议: `openai_chat` (v3 Chat Completions 协议)
   - 模型: 火山方舟接入点 ID (如 `ep-xxxxxx`)

---

## 🛠️ 核心架构与目录结构

```
D:\newzm\assets\AntigravityPro\agent\
├── models/
│   ├── state.json              # 模型注册表（当前状态、默认模型）
│   └── providers/
│       └── grok.json           # Grok 及其他厂商详细配置与模型列表
├── tools/
│   ├── __init__.py
│   └── delegate.py             # delegate_task 核心委派引擎
├── manager.py                  # CLI 统一管理器
├── mcp_server.py               # 标准 MCP (Model Context Protocol) 服务端
├── gateway.py                  # 本地 OpenAI 兼容网关 (HTTP 代理)
├── AGENTS.md                   # 供各类 Agent 阅读的委派调用指引
├── agent_prompt_snippet.md     # 可直接粘贴到 Agent 设定中的提示词片段
└── requirements.txt            # Python 依赖清单
```

---

## 🚀 让任意 Agent 调用 Grok-4.6 的 4 种方式

### 方式 1：标准 MCP 协议接入（推荐，适用于 Cursor / Antigravity / Windsurf 等）

运行命令获取配置：
```powershell
python manager.py mcp-config
```
输出如下配置，将其复制到 Agent 的 MCP 配置文件中：
```json
{
  "mcpServers": {
    "agent-model-connect": {
      "command": "python",
      "args": [
        "D:\\newzm\\assets\\AntigravityPro\\agent\\mcp_server.py"
      ]
    }
  }
}
```
**效果**：Agent 会自动加载 `delegate_task` 工具，在聊天中可以直接使用该工具将子任务发给 `grok-4.6`。

---

### 方式 2：本地 OpenAI 兼容网关（适用于 Codex / Dify / 仅支持自定义 API 的工具）

如果你使用的 Agent 软件只支持配置一个 OpenAI API 接口（如 Codex、NextChat、Chatbox）：

1. 在后台启动网关：
   ```powershell
   python manager.py serve --port 8765
   ```
2. 在客户端软件中设置：
   - **API Base URL**: `http://127.0.0.1:8765/v1`
   - **API Key**: 任意字符（如 `sk-local`）
   - **Model**: `grok-4.6`
3. 客户端发送的所有请求都会自动路由给本地调度引擎并转发到 Grok-4.6。

---

### 方式 3：Python 模块直接调用（适用于任何 Python 脚本 / 自定义 Agent）

```python
import sys
sys.path.insert(0, r"D:\newzm\assets\AntigravityPro\agent")
from tools.delegate import delegate_task

# 发起委派
result = delegate_task(
    task="请用 Python 编写一个处理并发任务的线程池封装",
    provider="grok",       # 可选，默认 grok
    model="grok-4.6"       # 可选，默认 grok-4.6
)

if result["success"]:
    print("模型输出:\n", result["result"])
else:
    print("调用失败:", result["error"])
```

---

### 方式 4：命令行即时测试

```powershell
# 快速委派一个问题
python tools/delegate.py "解释什么是狄利克雷分布" --model grok-4.6
```

---

## 📋 管理器 `manager.py` 常用命令

```powershell
python manager.py list                # 列出已注册的所有厂商及模型
python manager.py test grok           # 测试 Grok-4.6 连通性
python manager.py add                 # 交互式添加新厂商（如 Gemini、Claude、本地 Ollama）
python manager.py mcp-config          # 显示 MCP 客户端配置
python manager.py serve               # 启动本地代理网关服务
python manager.py enable <provider>   # 启用指定厂商
python manager.py disable <provider>  # 禁用指定厂商
python manager.py set-default <name>  # 修改默认厂商
python manager.py show-key <provider> # 检查 API Key 状态
```
