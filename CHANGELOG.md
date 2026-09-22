# 更新日志

本文件记录 APIson 每个版本对用户可见的变化。

## 1.1.0 - 2026-09-22

### 新增

- 新增 MK 开发者品牌图标，并提供 PNG、Windows ICO、macOS ICNS 三种格式。
- 新增一眼可识别的打开入口：Windows `打开 APIson.bat`、macOS `APIson.app`、Linux `APIson.desktop`。
- Windows 可一键创建带 MK 图标的桌面快捷方式。
- 新增跨平台 `bootstrap.py`，首次运行自动创建虚拟环境并安装依赖。
- 新增 Windows 的 `start_gui.bat` 和 `start_gateway.bat` 启动入口。
- Codex MCP 安装和配置导出会按 Windows、macOS、Linux 自动选择正确的 Python 路径。
- 新增 `delegate_tasks`，支持最多 16 个子任务、8 个工作线程并发委派。
- 新增 `review_results`，支持独立评审 Agent 并发评分、列出问题和修改建议。
- 支持一键将 APIson MCP Server 安装到 Codex 的本机全局配置。
- 支持检测 Codex MCP 安装状态并测试 `delegate_task` 是否成功注册。
- 增加委派调用日志，记录模型、耗时、Token 用量和错误，不保存任务及回复正文。
- 更新检查窗口显示完整版本变更内容。
- 修复提交后 `VERSION` 中的旧 SHA 导致更新界面误报的问题。

### 调整

- Codex 安装配置将 APIson 设为必需 MCP，并把工具超时提高到 300 秒，防止新任务偶发遗漏工具。
- 明确区分“安装 MCP 工具”和“复制 Agent 调用规则”。
- Agent 提示词改为调用已安装的 `delegate_task`，不再要求 Agent 临时生成一套委派脚本。
