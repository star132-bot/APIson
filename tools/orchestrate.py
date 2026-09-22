"""Concurrent delegation and independent result review for APIson."""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from tools.delegate import delegate_task


def _bounded_workers(requested: int, item_count: int) -> int:
    return max(1, min(int(requested or 4), item_count, 8))


def delegate_tasks(tasks: list[dict[str, Any]], max_workers: int = 4) -> dict:
    """Run independent model tasks concurrently and preserve the requested order."""
    if not tasks:
        raise ValueError("tasks 至少需要包含一个子任务")
    if len(tasks) > 16:
        raise ValueError("单批最多支持 16 个子任务")

    normalized = []
    for index, item in enumerate(tasks):
        task_text = str(item.get("task", "")).strip()
        if not task_text:
            raise ValueError(f"第 {index + 1} 个子任务缺少 task")
        normalized.append({
            "id": str(item.get("id") or f"task-{index + 1}"),
            "task": task_text,
            "provider": item.get("provider"),
            "model": item.get("model"),
            "system_prompt": item.get("system_prompt"),
            "timeout": max(1, min(int(item.get("timeout", 60)), 300)),
        })

    started = time.monotonic()
    worker_count = _bounded_workers(max_workers, len(normalized))
    results: list[dict | None] = [None] * len(normalized)

    def run_one(index: int, item: dict) -> tuple[int, dict]:
        result = delegate_task(
            task=item["task"],
            provider=item["provider"],
            model=item["model"],
            system_prompt=item["system_prompt"],
            timeout=item["timeout"],
        )
        result["id"] = item["id"]
        return index, result

    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="apison-agent") as pool:
        futures = [pool.submit(run_one, index, item) for index, item in enumerate(normalized)]
        for future in as_completed(futures):
            index, result = future.result()
            results[index] = result

    completed = [item for item in results if item is not None]
    return {
        "success": all(item.get("success", False) for item in completed),
        "parallel": True,
        "max_workers": worker_count,
        "task_count": len(normalized),
        "succeeded": sum(1 for item in completed if item.get("success")),
        "failed": sum(1 for item in completed if not item.get("success")),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "results": completed,
    }


def _parse_review(text: str) -> dict:
    original = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", original, re.S)
    candidates = [fenced.group(1), original] if fenced else [original]
    decoder = json.JSONDecoder()
    data = None
    while candidates and data is None:
        candidate = candidates.pop(0).strip()
        try:
            decoded = json.loads(candidate)
            if isinstance(decoded, dict) and "score" in decoded:
                data = decoded
                break
            if isinstance(decoded, str) and decoded != candidate:
                candidates.append(decoded)
        except (json.JSONDecodeError, TypeError):
            pass
        for match in re.finditer(r"\{", candidate):
            try:
                decoded, _ = decoder.raw_decode(candidate[match.start():])
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(decoded, dict) and "score" in decoded:
                data = decoded
                break
            if isinstance(decoded, str) and decoded != candidate:
                candidates.append(decoded)
    if data is None:
        score_match = re.search(r"[\"']?(?:score|评分)[\"']?\s*[:：]\s*(\d{1,3})", text, re.I)
        return {"score": min(int(score_match.group(1)), 100) if score_match else None,
                "summary": text.strip(), "issues": [], "suggestions": []}
    score = data.get("score")
    if isinstance(score, (int, float)):
        score = max(0, min(int(score), 100))
    else:
        score = None
    return {
        "score": score,
        "summary": str(data.get("summary", "")),
        "issues": data.get("issues", []) if isinstance(data.get("issues", []), list) else [],
        "suggestions": data.get("suggestions", []) if isinstance(data.get("suggestions", []), list) else [],
    }


def review_results(
    items: list[dict[str, Any]],
    rubric: str,
    provider: str | None = None,
    model: str | None = None,
    max_workers: int = 4,
    timeout: int = 90,
) -> dict:
    """Have independent reviewer agents score outputs concurrently."""
    if not items:
        raise ValueError("items 至少需要包含一个待评审结果")
    if len(items) > 16:
        raise ValueError("单批最多支持 16 个评审项")
    rubric = rubric.strip() or "正确性、完整性、可维护性、与任务要求的一致性"

    review_tasks = []
    for index, item in enumerate(items):
        item_id = str(item.get("id") or f"result-{index + 1}")
        original_task = str(item.get("task", "")).strip()
        result_text = str(item.get("result", "")).strip()
        if not result_text:
            raise ValueError(f"评审项 {item_id} 缺少 result")
        prompt = (
            "你是独立质量评审员。请审查以下交付结果。\n\n"
            f"原任务：\n{original_task}\n\n交付结果：\n{result_text}\n\n"
            f"评分标准：{rubric}\n\n"
            "只返回 JSON："
            '{"score":0到100的整数,"summary":"一句话结论",'
            '"issues":["具体问题"],"suggestions":["具体修改建议"]}'
        )
        review_tasks.append({
            "id": item_id,
            "task": prompt,
            "provider": provider,
            "model": model,
            "system_prompt": "你是严格、公正的交付质量评审员。不得迎合被评审结果。",
            "timeout": timeout,
        })

    batch = delegate_tasks(review_tasks, max_workers=max_workers)
    reviews = []
    for result in batch["results"]:
        parsed = _parse_review(result.get("result", "")) if result.get("success") else {
            "score": None, "summary": result.get("error", "评审失败"), "issues": [], "suggestions": []
        }
        reviews.append({
            "id": result["id"],
            "success": result.get("success", False),
            "provider": result.get("provider"),
            "model": result.get("model"),
            **parsed,
            "usage": result.get("usage", {}),
            "elapsed_ms": result.get("elapsed_ms", 0),
        })

    scores = [item["score"] for item in reviews if item["score"] is not None]
    return {
        "success": all(item["success"] for item in reviews),
        "parallel": True,
        "review_count": len(reviews),
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "elapsed_ms": batch["elapsed_ms"],
        "reviews": reviews,
    }
