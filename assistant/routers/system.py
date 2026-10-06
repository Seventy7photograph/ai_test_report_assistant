"""系统状态、模型探活、样例数据。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import (
    APP_NAME,
    APP_VERSION,
    available_models,
    db_path,
    llm_settings,
    spa_dir,
)
from ..llm import probe
from ..samples import SAMPLES
from ..schemas import LLMTestResponse, SampleDataset, StatusResponse
from .. import store

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/system/status", response_model=StatusResponse)
async def status() -> StatusResponse:
    settings = llm_settings()
    try:
        count = store.count_reports()
    except Exception:  # 存档不可用不应拖垮整个界面
        count = 0

    return StatusResponse(
        app_name=APP_NAME,
        app_version=APP_VERSION,
        llm_configured=settings.configured,
        provider=settings.provider,
        base_url=settings.base_url,
        model=settings.model,
        models=available_models(),
        temperature=settings.temperature,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
        storage_backend="SQLite",
        storage_path=str(db_path()),
        report_count=count,
        frontend_built=spa_dir().is_dir(),
    )


@router.post("/system/llm-test", response_model=LLMTestResponse)
async def llm_test() -> LLMTestResponse:
    settings = llm_settings()
    if not settings.configured:
        raise HTTPException(
            status_code=503,
            detail="未配置 LLM_API_KEY。请复制 .env.example 为 .env 并填写 API Key。",
        )
    latency, reply = await probe(settings)
    return LLMTestResponse(
        ok=True,
        model=settings.model,
        provider=settings.provider,
        latency_ms=latency,
        message=reply or "服务正常",
    )


@router.get("/samples", response_model=list[SampleDataset])
async def samples() -> list[SampleDataset]:
    return SAMPLES
