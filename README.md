# Agent Model Connect (APIson) — 多模型调度与助手委派平台

用于给你的各类 AI Agent（Antigravity、Cursor、Claude Code、Codex CLI、Dify、Cline、Trae 等）统一接入与调度外部大模型池（火山引擎方舟、DeepSeek、阿里百炼、智谱、Kimi、硅基流动、Claude 3.7、Gemini 2.5、OpenAI、Grok、OpenRouter、本地 Ollama 等）。

主 Agent 保持原有工作流不变，遇到复杂代码、长文本、重度推理或特定专长任务时，可将子任务**安全委派**给外部助手模型或子代理（Subagents）执行。

---

## 🖥️ 可视化管理窗口 (GUI)

支持 macOS、Windows 及 Linux 跨平台运行：

### 启动方式：
1. **macOS / Linux 一键启动**：
   ```bash
   chmod +x start_gui.sh
   ./start_gui.sh
   ```
2. **Windows 一键启动**：
   双击根目录下的 `启动模型管理器.bat`
3. **命令行通用启动**：
   ```bash
   python manager.py gui
   # 或
   python gui.py
   ```

### 核心亮点：
- ⚡ **15+ 主流厂商官方预设**：一键载入火山方舟（OpenAI / Anthropic 双协议）、DeepSeek、阿里百炼、智谱、月之暗面 Kimi、硅基流动、OpenAI、Anthropic、Google Gemini、Grok、OpenRouter、Groq、本地 Ollama / LM Studio 等。
- 🧠 **7 大模型专长分类与 Subagent 自动派工**：系统自动推导模型特征（深度推理、敏捷编程、极速响应、全景长文、智能检索、多模态、通用协作），自动生成多子代理角色规范与注入提示词。
- 🔍 **模型即时搜索与能力标签过滤**：左侧卡片列表支持毫秒级模糊搜索与专长标签过滤。
- 💰 **API 账户余额与额度查询**：支持 DeepSeek、硅基流动、Kimi、OpenRouter 及各类 One API / New API 中转站的余额与使用量实时查询。
- ⚡ **并发测试与批量检测**：支持单模型快速测试、一键批量并发连通性测试与批量查余额。
- 🧩 **一键多格式导出**：
  - 💬 **Agent 注入提示词**（含子代理分工规范与自动落地配置）
  - 🐍 **独立 Python 调用文件**（开箱即用的完整脚本）
  - 🧩 **标准 MCP 插件配置**（适用于 Cursor / Antigravity / Windsurf 等）

---

## 🛠️ 项目目录结构

```
APIson/
├── models/
│   ├── state.json              # 本地模型注册表（已被 gitignore，保护 Key 安全）
│   └── providers/              # 厂商配置模板目录
├── tools/
│   ├── balance.py              # API 余额与额度查询引擎
│   └── delegate.py             # delegate_task 核心委派与推理大模型协议解析引擎
├── manager.py                  # CLI 统一管理工具
├── gui.py                      # CustomTkinter 桌面现代化深色面板
├── mcp_server.py               # 标准 MCP (Model Context Protocol) 服务端
├── gateway.py                  # 本地 OpenAI 兼容网关 (HTTP 代理服务)
├── start_gui.sh                # macOS/Linux GUI 启动脚本
├── start_gateway.sh            # 本地网关启动脚本
└── requirements.txt            # Python 依赖清单
```

---

## 🚀 4 种调用与集成方式

### 方式 1：标准 MCP 协议接入（Cursor / Antigravity / Windsurf 等）

运行命令获取当前环境的 MCP 配置：
```bash
python manager.py mcp-config
```
输出对应配置，直接粘贴到 Agent 客户端的 MCP 配置文件中即可。

---

### 方式 2：本地 OpenAI 兼容网关（Codex / Dify / NextChat / 仅支持自定义 API 的工具）

1. 启动本地网关：
   ```bash
   ./start_gateway.sh
   # 或
   python manager.py serve --port 8765
   ```
2. 在客户端软件中设置：
   - **API Base URL**: `http://127.0.0.1:8765/v1`
   - **API Key**: 任意字符（如 `sk-local`）
   - **Model**: `grok-4.6` 或配置中的任意模型名称

---

### 方式 3：Python 脚本直接调用

```python
from tools.delegate import delegate_task

result = delegate_task(
    task="请用 Python 编写一个高性能并发请求池",
    provider="grok",       # 可选，默认当前激活模型
    model="grok-4.6"
)

if result["success"]:
    print("模型输出:\n", result["result"])
else:
    print("调用失败:", result["error"])
```

---

### 方式 4：命令行即时管理与测试

```bash
python manager.py list                # 列出已配置的模型助手
python manager.py balance             # 一键查询所有模型账户余额与额度
python manager.py test grok           # 测试指定模型连通性
python manager.py mcp-config          # 显示 MCP 客户端配置
python manager.py serve               # 启动本地代理网关服务
python manager.py enable <provider>   # 启用指定厂商
python manager.py disable <provider>  # 禁用指定厂商
python manager.py set-default <name>  # 修改默认模型
```
