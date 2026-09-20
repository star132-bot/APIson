"""
tools/balance.py
API 余额与使用额度查询模块。
支持主流官方大模型（DeepSeek、硅基流动、月之暗面、OpenRouter 等）以及各类 One API / New API 中转站的余额/额度自动查询。
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlparse


def query_balance(
    base_url: str,
    api_key: str,
    provider_id: str = "",
    provider_name: str = ""
) -> Dict[str, Any]:
    """
    查询指定提供商或 Base URL 的 API 余额/额度。
    
    返回字典结构：
    {
        "supported": bool,       # 是否支持该厂商/协议的余额查询
        "success": bool,         # 查询是否成功
        "balance": Optional[str],# 格式化余额（如 "¥ 25.80 CNY"、"$ 10.00 USD" 或 "本地免费"）
        "details": Optional[str],# 附加明细（如 "充值: ¥20.00 | 赠送: ¥5.80"）
        "message": str,          # 用户提示信息或官方跳转说明
        "provider_type": str     # 识别到的厂商/服务类型
    }
    """
    base_url = (base_url or "").strip().rstrip("/")
    api_key = (api_key or "").strip()
    provider_id = (provider_id or "").lower()
    provider_name = (provider_name or "").lower()

    if not base_url and not api_key:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "请先配置 API Base URL 与 API Key",
            "provider_type": "unknown"
        }

    # 1. 本地模型判定 (Ollama, LM Studio, vLLM, localhost)
    if any(k in base_url.lower() for k in ["localhost", "127.0.0.1", "0.0.0.0"]) or \
       any(k in provider_id for k in ["ollama", "lmstudio", "local"]):
        return {
            "supported": True,
            "success": True,
            "balance": "本地免费 / 无限额度",
            "details": "本地部署模型无需计费消耗",
            "message": "本地离线模型，运行不消耗任何在线 API 额度。",
            "provider_type": "local"
        }

    if not api_key:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "未填写 API Key，无法查询账户余额",
            "provider_type": "missing_key"
        }

    # 2. DeepSeek 官方
    if "api.deepseek.com" in base_url or "deepseek" in provider_id:
        return _check_deepseek_balance(api_key)

    # 3. 硅基流动 (SiliconFlow)
    if "siliconflow.cn" in base_url or "siliconflow" in provider_id:
        return _check_siliconflow_balance(api_key)

    # 4. 月之暗面 (Moonshot AI / Kimi)
    if "api.moonshot.cn" in base_url or "moonshot" in provider_id or "kimi" in provider_id:
        return _check_moonshot_balance(api_key)

    # 5. OpenRouter
    if "openrouter.ai" in base_url or "openrouter" in provider_id:
        return _check_openrouter_balance(api_key)

    # 6. 火山方舟 (Volcengine Ark)
    if "volces.com" in base_url or "volc" in provider_id or "ark" in provider_id:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "火山引擎采用云账号统一计费，官方未开放 API Key 直查余额，请登录控制台【费用中心】查看。",
            "provider_type": "volcengine"
        }

    # 7. OpenAI 官方
    if "api.openai.com" in base_url or (provider_id == "openai" and "openai.com" in base_url):
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "OpenAI 官方未开放标准 API Key 查余额接口，请登录 platform.openai.com 查看。",
            "provider_type": "openai_official"
        }

    # 8. Anthropic 官方
    if "api.anthropic.com" in base_url or "anthropic" in provider_id:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "Claude 官方未开放 API Key 查余额接口，请登录 console.anthropic.com 查看。",
            "provider_type": "anthropic_official"
        }

    # 9. Google Gemini 官方
    if "generativelanguage.googleapis.com" in base_url or "gemini" in provider_id:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "Gemini 采用 GCP 统一结算，请前往 Google AI Studio / GCP 控制台查看。",
            "provider_type": "gemini_official"
        }

    # 10. 阿里百炼 / DashScope 官方
    if "dashscope.aliyuncs.com" in base_url or "qwen" in provider_id or "dashscope" in provider_id:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "阿里百炼通过阿里云统一计费，请前往阿里云控制台【费用中心】查看。",
            "provider_type": "dashscope_official"
        }

    # 11. 智谱清言 官方
    if "open.bigmodel.cn" in base_url or "zhipu" in provider_id or "glm" in provider_id:
        return {
            "supported": False,
            "success": False,
            "balance": None,
            "details": None,
            "message": "智谱开放平台官方未提供 API Key 查余额接口，请前往 open.bigmodel.cn 控制台查看。",
            "provider_type": "zhipu_official"
        }

    # 12. 第三方中转站 / 代理站 / One API / New API 探测
    return _check_oneapi_relay_balance(base_url, api_key)


def _check_deepseek_balance(api_key: str) -> Dict[str, Any]:
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "APIson/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("is_available") is not None:
                infos = data.get("balance_infos", [])
                if infos:
                    info = infos[0]
                    curr = info.get("currency", "CNY")
                    symbol = "¥" if curr == "CNY" else "$"
                    total = info.get("total_balance", "0.00")
                    granted = info.get("granted_balance", "0.00")
                    topped = info.get("topped_up_balance", "0.00")
                    return {
                        "supported": True,
                        "success": True,
                        "balance": f"{symbol} {total} {curr}",
                        "details": f"充值: {symbol}{topped} | 赠送: {symbol}{granted}",
                        "message": f"DeepSeek 官方账户可用余额: {symbol}{total} {curr}",
                        "provider_type": "deepseek"
                    }
                return {
                    "supported": True,
                    "success": True,
                    "balance": "正常可用",
                    "details": None,
                    "message": "DeepSeek 账户状态正常可用",
                    "provider_type": "deepseek"
                }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {
                "supported": True,
                "success": False,
                "balance": None,
                "details": None,
                "message": "DeepSeek API Key 无效或已过期 (HTTP 401)",
                "provider_type": "deepseek"
            }
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"DeepSeek 余额查询接口异常: HTTP {e.code}",
            "provider_type": "deepseek"
        }
    except Exception as e:
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"DeepSeek 连接失败: {e}",
            "provider_type": "deepseek"
        }


def _check_siliconflow_balance(api_key: str) -> Dict[str, Any]:
    url = "https://api.siliconflow.cn/v1/user/info"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "APIson/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            user_data = data.get("data", {})
            total = user_data.get("totalBalance", user_data.get("balance", "0.00"))
            charge = user_data.get("chargeBalance", "0.00")
            name = user_data.get("name", "")
            return {
                "supported": True,
                "success": True,
                "balance": f"¥ {total} CNY",
                "details": f"用户: {name} | 充值余额: ¥{charge}",
                "message": f"硅基流动可用余额: ¥ {total} CNY",
                "provider_type": "siliconflow"
            }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {
                "supported": True,
                "success": False,
                "balance": None,
                "details": None,
                "message": "硅基流动 API Key 无效 (HTTP 401)",
                "provider_type": "siliconflow"
            }
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"硅基流动查询失败: HTTP {e.code}",
            "provider_type": "siliconflow"
        }
    except Exception as e:
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"硅基流动连接失败: {e}",
            "provider_type": "siliconflow"
        }


def _check_moonshot_balance(api_key: str) -> Dict[str, Any]:
    url = "https://api.moonshot.cn/v1/users/me/balance"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "APIson/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            balance_data = data.get("data", {})
            avail = balance_data.get("available_balance", 0.0)
            cash = balance_data.get("cash_balance", 0.0)
            voucher = balance_data.get("voucher_balance", 0.0)
            return {
                "supported": True,
                "success": True,
                "balance": f"¥ {avail:.2f} CNY",
                "details": f"现金: ¥{cash:.2f} | 代金券: ¥{voucher:.2f}",
                "message": f"月之暗面 (Kimi) 可用余额: ¥ {avail:.2f} CNY",
                "provider_type": "moonshot"
            }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {
                "supported": True,
                "success": False,
                "balance": None,
                "details": None,
                "message": "月之暗面 API Key 无效 (HTTP 401)",
                "provider_type": "moonshot"
            }
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"月之暗面查询失败: HTTP {e.code}",
            "provider_type": "moonshot"
        }
    except Exception as e:
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"月之暗面连接失败: {e}",
            "provider_type": "moonshot"
        }


def _check_openrouter_balance(api_key: str) -> Dict[str, Any]:
    url = "https://openrouter.ai/api/v1/credits"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "APIson/2.0"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            credits_data = data.get("data", {})
            total = float(credits_data.get("total_credits", 0.0))
            usage = float(credits_data.get("total_usage", 0.0))
            remain = max(0.0, total - usage)
            return {
                "supported": True,
                "success": True,
                "balance": f"$ {remain:.2f} USD",
                "details": f"总积分: ${total:.2f} | 已消耗: ${usage:.2f}",
                "message": f"OpenRouter 剩余可用额度: $ {remain:.2f} USD",
                "provider_type": "openrouter"
            }
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {
                "supported": True,
                "success": False,
                "balance": None,
                "details": None,
                "message": "OpenRouter API Key 无效 (HTTP 401)",
                "provider_type": "openrouter"
            }
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"OpenRouter 查询失败: HTTP {e.code}",
            "provider_type": "openrouter"
        }
    except Exception as e:
        return {
            "supported": True,
            "success": False,
            "balance": None,
            "details": None,
            "message": f"OpenRouter 连接失败: {e}",
            "provider_type": "openrouter"
        }


def _check_oneapi_relay_balance(base_url: str, api_key: str) -> Dict[str, Any]:
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    clean_base = base_url.rstrip("/")

    candidate_sub_urls = [
        f"{clean_base}/dashboard/billing/subscription",
        f"{origin}/dashboard/billing/subscription",
        f"{clean_base}/subscription",
        f"{origin}/api/user/self"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "APIson/2.0"
    }

    sub_data = None
    successful_url = None

    for url in candidate_sub_urls:
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    raw = resp.read().decode("utf-8", errors="ignore")
                    sub_data = json.loads(raw)
                    successful_url = url
                    break
        except Exception:
            continue

    if sub_data:
        hard_limit = sub_data.get("hard_limit_usd") or sub_data.get("hard_limit") or sub_data.get("cost_limit")
        if hard_limit is not None:
            now = datetime.now()
            start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            
            usage_url = successful_url.replace("/subscription", f"/usage?start_date={start_date}&end_date={end_date}")
            total_usage = 0.0
            try:
                ureq = urllib.request.Request(usage_url, headers=headers, method="GET")
                with urllib.request.urlopen(ureq, timeout=3) as uresp:
                    udata = json.loads(uresp.read().decode("utf-8"))
                    raw_usage = udata.get("total_usage", 0.0)
                    total_usage = float(raw_usage) / 100.0 if float(raw_usage) > float(hard_limit) else float(raw_usage)
            except Exception:
                pass

            remain = max(0.0, float(hard_limit) - total_usage)
            return {
                "supported": True,
                "success": True,
                "balance": f"$ {remain:.2f} USD",
                "details": f"总额度: ${float(hard_limit):.2f} | 已消耗: ${total_usage:.2f}",
                "message": f"中转站可用额度: $ {remain:.2f} USD",
                "provider_type": "oneapi"
            }

        if sub_data.get("success") and "data" in sub_data:
            user = sub_data["data"]
            quota = user.get("quota", 0)
            quota_usd = quota / 500000.0
            return {
                "supported": True,
                "success": True,
                "balance": f"$ {quota_usd:.2f} USD",
                "details": f"配额点数: {quota}",
                "message": f"代理站可用配额: $ {quota_usd:.2f} USD",
                "provider_type": "oneapi"
            }

    host = parsed.netloc or base_url
    return {
        "supported": False,
        "success": False,
        "balance": None,
        "details": None,
        "message": f"服务商（{host}）未开放 Bearer 余额直查接口。建议在对应平台控制台查看实时额度。",
        "provider_type": "custom"
    }
