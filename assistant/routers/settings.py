"""界面可编辑的模型配置。

优先级：界面保存的覆盖项 > 后端 .env 默认。
清空某一项即回落到 .env；「恢复默认」清空全部覆盖项，
等价于回到只有 .env 的状态，所以后端默认配置始终可用。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import store
from ..config import available_models, env_defaults, llm_settings, saved_overrides
from ..llm import probe
from ..schemas import (
    LLMSettingsUpdate,
    LLMSettingsView,
    LLMTestResponse,
    SettingsTestRequest,
)

router = APIRouter(prefix="/api", tags=["settings"])

_FIELDS = ("base_url", "model", "models", "temperature", "timeout", "max_retries", "api_key")


def _mask(secret: str) -> str | None:
    """只露尾巴。前缀同样会泄露信息，能不给就不给。"""

    if not secret:
        return None
    if len(secret) <= 4:
        return "*" * len(secret)
    return f"{'*' * 6}{secret[-4:]}"


def _view() -> LLMSettingsView:
    settings = llm_settings()
    saved = saved_overrides()
    defaults = env_defaults()
    stored_key = str(saved.get("api_key") or "")

    def source(key: str) -> str:
        value = saved.get(key)
        return "saved" if value not in (None, "", []) else "env"

    visible_env = {key: value for key, value in defaults.items() if key != "api_key"}

    return LLMSettingsView(
        base_url=settings.base_url,
        model=settings.model,
        models=available_models(),
        temperature=settings.temperature,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
        api_key_set=settings.configured,
        api_key_masked=_mask(stored_key),
        api_key_stored=bool(stored_key),
        sources={key: source(key) for key in _FIELDS},
        env={**visible_env, "api_key_set": bool(defaults["api_key"])},
    )


@router.get("/settings", response_model=LLMSettingsView)
async def read_settings() -> LLMSettingsView:
    return _view()


@router.put("/settings", response_model=LLMSettingsView)
async def update_settings(payload: LLMSettingsUpdate) -> LLMSettingsView:
    """整体替换覆盖项：留空 = 该项回落 .env 默认。

    api_key 不回显，所以不传就保持原样，要清除得置 clear_api_key。
    """

    values: dict[str, object] = {
        "base_url": (payload.base_url or "").strip(),
        "model": (payload.model or "").strip(),
        "models": [item.strip() for item in (payload.models or []) if item.strip()],
        "temperature": payload.temperature,
        "timeout": payload.timeout,
        "max_retries": payload.max_retries,
    }

    if payload.clear_api_key:
        values["api_key"] = ""
    elif payload.api_key and payload.api_key.strip():
        values["api_key"] = payload.api_key.strip()

    store.save_settings(values)
    return _view()


@router.delete("/settings", response_model=LLMSettingsView)
async def reset_settings() -> LLMSettingsView:
    """清空全部覆盖项，回到 .env 默认。"""

    store.clear_settings()
    return _view()


@router.post("/settings/test", response_model=LLMTestResponse)
async def test_settings(payload: SettingsTestRequest | None = None) -> LLMTestResponse:
    """用「当前生效配置 + 本次表单改动」探活，未保存也能先验证。

    api_key 留空时沿用已保存或 .env 里的 Key，不必为了测试重新输入。
    """

    base = llm_settings()
    candidate_key = (payload.api_key or "").strip() if payload else ""
    candidate_base = (payload.base_url or "").strip().rstrip("/") if payload else ""
    candidate_model = (payload.model or "").strip() if payload else ""

    resolved = base.__class__(
        api_key=candidate_key or base.api_key,
        base_url=candidate_base or base.base_url,
        model=candidate_model or base.model,
        temperature=base.temperature,
        timeout=payload.timeout if payload and payload.timeout else base.timeout,
        max_retries=base.max_retries,
    )

    if not resolved.configured:
        raise HTTPException(
            status_code=503,
            detail="未配置 API Key。请在下方填入，或复制 .env.example 为 .env 并填写 LLM_API_KEY。",
        )

    latency, reply = await probe(resolved)
    return LLMTestResponse(
        ok=True,
        model=resolved.model,
        provider=resolved.provider,
        latency_ms=latency,
        message=reply or "服务正常",
    )
