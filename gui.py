"""
gui.py — Agent Model Connect 现代化桌面图形化管理面板 (UI 美化增强版)
基于 CustomTkinter 打造的高颜值 Win11/macOS 暗色微光质感桌面管理控制台。

特色体验：
1. 【微光质感视觉体系】：采用深空暗蓝 (#0B0F19) 底色、分层晶透卡片与柔光边界 (#1F2E4A)，极具极客与科技感。
2. 【多模型组合勾选注入】：左侧列表支持多模型复选（Checkboxes），提供“全选 / 清空”并带动态计数。
3. 【智能专长标签体系】：自动识别模型特性，配备专属色系的专长徽章（深度推理 / 敏捷编码 / 全景长文 / 通用协作）。
4. 【自执行 Agent 注入提示词】：发给任意 Agent，自动落地工作区配置并分配 Subagents 子代理角色。
5. 【多格式导出选项卡】：一键切换并复制 Agent 注入提示词、免依赖独立 Python 文件及标准 MCP 插件配置。
"""

import sys
import os
import json
import time
import threading
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

# 路径定位
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.delegate import delegate_task, _load_state
from tools.updater import check_update, do_update
from tools.codex_mcp import get_codex_mcp_status, install_codex_mcp, test_mcp_server

_STATE_FILE = _ROOT / "models" / "state.json"
_PROVIDERS_DIR = _ROOT / "models" / "providers"

# 全局主题基调
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# 官方主流模型快速预设 (涵盖国内大厂、国际顶尖、开源托管与本地部署)
PRESETS = {
    # ── 国内主流平台 ──
    "【预设】火山方舟 Agent Plan - 兼容 OpenAI 协议 (deepseek-v4-pro / doubao-seed)": {
        "provider": "volces-openai",
        "name": "火山方舟 (OpenAI协议)",
        "url": "https://ark.cn-beijing.volces.com/api/plan/v3",
        "protocol": "openai_chat",
        "model": "deepseek-v4-pro",
        "thinking": "high",
        "key": "",
        "models": ["deepseek-v4-pro", "deepseek-v4-flash", "doubao-seed-2.0-pro", "doubao-seed-2.0-lite", "claude-3-5-sonnet"],
        "hint": "适配 Cursor / Trae / Roo / OpenClaw / Hermes 等。支持 DeepSeek 4.0 旗舰推理"
    },
    "【预设】火山方舟 Agent Plan - 兼容 Anthropic 协议 (Claude Code)": {
        "provider": "volces-claude",
        "name": "火山方舟 (Anthropic协议)",
        "url": "https://ark.cn-beijing.volces.com/api/plan",
        "protocol": "anthropic",
        "model": "deepseek-v4-pro",
        "thinking": "high",
        "key": "",
        "models": ["deepseek-v4-pro", "deepseek-v4-flash", "claude-3-5-sonnet", "doubao-seed-2.0-pro", "doubao-seed-2.0-lite"],
        "hint": "适配 Claude Code。专属 Base URL: https://ark.cn-beijing.volces.com/api/plan"
    },
    "【预设】DeepSeek 官方平台 - deepseek-reasoner (R1) / chat (V3)": {
        "provider": "deepseek",
        "name": "DeepSeek (深度求索)",
        "url": "https://api.deepseek.com",
        "protocol": "openai_chat",
        "model": "deepseek-reasoner",
        "thinking": "high",
        "key": "",
        "models": ["deepseek-reasoner", "deepseek-chat"],
        "hint": "DeepSeek 官方推理大模型 (R1) 与通用对话模型 (V3)"
    },
    "【预设】阿里百炼通义千问 (DashScope) - qwen-max / coder-turbo": {
        "provider": "qwen-dashscope",
        "name": "阿里通义千问 (百炼)",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "protocol": "openai_chat",
        "model": "qwen-max",
        "key": "",
        "models": ["qwen-max", "qwen-plus", "qwen-coder-turbo", "qwen2.5-72b-instruct", "qwen2.5-coder-32b-instruct"],
        "hint": "阿里百炼 OpenAI 兼容端点，代码与通用综合能力极佳"
    },
    "【预设】智谱 AI (清言 GLM) - glm-4-plus / glm-4-long": {
        "provider": "zhipu-glm",
        "name": "智谱 GLM (BigModel)",
        "url": "https://open.bigmodel.cn/api/paas/v4",
        "protocol": "openai_chat",
        "model": "glm-4-plus",
        "key": "",
        "models": ["glm-4-plus", "glm-4-long", "glm-4-flash", "glm-4-air"],
        "hint": "智谱开放平台，支持百万长上下文 (glm-4-long) 与超快 flash"
    },
    "【预设】月之暗面 (Kimi / Moonshot) - moonshot-v1-128k": {
        "provider": "moonshot-kimi",
        "name": "月之暗面 (Kimi)",
        "url": "https://api.moonshot.cn/v1",
        "protocol": "openai_chat",
        "model": "moonshot-v1-128k",
        "key": "",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"],
        "hint": "Kimi 官方长上下文对话模型"
    },
    "【预设】硅基流动 (SiliconFlow) - 全开源加速托管": {
        "provider": "siliconflow",
        "name": "硅基流动 (SiliconFlow)",
        "url": "https://api.siliconflow.cn/v1",
        "protocol": "openai_chat",
        "model": "deepseek-ai/DeepSeek-R1",
        "thinking": "high",
        "key": "",
        "models": ["deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-Coder-32B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"],
        "hint": "高并发免运维的开源大模型云端托管服务"
    },
    # ── 国际前沿与聚合通道 ──
    "【预设】OpenAI 官方平台 - gpt-4o / o3-mini / o1": {
        "provider": "openai",
        "name": "OpenAI 官方",
        "url": "https://api.openai.com/v1",
        "protocol": "openai_chat",
        "model": "gpt-4o",
        "thinking": "medium",
        "key": "",
        "models": ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1", "o1-mini"],
        "hint": "OpenAI 官方最新旗舰多模态及前沿推理大模型"
    },
    "【预设】Anthropic Claude 官方 - claude-3-7-sonnet / 3-5-sonnet": {
        "provider": "anthropic",
        "name": "Anthropic Claude",
        "url": "https://api.anthropic.com",
        "protocol": "anthropic",
        "model": "claude-3-7-sonnet-20250219",
        "thinking": "high",
        "key": "",
        "models": ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
        "hint": "Anthropic 官方前沿编程与长篇推理大模型"
    },
    "【预设】Google Gemini (官方兼容端点) - gemini-2.5-pro / flash": {
        "provider": "gemini",
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "protocol": "openai_chat",
        "model": "gemini-2.5-pro",
        "key": "",
        "models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
        "hint": "支持超长上下文与全景分析的 Google Gemini 官方端点"
    },
    "【预设】Grok xAI (中转/官方) - grok-4.6": {
        "provider": "grok",
        "name": "Grok (xAI)",
        "url": "https://194834.xyz/v1",
        "protocol": "openai_chat",
        "model": "grok-4.6",
        "key": "",
        "models": ["grok-4.6", "grok-beta"],
        "hint": "已实测通过的 Grok 4.6 旗舰模型"
    },
    "【预设】OpenRouter (全球聚合网关) - 多模型一体化": {
        "provider": "openrouter",
        "name": "OpenRouter (聚合网关)",
        "url": "https://openrouter.ai/api/v1",
        "protocol": "openai_chat",
        "model": "anthropic/claude-3.7-sonnet",
        "key": "",
        "models": ["anthropic/claude-3.7-sonnet", "openai/gpt-4o", "deepseek/deepseek-r1", "google/gemini-2.5-pro"],
        "hint": "全球聚合网关，一个 API Key 调用全网所有顶尖大模型"
    },
    "【预设】Groq (全球极速推理) - 超低延迟 LPU": {
        "provider": "groq",
        "name": "Groq (极速推理)",
        "url": "https://api.groq.com/openai/v1",
        "protocol": "openai_chat",
        "model": "llama-3.3-70b-versatile",
        "key": "",
        "models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768"],
        "hint": "Groq LPU 超高吞吐极速推理端点"
    },
    # ── 本地私有部署 ──
    "【预设】本地 Ollama (本地开源模型)": {
        "provider": "ollama",
        "name": "本地 Ollama",
        "url": "http://localhost:11434/v1",
        "protocol": "openai_chat",
        "model": "qwen2.5-coder:7b",
        "key": "ollama",
        "models": ["qwen2.5-coder:7b", "deepseek-r1:7b", "llama3.1:8b"],
        "hint": "本地运行的开源大模型服务 (自动拉取本机构建的模型)"
    },
    "【预设】本地 LM Studio / vLLM (本地 OpenAI 服务)": {
        "provider": "local-openai",
        "name": "本地 LM Studio / vLLM",
        "url": "http://localhost:1234/v1",
        "protocol": "openai_chat",
        "model": "local-model",
        "key": "not-needed",
        "models": ["local-model"],
        "hint": "本地 LM Studio (1234) 或 vLLM (8000) 运行的 OpenAI 兼容端点"
    }
}


def load_state_dict() -> dict:
    if not _STATE_FILE.exists():
        return {"version": "1.0", "default_provider": None, "providers": {}}
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(_STATE_FILE, encoding="utf-8-sig") as f:
            return json.load(f)


def save_state_dict(data: dict):
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def detect_model_role(p_id: str, name: str, model: str) -> dict:
    """根据模型名称智能推断专长角色与子代理配置（覆盖 7 大专长领域）"""
    combined = f"{p_id} {name} {model}".lower()

    # 1. 深度推理 (Reasoning)
    if any(k in combined for k in ["deepseek-v4-pro", "deepseek-r1", "reasoner", "reason", "r1", "o1", "o3", "qwq", "distill", "thinking"]):
        return {
            "role_id": f"subagent-reasoner-{p_id}",
            "role_title": f"深度推理专家 ({name})",
            "tag": "🧠 深度推理",
            "tag_color": ("#FEE2E2", "#381014"),
            "tag_border": "#7F1D1D",
            "tag_text_color": ("#991B1B", "#F87171"),
            "specialty": "负责复杂算法设计、数理逻辑推导、核心架构方案决策及疑难 Bug 深度根因排查"
        }
    # 2. 敏捷编程 (Coding)
    elif any(k in combined for k in ["coder", "codex", "codestral", "qwen-coder", "claude-3-7", "sonnet", "dev", "code"]):
        return {
            "role_id": f"subagent-coder-{p_id}",
            "role_title": f"敏捷开发专家 ({name})",
            "tag": "💻 敏捷编程",
            "tag_color": ("#FEF3C7", "#361B04"),
            "tag_border": "#92400E",
            "tag_text_color": ("#92400E", "#FBBF24"),
            "specialty": "负责高吞吐全栈编码、组件抽象重构、测试用例编写与多文件代码协同"
        }
    # 3. 极速响应 (Fast / Lightweight)
    elif any(k in combined for k in ["flash", "haiku", "mini", "4o-mini", "turbo", "lite", "speed", "groq", "small", "7b", "8b"]):
        return {
            "role_id": f"subagent-fast-{p_id}",
            "role_title": f"极速响应专家 ({name})",
            "tag": "⚡ 极速响应",
            "tag_color": ("#ECFDF5", "#06321F"),
            "tag_border": "#047857",
            "tag_text_color": ("#047857", "#34D399"),
            "specialty": "负责高频即时任务处理、轻量化自动化脚本、意图初筛与超低延迟快速路由"
        }
    # 4. 全景长文 (Long Context / Research)
    elif any(k in combined for k in ["long", "128k", "200k", "1m", "moonshot", "kimi", "glm-long", "gemini-pro", "gemini-2.5"]):
        return {
            "role_id": f"subagent-researcher-{p_id}",
            "role_title": f"全景长文专家 ({name})",
            "tag": "📚 全景长文",
            "tag_color": ("#E0E7FF", "#181838"),
            "tag_border": "#3730A3",
            "tag_text_color": ("#3730A3", "#818CF8"),
            "specialty": "负责超长项目上下文理解、全库依赖检索、多模态技术白皮书与技术文档生成"
        }
    # 5. 智能联网检索 (Search & Grounding)
    elif any(k in combined for k in ["search", "perplexity", "sonar", "browse", "online", "harness"]):
        return {
            "role_id": f"subagent-searcher-{p_id}",
            "role_title": f"联网检索专家 ({name})",
            "tag": "🔍 智能检索",
            "tag_color": ("#CFFAFE", "#082F49"),
            "tag_border": "#0284C7",
            "tag_text_color": ("#0284C7", "#38BDF8"),
            "specialty": "负责全网最新技术信息查证、前沿开源组件调研、官方 API 最新规范考证"
        }
    # 6. 多模态视觉 (Multimodal Vision)
    elif any(k in combined for k in ["vision", "vl", "omni", "4o", "multimodal", "image"]):
        return {
            "role_id": f"subagent-vision-{p_id}",
            "role_title": f"多模态视觉专家 ({name})",
            "tag": "🎨 多模态视觉",
            "tag_color": ("#FCE7F3", "#3B0728"),
            "tag_border": "#9D174D",
            "tag_text_color": ("#9D174D", "#F472B6"),
            "specialty": "负责 UI/UX 原型图与架构流程图精确识别、前端界面还原度比对及图像理解"
        }
    # 7. 通用协同助手 (General Assistant)
    else:
        return {
            "role_id": f"subagent-assistant-{p_id}",
            "role_title": f"通用协同助手 ({name})",
            "tag": "🤖 通用协作",
            "tag_color": ("#F3E8FF", "#2E0E46"),
            "tag_border": "#6B21A8",
            "tag_text_color": ("#6B21A8", "#C084FC"),
            "specialty": "负责日常子任务委派分流、格式整理校验、代码微调及跨模型协同调度"
        }


class ModelConnectGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Agent Model Connect — 模型助手调度与多模型注入面板")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        cx = max(0, (sw - 1220) // 2)
        cy = max(0, (sh - 870) // 2)
        self.geometry(f"1220x870+{cx}+{cy}")
        self.minsize(1080, 750)
        self.configure(fg_color=("#F1F5F9", "#0B0F19"))


        # 加载应用图标
        ico_file = _ROOT / "icon.ico"
        if ico_file.exists():
            try:
                self.iconbitmap(str(ico_file))
            except Exception:
                pass

        # 核心数据状态
        self.current_state = load_state_dict()
        self.selected_provider_id = None
        self.selected_for_injection = set(self.current_state.get("providers", {}).keys())
        self.check_vars = {}
        self.testing_models = set()
        self.model_test_results = {}
        self.checking_balances = set()
        self.model_balance_results = {}
        self.card_badges = {}
        self.card_containers = {}
        self.active_role_filter = "全部"
        self.role_filter_btns = {}
        self._update_info = None  # 缓存更新检查结果

        # 构建界面布局
        self._build_layout()
        self._refresh_model_list()

        # 自动提升窗口并获取焦点
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass




    def _build_layout(self):
        # ─── 顶部导航栏 (微光质感) ─────────────────────────────────────────────
        header_frame = ctk.CTkFrame(
            self,
            corner_radius=0,
            height=68,
            fg_color=("#FFFFFF", "#111827"),
            border_width=1,
            border_color=("#E2E8F0", "#1F2937")
        )
        header_frame.pack(side=ctk.TOP, fill=ctk.X)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side=ctk.LEFT, padx=22, pady=10)

        # 标题行带精致在线徽章
        title_top = ctk.CTkFrame(title_box, fg_color="transparent")
        title_top.pack(anchor="w")

        lbl_logo = ctk.CTkLabel(
            title_top,
            text="🤖 AGENT MODEL CONNECT",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        )
        lbl_logo.pack(side=ctk.LEFT)

        online_badge = ctk.CTkLabel(
            title_top,
            text="● ENGINE ACTIVE",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=("#DCFCE7", "#052E16"),
            text_color=("#16A34A", "#4ADE80"),
            corner_radius=10,
            padx=8,
            pady=1
        )
        online_badge.pack(side=ctk.LEFT, padx=(10, 0))

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="外部模型接入池 · 多模型组合勾选 · 一键生成 Agent 注入提示词与 Subagents 子代理分工",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748B", "#94A3B8")
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # 顶部右侧控制区
        top_right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_right_box.pack(side=ctk.RIGHT, padx=22)

        # 主题切换胶囊按钮
        self.theme_switch = ctk.CTkSegmentedButton(
            top_right_box,
            values=["深色", "浅色", "系统"],
            command=self._on_theme_changed,
            font=ctk.CTkFont(size=11),
            selected_color="#6366F1",
            selected_hover_color="#4F46E5"
        )
        self.theme_switch.set("深色")
        self.theme_switch.pack(side=ctk.LEFT, padx=(0, 14))

        btn_gateway = ctk.CTkButton(
            top_right_box,
            text="🚀 本地 OpenAI 网关",
            width=140,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            corner_radius=8,
            command=self._start_gateway_threaded
        )
        btn_gateway.pack(side=ctk.LEFT)

        self.lbl_version = ctk.CTkLabel(
            top_right_box,
            text="v···",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=("#475569", "#94A3B8"),
        )
        self.lbl_version.pack(side=ctk.LEFT, padx=(12, 0))

        self.btn_update = ctk.CTkButton(
            top_right_box,
            text="🔄 检查更新",
            width=92,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#334155", "#E2E8F0"),
            corner_radius=6,
            command=lambda: self._check_for_updates_threaded(manual=True),
        )
        self.btn_update.pack(side=ctk.LEFT, padx=(6, 0))

        self.lbl_update_status = ctk.CTkLabel(
            top_right_box,
            text="● 已是最新版本",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=("#16A34A", "#4ADE80"),
            fg_color=("#DCFCE7", "#052E16"),
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.lbl_update_status.pack(side=ctk.LEFT, padx=(6, 0))

        # ─── 主体分栏 ──────────────────────────────────────────────────────────
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill=ctk.BOTH, expand=True, padx=18, pady=14)

        # ─── 左侧：模型助手列表栏 (暗调卡片) ───────────────────────────────────
        left_card = ctk.CTkFrame(
            main_container,
            width=360,
            corner_radius=14,
            fg_color=("#FFFFFF", "#131C2E"),
            border_width=1,
            border_color=("#E2E8F0", "#1E2A44")
        )
        left_card.pack(side=ctk.LEFT, fill=ctk.Y, padx=(0, 14))
        left_card.pack_propagate(False)

        # 左侧顶部标题栏
        left_header = ctk.CTkFrame(left_card, fg_color="transparent")
        left_header.pack(fill=ctk.X, padx=14, pady=(14, 4))

        ctk.CTkLabel(
            left_header,
            text="已接入模型助手",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#0F172A", "#F8FAFC")
        ).pack(side=ctk.LEFT)

        btn_add = ctk.CTkButton(
            left_header,
            text="➕ 新建",
            width=62,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB",
            corner_radius=6,
            command=self._clear_form
        )
        btn_add.pack(side=ctk.RIGHT)

        # 多选快捷控制条 (全选 / 清空 / 计数)
        select_bar = ctk.CTkFrame(left_card, fg_color="transparent")
        select_bar.pack(fill=ctk.X, padx=14, pady=(0, 8))

        self.lbl_select_count = ctk.CTkLabel(
            select_bar,
            text="待注入: 0 个",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#4F46E5", "#818CF8")
        )
        self.lbl_select_count.pack(side=ctk.LEFT)

        btn_unselect_all = ctk.CTkButton(
            select_bar,
            text="清空",
            width=36,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#475569", "#94A3B8"),
            corner_radius=4,
            command=self._unselect_all_injection
        )
        btn_unselect_all.pack(side=ctk.RIGHT, padx=(2, 0))

        btn_select_all = ctk.CTkButton(
            select_bar,
            text="全选",
            width=36,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#475569", "#94A3B8"),
            corner_radius=4,
            command=self._select_all_injection
        )
        btn_select_all.pack(side=ctk.RIGHT, padx=(2, 0))

        self.btn_batch_balance = ctk.CTkButton(
            select_bar,
            text="💰 查余额",
            width=62,
            height=22,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            corner_radius=4,
            command=self._batch_check_balances
        )
        self.btn_batch_balance.pack(side=ctk.RIGHT, padx=(2, 0))

        self.btn_batch_test = ctk.CTkButton(
            select_bar,
            text="⚡ 一键测试",
            width=68,
            height=22,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            text_color="#FFFFFF",
            corner_radius=4,
            command=self._batch_test_models
        )
        self.btn_batch_test.pack(side=ctk.RIGHT)

        # 搜索与角色快捷筛选栏（为多模型管理提供敏捷检索）
        filter_box = ctk.CTkFrame(left_card, fg_color="transparent")
        filter_box.pack(fill=ctk.X, padx=12, pady=(0, 6))

        self.ent_search = ctk.CTkEntry(
            filter_box,
            placeholder_text="🔍 快速检索模型名称或标识...",
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=6,
            fg_color=("#F1F5F9", "#0B111E"),
            border_color=("#E2E8F0", "#1C2945")
        )
        self.ent_search.pack(fill=ctk.X, pady=(0, 4))
        self.ent_search.bind("<KeyRelease>", lambda e: self._filter_model_list())

        # 角色专长过滤标签栏
        tag_filter_bar = ctk.CTkFrame(filter_box, fg_color="transparent")
        tag_filter_bar.pack(fill=ctk.X)

        self.role_filter_btns = {}
        for r_name in ["全部", "🧠推理", "💻编程", "⚡极速", "📚长文"]:
            btn = ctk.CTkButton(
                tag_filter_bar,
                text=r_name,
                width=42,
                height=20,
                font=ctk.CTkFont(size=10),
                fg_color=("#6366F1" if r_name == "全部" else ("#F1F5F9", "#1E293B")),
                hover_color=("#4F46E5", "#334155"),
                text_color=("#FFFFFF" if r_name == "全部" else ("#475569", "#94A3B8")),
                corner_radius=4,
                command=lambda rn=r_name: self._set_role_filter(rn)
            )
            btn.pack(side=ctk.LEFT, padx=(0, 3))
            self.role_filter_btns[r_name] = btn

        # 左侧可滚动卡片列表容器
        self.provider_scroll = ctk.CTkScrollableFrame(
            left_card,
            corner_radius=10,
            fg_color=("#F8FAFC", "#0C1322"),
            border_width=1,
            border_color=("#F1F5F9", "#172238")
        )
        self.provider_scroll.pack(fill=ctk.BOTH, expand=True, padx=10, pady=4)

        # 左侧底部操作栏（高亮核心按钮）
        left_footer = ctk.CTkFrame(left_card, fg_color="transparent")
        left_footer.pack(fill=ctk.X, padx=12, pady=(10, 14))

        self.btn_copy_prompt_left = ctk.CTkButton(
            left_footer,
            text="✨ 一键复制 Agent 注入提示词",
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            corner_radius=8,
            command=self._copy_injection_prompt
        )
        self.btn_copy_prompt_left.pack(fill=ctk.X, pady=(0, 6))

        self.btn_delete = ctk.CTkButton(
            left_footer,
            text="🗑️ 移除当前编辑模型",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color="#EF4444",
            text_color=("#64748B", "#94A3B8"),
            corner_radius=6,
            command=self._delete_selected
        )
        self.btn_delete.pack(fill=ctk.X)

        # ─── 右侧：配置卡片与导出 Tab ──────────────────────────────────────────
        right_container = ctk.CTkFrame(main_container, fg_color="transparent")
        right_container.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)

        # 卡片 1：模型配置与连通测试
        config_card = ctk.CTkFrame(
            right_container,
            corner_radius=14,
            fg_color=("#FFFFFF", "#131C2E"),
            border_width=1,
            border_color=("#E2E8F0", "#1E2A44")
        )
        config_card.pack(fill=ctk.X, pady=(0, 12))

        # 快速预设模板选择条
        preset_bar = ctk.CTkFrame(config_card, fg_color="transparent")
        preset_bar.pack(fill=ctk.X, padx=18, pady=(14, 8))

        ctk.CTkLabel(
            preset_bar,
            text="⚡ 快速载入预设:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#4F46E5", "#818CF8")
        ).pack(side=ctk.LEFT, padx=(0, 8))

        self.cmb_preset = ctk.CTkOptionMenu(
            preset_bar,
            values=list(PRESETS.keys()),
            command=self._on_preset_selected,
            font=ctk.CTkFont(size=12),
            height=32,
            fg_color=("#F1F5F9", "#1A253C"),
            button_color=("#E2E8F0", "#243352"),
            button_hover_color=("#CBD5E1", "#33476E"),
            text_color=("#0F172A", "#F8FAFC"),
            corner_radius=8,
            dynamic_resizing=False
        )
        self.cmb_preset.set("点此选择官方主流预设（DeepSeek / Grok / Gemini / 火山引擎）...")
        self.cmb_preset.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        # 表单字段网格 (对齐优化)
        form_grid = ctk.CTkFrame(config_card, fg_color="transparent")
        form_grid.pack(fill=ctk.X, padx=18, pady=4)
        form_grid.columnconfigure(1, weight=1)
        form_grid.columnconfigure(3, weight=1)

        # 行 1: 厂商标识 & 显示名称
        ctk.CTkLabel(form_grid, text="厂商标识:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=0, column=0, sticky="w", pady=6)
        self.ent_provider = ctk.CTkEntry(
            form_grid,
            placeholder_text="如 deepseek 或 grok",
            height=34,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0C1322"),
            border_color=("#E2E8F0", "#22314E")
        )
        self.ent_provider.grid(row=0, column=1, sticky="ew", padx=(8, 16), pady=6)

        ctk.CTkLabel(form_grid, text="显示名称:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=0, column=2, sticky="w", pady=6)
        self.ent_name = ctk.CTkEntry(
            form_grid,
            placeholder_text="如 DeepSeek (深度求索)",
            height=34,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0C1322"),
            border_color=("#E2E8F0", "#22314E")
        )
        self.ent_name.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=6)

        # 行 2: Base URL
        ctk.CTkLabel(form_grid, text="API Base URL:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=1, column=0, sticky="w", pady=6)
        self.ent_url = ctk.CTkEntry(
            form_grid,
            placeholder_text="https://api.deepseek.com",
            height=34,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0C1322"),
            border_color=("#E2E8F0", "#22314E")
        )
        self.ent_url.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=6)
        self.ent_url.bind("<KeyRelease>", self._on_url_modified)
        self.ent_url.bind("<FocusOut>", self._on_url_modified)

        # 行 3: 接口协议 & 模型名称
        ctk.CTkLabel(form_grid, text="接口协议:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=2, column=0, sticky="w", pady=6)
        self.cmb_protocol = ctk.CTkOptionMenu(
            form_grid,
            values=["openai_chat", "anthropic", "gemini"],
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color=("#F8FAFC", "#0C1322"),
            button_color=("#E2E8F0", "#22314E"),
            button_hover_color=("#CBD5E1", "#33476E"),
            text_color=("#0F172A", "#F8FAFC"),
            corner_radius=8
        )
        self.cmb_protocol.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=6)

        ctk.CTkLabel(form_grid, text="模型名称:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=2, column=2, sticky="w", pady=6)
        model_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        model_box.grid(row=2, column=3, sticky="ew", padx=(8, 0), pady=6)

        self.cmb_model = ctk.CTkComboBox(
            model_box,
            values=["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-reasoner", "deepseek-chat"],
            height=34,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0C1322"),
            border_color=("#E2E8F0", "#22314E"),
            command=self._on_combobox_selected
        )
        self.cmb_model.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
        self.cmb_model._entry.bind("<KeyRelease>", self._on_model_modified)
        self.cmb_model._entry.bind("<FocusOut>", self._on_model_modified)

        self.btn_fetch = ctk.CTkButton(
            model_box,
            text="🔄 拉取",
            width=64,
            height=34,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#334155", "#E2E8F0"),
            corner_radius=8,
            command=self._fetch_remote_models_threaded
        )
        self.btn_fetch.pack(side=ctk.RIGHT, padx=(6, 0))

        # 行 4: API Key
        ctk.CTkLabel(form_grid, text="API Key (密钥):", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=3, column=0, sticky="w", pady=6)
        key_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        key_box.grid(row=3, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=6)

        self.ent_key = ctk.CTkEntry(
            key_box,
            show="*",
            placeholder_text="填入对应平台的 API Key",
            height=34,
            corner_radius=8,
            fg_color=("#F8FAFC", "#0C1322"),
            border_color=("#E2E8F0", "#22314E")
        )
        self.ent_key.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        self.btn_toggle_key = ctk.CTkButton(
            key_box,
            text="👁️ 显示",
            width=65,
            height=34,
            fg_color=("#F1F5F9", "#1E293B"),
            hover_color=("#E2E8F0", "#334155"),
            text_color=("#334155", "#E2E8F0"),
            corner_radius=8,
            command=self._toggle_key_visibility
        )
        self.btn_toggle_key.pack(side=ctk.RIGHT, padx=(6, 0))

        # 行 5: 思考强度
        ctk.CTkLabel(form_grid, text="思考强度:", font=ctk.CTkFont(size=12), text_color=("#475569", "#94A3B8")).grid(row=4, column=0, sticky="w", pady=6)
        thinking_box = ctk.CTkFrame(form_grid, fg_color="transparent")
        thinking_box.grid(row=4, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=6)

        self.cmb_thinking = ctk.CTkOptionMenu(
            thinking_box,
            values=["auto (默认)", "low", "medium", "high"],
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#F8FAFC", "#0C1322"),
            button_color=("#E2E8F0", "#22314E"),
            button_hover_color=("#CBD5E1", "#33476E"),
            text_color=("#7C3AED", "#C4B5FD"),
            corner_radius=8,
            command=self._on_thinking_changed,
        )
        self.cmb_thinking.set("auto (默认)")
        self.cmb_thinking.pack(side=ctk.LEFT)

        self.lbl_thinking_desc = ctk.CTkLabel(
            thinking_box,
            text="  ⚙️ [系统默认] 遵循模型默认行为 (自动适配 o1/o3/R1/Claude 3.7 thinking 等)",
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        )
        self.lbl_thinking_desc.pack(side=ctk.LEFT, padx=(8, 0))

        # 操作控制与连通测试状态栏
        action_bar = ctk.CTkFrame(config_card, fg_color="transparent")
        action_bar.pack(fill=ctk.X, padx=18, pady=(12, 16))

        self.btn_save = ctk.CTkButton(
            action_bar,
            text="💾 保存配置",
            width=95,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#475569", "#334155"),
            hover_color=("#334155", "#475569"),
            corner_radius=8,
            command=self._save_form
        )
        self.btn_save.pack(side=ctk.LEFT, padx=(0, 8))

        self.btn_test = ctk.CTkButton(
            action_bar,
            text="⚡ 连通性测试",
            width=120,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=8,
            command=self._test_model_threaded
        )
        self.btn_test.pack(side=ctk.LEFT, padx=(0, 8))

        self.btn_balance = ctk.CTkButton(
            action_bar,
            text="💰 查询余额",
            width=105,
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            corner_radius=8,
            command=self._check_balance_threaded
        )
        self.btn_balance.pack(side=ctk.LEFT, padx=(0, 10))

        self.lbl_test_status = ctk.CTkLabel(
            action_bar,
            text="● 就绪，可测试模型连通性或查询账户余额",
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#94A3B8"),
            anchor="w"
        )
        self.lbl_test_status.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

        # 卡片 2：现代化导出 Tab 卡片
        export_card = ctk.CTkFrame(
            right_container,
            corner_radius=14,
            fg_color=("#FFFFFF", "#131C2E"),
            border_width=1,
            border_color=("#E2E8F0", "#1E2A44")
        )
        export_card.pack(fill=ctk.BOTH, expand=True)

        self.tabview = ctk.CTkTabview(
            export_card,
            corner_radius=10,
            segmented_button_fg_color=("#F1F5F9", "#0C1322"),
            segmented_button_selected_color="#6366F1",
            segmented_button_selected_hover_color="#4F46E5"
        )
        self.tabview.pack(fill=ctk.BOTH, expand=True, padx=14, pady=(6, 12))

        # Tab 1: Agent 注入提示词
        tab_prompt = self.tabview.add("🤖 Agent 注入提示词 (含子代理分工)")
        prompt_top_bar = ctk.CTkFrame(tab_prompt, fg_color="transparent")
        prompt_top_bar.pack(fill=ctk.X, pady=(0, 6))

        ctk.CTkLabel(
            prompt_top_bar,
            text="💡 提示：发给主 Agent 后，主 Agent 自动落盘配置并开启【动态分析与主动委派助手】机制",
            font=ctk.CTkFont(size=11),
            text_color=("#6366F1", "#A5B4FC")
        ).pack(side=ctk.LEFT)

        btn_copy_p = ctk.CTkButton(
            prompt_top_bar,
            text="📋 一键复制提示词",
            width=135,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#6366F1",
            hover_color="#4F46E5",
            corner_radius=6,
            command=self._copy_injection_prompt
        )
        btn_copy_p.pack(side=ctk.RIGHT)

        self.txt_prompt = ctk.CTkTextbox(
            tab_prompt,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("#F8FAFC", "#0A0E17"),
            text_color=("#0F172A", "#E2E8F0"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#19243C"),
            wrap="word"
        )
        self.txt_prompt.pack(fill=ctk.BOTH, expand=True)

        # Tab 2: 独立 Python 代码
        tab_code = self.tabview.add("🐍 独立 Python 调用文件")
        code_top_bar = ctk.CTkFrame(tab_code, fg_color="transparent")
        code_top_bar.pack(fill=ctk.X, pady=(0, 6))

        ctk.CTkLabel(
            code_top_bar,
            text="💡 提示：完全自包含、免环境依赖的单文件调用脚本（含数据库批处理示例）",
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#94A3B8")
        ).pack(side=ctk.LEFT)

        btn_copy_c = ctk.CTkButton(
            code_top_bar,
            text="📋 一键复制代码",
            width=125,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            corner_radius=6,
            command=lambda: self._copy_text(self.txt_code.get("1.0", "end-1c"), "代码已复制")
        )
        btn_copy_c.pack(side=ctk.RIGHT)

        self.txt_code = ctk.CTkTextbox(
            tab_code,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("#F8FAFC", "#0A0E17"),
            text_color=("#0F172A", "#E2E8F0"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#19243C"),
            wrap="none"
        )
        self.txt_code.pack(fill=ctk.BOTH, expand=True)

        # Tab 3: MCP 插件配置
        tab_mcp = self.tabview.add("🧩 MCP 插件配置")
        mcp_top_bar = ctk.CTkFrame(tab_mcp, fg_color="transparent")
        mcp_top_bar.pack(fill=ctk.X, pady=(0, 6))

        ctk.CTkLabel(
            mcp_top_bar,
            text="💡 MCP 必须先安装；提示词只负责告诉 Agent 何时调用",
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#94A3B8")
        ).pack(side=ctk.LEFT)

        btn_copy_m = ctk.CTkButton(
            mcp_top_bar,
            text="📋 一键复制 MCP",
            width=125,
            height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0D9488",
            hover_color="#0F766E",
            corner_radius=6,
            command=lambda: self._copy_text(self.txt_mcp.get("1.0", "end-1c"), "MCP 配置已复制")
        )
        btn_copy_m.pack(side=ctk.RIGHT)

        btn_test_mcp = ctk.CTkButton(
            mcp_top_bar, text="🧪 测试 MCP", width=105, height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#475569", hover_color="#334155", corner_radius=6,
            command=self._test_codex_mcp_threaded,
        )
        btn_test_mcp.pack(side=ctk.RIGHT, padx=(0, 6))

        btn_install_codex = ctk.CTkButton(
            mcp_top_bar, text="⚡ 安装到 Codex", width=125, height=30,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7C3AED", hover_color="#6D28D9", corner_radius=6,
            command=self._install_codex_mcp,
        )
        btn_install_codex.pack(side=ctk.RIGHT, padx=(0, 6))

        self.txt_mcp = ctk.CTkTextbox(
            tab_mcp,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("#F8FAFC", "#0A0E17"),
            text_color=("#0F172A", "#E2E8F0"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#19243C"),
            wrap="none"
        )
        self.txt_mcp.pack(fill=ctk.BOTH, expand=True)

        # ─── 底部状态栏 ────────────────────────────────────────────────────────
        self.status_bar = ctk.CTkLabel(
            self,
            text="● 系统就绪 · 支持多模型组合勾选注入、Subagents 子代理自动化挂载与自执行配置生成",
            height=26,
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#64748B"),
            fg_color=("#E2E8F0", "#0F172A"),
            anchor="w",
            padx=18
        )
        self.status_bar.pack(side=ctk.BOTTOM, fill=ctk.X)

    # ─── 交互与业务逻辑 ───────────────────────────────────────────────────────

    def _on_theme_changed(self, choice):
        mode_map = {"深色": "Dark", "浅色": "Light", "系统": "System"}
        ctk.set_appearance_mode(mode_map.get(choice, "Dark"))

    def _toggle_key_visibility(self):
        if self.ent_key.cget("show") == "*":
            self.ent_key.configure(show="")
            self.btn_toggle_key.configure(text="🙈 隐藏")
        else:
            self.ent_key.configure(show="*")
            self.btn_toggle_key.configure(text="👁️ 显示")

    def _on_preset_selected(self, choice):
        if choice in PRESETS:
            p_data = PRESETS[choice]
            self.ent_provider.delete(0, "end")
            self.ent_provider.insert(0, p_data["provider"])

            self.ent_name.delete(0, "end")
            self.ent_name.insert(0, p_data["name"])

            self.ent_url.delete(0, "end")
            self.ent_url.insert(0, p_data["url"])

            self.cmb_protocol.set(p_data["protocol"])
            self.cmb_model.set(p_data["model"])

            if "models" in p_data:
                self.cmb_model.configure(values=p_data["models"])

            if p_data.get("key"):
                self.ent_key.delete(0, "end")
                self.ent_key.insert(0, p_data["key"])

            thinking_val = p_data.get("thinking", "auto (默认)")
            self.cmb_thinking.set(thinking_val)
            self._on_thinking_changed(thinking_val)

            self.lbl_test_status.configure(
                text=f"● 已载入预设: {p_data.get('hint','')[:40]}",
                text_color=("#4F46E5", "#818CF8")
            )
            self._update_all_exports(
                p_data["provider"], p_data["name"], p_data["model"],
                p_data["url"], p_data.get("key", ""), p_data["protocol"]
            )

    def _on_combobox_selected(self, choice):
        self._on_model_modified()

    def _on_thinking_changed(self, val):
        if not hasattr(self, "lbl_thinking_desc"):
            return
        if val == "high":
            self.lbl_thinking_desc.configure(
                text="  🔥 [高思考强度] 启用深度链式思考，上限最高 (适合复杂架构/算法推理)",
                text_color=("#7C3AED", "#C4B5FD")
            )
        elif val == "medium":
            self.lbl_thinking_desc.configure(
                text="  ⚖️ [中等思考强度] 兼顾思考深度与响应速度，日常开发推荐",
                text_color=("#0284C7", "#7DD3FC")
            )
        elif val == "low":
            self.lbl_thinking_desc.configure(
                text="  ⚡ [轻量思考] 快速推理响应，低延迟低消耗",
                text_color=("#16A34A", "#86EFAC")
            )
        else:
            self.lbl_thinking_desc.configure(
                text="  ⚙️ [系统默认] 遵循模型默认行为 (自动适配 o1/o3/R1/Claude 3.7 thinking 等)",
                text_color=("#64748B", "#94A3B8")
            )

    def _set_role_filter(self, role_name: str):
        self.active_role_filter = role_name
        for rn, btn in getattr(self, "role_filter_btns", {}).items():
            if rn == role_name:
                btn.configure(fg_color="#6366F1", text_color="#FFFFFF")
            else:
                btn.configure(fg_color=("#F1F5F9", "#1E293B"), text_color=("#475569", "#94A3B8"))
        self._filter_model_list()

    def _filter_model_list(self):
        query = (self.ent_search.get().strip().lower()) if hasattr(self, "ent_search") else ""
        role_f = getattr(self, "active_role_filter", "全部")

        for p_id, item in getattr(self, "card_containers", {}).items():
            card, name, model, proto, tag = item
            match_query = True
            if query:
                match_query = (
                    query in p_id.lower() or
                    query in name.lower() or
                    query in model.lower() or
                    query in proto.lower() or
                    query in tag.lower()
                )

            match_role = True
            if role_f != "全部":
                if role_f == "🧠推理" and "推理" not in tag:
                    match_role = False
                elif role_f == "💻编程" and "编程" not in tag and "编码" not in tag:
                    match_role = False
                elif role_f == "⚡极速" and "极速" not in tag and "敏捷" not in tag:
                    match_role = False
                elif role_f == "📚长文" and "长文" not in tag and "全景" not in tag:
                    match_role = False

            if match_query and match_role:
                if not card.winfo_ismapped():
                    card.pack(fill=ctk.X, pady=4, padx=2)
            else:
                if card.winfo_ismapped():
                    card.pack_forget()

    def _on_url_modified(self, event=None):
        url = self.ent_url.get().strip()
        url_lower = url.lower()
        if not url:
            return

        # 1. 火山方舟（Volcano Engine Ark）自动识别
        if "ark.cn-beijing.volces.com" in url_lower or "volces.com" in url_lower:
            if "/api/plan/v3" in url_lower:
                if self.cmb_protocol.get() != "openai_chat":
                    self.cmb_protocol.set("openai_chat")
                    self.lbl_test_status.configure(
                        text="💡 已识别为【火山方舟 OpenAI 协议】(适配 Cursor / Trae / Roo / Hermes / OpenClaw 等)",
                        text_color="#10B981"
                    )
            elif "/api/plan" in url_lower:
                if self.cmb_protocol.get() != "anthropic":
                    self.cmb_protocol.set("anthropic")
                    self.lbl_test_status.configure(
                        text="💡 已识别为【火山方舟 Anthropic 协议】(适配 Claude Code)",
                        text_color="#10B981"
                    )
            volces_models = ["deepseek-v4-pro", "deepseek-v4-flash", "claude-3-5-sonnet", "doubao-seed-2.0-pro", "doubao-seed-2.0-lite"]
            curr_vals = list(self.cmb_model.cget("values") or [])
            if "deepseek-v4-pro" not in curr_vals:
                self.cmb_model.configure(values=volces_models)
                cur_m = self.cmb_model.get().strip()
                if not cur_m or cur_m in ["deepseek-reasoner", "custom-model"]:
                    self.cmb_model.set("deepseek-v4-pro")

        # 2. 阿里百炼通义千问 (DashScope)
        elif "dashscope.aliyuncs.com" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【阿里百炼通义千问 (OpenAI兼容协议)】", text_color="#10B981")
            qwen_models = ["qwen-max", "qwen-plus", "qwen-coder-turbo", "qwen2.5-72b-instruct", "qwen2.5-coder-32b-instruct"]
            self.cmb_model.configure(values=qwen_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("qwen-max")

        # 3. 智谱 AI (清言 GLM)
        elif "open.bigmodel.cn" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【智谱 GLM 开放平台 (OpenAI兼容协议)】", text_color="#10B981")
            glm_models = ["glm-4-plus", "glm-4-long", "glm-4-flash", "glm-4-air"]
            self.cmb_model.configure(values=glm_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("glm-4-plus")

        # 4. 月之暗面 (Moonshot / Kimi)
        elif "moonshot.cn" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【月之暗面 Kimi (OpenAI兼容协议)】", text_color="#10B981")
            kimi_models = ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"]
            self.cmb_model.configure(values=kimi_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("moonshot-v1-128k")

        # 5. 硅基流动 (SiliconFlow)
        elif "siliconflow.cn" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【硅基流动 SiliconFlow (OpenAI兼容协议)】", text_color="#10B981")
            sf_models = ["deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-Coder-32B-Instruct"]
            self.cmb_model.configure(values=sf_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("deepseek-ai/DeepSeek-R1")

        # 6. OpenAI 官方端点
        elif "api.openai.com" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【OpenAI 官方端点 (OpenAI协议)】", text_color="#10B981")
            oai_models = ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1", "o1-mini"]
            self.cmb_model.configure(values=oai_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("gpt-4o")

        # 7. Anthropic 官方端点
        elif "anthropic.com" in url_lower:
            if self.cmb_protocol.get() != "anthropic":
                self.cmb_protocol.set("anthropic")
                self.lbl_test_status.configure(text="💡 已识别为【Anthropic Claude 原生协议】", text_color="#10B981")
            claude_models = ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]
            self.cmb_model.configure(values=claude_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("claude-3-7-sonnet-20250219")

        # 8. Google Gemini 官方端点
        elif "generativelanguage.googleapis.com" in url_lower:
            if "/openai" in url_lower:
                if self.cmb_protocol.get() != "openai_chat":
                    self.cmb_protocol.set("openai_chat")
                    self.lbl_test_status.configure(text="💡 已识别为【Google Gemini 兼容端点 (OpenAI协议)】", text_color="#10B981")
            else:
                if self.cmb_protocol.get() != "gemini":
                    self.cmb_protocol.set("gemini")
                    self.lbl_test_status.configure(text="💡 已识别为【Google Gemini 原生协议】", text_color="#10B981")
            gemini_models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
            self.cmb_model.configure(values=gemini_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("gemini-2.5-pro")

        # 9. OpenRouter 聚合网关
        elif "openrouter.ai" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【OpenRouter 全球聚合端点】", text_color="#10B981")
            router_models = ["anthropic/claude-3.7-sonnet", "openai/gpt-4o", "deepseek/deepseek-r1", "google/gemini-2.5-pro"]
            self.cmb_model.configure(values=router_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("anthropic/claude-3.7-sonnet")

        # 10. Groq 极速推理
        elif "api.groq.com" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【Groq 极速推理端点 (OpenAI协议)】", text_color="#10B981")
            groq_models = ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768"]
            self.cmb_model.configure(values=groq_models)
            if not self.cmb_model.get() or self.cmb_model.get() in ["deepseek-reasoner", "custom-model"]:
                self.cmb_model.set("llama-3.3-70b-versatile")

        # 11. 本地 Ollama
        elif "11434" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")
                self.lbl_test_status.configure(text="💡 已识别为【本地 Ollama 服务端点】", text_color="#10B981")

        # 12. 标准 OpenAI / v1 接口
        elif "/v1" in url_lower or "deepseek.com" in url_lower:
            if self.cmb_protocol.get() != "openai_chat":
                self.cmb_protocol.set("openai_chat")

    def _on_model_modified(self, event=None):
        val = self.cmb_model.get().strip()
        if not val:
            return

        # 智能容错：用户误将 API Key (形如 ark-xxx 或 sk-xxx) 填入模型名称输入框
        if val.startswith("ark-") or val.startswith("sk-"):
            self.ent_key.delete(0, "end")
            self.ent_key.insert(0, val)

            url = self.ent_url.get().strip().lower()
            if "volces.com" in url or val.startswith("ark-"):
                default_m = "deepseek-v4-pro"
                volces_models = ["deepseek-v4-pro", "deepseek-v4-flash", "claude-3-5-sonnet", "doubao-seed-2.0-pro", "doubao-seed-2.0-lite"]
                self.cmb_model.configure(values=volces_models)
            else:
                default_m = "deepseek-chat"

            self.cmb_model.set(default_m)
            self.lbl_test_status.configure(
                text=f"💡 检测到输入为 API Key，已自动转移至密钥框，模型已自动设为【{default_m}】",
                text_color="#F59E0B"
            )
            return

        # 智能容错：用户输入 deepseekpro4.0 或 deepseekpro，自动修正为火山官方 DeepSeek 模型标识 deepseek-v4-pro
        val_clean = val.lower().replace(" ", "").replace("_", "-")
        if val_clean in ["deepseekpro4.0", "deepseekpro", "deepseek-pro-4.0", "deepseek-pro", "deepseek4.0"]:
            self.cmb_model.set("deepseek-v4-pro")
            self.lbl_test_status.configure(
                text="💡 已为您将 deepseekpro4.0 智能修正为火山方舟官方标识【deepseek-v4-pro】",
                text_color="#10B981"
            )

    # ─── 多模型勾选操作 ────────────────────────────────────────────────────────

    def _select_all_injection(self):
        providers = self.current_state.get("providers", {})
        self.selected_for_injection = set(providers.keys())
        for pid, var in self.check_vars.items():
            var.set(True)
        self._update_selection_displays()

    def _unselect_all_injection(self):
        self.selected_for_injection.clear()
        for pid, var in self.check_vars.items():
            var.set(False)
        self._update_selection_displays()

    def _on_checkbox_toggled(self, p_id):
        var = self.check_vars.get(p_id)
        if var and var.get():
            self.selected_for_injection.add(p_id)
        else:
            self.selected_for_injection.discard(p_id)
        self._update_selection_displays()

    def _update_selection_displays(self):
        count = len(self.selected_for_injection)
        self.lbl_select_count.configure(text=f"待注入: {count} 个")
        self.btn_copy_prompt_left.configure(text=f"✨ 复制注入提示词 ({count}个)")
        self._refresh_prompt_display()

    # ─── 列表刷新与卡片渲染 ───────────────────────────────────────────────────

    def _refresh_model_list(self):
        for widget in self.provider_scroll.winfo_children():
            widget.destroy()

        self.card_badges = {}
        self.card_containers = {}
        self.current_state = load_state_dict()
        providers = self.current_state.get("providers", {})

        self.selected_for_injection = {pid for pid in self.selected_for_injection if pid in providers}
        if not self.selected_for_injection and providers:
            self.selected_for_injection = set(providers.keys())

        if not providers:
            lbl_empty = ctk.CTkLabel(
                self.provider_scroll,
                text="暂无配置模型\n请点击右上角【➕ 新建】",
                font=ctk.CTkFont(size=12),
                text_color="gray50"
            )
            lbl_empty.pack(pady=40)
            self._update_selection_displays()
            return

        for p_id, p_cfg in providers.items():
            name = p_cfg.get("name", p_id)
            model = p_cfg.get("model", "未设定")
            proto = p_cfg.get("protocol", "openai_chat")
            is_selected = (p_id == self.selected_provider_id)
            role_meta = detect_model_role(p_id, name, model)

            # 卡片背景与边框：选中时带鲜艳的高亮轮廓
            card = ctk.CTkFrame(
                self.provider_scroll,
                corner_radius=10,
                fg_color=("#EDE9FE" if is_selected else ("#FFFFFF", "#141E33")),
                border_width=1.5 if is_selected else 1,
                border_color=("#6366F1" if is_selected else ("#E2E8F0", "#1C2945")),
                cursor="hand2"
            )
            card.pack(fill=ctk.X, pady=4, padx=2)

            # 点击切换右侧表单查看与编辑
            card.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            # 卡片头部行：复选框 + 模型名称 + 角色标签
            top_line = ctk.CTkFrame(card, fg_color="transparent")
            top_line.pack(fill=ctk.X, padx=10, pady=(8, 2))
            top_line.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            chk_var = ctk.BooleanVar(value=(p_id in self.selected_for_injection))
            self.check_vars[p_id] = chk_var

            chk = ctk.CTkCheckBox(
                top_line,
                text="",
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=5,
                border_width=2,
                fg_color="#6366F1",
                hover_color="#4F46E5",
                variable=chk_var,
                command=lambda pid=p_id: self._on_checkbox_toggled(pid)
            )
            chk.pack(side=ctk.LEFT, padx=(0, 6))

            title_lbl = ctk.CTkLabel(
                top_line,
                text=name,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("#0F172A", "#F8FAFC"),
                anchor="w"
            )
            title_lbl.pack(side=ctk.LEFT, fill=ctk.X, expand=True)
            title_lbl.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            # 角色标签徽章
            role_badge = ctk.CTkLabel(
                top_line,
                text=role_meta["tag"],
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=role_meta["tag_color"],
                text_color=role_meta["tag_text_color"],
                corner_radius=5,
                padx=6,
                pady=2
            )
            role_badge.pack(side=ctk.RIGHT)
            role_badge.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            # 卡片次级行：模型标识 + 协议徽章
            sub_box = ctk.CTkFrame(card, fg_color="transparent")
            sub_box.pack(fill=ctk.X, padx=10, pady=(2, 8))
            sub_box.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            model_lbl = ctk.CTkLabel(
                sub_box,
                text=f"模型: {model}",
                font=ctk.CTkFont(family="Consolas", size=10),
                text_color=("#64748B", "#94A3B8"),
                anchor="w"
            )
            model_lbl.pack(side=ctk.LEFT)
            model_lbl.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            thinking_intensity = p_cfg.get("thinking_intensity")
            if thinking_intensity and not thinking_intensity.startswith("auto"):
                thinking_badge = ctk.CTkLabel(
                    sub_box,
                    text=f"🧠{thinking_intensity}",
                    font=ctk.CTkFont(size=9, weight="bold"),
                    fg_color=("#EDE9FE", "#2E1065"),
                    text_color=("#7C3AED", "#C4B5FD"),
                    corner_radius=4,
                    padx=4,
                    pady=1
                )
                thinking_badge.pack(side=ctk.LEFT, padx=(5, 0))
                thinking_badge.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            proto_text = "Claude" if proto == "anthropic" else ("Gemini" if proto == "gemini" else "OpenAI")
            proto_badge = ctk.CTkLabel(
                sub_box,
                text=proto_text,
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=("#DBEAFE", "#172554") if proto == "anthropic" else ("#DCFCE7", "#052E16"),
                text_color=("#1D4ED8", "#93C5FD") if proto == "anthropic" else ("#15803D", "#86EFAC"),
                corner_radius=4,
                padx=5,
                pady=1
            )
            proto_badge.pack(side=ctk.RIGHT)
            proto_badge.bind("<Button-1>", lambda e, pid=p_id: self._select_provider(pid))

            # 单卡片一键测试按钮 ⚡ 与 查余额按钮 💰
            btn_quick_test = ctk.CTkButton(
                sub_box,
                text="⚡",
                width=24,
                height=18,
                font=ctk.CTkFont(size=10),
                fg_color=("#F1F5F9", "#1E293B"),
                hover_color=("#E2E8F0", "#334155"),
                text_color=("#10B981", "#34D399"),
                corner_radius=4,
                command=lambda pid=p_id: self._test_single_provider_by_id(pid)
            )
            btn_quick_test.pack(side=ctk.RIGHT, padx=(0, 4))

            btn_quick_bal = ctk.CTkButton(
                sub_box,
                text="💰",
                width=24,
                height=18,
                font=ctk.CTkFont(size=10),
                fg_color=("#F1F5F9", "#1E293B"),
                hover_color=("#E2E8F0", "#334155"),
                text_color=("#0284C7", "#38BDF8"),
                corner_radius=4,
                command=lambda pid=p_id: self._check_single_provider_balance_by_id(pid)
            )
            btn_quick_bal.pack(side=ctk.RIGHT, padx=(0, 4))

            # 卡片独立测试状态徽章 (预先创建，通过 _render_card_badge 动态配置)
            test_status_badge = ctk.CTkLabel(
                sub_box,
                text="",
                font=ctk.CTkFont(size=9, weight="bold"),
                corner_radius=4,
                padx=5,
                pady=1
            )
            self.card_badges[p_id] = test_status_badge
            self.card_containers[p_id] = (card, name, model, proto, role_meta["tag"])
            self._render_card_badge(p_id)

        # 默认选中第一个进行编辑
        if not self.selected_provider_id and providers:
            first_id = list(providers.keys())[0]
            self._select_provider(first_id)
        else:
            self._update_selection_displays()

        # 根据当前搜索词与标签即时刷新显示
        self._filter_model_list()

    def _render_card_badge(self, p_id: str):
        """动态更新单个卡片的测试状态徽章与余额徽章，无需重构整列 UI"""
        badge = self.card_badges.get(p_id)
        if not badge or not badge.winfo_exists():
            return

        if p_id in self.checking_balances:
            badge.configure(
                text="💰查询中",
                fg_color=("#E0F2FE", "#082F49"),
                text_color=("#0284C7", "#7DD3FC")
            )
            badge.pack(side=ctk.RIGHT, padx=(0, 4))
            return

        if p_id in self.testing_models:
            badge.configure(
                text="⏳测试中",
                fg_color=("#FEF3C7", "#451A03"),
                text_color=("#D97706", "#FDE68A")
            )
            badge.pack(side=ctk.RIGHT, padx=(0, 4))
            return

        t_res = self.model_test_results.get(p_id)
        b_res = self.model_balance_results.get(p_id)

        if t_res:
            if t_res.get("status") == "success":
                badge.configure(
                    text=f"✅ {t_res.get('elapsed', 0)}ms",
                    fg_color=("#DCFCE7", "#064E3B"),
                    text_color=("#16A34A", "#86EFAC")
                )
                badge.pack(side=ctk.RIGHT, padx=(0, 4))
                return
            elif t_res.get("status") == "failed":
                badge.configure(
                    text="❌ 失败",
                    fg_color=("#FEE2E2", "#450A0A"),
                    text_color=("#DC2626", "#FCA5A5")
                )
                badge.pack(side=ctk.RIGHT, padx=(0, 4))
                return

        if b_res:
            if b_res.get("success") and b_res.get("balance"):
                badge.configure(
                    text=f"💰{b_res['balance']}",
                    fg_color=("#E0F2FE", "#082F49"),
                    text_color=("#0284C7", "#7DD3FC")
                )
                badge.pack(side=ctk.RIGHT, padx=(0, 4))
                return
            elif not b_res.get("supported"):
                badge.configure(
                    text="ℹ️控制台",
                    fg_color=("#FEF3C7", "#451A03"),
                    text_color=("#D97706", "#FDE68A")
                )
                badge.pack(side=ctk.RIGHT, padx=(0, 4))
                return
            else:
                badge.configure(
                    text="💰失败",
                    fg_color=("#FEE2E2", "#450A0A"),
                    text_color=("#DC2626", "#FCA5A5")
                )
                badge.pack(side=ctk.RIGHT, padx=(0, 4))
                return

        badge.pack_forget()

    def _select_provider(self, p_id):
        self.selected_provider_id = p_id
        providers = self.current_state.get("providers", {})
        cfg = providers.get(p_id, {})

        self.ent_provider.delete(0, "end")
        self.ent_provider.insert(0, p_id)

        self.ent_name.delete(0, "end")
        self.ent_name.insert(0, cfg.get("name", p_id))

        self.ent_url.delete(0, "end")
        self.ent_url.insert(0, cfg.get("base_url", ""))

        self.cmb_protocol.set(cfg.get("protocol", "openai_chat"))

        self.ent_key.delete(0, "end")
        self.ent_key.insert(0, cfg.get("api_key", ""))

        current_model = cfg.get("model", "")
        self.cmb_model.set(current_model)
        self.cmb_model.configure(values=[current_model] if current_model else [])

        thinking_intensity = cfg.get("thinking_intensity")
        self.cmb_thinking.set(thinking_intensity if thinking_intensity else "auto (默认)")
        self._on_thinking_changed(thinking_intensity if thinking_intensity else "auto (默认)")

        # 恢复状态提示或显示已知余额/测试结果
        b_res = self.model_balance_results.get(p_id)
        t_res = self.model_test_results.get(p_id)
        if b_res and b_res.get("success"):
            bal_str = b_res.get("balance", "")
            dt = b_res.get("details")
            self.lbl_test_status.configure(
                text=f"💰 当前余额: {bal_str}" + (f" ({dt})" if dt else ""),
                text_color="#10B981"
            )
        elif t_res and t_res.get("status") == "success":
            self.lbl_test_status.configure(
                text=f"● 测试通过 (耗时 {t_res.get('elapsed', 0)}ms)，可点击蓝色按钮查询余额",
                text_color="#10B981"
            )
        else:
            self.lbl_test_status.configure(
                text="● 已就绪，可测试模型连通性或查询账户余额",
                text_color=("#64748B", "#94A3B8")
            )

        self._update_all_exports(
            p_id, cfg.get("name", p_id), current_model,
            cfg.get("base_url", ""), cfg.get("api_key", ""), cfg.get("protocol", "openai_chat")
        )
        self._highlight_selected_card()

    def _highlight_selected_card(self):
        for p_id, item in getattr(self, "card_containers", {}).items():
            card = item[0]
            if p_id == self.selected_provider_id:
                card.configure(
                    fg_color=("#EDE9FE", "#1E2945"),
                    border_width=1.5,
                    border_color=("#6366F1", "#6366F1")
                )
            else:
                card.configure(
                    fg_color=("#FFFFFF", "#141E33"),
                    border_width=1,
                    border_color=("#E2E8F0", "#1C2945")
                )

    def _clear_form(self):
        self.selected_provider_id = None
        self.ent_provider.delete(0, "end")
        self.ent_provider.insert(0, "custom-model")

        self.ent_name.delete(0, "end")
        self.ent_name.insert(0, "新模型助手")

        self.ent_url.delete(0, "end")
        self.ent_url.insert(0, "https://api.deepseek.com")

        self.cmb_protocol.set("openai_chat")
        self.ent_key.delete(0, "end")
        self.cmb_model.set("deepseek-reasoner")
        self.cmb_thinking.set("auto (默认)")
        self._on_thinking_changed("auto (默认)")
        self.lbl_test_status.configure(text="● 已清空表单，请填写新配置或选择上方快速预设", text_color=("#64748B", "#94A3B8"))
        self._highlight_selected_card()

    def _save_form(self):
        p_id = self.ent_provider.get().strip().lower()
        if not p_id:
            messagebox.showerror("错误", "厂商标识符不能为空！")
            return

        name = self.ent_name.get().strip() or p_id
        url = self.ent_url.get().strip().rstrip("/")
        protocol = self.cmb_protocol.get().strip() or "openai_chat"
        key = self.ent_key.get().strip()
        model = self.cmb_model.get().strip()
        thinking_raw = self.cmb_thinking.get()
        thinking_intensity = None if thinking_raw.startswith("auto") else thinking_raw

        if not url or not model:
            messagebox.showerror("错误", "Base URL 与模型名称均不能为空！")
            return

        cfg = {
            "name": name,
            "base_url": url,
            "model": model,
            "protocol": protocol,
            "enabled": True,
            "api_key": key,
            "description": f"{name} 助手模型",
        }
        if thinking_intensity:
            cfg["thinking_intensity"] = thinking_intensity

        self.current_state.setdefault("providers", {})[p_id] = cfg
        if not self.current_state.get("default_provider"):
            self.current_state["default_provider"] = p_id

        self.selected_for_injection.add(p_id)

        save_state_dict(self.current_state)
        self.selected_provider_id = p_id
        self._refresh_model_list()
        self._update_all_exports(p_id, name, model, url, key, protocol)
        messagebox.showinfo("成功", f"🎉 配置 [{name}] 已成功保存！")

    def _delete_selected(self):
        if not self.selected_provider_id:
            return
        p_id = self.selected_provider_id
        if messagebox.askyesno("确认删除", f"确定要移除模型助手 [{p_id}] 吗？"):
            if p_id in self.current_state.get("providers", {}):
                del self.current_state["providers"][p_id]
                save_state_dict(self.current_state)
            self.selected_for_injection.discard(p_id)
            self.selected_provider_id = None
            self._refresh_model_list()

    def _fetch_remote_models_threaded(self):
        threading.Thread(target=self._fetch_remote_models, daemon=True).start()

    def _fetch_remote_models(self):
        url = self.ent_url.get().strip().rstrip("/")
        key = self.ent_key.get().strip()

        if not url:
            self.after(0, lambda: self.lbl_test_status.configure(text="⚠️ 请先输入 API Base URL！", text_color="#EF4444"))
            return

        self.after(0, lambda: self.btn_fetch.configure(text="⏳...", state="disabled"))

        # 火山方舟 Agent Plan 专有端点处理：不走通用 /models，直接注入官方已验证全量模型
        if "volces.com" in url.lower() or "api/plan" in url.lower():
            volces_models = [
                "deepseek-v4-pro",
                "deepseek-v4-flash",
                "claude-3-5-sonnet",
                "doubao-seed-2.0-pro",
                "doubao-seed-2.0-lite"
            ]
            self.after(0, lambda: self.cmb_model.configure(values=volces_models))
            self.after(0, lambda: self.cmb_model.set("deepseek-v4-pro"))
            self.after(0, lambda: self.lbl_test_status.configure(
                text=f"✨ 已自动载入火山方舟 Plan 官方模型清单 ({len(volces_models)}个，默认 deepseek-v4-pro)",
                text_color="#10B981"
            ))
            self.after(0, lambda: self.btn_fetch.configure(text="🔄 拉取", state="normal"))
            return

        try:
            import requests
            req_url = f"{url}/models" if not url.endswith("/models") else url
            headers = {}
            if key:
                headers["Authorization"] = f"Bearer {key}"
                headers["x-api-key"] = key
            resp = requests.get(req_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", []) if "id" in m]
                if models:
                    self.after(0, lambda: self.cmb_model.configure(values=models))
                    self.after(0, lambda: self.lbl_test_status.configure(
                        text=f"✅ 成功拉取到 {len(models)} 个可用模型，请在下拉框选择！",
                        text_color="#10B981"
                    ))
                else:
                    self.after(0, lambda: self.lbl_test_status.configure(
                        text="● 服务端未返回公共模型列表，可直接手动输入模型名称",
                        text_color=("#64748B", "#94A3B8")
                    ))
            else:
                self.after(0, lambda: self.lbl_test_status.configure(
                    text=f"● 远端返回 HTTP {resp.status_code}，可直接手动输入模型名称",
                    text_color=("#64748B", "#94A3B8")
                ))
        except Exception as e:
            self.after(0, lambda: self.lbl_test_status.configure(
                text=f"❌ 拉取连接失败: {str(e)[:45]}，可直接手动输入模型名称",
                text_color="#EF4444"
            ))
        finally:
            self.after(0, lambda: self.btn_fetch.configure(text="🔄 拉取", state="normal"))

    # ─── 连通性测试 ───────────────────────────────────────────────────────────

    def _test_single_provider_by_id(self, p_id: str):
        """通过模型卡片上的 ⚡ 按钮直接测试该模型"""
        providers = self.current_state.get("providers", {})
        cfg = providers.get(p_id)
        if not cfg:
            return
        self._test_provider_async(p_id, cfg)

    def _test_model_threaded(self):
        """右侧表单中的“⚡ 开始连通性与生成测试”按钮"""
        p_id = self.ent_provider.get().strip().lower()
        name = self.ent_name.get().strip() or p_id
        url = self.ent_url.get().strip().rstrip("/")
        protocol = self.cmb_protocol.get().strip() or "openai_chat"
        key = self.ent_key.get().strip()
        model = self.cmb_model.get().strip()

        if not url or not model:
            self.lbl_test_status.configure(text="❌ Base URL 和模型名称不能为空！", text_color="#EF4444")
            return

        cfg = {
            "name": name,
            "base_url": url,
            "protocol": protocol,
            "model": model,
            "api_key": key,
            "enabled": True
        }
        self.current_state.setdefault("providers", {})[p_id] = cfg
        save_state_dict(self.current_state)
        self._test_provider_async(p_id, cfg)

    def _batch_test_models(self):
        """一键测试勾选的所有模型助手 (若未勾选则测试全部已接入模型)"""
        providers = self.current_state.get("providers", {})
        if not providers:
            self.lbl_test_status.configure(text="● 暂无已配置的模型助手可供测试", text_color=("#64748B", "#94A3B8"))
            return

        target_ids = list(self.selected_for_injection) if self.selected_for_injection else list(providers.keys())
        for p_id in target_ids:
            if p_id in providers:
                self._test_provider_async(p_id, providers[p_id], is_batch=True)

    def _test_provider_async(self, p_id: str, cfg: dict, is_batch: bool = False):
        """核心异步测试逻辑：多模型并发运行，互不阻塞，在主线程安全更新状态徽章"""
        if p_id in self.testing_models:
            return

        self.testing_models.add(p_id)
        self.model_test_results[p_id] = {"status": "testing"}
        self._render_card_badge(p_id)
        self._update_test_ui_status()

        name = cfg.get("name", p_id)
        model = cfg.get("model", "")
        url = cfg.get("base_url", "").rstrip("/")
        key = cfg.get("api_key", "")
        protocol = cfg.get("protocol", "openai_chat")

        def _worker():
            start_t = time.monotonic()
            try:
                res = delegate_task(
                    task="请回复'连接成功'这四个字，不要其他内容。",
                    provider=p_id,
                    model=model,
                    api_key=key,
                    timeout=25
                )
                elapsed = res.get("elapsed_ms", int((time.monotonic() - start_t) * 1000))
                self.after(0, lambda: self._on_test_finished(p_id, res, elapsed, name, model, url, key, protocol))
            except Exception as e:
                err_res = {"success": False, "error": str(e)}
                elapsed = int((time.monotonic() - start_t) * 1000)
                self.after(0, lambda: self._on_test_finished(p_id, err_res, elapsed, name, model, url, key, protocol))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_test_finished(self, p_id: str, res: dict, elapsed: int, name: str, model: str, url: str, key: str, protocol: str):
        """在 Tkinter 主事件循环中安全执行测试完成回调"""
        self.testing_models.discard(p_id)
        if res.get("success"):
            reply = res.get("result", "").strip().replace("\n", " ")
            self.model_test_results[p_id] = {
                "status": "success",
                "elapsed": elapsed,
                "reply": reply
            }
            if p_id == self.selected_provider_id:
                self._update_all_exports(p_id, name, model, url, key, protocol)
        else:
            err = res.get("error", "未知错误")
            self.model_test_results[p_id] = {
                "status": "failed",
                "elapsed": elapsed,
                "error": err
            }

        self._render_card_badge(p_id)
        self._update_test_ui_status()

    def _update_test_ui_status(self):
        active_count = len(self.testing_models)
        if active_count > 0:
            self.btn_batch_test.configure(state="disabled", text=f"⏳ 正在测试({active_count})")
            if self.selected_provider_id in self.testing_models:
                self.lbl_test_status.configure(
                    text=f"⏳ 正在测试 [{self.selected_provider_id}] (当前并发 {active_count} 个)...",
                    text_color=("#4F46E5", "#818CF8")
                )
            else:
                self.lbl_test_status.configure(
                    text=f"⏳ 正在并发测试 {active_count} 个模型助手...",
                    text_color=("#4F46E5", "#818CF8")
                )
        else:
            self.btn_batch_test.configure(state="normal", text="⚡ 一键测试")
            # 汇总或显示当前模型结果
            if self.selected_provider_id and self.selected_provider_id in self.model_test_results:
                r = self.model_test_results[self.selected_provider_id]
                if r["status"] == "success":
                    cur_p = self.current_state.get("providers", {}).get(self.selected_provider_id, {})
                    ti = cur_p.get("thinking_intensity")
                    ti_str = f" | 🧠思考: {ti}" if ti and not ti.startswith("auto") else ""
                    self.lbl_test_status.configure(
                        text=f"✅ [{self.selected_provider_id}] 成功！耗时 {r['elapsed']}ms{ti_str} | 响应: {r['reply'][:30]}",
                        text_color="#10B981"
                    )
                elif r["status"] == "failed":
                    self.lbl_test_status.configure(
                        text=f"❌ [{self.selected_provider_id}] 失败: {r.get('error', '')[:50]}",
                        text_color="#EF4444"
                    )
            else:
                successes = sum(1 for v in self.model_test_results.values() if v.get("status") == "success")
                fails = sum(1 for v in self.model_test_results.values() if v.get("status") == "failed")
                if successes + fails > 0:
                    self.lbl_test_status.configure(
                        text=f"● 测试完成：{successes} 成功，{fails} 失败。点击卡片可查看详细配置与结果",
                        text_color="#10B981" if fails == 0 else "#F59E0B"
                    )
                else:
                    self.lbl_test_status.configure(
                        text="● 就绪，可点击左侧【⚡ 一键测试】或模型卡片上的【⚡】",
                        text_color=("#64748B", "#94A3B8")
                    )

    # ─── 余额与额度查询 ───────────────────────────────────────────────────────

    def _check_single_provider_balance_by_id(self, p_id: str):
        """通过模型卡片上的 💰 按钮查询该模型余额"""
        providers = self.current_state.get("providers", {})
        cfg = providers.get(p_id)
        if not cfg:
            return
        self._check_provider_balance_async(p_id, cfg)

    def _check_balance_threaded(self):
        """右侧表单中的“💰 查询余额”按钮"""
        p_id = self.ent_provider.get().strip().lower()
        name = self.ent_name.get().strip() or p_id
        url = self.ent_url.get().strip().rstrip("/")
        key = self.ent_key.get().strip()
        protocol = self.cmb_protocol.get().strip() or "openai_chat"

        if not url:
            self.lbl_test_status.configure(text="❌ API Base URL 不能为空！", text_color="#EF4444")
            return

        cfg = {
            "name": name,
            "base_url": url,
            "api_key": key,
            "protocol": protocol
        }
        self._check_provider_balance_async(p_id, cfg)

    def _batch_check_balances(self):
        """左侧顶部【💰 查余额】一键批量查询"""
        providers = self.current_state.get("providers", {})
        if not providers:
            self.lbl_test_status.configure(text="● 暂无已配置的模型助手", text_color=("#64748B", "#94A3B8"))
            return

        target_ids = list(self.selected_for_injection) if self.selected_for_injection else list(providers.keys())
        for p_id in target_ids:
            if p_id in providers:
                self._check_provider_balance_async(p_id, providers[p_id])

    def _check_provider_balance_async(self, p_id: str, cfg: dict):
        """核心异步查询余额逻辑：在后台线程请求，不卡顿界面"""
        if p_id in self.checking_balances:
            return

        self.checking_balances.add(p_id)
        self._render_card_badge(p_id)
        if hasattr(self, "btn_balance"):
            self.btn_balance.configure(state="disabled", text="⏳ 查询中...")
        if hasattr(self, "btn_batch_balance"):
            self.btn_batch_balance.configure(state="disabled", text=f"⏳({len(self.checking_balances)})")

        url = cfg.get("base_url", "").strip()
        key = cfg.get("api_key", "").strip()
        name = cfg.get("name", p_id)

        self.lbl_test_status.configure(
            text=f"● 正在查询 [{name}] 账户余额与额度...",
            text_color=("#0284C7", "#38BDF8")
        )

        def _worker():
            try:
                from tools.balance import query_balance
                res = query_balance(url, key, p_id, name)
                self.after(0, lambda: self._on_balance_finished(p_id, res, name))
            except Exception as e:
                err_res = {
                    "supported": True,
                    "success": False,
                    "balance": None,
                    "message": f"查询异常: {str(e)}",
                    "provider_type": "error"
                }
                self.after(0, lambda: self._on_balance_finished(p_id, err_res, name))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_balance_finished(self, p_id: str, res: dict, name: str):
        """在 Tkinter 主事件循环中安全执行余额查询回调"""
        self.checking_balances.discard(p_id)
        self.model_balance_results[p_id] = res
        self._render_card_badge(p_id)

        if hasattr(self, "btn_balance"):
            self.btn_balance.configure(state="normal", text="💰 查询余额")

        active_count = len(self.checking_balances)
        if hasattr(self, "btn_batch_balance"):
            if active_count > 0:
                self.btn_batch_balance.configure(state="disabled", text=f"⏳({active_count})")
            else:
                self.btn_batch_balance.configure(state="normal", text="💰 查余额")

        if self.selected_provider_id == p_id or active_count == 0:
            if res.get("success"):
                bal = res.get("balance", "")
                details = res.get("details")
                dt = f" ({details})" if details else ""
                self.lbl_test_status.configure(
                    text=f"💰 [{name}] 余额: {bal}{dt}",
                    text_color="#10B981"
                )
            elif not res.get("supported"):
                self.lbl_test_status.configure(
                    text=f"ℹ️ {res.get('message')}",
                    text_color="#F59E0B"
                )
            else:
                self.lbl_test_status.configure(
                    text=f"❌ {res.get('message')}",
                    text_color="#EF4444"
                )


    # ─── 导出与提示词生成引擎 ─────────────────────────────────────────────────

    def _update_all_exports(self, p_id=None, name=None, model=None, url="", key="", protocol="openai_chat"):
        self._refresh_prompt_display()
        self._update_code_display(p_id, name, model, url, key, protocol)
        self._update_mcp_display()

    def _generate_injection_prompt(self) -> str:
        providers = self.current_state.get("providers", {})
        target_ids = [pid for pid in providers if pid in self.selected_for_injection]
        if not target_ids:
            if self.selected_provider_id and self.selected_provider_id in providers:
                target_ids = [self.selected_provider_id]
            else:
                target_ids = list(providers.keys())

        if not target_ids:
            return "暂未勾选或配置任何外部模型，请在左侧添加并勾选模型。"

        models_info = []
        subagent_roles = []

        for pid in target_ids:
            cfg = providers.get(pid, {})
            name = cfg.get("name", pid)
            model = cfg.get("model", "default")
            proto = cfg.get("protocol", "openai_chat")
            url = cfg.get("base_url", "")
            role_meta = detect_model_role(pid, name, model)

            ti = cfg.get("thinking_intensity", "auto (默认)")
            models_info.append({
                "id": pid,
                "name": name,
                "model": model,
                "protocol": proto,
                "base_url": url,
                "thinking_intensity": ti,
                "role_id": role_meta["role_id"],
                "role_title": role_meta["role_title"],
                "specialty": role_meta["specialty"],
                "tag": role_meta["tag"]
            })

            subagent_roles.append(
                f"- **`{role_meta['role_id']}`** ({role_meta['role_title']})：\n"
                f"  - 挂载模型: `{model}` (厂商: {name}, 协议: `{proto}`, 思考强度: `{ti}`)\n"
                f"  - 专长职责: {role_meta['specialty']}\n"
                f"  - 委派调用: MCP 工具 `delegate_task(task=\"<子任务>\", provider=\"{pid}\", model=\"{model}\")`"
            )

        table_lines = [
            f"| `{m['id']}` | **{m['name']}** | `{m['model']}` | `{m['protocol']}` | `{m['thinking_intensity']}` | {m['tag']} |"
            for m in models_info
        ]
        table_str = "\n".join(table_lines)
        subagents_str = "\n".join(subagent_roles)

        prompt = f"""请为当前工作区启用 APIson 多模型委派规则。

前提：APIson MCP 应已由 APIson 管理面板安装到客户端。请先检查当前工具列表是否存在 `delegate_task`。如果工具不存在，请明确报告“APIson MCP 尚未加载，需要在 APIson 中安装并重启客户端”，不要声称已经委派，也不要临时生成替代脚本。

### 可用助手

| 模型标识 | 显示名称 | 具体模型 | 协议 | 思考强度 | 专长定位 |
| :--- | :--- | :--- | :--- | :--- | :--- |
{table_str}

### 委派角色

{subagents_str}

### 必须遵守的调用规则

1. 遇到复杂推理、大规模代码实现、代码审查、批量处理、长文分析，或两个以上可独立执行的子任务时，必须实际调用 `delegate_task`。
2. 用户明确要求使用 APIson、外部模型或指定 provider 时，必须调用 `delegate_task`，不得直接模拟助手回复。
3. 调用时传入完整、自包含的 `task`，并根据上表填写 `provider` 和 `model`。
4. 只有工具返回 `success: true` 后才能声称委派成功；失败时应报告 `error` 并继续处理可完成的部分。
5. 主 Agent 负责检查、验证并整合外部助手结果。
6. 不得在项目规则、聊天回复或代码中复制、暴露 API Key。

请把以上规则写入当前项目适用的 Agent 规则文件（例如 `AGENTS.md`、`CLAUDE.md` 或 `.cursor/rules/`），随后调用一次 `delegate_task` 做真实连通性验证，并汇报 provider、model、耗时和 usage。
"""
        return prompt.strip()

    def _refresh_prompt_display(self):
        prompt_text = self._generate_injection_prompt()
        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("1.0", prompt_text)

    def _update_code_display(self, p_id=None, name=None, model=None, url="", key="", protocol="openai_chat"):
        clean_name = name or (self.ent_name.get().strip() if hasattr(self, "ent_name") else "当前模型")
        clean_url = (url or (self.ent_url.get().strip() if hasattr(self, "ent_url") else "")).rstrip("/")
        clean_key = key or (self.ent_key.get().strip() if hasattr(self, "ent_key") else "")
        clean_model = model or (self.cmb_model.get().strip() if hasattr(self, "cmb_model") else "claude-3-5-sonnet")
        clean_proto = "anthropic" if protocol == "anthropic" else ("gemini" if protocol == "gemini" else "openai")
        clean_thinking = self.cmb_thinking.get() if hasattr(self, "cmb_thinking") else "auto"
        if clean_thinking.startswith("auto"):
            clean_thinking = "auto"

        code_text = f'''"""
通用大模型调用工具 - {clean_name} ({clean_model})
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

特点:
1. 完全自包含独立文件：无任何本地环境路径依赖，只要有 requests 即可在任何项目或服务器直接运行。
2. 已预置测试通过的 Base URL、API Key、思考强度 ({clean_thinking}) 与推荐模型参数。
3. 针对数据库/批处理场景：提供单次调用 call_llm 与数据库列表批量处理示例。
"""

import os
import json
import time
from typing import Union, List, Dict, Optional, Any
import requests

# 预置配置信息
CONFIG = {{
    "base_url": "{clean_url}",
    "api_key": "{clean_key}",
    "model": "{clean_model}",
    "protocol": "{clean_proto}",
    "thinking_intensity": "{clean_thinking}"
}}


def call_llm(
    prompt: Union[str, List[Dict[str, str]]],
    system: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    protocol: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 4096,
    timeout: int = 45,
    retries: int = 2
) -> str:
    key = api_key or CONFIG["api_key"]
    m = model or CONFIG["model"]
    url = (base_url or CONFIG["base_url"]).rstrip("/")
    proto = (protocol or CONFIG["protocol"]).lower()

    if isinstance(prompt, str):
        messages = [{{"role": "user", "content": prompt}}]
    elif isinstance(prompt, list):
        messages = list(prompt)
    else:
        raise ValueError("prompt 参数必须为字符串或消息字典列表")

    last_err = None
    for attempt in range(retries + 1):
        try:
            if proto in ("anthropic", "claude"):
                endpoint = f"{{url}}/v1/messages" if not url.endswith(("/messages", "/v1")) else (f"{{url}}/messages" if url.endswith("/v1") else url)
                headers = {{
                    "x-api-key": key,
                    "Authorization": f"Bearer {{key}}",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }}
                payload = {{
                    "model": m,
                    "max_tokens": max_tokens,
                    "messages": messages
                }}
                if system:
                    payload["system"] = system
                resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
                if resp.status_code != 200:
                    raise RuntimeError(f"Anthropic 接口报错 [{{resp.status_code}}]: {{resp.text}}")
                data = resp.json()
                blocks = [b.get("text", "") for b in data.get("content", []) if isinstance(b, dict) and b.get("type") == "text"]
                return "".join(blocks).strip() if blocks else str(data.get("text", "")).strip()

            else:  # openai
                endpoint = f"{{url}}/chat/completions" if not url.endswith("/chat/completions") else url
                headers = {{
                    "Authorization": f"Bearer {{key}}",
                    "Content-Type": "application/json"
                }}
                full_msgs = []
                if system:
                    full_msgs.append({{"role": "system", "content": system}})
                full_msgs.extend(messages)
                payload = {{
                    "model": m,
                    "messages": full_msgs,
                    "max_tokens": max_tokens
                }}
                if temperature is not None:
                    payload["temperature"] = temperature
                resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
                if resp.status_code != 200:
                    raise RuntimeError(f"OpenAI 接口报错 [{{resp.status_code}}]: {{resp.text}}")
                return resp.json()["choices"][0]["message"]["content"].strip()

        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"模型调用失败 (已重试 {{retries}} 次): {{last_err}}") from last_err


def process_database_records(
    db_rows: List[Dict[str, Any]],
    input_field: str = "content",
    output_field: str = "ai_analysis",
    task_prompt: str = "请对以下内容进行要点提炼与分类："
) -> List[Dict[str, Any]]:
    print(f"[*] 开始处理数据库记录，共 {{len(db_rows)}} 条...")
    for idx, row in enumerate(db_rows):
        text = str(row.get(input_field, ""))
        try:
            row[output_field] = call_llm(prompt=f"{{task_prompt}}\\n\\n{{text}}")
            row["_status"] = "SUCCESS"
        except Exception as err:
            row[output_field] = None
            row["_status"] = f"ERROR: {{err}}"
        print(f"[{{idx+1}}/{{len(db_rows)}}] 处理完成 (ID: {{row.get('id', idx)}})")
    return db_rows


if __name__ == "__main__":
    print("=== 测试调用当前模型 ===")
    answer = call_llm("请回答'连接正常'四个字。")
    print("模型回复:", answer)
'''
        self.txt_code.delete("1.0", "end")
        self.txt_code.insert("1.0", code_text)

    def _update_mcp_display(self):
        mcp_script = str(_ROOT / "mcp_server.py")
        mcp_cfg = {
            "mcpServers": {
                "agent-model-connect": {
                    "command": "python",
                    "args": [
                        mcp_script
                    ]
                }
            }
        }
        json_str = json.dumps(mcp_cfg, ensure_ascii=False, indent=2)
        self.txt_mcp.delete("1.0", "end")
        self.txt_mcp.insert("1.0", json_str)

    def _install_codex_mcp(self):
        try:
            result = install_codex_mcp()
            backup = result.get("backup")
            backup_text = f"\n备份文件：{backup}" if backup else ""
            messagebox.showinfo(
                "Codex MCP 安装成功",
                f"✅ {result['message']}\n\n配置文件：{result['config']}"
                f"{backup_text}\n\n切换 Codex 账号不会删除此本机配置。",
            )
        except Exception as exc:
            messagebox.showerror("Codex MCP 安装失败", str(exc))

    def _test_codex_mcp_threaded(self):
        self.status_bar.configure(text="⏳ 正在测试 APIson MCP Server...")
        def _run():
            status = get_codex_mcp_status()
            result = test_mcp_server()
            self.after(0, lambda: self._show_mcp_test(status, result))
        threading.Thread(target=_run, daemon=True).start()

    def _show_mcp_test(self, status, result):
        self.status_bar.configure(text="● 系统就绪 · APIson 多模型委派平台")
        if result.get("success"):
            installed = "已写入 Codex 配置" if status.get("installed") else "尚未写入 Codex 配置"
            messagebox.showinfo(
                "MCP 测试成功",
                f"✅ {result['message']}\n✅ Server 工具：{', '.join(result.get('tools', []))}"
                f"\n{'✅' if status.get('installed') else '⚠️'} {installed}\n\n"
                "此测试不调用外部模型，不消耗 API 额度。",
            )
        else:
            messagebox.showerror("MCP 测试失败", result.get("error") or result.get("message"))

    # ─── 复制工具方法 ─────────────────────────────────────────────────────────

    def _copy_text(self, text, title="已复制", custom_msg=None):
        if not text or not text.strip():
            messagebox.showwarning("提示", "当前内容为空，无法复制！")
            return
        self.clipboard_clear()
        self.clipboard_append(text.strip())
        msg = custom_msg or f"已成功复制到系统剪贴板！\n可以直接粘贴到任何项目文件或脚本中使用。"
        messagebox.showinfo(title, msg)

    def _copy_injection_prompt(self):
        count = len(self.selected_for_injection)
        prompt_text = self.txt_prompt.get("1.0", "end-1c")
        self._copy_text(
            prompt_text,
            title="提示词已复制",
            custom_msg=(
                f"🎉 已成功复制包含 {count} 个外部模型的 Agent 注入提示词！\n\n"
                "【下一步操作】\n"
                "1. 将复制的内容直接发给你的 AI Agent (Antigravity / Cursor / Claude Code 等)。\n"
                "2. Agent 将自动在当前工作区生成 .agent_models 目录、落实在地配置并定义 Subagents 子代理。\n"
                "3. 后续即可永久指挥 Agent 及其子代理协同调用这些模型！"
            )
        )

    def _start_gateway_threaded(self):
        def _run():
            from gateway import app
            app.run(host="127.0.0.1", port=8765, debug=False)
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        messagebox.showinfo(
            "网关已启动",
            "🚀 本地 OpenAI 兼容网关已在后台运行！\n\n"
            "地址: http://127.0.0.1:8765/v1\n"
            "支持将任何仅支持 OpenAI API 的软件（如 Codex、Dify、Chatbox）\n"
            "指向此地址直接使用已配置的模型。"
        )

    def _check_for_updates_threaded(self, manual=True):
        self.btn_update.configure(text="⏳ 检查中...", state="disabled")
        self.lbl_update_status.configure(
            text="⏳ 正在检测...",
            fg_color=("#F1F5F9", "#1E293B"),
            text_color=("#64748B", "#94A3B8")
        )
        threading.Thread(target=self._check_for_updates, args=(manual,), daemon=True).start()

    def _check_for_updates(self, manual=True):
        info = check_update()
        self._update_info = info
        self.after(0, lambda: self._on_update_checked(info, manual))

    def _on_update_checked(self, info, manual=True):
        self.btn_update.configure(state="normal")
        local_sha = info.get("local_sha", "?")
        remote_sha = info.get("remote_sha", "?")
        self.lbl_version.configure(text=f"v{local_sha}")

        if info.get("error"):
            self.btn_update.configure(
                text="🔄 检查更新",
                fg_color=("#F1F5F9", "#1E293B"),
                text_color=("#334155", "#E2E8F0")
            )
            self.lbl_update_status.configure(
                text="⚠️ 检查异常",
                fg_color=("#FEE2E2", "#450A0A"),
                text_color=("#DC2626", "#FCA5A5")
            )
            if manual:
                messagebox.showwarning(
                    "检查更新",
                    f"无法连接到 GitHub 检查更新：\n{info.get('error')}\n\n请检查网络连接或直接访问 GitHub 仓库。"
                )
            return

        if info.get("has_update"):
            self.lbl_update_status.configure(
                text=f"🔴 发现新版本 v{remote_sha}",
                fg_color=("#FEF3C7", "#451A03"),
                text_color=("#D97706", "#FDE68A")
            )
            self.btn_update.configure(
                text="⬆️ 立即更新",
                fg_color="#F59E0B",
                hover_color="#D97706",
                text_color="#FFFFFF",
            )
            msg = info.get("release_notes") or info.get("remote_message", "")
            if len(msg) > 3500:
                msg = msg[:3500] + "\n\n……更多内容请查看 CHANGELOG.md"
            date = info.get("remote_date", "")[:10]
            if manual:
                if messagebox.askyesno(
                    "发现新版本",
                    f"🚀 检测到 GitHub 官方仓库有新版本！\n\n"
                    f"当前本地版本: v{local_sha}\n"
                    f"远程最新版本: v{remote_sha} ({date})\n\n"
                    f"本次更新内容：\n{msg}\n\n"
                    f"是否立即自动拉取并更新？"
                ):
                    self._do_update_threaded()
        else:
            self.lbl_update_status.configure(
                text="● 已是最新版本",
                fg_color=("#DCFCE7", "#052E16"),
                text_color=("#16A34A", "#4ADE80")
            )
            self.btn_update.configure(
                text="🔄 检查更新",
                fg_color=("#F1F5F9", "#1E293B"),
                hover_color=("#E2E8F0", "#334155"),
                text_color=("#334155", "#E2E8F0")
            )
            if manual:
                messagebox.showinfo(
                    "检查更新",
                    f"🎉 当前已是最高版本（最新版本）！\n\n"
                    f"当前本地版本: v{local_sha}\n"
                    f"GitHub 最新版本: v{remote_sha}\n\n"
                    f"本地代码已与 GitHub 仓库 (star132-bot/APIson) 保持最新，无需更新。"
                )

    def _do_update_threaded(self):
        self.btn_update.configure(text="⬇️ 更新中...", state="disabled")
        threading.Thread(target=self._do_update, daemon=True).start()

    def _do_update(self):
        result = do_update()
        self.after(0, lambda: self._on_update_done(result))

    def _on_update_done(self, result):
        self.btn_update.configure(state="normal", text="🔄 检查更新",
                                   fg_color=("#F1F5F9", "#1E293B"), text_color=("#334155", "#E2E8F0"))
        if result.get("success"):
            messagebox.showinfo(
                "更新成功",
                "✅ 已更新到最新版本！\n\n请重启应用以使新版本生效。\n\n"
                "本次更新内容：\n" + (result.get("release_notes") or result.get("output", ""))[:3500]
            )
            self._check_for_updates_threaded(manual=False)
        else:
            messagebox.showerror("更新失败", result.get("error", "未知错误"))

    def _auto_check_version(self):
        """启动时后台异步执行一次自动检测与状态渲染"""
        self._check_for_updates_threaded(manual=False)


def launch():
    app = ModelConnectGUI()
    app._auto_check_version()
    app.mainloop()


if __name__ == "__main__":
    launch()
