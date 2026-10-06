"""运行时配置。所有可调项集中在环境变量里解析，便于自部署。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "AI 测试报告助手"
APP_VERSION = "2.0.0"

DEFAULT_INSTRUCTION = "生成测试总结、风险分析、缺陷归纳和下一步建议。"

KNOWN_PROVIDERS = {
    "api.deepseek.com": "DeepSeek",
    "dashscope.aliyuncs.com": "阿里云百炼",
    "api.openai.com": "OpenAI",
    "api.moonshot.cn": "Moonshot",
    "open.bigmodel.cn": "智谱 AI",
    "api.siliconflow.cn": "SiliconFlow",
}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    base_url: str
    model: str
    temperature: float
    timeout: float
    max_retries: int

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def provider(self) -> str:
        """从 base_url 推断服务商标签，仅用于界面展示。"""
        host = urlparse(self.base_url).netloc or self.base_url
        host = host.split("@")[-1].split(":")[0]
        return KNOWN_PROVIDERS.get(host, host or "自定义")


def llm_settings(model: str | None = None, temperature: float | None = None) -> LLMSettings:
    base = os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
    chosen = (model or os.getenv("LLM_MODEL", "deepseek-chat")).strip() or "deepseek-chat"
    return LLMSettings(
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        base_url=base or "https://api.deepseek.com",
        model=chosen,
        temperature=0.2 if temperature is None else temperature,
        timeout=_env_float("LLM_TIMEOUT", 120.0),
        max_retries=max(0, _env_int("LLM_MAX_RETRIES", 2)),
    )


def available_models() -> list[str]:
    """可选模型列表：来自 .env，逗号分隔。首个为默认。"""
    raw = os.getenv("LLM_MODELS", "").strip()
    models = [item.strip() for item in raw.split(",") if item.strip()]
    default = os.getenv("LLM_MODEL", "deepseek-chat").strip() or "deepseek-chat"
    if default not in models:
        models.insert(0, default)
    return models


def data_dir() -> Path:
    configured = os.getenv("DATA_DIR", "").strip()
    path = Path(configured).expanduser() if configured else BASE_DIR / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "reports.db"


def legacy_static_dir() -> Path:
    return BASE_DIR / "static"


def spa_dir() -> Path:
    """Vite 构建产物目录。"""
    return BASE_DIR / "frontend" / "dist"
