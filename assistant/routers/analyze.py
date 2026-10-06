"""分析接口：指标计算、报告生成、流式生成。"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from .. import store
from ..config import llm_settings
from ..llm import complete, stream as llm_stream
from ..metrics import compute_metrics
from ..prompts import build_user_prompt
from ..schemas import AnalyzeRequest, AnalyzeResponse, MetricsRequest, MetricsResult

router = APIRouter(prefix="/api", tags=["analyze"])


def _prepare(req: AnalyzeRequest) -> tuple[MetricsResult, str]:
    """先算指标，再把原始数据整理成便于模型阅读的形式。"""

    result = compute_metrics(req.test_data)
    normalized = req.test_data
    try:
        normalized = json.dumps(json.loads(req.test_data), ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, TypeError):
        pass
    return result, normalized


def _default_title(req: AnalyzeRequest, result: MetricsResult) -> str:
    if req.title and req.title.strip():
        return req.title.strip()
    if result.version:
        return f"{result.version} 测试报告"
    return "未命名测试报告"


@router.post("/metrics", response_model=MetricsResult)
async def metrics(req: MetricsRequest) -> MetricsResult:
    """纯计算，不调用模型。用于界面上实时读数。"""

    return compute_metrics(req.test_data)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    result, normalized = _prepare(req)
    settings = llm_settings(model=req.model, temperature=req.temperature)
    user_prompt = build_user_prompt(result, normalized, req.instruction)

    started = time.perf_counter()
    report, usage = await complete(user_prompt, settings)
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    created_at = store.utc_now_iso()
    report_id: str | None = None

    if req.save:
        try:
            report_id = store.save_report(
                {
                    "created_at": created_at,
                    "title": _default_title(req, result),
                    "version": result.version,
                    "model": settings.model,
                    "provider": settings.provider,
                    "instruction": req.instruction,
                    "source_data": req.test_data,
                    "report": report,
                    "metrics": result.metrics.model_dump() if result.metrics else None,
                    "defects": [d.model_dump() for d in result.defects],
                    "usage": usage,
                    "warnings": result.warnings,
                    "elapsed_ms": elapsed_ms,
                }
            )
        except Exception as exc:  # 存档失败不应该让报告丢失
            result.warnings.append(f"存档写入失败：{exc}")

    return AnalyzeResponse(
        id=report_id,
        report=report,
        model=settings.model,
        provider=settings.provider,
        metrics=result.metrics,
        warnings=result.warnings,
        version=result.version,
        created_at=created_at,
        elapsed_ms=elapsed_ms,
        usage=usage,
    )


def _sse(event: str, payload: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest) -> StreamingResponse:
    """流式生成。事件顺序：meta → metrics → delta* → done（或 error）。"""

    result, normalized = _prepare(req)
    settings = llm_settings(model=req.model, temperature=req.temperature)
    user_prompt = build_user_prompt(result, normalized, req.instruction)
    created_at = store.utc_now_iso()

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "model": settings.model,
                "provider": settings.provider,
                "created_at": created_at,
                "version": result.version,
                "warnings": result.warnings,
            },
        )
        if result.metrics:
            yield _sse("metrics", result.metrics.model_dump())

        started = time.perf_counter()
        chunks: list[str] = []
        try:
            async for delta in llm_stream(user_prompt, settings):
                chunks.append(delta)
                yield _sse("delta", {"text": delta})
        except HTTPException as exc:
            yield _sse("error", {"detail": exc.detail, "status": exc.status_code})
            return
        except Exception as exc:  # 兜底，避免流悬挂
            yield _sse("error", {"detail": f"生成中断：{exc}", "status": 500})
            return

        report = "".join(chunks)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        report_id: str | None = None
        warnings = list(result.warnings)

        if req.save and report.strip():
            try:
                report_id = store.save_report(
                    {
                        "created_at": created_at,
                        "title": _default_title(req, result),
                        "version": result.version,
                        "model": settings.model,
                        "provider": settings.provider,
                        "instruction": req.instruction,
                        "source_data": req.test_data,
                        "report": report,
                        "metrics": result.metrics.model_dump() if result.metrics else None,
                        "defects": [d.model_dump() for d in result.defects],
                        "usage": None,
                        "warnings": warnings,
                        "elapsed_ms": elapsed_ms,
                    }
                )
            except Exception as exc:
                warnings.append(f"存档写入失败：{exc}")

        yield _sse(
            "done",
            {
                "id": report_id,
                "elapsed_ms": elapsed_ms,
                "warnings": warnings,
                "saved": bool(report_id),
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
