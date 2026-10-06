"""存档接口：列表、详情、删除、导出、趋势。"""

from __future__ import annotations

import json
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from .. import store
from ..exporters import to_docx, to_html, to_markdown
from ..schemas import DeleteResponse, ReportDetail, ReportListResponse, TrendPoint

router = APIRouter(prefix="/api", tags=["reports"])

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="按标题/版本/模型/正文搜索"),
    verdict: str | None = Query(None, description="按判定过滤"),
) -> ReportListResponse:
    items, total = store.list_reports(limit=limit, offset=offset, query=q, verdict=verdict)
    return ReportListResponse(items=items, total=total)


@router.get("/trends", response_model=list[TrendPoint])
async def trends(limit: int = Query(12, ge=2, le=50)) -> list[TrendPoint]:
    return [TrendPoint(**point) for point in store.trend_points(limit=limit)]


@router.get("/reports/{report_id}", response_model=ReportDetail)
async def get_report(report_id: str) -> ReportDetail:
    record = store.get_report(report_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"存档 {report_id} 不存在。")
    return ReportDetail(**record)


@router.delete("/reports/{report_id}", response_model=DeleteResponse)
async def delete_report(report_id: str) -> DeleteResponse:
    if not store.delete_report(report_id):
        raise HTTPException(status_code=404, detail=f"存档 {report_id} 不存在。")
    return DeleteResponse(deleted=True, id=report_id)


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: str,
    export_format: str = Query("md", alias="format", pattern="^(md|html|docx|json)$"),
) -> Response:
    record = store.get_report(report_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"存档 {report_id} 不存在。")

    stem = (record.get("title") or "测试报告").strip().replace("/", "-").replace("\\", "-")
    filename = f"{stem}_{report_id}.{export_format}"
    disposition = f"attachment; filename*=UTF-8''{quote(filename)}"

    if export_format == "md":
        return Response(
            content=to_markdown(record),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": disposition},
        )
    if export_format == "html":
        return Response(
            content=to_html(record),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": disposition},
        )
    if export_format == "docx":
        return Response(
            content=to_docx(record),
            media_type=_DOCX_MIME,
            headers={"Content-Disposition": disposition},
        )
    return Response(
        content=json.dumps(record, ensure_ascii=False, indent=2),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": disposition},
    )
