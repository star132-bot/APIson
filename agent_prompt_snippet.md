## 可用的委派工具 (delegate_task)

你有能力将子任务委派给专门的助手模型。当遇到以下情况时，考虑使用委派：
- 任务重复性高、推理量大（委派给 Grok）
- 需要长文本处理（委派给 Gemini）
- 并行处理多个独立子任务时

### 使用方式

调用 `delegate_task` 工具：
- `task`：清晰描述子任务内容（自然语言）
- `provider`（可选）：指定模型提供商（grok / gemini / claude）
- `model`（可选）：指定具体模型版本

### 已注册的助手模型

| 提供商 | 模型 | 适合任务 | 状态 |
|--------|------|----------|------|
| grok | grok-4 | 代码生成、推理、数学 | ✅ 启用 |

### 示例

将代码审查任务委派给 Grok：
```python
delegate_task(
    task="请审查以下 Python 代码，找出所有潜在 bug 和性能问题：\n[代码内容]",
    provider="grok"
)
```

### 返回结果

`delegate_task` 返回字典：
```json
{
  "success": true,
  "provider": "grok",
  "model": "grok-4",
  "result": "助手模型的回复内容",
  "error": "",
  "usage": {"prompt_tokens": 100, "completion_tokens": 200},
  "elapsed_ms": 1500
}
```

当 `success` 为 `false` 时，查看 `error` 字段了解失败原因。
