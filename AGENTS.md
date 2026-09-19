# AGENTS.md — 助手模型与任务委派说明

如果你是一个 AI Agent（如 Antigravity, Cursor, Claude Code, Windsurf 等），请阅读本说明：

## 1. 你的助手模型池

当前系统已接入外部高性能 AI 助手模型池，你可以将耗时、重复性高或需要专门推理的子任务委派给外部助手执行：

| 助手标识 | 默认模型 | 特长 / 适合任务 | 状态 |
|---------|---------|----------------|------|
| `grok`  | `grok-4.6` | 批量代码生成、复杂数学/逻辑推理、重复性文本处理 | ✅ 已就绪 |

---

## 2. 如何调用委派？

### 途径 A：作为 Python 模块直接调用 (推荐)

在你的代码或临时脚本中：
```python
import sys
sys.path.insert(0, r"D:\newzm\assets\AntigravityPro\agent")
from tools.delegate import delegate_task

result = delegate_task(
    task="这是要委托给 Grok-4.6 的具体子任务描述...",
    provider="grok",        # 可选，默认即为 grok
    model="grok-4.6",       # 可选，默认即为 grok-4.6
    system_prompt="你是一个代码分析专家..." # 可选
)

if result["success"]:
    answer = result["result"]
    print("Grok-4.6 回复:", answer)
else:
    print("失败原因:", result["error"])
```

### 途径 B：通过命令行运行

```powershell
python D:\newzm\assets\AntigravityPro\agent\tools\delegate.py "提取以下数据中的所有邮箱..." --model grok-4.6
```

### 途径 C：通过 MCP 工具协议调用

如果你的环境加载了 `agent-model-connect` MCP 服务，你可以直接像调用系统原生工具一样调用 `delegate_task(task="...")`。

### 途径 D：通过本地 HTTP OpenAI 代理

在终端执行 `python manager.py serve` 后，任何 Agent 都可以请求：
- **Base URL**: `http://127.0.0.1:8765/v1`
- **Model**: `grok-4.6`
- **API Key**: 任意非空字符串

---

## 3. 委派最佳实践

1. **大任务拆分**：主 Agent 负责规划步骤，把细碎且重复的单元（如逐个文件编写、批量测试用例生成）逐项发给 `grok-4.6`。
2. **上下文精确**：委派给 `task` 的内容应当包含足够的上下文，让 Grok 能够独立完成该单项任务。
3. **结果校验**：委派返回后，主 Agent 负责校验其返回结果并汇总呈现给用户。
