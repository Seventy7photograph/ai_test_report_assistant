"""AI 测试报告助手 —— 服务入口。

后端职责划分：
  - 指标（通过率、执行率、缺陷分布、判定）由 metrics 确定性计算；
  - 模型只负责归纳、风险解释与建议；
  - 结果落到本地 SQLite，可列表、可对比、可导出。
"""

from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from assistant import store
from assistant.config import APP_NAME, APP_VERSION, legacy_static_dir, spa_dir
from assistant.routers import analyze, reports, system

# Windows 注册表常把 .js 登记成 text/plain，会让 <script type="module"> 被浏览器拒绝。
# 这里显式声明前端产物的类型，避免依赖宿主机的 mimetypes 配置。
for _extension, _mime in {
    ".js": "text/javascript",
    ".mjs": "text/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".map": "application/json",
    ".svg": "image/svg+xml",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".webmanifest": "application/manifest+json",
}.items():
    mimetypes.add_type(_mime, _extension)

_NOT_BUILT_PAGE = """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>AI 测试报告助手</title></head>
<body style="font-family:system-ui;max-width:44rem;margin:12vh auto;padding:0 1.5rem;line-height:1.8;color:#14171a">
<h1 style="margin:0 0 .5rem">AI 测试报告助手</h1>
<p style="color:#5a6068;margin:0 0 2rem">后端已就绪，前端尚未构建。</p>
<ol>
  <li>进入 <code>frontend/</code> 目录</li>
  <li>执行 <code>npm install</code></li>
  <li>执行 <code>npm run build</code></li>
  <li>刷新本页</li>
</ol>
<p style="color:#5a6068;font-size:.875rem">
开发模式可执行 <code>npm run dev</code>，前端会通过 Vite 代理访问本服务。
</p>
<p style="font-size:.875rem"><a href="/docs">查看 API 文档 →</a></p>
</body></html>
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="把测试执行数据变成可核对、可归档的测试报告。指标由服务端计算，分析由模型撰写。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store.init_db()  # 保证不依赖 lifespan 的调用方（例如 TestClient）也能直接使用

app.include_router(system.router)
app.include_router(analyze.router)
app.include_router(reports.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": APP_VERSION}


_dist = spa_dir()

if _dist.is_dir():
    _assets = _dist / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    _root = _dist.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        candidate = (_root / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(_root):
            return FileResponse(candidate)
        return FileResponse(_root / "index.html")

else:
    _legacy = legacy_static_dir() / "index.html"

    @app.get("/", include_in_schema=False)
    async def index_fallback() -> HTMLResponse:
        if _legacy.is_file():
            return HTMLResponse(_legacy.read_text(encoding="utf-8"))
        return HTMLResponse(_NOT_BUILT_PAGE)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
