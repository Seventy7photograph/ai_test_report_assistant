"""运行时配置。所有可调项集中在环境变量里解析，便于自部署。"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
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


def provider_label(host: str) -> str:
    """把 base_url 的主机名翻成界面能读的服务商标签。

    自建/本地部署时主机名往往就是一个 IP，直接显示 127.0.0.1 没有信息量。
    """

    if not host:
        return "自定义"
    if host in KNOWN_PROVIDERS:
        return KNOWN_PROVIDERS[host]
    if host == "localhost" or host.endswith(".local"):
        return "本地服务"
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return host
    if address.is_loopback or address.is_private or address.is_link_local:
        return "本地服务"
    return host


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


def _env_ratio(name: str, default: float) -> float:
    """比例型阈值：夹在 0–1。写 `5` 或 `-1` 都不能把判定搞乱。"""

    value = _env_float(name, default)
    return min(max(value, 0.0), 1.0)


THRESHOLD_FIELDS = ("fail_rate", "blocked_rate", "execution_floor", "pass_line")


@dataclass(frozen=True)
class VerdictThresholds:
    """发版判定的阈值。不同业务的发版标准差别很大，所以不写死在规则里。"""

    fail_rate: float = 0.05
    blocked_rate: float = 0.05
    execution_floor: float = 0.9
    pass_line: float = 0.95

    def as_dict(self) -> dict[str, float]:
        return {key: float(getattr(self, key)) for key in THRESHOLD_FIELDS}


def saved_overrides() -> dict[str, Any]:
    """界面保存的覆盖项。

    延迟导入 store：store 需要 config 的路径解析，导入期不能反向依赖。
    存档坏掉时回落到 .env，而不是让整个服务起不来。
    """

    try:
        from . import store

        return store.load_settings()
    except Exception:
        return {}


def env_defaults() -> dict[str, Any]:
    """后端 .env 提供的默认值，也是界面「留空即回落」的目标。"""

    return {
        "api_key": os.getenv("LLM_API_KEY", "").strip(),
        "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
        or "https://api.deepseek.com",
        "model": os.getenv("LLM_MODEL", "deepseek-chat").strip() or "deepseek-chat",
        "models": [item.strip() for item in os.getenv("LLM_MODELS", "").split(",") if item.strip()],
        "temperature": 0.2,
        "timeout": _env_float("LLM_TIMEOUT", 120.0),
        "max_retries": max(0, _env_int("LLM_MAX_RETRIES", 2)),
        "thresholds": {
            "fail_rate": _env_ratio("VERDICT_FAIL_RATE", 0.05),
            "blocked_rate": _env_ratio("VERDICT_BLOCKED_RATE", 0.05),
            "execution_floor": _env_ratio("VERDICT_EXECUTION_FLOOR", 0.9),
            "pass_line": _env_ratio("VERDICT_PASS_LINE", 0.95),
        },
    }


def verdict_thresholds() -> VerdictThresholds:
    """发版判定阈值：界面保存的优先，逐项回落到 .env。"""

    merged = dict(env_defaults()["thresholds"])
    saved = saved_overrides().get("thresholds")
    if isinstance(saved, dict):
        for key in THRESHOLD_FIELDS:
            value = saved.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                merged[key] = min(max(float(value), 0.0), 1.0)
    return VerdictThresholds(**merged)


def _pick(saved: dict[str, Any], key: str, fallback: Any) -> Any:
    value = saved.get(key)
    if value is None or value == "" or value == []:
        return fallback
    return value


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
        return provider_label(host)


def llm_settings(model: str | None = None, temperature: float | None = None) -> LLMSettings:
    """生效配置：界面保存的覆盖项优先，缺失项回落 .env。

    两条路并存 —— 从没保存过任何配置时，行为与「只有 .env」完全一致。
    """

    saved = saved_overrides()
    defaults = env_defaults()

    base = str(_pick(saved, "base_url", defaults["base_url"])).strip().rstrip("/")
    default_model = str(_pick(saved, "model", defaults["model"])).strip() or "deepseek-chat"
    chosen = (model or default_model).strip() or "deepseek-chat"

    if temperature is not None:
        resolved_temperature = temperature
    else:
        try:
            resolved_temperature = float(_pick(saved, "temperature", defaults["temperature"]))
        except (TypeError, ValueError):
            resolved_temperature = float(defaults["temperature"])

    try:
        timeout = float(_pick(saved, "timeout", defaults["timeout"]))
    except (TypeError, ValueError):
        timeout = float(defaults["timeout"])

    try:
        retries = max(0, int(_pick(saved, "max_retries", defaults["max_retries"])))
    except (TypeError, ValueError):
        retries = int(defaults["max_retries"])

    return LLMSettings(
        api_key=str(_pick(saved, "api_key", defaults["api_key"])).strip(),
        base_url=base or "https://api.deepseek.com",
        model=chosen,
        temperature=resolved_temperature,
        timeout=timeout,
        max_retries=retries,
    )


def available_models() -> list[str]:
    """可选模型列表：界面保存的优先，否则用 .env 的 LLM_MODELS。首个为默认。"""

    saved = saved_overrides()
    defaults = env_defaults()
    raw = _pick(saved, "models", defaults["models"])
    models = [str(item).strip() for item in raw if str(item).strip()] if isinstance(raw, list) else []
    default = str(_pick(saved, "model", defaults["model"])).strip() or "deepseek-chat"
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
