import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="AI Test Report Assistant", version="1.0.0")
BASE_DIR = Path(__file__).parent


class AnalyzeRequest(BaseModel):
    test_data: str = Field(..., min_length=1, description="测试结果文本或JSON")
    instruction: str = Field(
        default="生成测试总结、风险分析、缺陷归纳和下一步建议。",
        description="额外分析要求",
    )


class AnalyzeResponse(BaseModel):
    report: str
    model: str


def get_config():
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("LLM_MODEL", "deepseek-chat")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="未配置 LLM_API_KEY。请复制 .env.example 为 .env 并填写 API Key。",
        )
    return api_key, base_url, model


SYSTEM_PROMPT = """你是一名企业级软件测试分析助手。
你的任务是分析测试执行数据，输出结构化、可执行的测试报告。
必须：
1. 区分事实数据与推断；
2. 优先关注P0/P1、高风险模块、阻塞项；
3. 给出通过率、失败率等可计算指标；
4. 不虚构输入中不存在的缺陷或业务事实；
5. 最终输出包含：测试概况、关键指标、主要缺陷/风险、风险判断依据、建议与下一步。
使用简洁的中文 Markdown。"""


async def call_llm(user_prompt: str):
    api_key, base_url, model = get_config()
    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="大模型 API 请求超时")
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:1000]
        raise HTTPException(
            status_code=502,
            detail=f"大模型 API 返回错误：{exc.response.status_code} {detail}",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"大模型 API 网络请求失败：{exc}")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="大模型返回结构异常，请检查模型接口兼容性。")


@app.get("/")
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    try:
        parsed: Any = json.loads(req.test_data)
        normalized = json.dumps(parsed, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        normalized = req.test_data

    user_prompt = f"""请分析以下软件测试数据。

【测试数据】
{normalized}

【额外要求】
{req.instruction}

请不要编造数据；能计算的指标请直接计算。"""
    report = await call_llm(user_prompt)
    _, _, model = get_config()
    return AnalyzeResponse(report=report, model=model)
