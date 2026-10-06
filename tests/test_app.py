"""后端契约测试。

重点覆盖：确定性指标计算（产品定位的核心）、存档读写、错误路径。
不依赖真实模型服务——凡是需要模型的地方都用错误路径或纯计算接口覆盖。
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import app
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
    async def fake_stream(prompt: str, settings):
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