"""后端契约测试。

重点覆盖：确定性指标计算（产品定位的核心）、存档读写、错误路径。
不依赖真实模型服务——凡是需要模型的地方都用错误路径或纯计算接口覆盖。
"""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app import app
from assistant.config import LLMSettings
from assistant.metrics import compute_metrics, normalize_priority, normalize_status

client = TestClient(app)


# ------------------------------------------------------------------ 基础

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "AI 测试报告助手" in response.text


# ------------------------------------------------------------------ 指标

def test_metrics_basic_sample():
    payload = {
        "version": "4.2.0",
        "total_cases": 500,
        "passed": 468,
        "failed": 22,
        "blocked": 10,
        "defects": [
            {"id": "BUG-001", "priority": "P0", "module": "案件管理", "status": "open"},
            {"id": "BUG-002", "priority": "P1", "module": "权限管理", "status": "open"},
            {"id": "BUG-003", "priority": "P1", "module": "接口", "status": "resolved"},
        ],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    metrics = result.metrics
    assert metrics is not None
    assert result.version == "4.2.0"
    assert metrics.total == 500
    assert metrics.passed == 468
    assert abs(metrics.pass_rate - 0.936) < 1e-9
    assert abs(metrics.execution_rate - 0.98) < 1e-9
    assert metrics.defects_total == 3
    assert metrics.defects_open == 2
    assert metrics.open_p0 == 1
    assert metrics.verdict == "reject"
    assert any("P0" in reason for reason in metrics.verdict_reasons)


def test_metrics_accepts_chinese_keys_and_severity_aliases():
    payload = {
        "版本": "4.3.0",
        "用例总数": 640,
        "通过": 634,
        "失败": 4,
        "阻塞": 2,
        "缺陷": [
            {"编号": "BUG-201", "优先级": "严重", "模块": "案件管理", "状态": "已修复"},
            {"编号": "BUG-202", "severity": "high", "component": "搜索", "status": "closed"},
        ],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    metrics = result.metrics
    assert metrics is not None
    assert metrics.total == 640
    assert metrics.defects_total == 2
    assert metrics.defects_open == 0
    assert metrics.verdict == "pass"
    assert [item.key for item in metrics.by_priority] == ["P1"]


def test_metrics_derives_total_when_missing():
    result = compute_metrics(json.dumps({"passed": 90, "failed": 8, "blocked": 2}))
    assert result.metrics is not None
    assert result.metrics.total == 100
    assert result.metrics.verdict == "conditional"
    assert result.warnings


def test_metrics_reports_plain_text_honestly():
    result = compute_metrics("用例总数 120，通过 96，失败 19，阻塞 5。")
    assert result.metrics is None
    assert result.source_format == "text"
    assert result.warnings


def test_metrics_extracts_json_from_noisy_text():
    raw = '执行日志开始\n{"total_cases": 10, "passed": 9, "failed": 1}\n执行日志结束'
    result = compute_metrics(raw)
    assert result.metrics is not None
    assert result.metrics.total == 10
    assert result.warnings


def test_priority_and_status_normalisation():
    assert normalize_priority("P0") == "P0"
    assert normalize_priority("致命") == "P0"
    assert normalize_priority("high") == "P1"
    assert normalize_priority(None) is None
    assert normalize_status("未关闭") == "open"
    assert normalize_status("已关闭") == "resolved"
    assert normalize_status("Won't Fix") == "rejected"


def test_metrics_endpoint():
    response = client.post("/api/metrics", json={"test_data": '{"total_cases": 4, "passed": 4}'})
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["total"] == 4
    assert body["metrics"]["verdict"] == "pass"


# ------------------------------------------------------------------ 系统

def test_status_endpoint_hides_secrets():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["app_version"]
    assert "api_key" not in json.dumps(body).lower()
    assert isinstance(body["models"], list)


def test_samples_endpoint():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 3
    assert {sample["id"] for sample in samples} >= {"basic", "text"}


def test_analyze_without_key_returns_actionable_error(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    response = client.post("/api/analyze", json={"test_data": '{"total_cases": 1, "passed": 1}'})
    assert response.status_code == 503
    assert "LLM_API_KEY" in response.json()["detail"]


# ------------------------------------------------------------------ 存档

def _seed_report() -> str:
    from assistant import store

    return store.save_report(
        {
            "title": "4.2.0 测试报告",
            "version": "4.2.0",
            "model": "test-model",
            "provider": "Test",
            "instruction": "测试",
            "source_data": '{"total_cases": 10, "passed": 9, "failed": 1}',
            "report": "## 测试概况\n本轮共执行 10 条用例。",
            "metrics": {
                "total": 10, "passed": 9, "failed": 1, "blocked": 0, "skipped": 0,
                "pass_rate": 0.9, "fail_rate": 0.1, "execution_rate": 1.0,
                "defects_total": 0, "defects_open": 0, "open_p0": 0, "open_p1": 0,
                "by_priority": [], "by_status": [], "by_module": [],
                "verdict": "conditional", "verdict_label": "有条件通过",
                "verdict_reasons": ["失败率 10.0% 高于 5% 阈值"],
            },
            "defects": [],
            "elapsed_ms": 1200,
        }
    )


def test_report_lifecycle_and_export():
    report_id = _seed_report()

    listing = client.get("/api/reports", params={"limit": 5})
    assert listing.status_code == 200
    assert any(item["id"] == report_id for item in listing.json()["items"])

    detail = client.get(f"/api/reports/{report_id}")
    assert detail.status_code == 200
    assert detail.json()["report"].startswith("## 测试概况")

    for fmt, marker in (("md", "# "), ("html", "<!doctype html>"), ("json", '"id"')):
        export = client.get(f"/api/reports/{report_id}/export", params={"format": fmt})
        assert export.status_code == 200, fmt
        assert marker in export.text, fmt
        assert "attachment" in export.headers["content-disposition"]

    docx = client.get(f"/api/reports/{report_id}/export", params={"format": "docx"})
    assert docx.status_code == 200
    assert docx.content[:2] == b"PK"

    assert client.delete(f"/api/reports/{report_id}").status_code == 200
    assert client.get(f"/api/reports/{report_id}").status_code == 404


def test_trends_include_saved_report():
    report_id = _seed_report()
    response = client.get("/api/trends", params={"limit": 10})
    assert response.status_code == 200
    assert any(point["id"] == report_id for point in response.json())
    client.delete(f"/api/reports/{report_id}")


def test_report_filters():
    report_id = _seed_report()
    response = client.get("/api/reports", params={"q": "4.2.0", "verdict": "conditional"})
    assert response.status_code == 200
    assert any(item["id"] == report_id for item in response.json()["items"])
    client.delete(f"/api/reports/{report_id}")


def test_export_unknown_id_returns_404():
    assert client.get("/api/reports/does-not-exist/export").status_code == 404


@pytest.mark.parametrize("path", ["/api/reports", "/api/trends", "/api/system/status"])
def test_read_endpoints_are_available(path):
    assert client.get(path).status_code == 200

# ------------------------------------------------------------------ 生成（桩替模型）

def _fake_complete(report: str = "## 测试概况\n本轮共执行 10 条用例。"):
    async def _complete(prompt: str, settings):
        assert "系统计算结果" in prompt
        return report, {"prompt_tokens": 10, "completion_tokens": 5}

    return _complete


def test_analyze_saves_and_returns_metrics(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr("assistant.routers.analyze.complete", _fake_complete())

    response = client.post(
        "/api/analyze",
        json={"test_data": '{"version": "1.0.0", "total_cases": 10, "passed": 9, "failed": 1}'},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["total"] == 10
    assert body["model"]
    assert body["id"]

    detail = client.get(f"/api/reports/{body['id']}").json()
    assert detail["version"] == "1.0.0"
    assert detail["title"] == "1.0.0 测试报告"
    client.delete(f"/api/reports/{body['id']}")


def test_analyze_can_skip_archiving(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr("assistant.routers.analyze.complete", _fake_complete())

    response = client.post(
        "/api/analyze",
        json={"test_data": '{"total_cases": 2, "passed": 2}', "save": False},
    )
    assert response.status_code == 200
    assert response.json()["id"] is None


def test_stream_emits_ordered_events(monkeypatch):
    async def fake_stream(prompt: str, settings, usage_sink=None):
        for piece in ("## 测试概况\n", "本轮共执行 10 条用例。"):
            yield piece

    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr("assistant.routers.analyze.llm_stream", fake_stream)

    with client.stream(
        "POST",
        "/api/analyze/stream",
        json={"test_data": '{"total_cases": 10, "passed": 9, "failed": 1}'},
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    order = [body.index(f"event: {name}") for name in ("meta", "metrics", "delta", "done")]
    assert order == sorted(order)
    assert "本轮共执行 10 条用例。" in body

    report_id = body.rsplit('"id": "', 1)[1].split('"')[0]
    client.delete(f"/api/reports/{report_id}")


# ------------------------------------------------------------------ 网络

def test_local_model_endpoints_bypass_system_proxy():
    """本机与内网模型服务不能被系统代理劫持。

    Windows 上 httpx 会读取注册表里的代理设置，而它的 no_proxy 匹配不认识
    ProxyOverride 里的 `127.*` 通配，本机请求因此被送给代理，
    拿回一个空 body 的 502，界面只看到「模型服务返回错误。（502）」。
    """
    from assistant.llm import _client, _host_bypasses_proxy

    assert _host_bypasses_proxy("127.0.0.1") is True
    assert _host_bypasses_proxy("localhost") is True
    assert _host_bypasses_proxy("::1") is True
    assert _host_bypasses_proxy("192.168.1.20") is True
    assert _host_bypasses_proxy("ollama.local") is True
    assert _host_bypasses_proxy("api.deepseek.com") is False
    assert _host_bypasses_proxy(None) is False

    def settings_for(base_url: str) -> LLMSettings:
        return LLMSettings(
            api_key="test-key",
            base_url=base_url,
            model="test-model",
            temperature=0.2,
            timeout=5.0,
            max_retries=0,
        )

    async def check() -> None:
        async with _client(settings_for("http://127.0.0.1:8011")) as local:
            assert local.trust_env is False
        async with _client(settings_for("https://api.deepseek.com")) as remote:
            assert remote.trust_env is True

    asyncio.run(check())


def test_settings_follow_env_then_saved_then_reset(monkeypatch):
    """三种状态：只有 .env → 界面保存 → 恢复默认。"""
    monkeypatch.setenv("LLM_API_KEY", "env-key")
    monkeypatch.setenv("LLM_MODEL", "env-model")
    monkeypatch.setenv("LLM_BASE_URL", "https://env.example")
    client.delete("/api/settings")

    view = client.get("/api/settings").json()
    assert view["model"] == "env-model"
    assert view["base_url"] == "https://env.example"
    assert view["sources"]["model"] == "env"
    assert view["api_key_masked"] is None
    assert view["env"]["api_key_set"] is True
    assert "api_key" not in view["env"]  # 不回显明文 Key

    saved = client.put(
        "/api/settings",
        json={
            "base_url": "https://saved.example/v1/",
            "model": "saved-model",
            "models": ["saved-model", "other"],
            "temperature": 0.5,
            "timeout": 30,
            "max_retries": 1,
            "api_key": "sk-abcdefgh1234",
        },
    ).json()
    assert saved["base_url"] == "https://saved.example/v1"  # 末尾斜杠归一化
    assert saved["sources"]["model"] == "saved"
    assert saved["api_key_stored"] is True
    assert saved["api_key_masked"].endswith("1234")
    assert "abcdefgh" not in saved["api_key_masked"]

    assert client.get("/api/system/status").json()["model"] == "saved-model"

    reset = client.delete("/api/settings").json()
    assert reset["model"] == "env-model"
    assert reset["api_key_stored"] is False
    assert reset["sources"]["api_key"] == "env"


def test_settings_partial_update_keeps_key_and_supports_clear(monkeypatch):
    """改模型不能顺手把 Key 清掉；要清除必须显式。"""
    monkeypatch.setenv("LLM_API_KEY", "env-key")
    client.delete("/api/settings")

    client.put("/api/settings", json={"model": "m1", "api_key": "sk-first-9876"})
    assert client.get("/api/settings").json()["api_key_stored"] is True

    client.put("/api/settings", json={"model": "m2"})
    view = client.get("/api/settings").json()
    assert view["model"] == "m2"
    assert view["api_key_stored"] is True

    cleared = client.put("/api/settings", json={"clear_api_key": True}).json()
    assert cleared["api_key_stored"] is False
    assert cleared["api_key_set"] is True  # 回落到 .env 的 Key
    client.delete("/api/settings")


def test_settings_blank_field_falls_back_to_env(monkeypatch):
    """界面留空 = 该项回落 .env，而不是写进去一个空值。"""
    monkeypatch.setenv("LLM_MODEL", "env-model")
    monkeypatch.setenv("LLM_TIMEOUT", "77")
    client.delete("/api/settings")

    client.put("/api/settings", json={"model": "saved-model", "timeout": 12})
    assert client.get("/api/settings").json()["timeout"] == 12

    view = client.put("/api/settings", json={"model": "", "timeout": None}).json()
    assert view["model"] == "env-model"
    assert view["sources"]["model"] == "env"
    assert view["timeout"] == 77.0
    assert view["sources"]["timeout"] == "env"
    client.delete("/api/settings")


def test_analyze_uses_saved_settings(monkeypatch):
    """界面保存的配置要真的作用到调用上，而不是只改显示。"""
    monkeypatch.setenv("LLM_MODEL", "env-model")
    seen: dict[str, object] = {}

    async def fake_complete(prompt: str, settings):
        seen["model"] = settings.model
        seen["base_url"] = settings.base_url
        seen["temperature"] = settings.temperature
        return "## 测试概况\n接口可用。", None

    monkeypatch.setattr("assistant.routers.analyze.complete", fake_complete)

    try:
        client.put(
            "/api/settings",
            json={"model": "ui-model", "base_url": "https://ui.example/v1", "temperature": 0.9},
        )
        response = client.post(
            "/api/analyze",
            json={"test_data": '{"total_cases": 1, "passed": 1}', "save": False},
        )
        assert response.status_code == 200
        assert seen["model"] == "ui-model"
        assert seen["base_url"] == "https://ui.example/v1"
        assert seen["temperature"] == 0.9
    finally:
        client.delete("/api/settings")


# ------------------------------------------------------------------ 指标回归

def test_negated_statuses_count_as_open():
    """unresolved / not fixed / 未解决 这些否定式曾经被读成「已修复」，
    导致 open_p0 归零、发版闸门被放行。"""
    for label in ("unresolved", "not resolved", "not fixed", "unfixed", "未解决", "没修复", "尚未修复"):
        assert normalize_status(label) == "open", label
    # 肯定式仍然正确
    assert normalize_status("resolved") == "resolved"
    assert normalize_status("fixed") == "resolved"
    assert normalize_status("已关闭") == "resolved"

    payload = {
        "total_cases": 10,
        "passed": 10,
        "defects": [{"id": "BUG-1", "priority": "P0", "status": "unresolved"}],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.open_p0 == 1
    assert result.metrics.verdict == "reject"


def test_test_case_list_is_not_mistaken_for_defects():
    """用例清单同样有 id / status，不能被当成 40 条缺陷。"""
    payload = {
        "total_cases": 40,
        "passed": 40,
        "cases": [
            {"case_id": f"TC-{i}", "title": f"用例 {i}", "status": "passed", "steps": ["a", "b"]}
            for i in range(40)
        ],
        "defects": [],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.defects_total == 0
    assert result.metrics.verdict == "pass"


def test_duplicate_defect_ids_are_deduped():
    payload = {
        "total_cases": 10,
        "passed": 9,
        "failed": 1,
        "defects": [
            {"id": "BUG-1", "priority": "P1", "status": "open"},
            {"id": "bug-1", "priority": "P1", "status": "open"},
            {"id": "BUG-2", "priority": "P2", "status": "open"},
        ],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.defects_total == 2
    assert any("重复" in warning for warning in result.warnings)


def test_missing_defect_status_counts_as_open():
    """状态缺失时按未关闭处理：宁可拦错，也不放行没读到的缺陷。"""
    payload = {
        "total_cases": 10,
        "passed": 10,
        "defects": [{"id": "B1", "priority": "P0"}],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.defects_open == 1
    assert result.metrics.verdict == "reject"
    assert any("状态" in warning for warning in result.warnings)


def test_negative_case_counts_are_clamped():
    """负数计数曾经能算出 60% 通过率这种鬼话，现在按 0 处理并告警。"""
    payload = {"total_cases": -5, "passed": -3, "failed": -2}
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.total == 0
    assert result.metrics.passed == 0
    assert any("负数" in warning for warning in result.warnings)


def test_pass_reason_mentions_open_defects():
    payload = {
        "total_cases": 100,
        "passed": 100,
        "defects": [{"id": "B1", "priority": "P2", "status": "open"}],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.verdict == "pass"
    assert any("未关闭缺陷" in reason for reason in result.metrics.verdict_reasons)


def test_html_export_neutralises_injected_scripts_and_urls():
    """导出的 HTML 同源打开，正文里的脚本/危险链接不能可执行。"""
    import re as _re

    from assistant.exporters import to_html

    record = {
        "title": "<script>alert('t')</script>报告",
        "model": "m<script>alert('m')</script>",
        "report": (
            "正常正文\n\n"
            "<script>alert('xss')</script>\n\n"
            "<img src=x onerror=alert(1)>\n\n"
            "[链接](javascript:alert(2))\n\n"
            "[另一条](VBScript:msgbox)\n\n"
            "自动链接 <https://example.com>\n\n"
            "> 引用"
        ),
    }
    out = to_html(record)
    assert "<script" not in out
    assert _re.search(r"<[^>]*onerror", out) is None
    assert "javascript:" not in out.lower()
    assert "vbscript:" not in out.lower()
    assert 'href="https://example.com"' in out
    assert "&lt;script&gt;" in out


def test_html_export_sanitizes_by_whitelist():
    """白名单消毒：只留安全标签与属性，危险 scheme 与协议相对地址一律丢掉。"""
    from html.parser import HTMLParser

    from assistant.exporters import to_html

    record = {
        "title": "t",
        "model": "m",
        "report": (
            "[外面](//evil.example/x)\n\n"
            "[脚本](javascript:alert(1))\n\n"
            "[内网](/reports/1)\n\n"
            "[正常](https://ok.example)\n\n"
            "![图](data:text/html,x)\n\n"
            "**粗体**\n\n"
            "| A | B |\n| - | - |\n| 1 | 2 |\n\n"
            "```py\nprint(1)\n```\n"
        ),
    }
    out = to_html(record)
    body = out[out.index("<body"):out.index("</body>")]

    attributes: list[tuple[str, str, str | None]] = []

    class Collector(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attributes.extend((tag, name, value) for name, value in attrs)

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

    Collector().feed(body)

    values = " ".join(str(value) for _tag, _name, value in attributes).lower()
    assert "javascript" not in values
    assert "vbscript" not in values
    assert "data:" not in values
    assert "evil.example" not in values
    assert any(value == "https://ok.example" for _t, _n, value in attributes)
    assert any(value == "/reports/1" for _t, _n, value in attributes)
    assert not [item for item in attributes if item[1].lower().startswith("on")]

    # Markdown 的排版能力不能被消毒误伤
    assert "<strong>" in body
    assert "<table>" in body and "<td>2</td>" in body
    assert "<pre>" in body


def test_unrecognised_status_never_opens_the_gate():
    """读不出来的状态曾经既不算未关闭也不算已修复，被闸门当成已关闭放行。"""
    for label in ("in review", "fixing", "待复核", "待验证", "pending verification", "N/A", "？"):
        assert normalize_status(label) in ("open", "unknown"), label

    for label in ("in review", "fixing", "待复核", "pending verification", "N/A"):
        payload = {
            "total_cases": 10,
            "passed": 10,
            "defects": [{"id": "B1", "priority": "P0", "status": label}],
        }
        result = compute_metrics(json.dumps(payload, ensure_ascii=False))
        assert result.metrics is not None
        assert result.metrics.open_p0 == 1, label
        assert result.metrics.verdict == "reject", label

    # 明确标成已修复 / 已驳回的仍然放行
    assert normalize_status("已回归") == "resolved"
    assert normalize_status("回归通过") == "resolved"
    assert normalize_status("验证通过") == "resolved"
    assert normalize_status("Won't Fix") == "rejected"


def test_same_id_in_different_modules_is_not_deduped():
    """不同模块复用同一编号是常见做法，不能当成重复丢掉。"""
    payload = {
        "total_cases": 10,
        "passed": 10,
        "defects": [
            {"id": "1", "module": "支付", "priority": "P0", "status": "open"},
            {"id": "1", "module": "登录", "priority": "P1", "status": "open"},
        ],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.metrics is not None
    assert result.metrics.defects_total == 2
    assert result.metrics.open_p0 == 1
    assert result.metrics.open_p1 == 1


def test_prompt_carries_authoritative_defect_details():
    """缺陷明细要进"权威口径"，模型才不用自己数原始数据。"""
    from assistant.prompts import build_user_prompt

    payload = {
        "version": "9.1",
        "total_cases": 100,
        "passed": 98,
        "failed": 2,
        "defects": [
            {"id": "BUG-1", "priority": "P0", "module": "支付", "status": "in review"},
            {"id": "BUG-2", "priority": "P2", "module": "登录", "status": "resolved"},
        ],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    prompt = build_user_prompt(result, "{}", "重点分析")
    start = prompt.index("【系统计算结果")
    authoritative = prompt[start:prompt.index("【原始测试数据", start)]
    assert "BUG-1" in authoritative
    assert "支付" in authoritative
    assert "未关闭" in authoritative
    assert "已修复" in authoritative


def test_oversized_input_is_truncated_before_the_model(monkeypatch):
    """几 MB 的日志不能整段塞进 prompt，但指标仍按完整数据算。"""
    seen: dict[str, object] = {}

    async def fake_complete(prompt: str, settings):
        seen["prompt"] = prompt
        return "## 测试概况\nok", None

    monkeypatch.setattr("assistant.routers.analyze.complete", fake_complete)
    big = '{"total_cases": 5000, "passed": 4900, "failed": 100, "note": "' + ("x" * 40000) + '"}'
    response = client.post("/api/analyze", json={"test_data": big, "save": False})
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["total"] == 5000  # 指标基于完整数据
    assert any("截断" in warning for warning in body["warnings"])
    assert len(seen["prompt"]) < 25000


def test_provider_label_reads_naturally_for_local_hosts():
    from assistant.config import provider_label

    assert provider_label("api.deepseek.com") == "DeepSeek"
    assert provider_label("127.0.0.1") == "本地服务"
    assert provider_label("localhost") == "本地服务"
    assert provider_label("192.168.1.20") == "本地服务"
    assert provider_label("") == "自定义"


# ------------------------------------------------------------------ 判定阈值

def test_verdict_thresholds_are_configurable():
    """阈值可配置：同一份数据在严格标准下不能放行。"""
    from assistant.config import VerdictThresholds

    data = json.dumps({"total_cases": 1000, "passed": 998, "failed": 2, "blocked": 0})
    assert compute_metrics(data).metrics.verdict == "pass"

    strict = compute_metrics(data, VerdictThresholds(fail_rate=0.0))
    assert strict.metrics.verdict == "conditional"
    assert any("0.0% 阈值" in reason for reason in strict.metrics.verdict_reasons)


def test_execution_floor_blocks_pass():
    """执行率不达标不能给"建议发版"。"""
    from assistant.config import VerdictThresholds

    data = json.dumps({"total_cases": 100, "passed": 40, "failed": 0, "skipped": 60})
    result = compute_metrics(data).metrics
    assert result.verdict == "conditional"
    assert any("执行率" in reason and "下限" in reason for reason in result.verdict_reasons)

    relaxed = compute_metrics(data, VerdictThresholds(execution_floor=0.0)).metrics
    assert relaxed.verdict == "pass"


def test_metrics_expose_both_pass_rate_denominators():
    data = json.dumps({"total_cases": 100, "passed": 95, "failed": 3, "blocked": 2})
    metrics = compute_metrics(data).metrics
    assert metrics.total == 100
    assert metrics.executed == 98
    assert abs(metrics.pass_rate - 0.95) < 1e-9  # 通过 ÷ 用例总数
    assert abs(metrics.effective_pass_rate - 95 / 98) < 1e-9  # 通过 ÷ 已执行


def test_thresholds_round_trip_through_settings(monkeypatch):
    monkeypatch.setenv("VERDICT_FAIL_RATE", "0.05")
    client.delete("/api/settings")

    view = client.get("/api/settings").json()
    assert view["thresholds"]["fail_rate"] == 0.05
    assert view["sources"]["thresholds"] == "env"
    assert view["env"]["thresholds"]["execution_floor"] == 0.9

    saved = client.put(
        "/api/settings", json={"thresholds": {"fail_rate": 0.01, "execution_floor": 0.8}}
    ).json()
    assert saved["thresholds"]["fail_rate"] == 0.01
    assert saved["thresholds"]["execution_floor"] == 0.8
    assert saved["thresholds"]["pass_line"] == 0.95  # 没填的项回落 .env
    assert saved["sources"]["thresholds"] == "saved"
    assert client.get("/api/system/status").json()["thresholds"]["fail_rate"] == 0.01

    # 越界值被夹住，认不出的键被丢弃
    clamped = client.put(
        "/api/settings", json={"thresholds": {"fail_rate": 5, "junk": 1}}
    ).json()
    assert clamped["thresholds"]["fail_rate"] == 1.0
    assert "junk" not in clamped["thresholds"]

    reset = client.put("/api/settings", json={"thresholds": {}}).json()
    assert reset["sources"]["thresholds"] == "env"
    assert reset["thresholds"]["fail_rate"] == 0.05


def test_defect_keeps_raw_status():
    payload = {
        "total_cases": 10,
        "passed": 10,
        "defects": [{"id": "B1", "priority": "P0", "status": "待复核"}],
    }
    result = compute_metrics(json.dumps(payload, ensure_ascii=False))
    assert result.defects[0].status == "open"
    assert result.defects[0].status_raw == "待复核"


# ------------------------------------------------------------------ 流式用量

def test_stream_requests_and_forwards_token_usage(monkeypatch):
    """流式默认不带 usage，要显式请求并回传，归档才记得到用量。"""
    import httpx

    from assistant.llm import stream as llm_stream

    body = (
        'data: {"choices":[{"delta":{"content":"甲"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"乙"}}],'
        '"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}\n\n'
        "data: [DONE]\n\n"
    )
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, content=body.encode(), headers={"content-type": "text/event-stream"})

    monkeypatch.setattr(
        "assistant.llm._client", lambda settings, timeout=None: httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    settings = LLMSettings(
        api_key="k", base_url="https://api.example", model="m",
        temperature=0.2, timeout=10.0, max_retries=0,
    )
    usage: dict[str, object] = {}

    async def run() -> list[str]:
        return [chunk async for chunk in llm_stream("提示", settings, usage.update)]

    assert asyncio.run(run()) == ["甲", "乙"]
    assert seen["payload"]["stream_options"] == {"include_usage": True}
    assert usage["total_tokens"] == 15


def test_stream_falls_back_when_provider_rejects_stream_options(monkeypatch):
    """不认 stream_options 的服务商会回 400 —— 去掉字段重来，而不是判定失败。"""
    import httpx

    from assistant.llm import stream as llm_stream

    body = 'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
    payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        if "stream_options" in payload:
            return httpx.Response(400, json={"error": {"message": "unknown field stream_options"}})
        return httpx.Response(200, content=body.encode(), headers={"content-type": "text/event-stream"})

    monkeypatch.setattr(
        "assistant.llm._client", lambda settings, timeout=None: httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    settings = LLMSettings(
        api_key="k", base_url="https://api.example", model="m",
        temperature=0.2, timeout=10.0, max_retries=0,
    )

    async def run() -> list[str]:
        return [chunk async for chunk in llm_stream("提示", settings, {}.update)]

    assert asyncio.run(run()) == ["ok"]
    assert len(payloads) == 2
    assert "stream_options" in payloads[0]
    assert "stream_options" not in payloads[1]
