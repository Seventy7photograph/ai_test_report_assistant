"""OpenAI-compatible Chat Completions 客户端。

只依赖 /chat/completions 这一个约定，因此 DeepSeek、Qwen、OpenAI、
Moonshot、SiliconFlow 等兼容服务都可以直接换 base_url 使用。
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator

import httpx
from fastapi import HTTPException

from .config import LLMSettings
from .prompts import SYSTEM_PROMPT

_RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def _endpoint(settings: LLMSettings) -> str:
    return f"{settings.base_url}/chat/completions"


def _headers(settings: LLMSettings) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }


def _payload(settings: LLMSettings, user_prompt: str, stream: bool = False) -> dict[str, Any]:
    return {
        "model": settings.model,
        "temperature": settings.temperature,
        "stream": stream,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }


def _require_key(settings: LLMSettings) -> None:
    if not settings.configured:
        raise HTTPException(
            status_code=503,
            detail="未配置 LLM_API_KEY。请复制 .env.example 为 .env 并填写 API Key。",
        )


def _http_error(exc: httpx.HTTPStatusError) -> HTTPException:
    status = exc.response.status_code
    body = exc.response.text[:600]
    hints = {
        401: "API Key 无效或已过期。",
        402: "账户额度不足。",
        403: "该 Key 无权访问此模型。",
        404: "接口地址或模型名不正确，请检查 LLM_BASE_URL 与 LLM_MODEL。",
        429: "请求过于频繁，已被服务方限流。",
    }
    hint = hints.get(status, "模型服务返回错误。")
    return HTTPException(status_code=502, detail=f"{hint}（{status}）{body}")


async def _request_with_retry(
    settings: LLMSettings, user_prompt: str
) -> httpx.Response:
    """带退避重试的普通（非流式）请求。"""

    last_error: Exception | None = None
    attempts = settings.max_retries + 1

    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.timeout) as client:
                response = await client.post(
                    _endpoint(settings),
                    headers=_headers(settings),
                    json=_payload(settings, user_prompt),
                )
                if response.status_code in _RETRY_STATUS and attempt < attempts - 1:
                    raise httpx.HTTPStatusError(
                        "retryable", request=response.request, response=response
                    )
                response.raise_for_status()
                return response
        except httpx.TimeoutException as exc:
            last_error = exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in _RETRY_STATUS and attempt < attempts - 1:
                last_error = exc
            else:
                raise _http_error(exc) from exc
        except httpx.HTTPError as exc:
            last_error = exc

        if attempt < attempts - 1:
            await asyncio.sleep(0.6 * (2**attempt))

    if isinstance(last_error, httpx.TimeoutException):
        raise HTTPException(status_code=504, detail=f"大模型 API 请求超时（{settings.timeout:.0f}s）。")
    if isinstance(last_error, httpx.HTTPStatusError):
        raise _http_error(last_error)
    raise HTTPException(status_code=502, detail=f"大模型 API 网络请求失败：{last_error}")


def _extract_content(data: Any) -> str:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502, detail="大模型返回结构异常，请检查模型接口兼容性。"
        ) from exc

    content = message.get("content")
    if isinstance(content, list):
        # 部分服务返回分段内容
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    if not isinstance(content, str) or not content.strip():
        raise HTTPException(status_code=502, detail="大模型返回了空内容。")
    return content


async def complete(user_prompt: str, settings: LLMSettings) -> tuple[str, dict[str, Any] | None]:
    """一次性生成，返回 (正文, usage)。"""

    _require_key(settings)
    response = await _request_with_retry(settings, user_prompt)
    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="大模型返回的不是合法 JSON。") from exc
    return _extract_content(data), data.get("usage")


async def stream(user_prompt: str, settings: LLMSettings) -> AsyncIterator[str]:
    """流式生成。逐段产出 delta 文本。"""

    _require_key(settings)
    attempts = settings.max_retries + 1

    for attempt in range(attempts):
        emitted = False
        try:
            async with httpx.AsyncClient(timeout=settings.timeout) as client:
                async with client.stream(
                    "POST",
                    _endpoint(settings),
                    headers=_headers(settings),
                    json=_payload(settings, user_prompt, stream=True),
                ) as response:
                    if response.status_code in _RETRY_STATUS and attempt < attempts - 1:
                        await response.aread()
                        await asyncio.sleep(0.6 * (2**attempt))
                        continue
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        await response.aread()
                        raise _http_error(exc) from exc

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            return
                        try:
                            payload = json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
                        try:
                            delta = payload["choices"][0]["delta"].get("content")
                        except (KeyError, IndexError, TypeError, AttributeError):
                            continue
                        if delta:
                            emitted = True
                            yield delta
                    return
        except httpx.TimeoutException as exc:
            if emitted:
                raise HTTPException(status_code=504, detail="流式响应中断：模型服务超时。") from exc
        except httpx.HTTPError as exc:
            if emitted or attempt >= attempts - 1:
                raise HTTPException(status_code=502, detail=f"模型服务连接失败：{exc}") from exc

        await asyncio.sleep(0.6 * (2**attempt))


async def probe(settings: LLMSettings) -> tuple[int, str]:
    """真实探活：用最小代价的请求确认服务可用，并返回延迟。"""

    _require_key(settings)
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=min(settings.timeout, 30.0)) as client:
        try:
            response = await client.post(
                _endpoint(settings),
                headers=_headers(settings),
                json={
                    "model": settings.model,
                    "temperature": 0,
                    "max_tokens": 8,
                    "messages": [
                        {"role": "system", "content": "你是一个连通性测试端点。"},
                        {"role": "user", "content": "回复：ok"},
                    ],
                },
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="探活超时，模型服务未在 30 秒内响应。") from exc
        except httpx.HTTPStatusError as exc:
            raise _http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"无法连接模型服务：{exc}") from exc

    latency = int((time.perf_counter() - started) * 1000)
    try:
        reply = _extract_content(response.json())
    except HTTPException:
        reply = "服务已响应，但返回结构无法解析。"
    return latency, reply.strip()[:120]
