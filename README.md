# AI 测试报告助手

一个面向软件测试场景的轻量级 AI 应用，用 Python + FastAPI 调用 OpenAI-compatible 大模型 API，将测试执行数据转换为结构化测试总结、风险分析和下一步建议。

## 1. 功能

- JSON / 文本测试数据输入
- 调用 DeepSeek、Qwen、OpenAI 等兼容 Chat Completions 的模型
- Prompt 驱动的测试总结
- 高优先级缺陷和风险分析
- API 超时、HTTP 错误、返回结构异常处理
- 浏览器可视化页面
- `/health` 健康检查
- Pytest 基础测试

## 2. 环境

Python 3.10+

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

复制 `.env.example` 为 `.env`，填入模型 API Key。

## 3. 启动

```bash
uvicorn app:app --reload
```

浏览器打开：

`http://127.0.0.1:8000`

## 4. API

`POST /api/analyze`

请求示例：

```json
{
  "test_data": "{\"total_cases\":500,\"passed\":468,\"failed\":22,\"blocked\":10}",
  "instruction": "重点分析高优先级缺陷和下一轮回归建议"
}
```
