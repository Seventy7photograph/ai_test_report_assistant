# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

用户指定：Vue 3 + TypeScript + Vite + Element Plus（前端），FastAPI（既有后端）。
构建路径：本会话为 code-first —— 环境无图像生成能力（`impeccable context` 未报告 IMAGE_GEN_AVAILABLE，且无图像转换工具），comp 轮按契约跳过。

## Users

_（推断，未经用户确认：本轮结构化提问工具在 Default 模式下不可用，用户未回答）_

- 主要：软件测试工程师（QA），在自己的开发机或内网环境上使用。刚跑完一轮测试，手里是一份原始的测试结果（JSON、接口返回、粘贴的文本），需要在几分钟内得到一份可读、可归档、可交给别人的测试报告。
- 次要：测试负责人 / 项目经理。不跑数据，读报告与历史趋势，关心版本风险与是否可发版。

任务（job to be done）：把"原始测试执行数据"转成"结论明确、指标可信、能直接贴进周报或缺陷复盘的报告"。

## Product Purpose

将测试执行数据转成结构化测试报告：服务端先确定性地计算可算指标（通过率、执行率、缺陷分布），再由大模型给出归纳、风险判断与下一步建议。存在意义是把写测试报告这件事从 30–60 分钟压缩到 1 分钟，同时不牺牲指标的可信度。

成功的样子：一份报告打开后 10 秒内能看出"这版能不能发"，并且每个数字都能追溯到输入。

## Positioning

**指标由代码算，判断由模型写。** 通过率、执行率、缺陷按优先级/模块/状态分布等一切可计算量都由服务端确定性计算并单独返回，模型只负责解释与建议，且被明确要求不得编造输入中不存在的事实。相邻的"AI 总结"工具通常把原始数据整包丢给模型并信任它的算术。

## Operating Context

- 使用场景：本地或内网自部署，单人或小团队；跑完测试后手动粘贴/上传结果，生成报告。
- 环境：Python 3.10+，Windows 为主。模型走 OpenAI-compatible 的 Chat Completions（DeepSeek / Qwen / OpenAI 等），用户在 `.env` 里配置 `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`。
- 输入现实：数据来源杂，格式不统一。同一份数据可能是完整 JSON、嵌套的接口返回、也可能是粘贴的表格文本。字段名不保证与样例一致。
- 输出用途：贴到群里 / 写进周报 / 归档留痕 / 发给开发追缺陷。因此导出（Markdown / HTML / Word）与历史留存是真实需求，不是加分项。
- 术语沿用中文测试行业习惯：用例、通过率、阻塞、P0/P1、回归、冒烟、发版。

## Capabilities and Constraints

已有（既有代码确认）：
- FastAPI 服务，`POST /api/analyze` 接收 `test_data` 文本 + `instruction`，调用兼容 Chat Completions 的模型，返回 Markdown 报告。
- JSON 输入会被规范化后拼进 prompt；非 JSON 原样送入。
- 超时 / HTTP 错误 / 返回结构异常有处理；`/health` 健康检查；单页静态页面。
- Pytest 基础测试（health、首页）。

本轮补齐：
- 服务端确定性指标计算（`POST /api/metrics` 与报告接口一并返回）。
- 报告持久化与历史：SQLite 本地存档、列表、详情、删除、跨版本趋势。
- 导出：Markdown / HTML / DOCX，服务端生成。
- 流式生成：SSE，逐字出报告，前端可实时呈现。
- 模型服务自检：`POST /api/system/llm-test` 真实探活并返回延迟。
- 前端重建为 Vue 3 + TS + Vite + Element Plus 多视图控制台。

约束（未决 / 有意不做的）：
- 不做用户体系与权限，不做多租户。
- 不做在线协作、评论、审批流。
- 不上云、不引入外部数据库；SQLite 文件存在项目内 `data/`，用户可自行备份。
- 不训练、不微调模型；不内置任何模型权重。
- 不记录用户的原始测试数据到任何外部服务，只写本地 SQLite。

## Brand Commitments

产品名沿用：**AI 测试报告助手**（既有标题与 README 用名）。中文界面。无既有 logo、无既有视觉资产、无用户明示的风格约束。

## Evidence on Hand

- `sample_test_results.json`：真实的示例输入（版本 4.2.0，500 用例 / 468 通过 / 22 失败 / 10 阻塞，3 条缺陷）。
- `README.md`、`.env.example`：产品名、启动方式、API 形状。
- `tests/test_app.py`：既有契约（`GET /health`、`GET /`）。

**缺失的、未来工作不得编造的**：没有真实客户、没有用户评价、没有性能基准、没有准确率指标、没有商业数据。报告中出现的一切数字只能来自用户输入或服务端对输入的计算。
