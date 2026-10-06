# AI 测试报告助手

把测试执行数据变成一份**可核对、可归档**的测试报告：数字由服务端确定性计算，模型只负责归纳、风险解释与建议。

前后端一体的本地应用，一条命令启动，浏览器即用。

## 1. 设计取向

- **指标不由模型编**：通过率、执行率、缺陷分布、结论判定都在 `assistant/metrics.py` 里算好，再作为"权威口径"注入 Prompt。模型被明确要求不得重算或改写数字。
- **读不到就是读不到**：纯文本、格式不完整或无法解析的输入，返回 `metrics: null` 并给出诚实提示，绝不凭空补数。
- **结论有规则**：未关闭的 P0 直接 `reject`；存在未关闭 P1、或失败率 / 阻塞率超过 5% 判 `conditional`；其余 `pass`。
- **留痕**：每次分析落 SQLite，可列表、可趋势、可两轮对比、可导出。

## 2. 功能

- 测试数据输入：JSON 或纯文本，内置 4 套示例数据集
- 确定性指标：用例统计、执行率、通过率、缺陷等级分布、结论判定
- AI 撰写：测试总结、风险分析、缺陷归纳、下一步建议
- 流式输出：SSE 逐字返回，报告边生成边读
- 报告存档：历史列表、趋势曲线（含 95% 门限）、任意两轮对比
- 报告导出：Markdown / HTML / DOCX
- 模型设置：服务商探测、模型切换、连通性自测
- 多模型：任何 OpenAI Chat Completions 兼容接口

## 3. 界面

| 路由 | 页面 | 内容 |
| --- | --- | --- |
| `/` | 工作台 | 左侧送检区（数据、指令、模型），右侧读数区与生成报告 |
| `/archive` | 存档 | 趋势曲线、筛选、历史表格、两轮对比 |
| `/reports/:id` | 报告详情 | 结论印章、检验项目表、缺陷表、报告正文、导出 |
| `/settings` | 设置 | 服务状态、模型列表、连通性自测 |

视觉上是一块**计量仪器读数面板**：石墨外壳、纸白面板、发丝分隔线、唯一强调色（青），零阴影。签名动效为"定值"——生成前读数是未定的虚线青色，生成完成后锁定为墨色、基线自左向右画出、结论印章压印。

## 4. 环境

- 后端：Python 3.10+（开发使用 3.11）
- 前端：Node.js 18+

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填入模型 API Key。

## 5. 启动

### 生产式（推荐）

```bash
cd frontend
npm install
npm run build      # 产物输出到 frontend/dist

cd ..
uvicorn app:app --reload
```

打开 `http://127.0.0.1:8000`。后端会自动托管构建产物；未构建时会显示构建指引页面。

### 开发式（前端热更新）

```bash
uvicorn app:app --reload        # 终端 1，后端 8000
cd frontend && npm run dev      # 终端 2，前端 5173，代理 /api 到 8000
```

## 6. 配置

全部通过环境变量（`.env`）配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | 空 | 模型 API Key；为空时界面提示未配置 |
| `LLM_BASE_URL` | `https://api.deepseek.com` | 兼容 OpenAI 的服务地址 |
| `LLM_MODEL` | `deepseek-chat` | 默认模型 |
| `LLM_MODELS` | 空 | 界面可切换的模型，逗号分隔，首个为默认 |
| `LLM_TIMEOUT` | `120` | 单次请求超时（秒） |
| `LLM_MAX_RETRIES` | `2` | 失败重试次数 |
| `DATA_DIR` | 项目内 `data/` | 存档目录（SQLite `reports.db`） |

## 7. API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/system/status` | 服务与模型配置状态 |
| `POST` | `/api/system/llm-test` | 模型连通性自测 |
| `GET` | `/api/samples` | 内置示例数据集 |
| `POST` | `/api/metrics` | 只算指标，不调模型 |
| `POST` | `/api/analyze` | 指标 + AI 报告（一次性返回） |
| `POST` | `/api/analyze/stream` | 同上，SSE 流式 |
| `GET` | `/api/reports` | 历史报告列表 |
| `GET` | `/api/trends` | 趋势数据点 |
| `GET` | `/api/reports/{id}` | 报告详情 |
| `DELETE` | `/api/reports/{id}` | 删除报告 |
| `GET` | `/api/reports/{id}/export?format=md\|html\|docx` | 导出 |

交互式文档：`http://127.0.0.1:8000/docs`

请求示例：

```json
POST /api/analyze
{
  "test_data": "{\"total_cases\":500,\"passed\":468,\"failed\":22,\"blocked\":10}",
  "instruction": "重点分析高优先级缺陷和下一轮回归建议",
  "model": "deepseek-chat",
  "save": true
}
```

`test_data` 也可以直接放完整的结构化数据（即内置的「基础样例」）：

```json
{
  "version": "4.2.0",
  "total_cases": 500,
  "passed": 468,
  "failed": 22,
  "blocked": 10,
  "defects": [
    {"id": "BUG-001", "priority": "P0", "module": "案件管理", "status": "open"},
    {"id": "BUG-002", "priority": "P1", "module": "权限管理", "status": "open"},
    {"id": "BUG-003", "priority": "P1", "module": "接口", "status": "resolved"}
  ]
}
```
## 8. 目录结构

```
app.py                     应用入口：路由挂载、MIME 修正、SPA 托管
assistant/
  config.py                环境变量解析、服务商探测、模型列表
  schemas.py               Pydantic 请求 / 响应模型
  metrics.py               确定性指标引擎（含结论判定规则）
  prompts.py               System Prompt 与用户 Prompt 组装
  llm.py                   Chat Completions 客户端：重试、SSE、探活
  store.py                 SQLite 存档：写入、列表、详情、趋势
  exporters.py             Markdown / HTML / DOCX 导出
  samples.py               4 套示例数据集
  routers/                 system / analyze / reports 三组接口
frontend/                  Vue 3 + TS + Vite + Element Plus
tests/test_app.py          22 项接口与指标测试
scripts/mock_llm.py        本地假模型服务（离线跑通全流程）
scripts/seed_demo.py       演示数据播种（--reset 清空重建）
```

## 9. 离线演示

不用真实 API Key 也能跑通整条链路：

```bash
# 终端 1：假模型，端口 8011
python scripts/mock_llm.py

# 终端 2：后端指向假模型
# PowerShell 7
$env:LLM_API_KEY="mock-key"; $env:LLM_BASE_URL="http://127.0.0.1:8011"; $env:LLM_MODEL="mock-report-model"
uvicorn app:app --port 8000

# 终端 3：播种演示存档
python scripts/seed_demo.py --reset
```

## 10. 测试

```bash
pytest tests              # 后端
cd frontend && npm run typecheck && npm run build   # 前端类型检查与构建
```
