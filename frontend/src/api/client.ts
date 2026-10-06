import type {
  AnalyzePayload,
  AnalyzeResponse,
  ExportFormat,
  LLMTestResult,
  MetricsResult,
  ReportDetail,
  ReportListResponse,
  SampleDataset,
  StreamHandlers,
  SystemStatus,
  TrendPoint,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
    if (Array.isArray(body?.detail)) {
      return body.detail.map((item: { msg?: string }) => item?.msg ?? '').filter(Boolean).join('；')
        || '请求参数不合法。'
    }
  } catch {
    /* 非 JSON 响应，退回到状态码文案 */
  }
  return `请求失败（HTTP ${response.status}）。`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError('无法连接后端服务，请确认 uvicorn 已启动。', 0)
  }
  if (!response.ok) {
    throw new ApiError(await readDetail(response), response.status)
  }
  return (await response.json()) as T
}

export const api = {
  status: () => request<SystemStatus>('/api/system/status'),

  llmTest: () => request<LLMTestResult>('/api/system/llm-test', { method: 'POST' }),

  samples: () => request<SampleDataset[]>('/api/samples'),

  metrics: (testData: string) =>
    request<MetricsResult>('/api/metrics', {
      method: 'POST',
      body: JSON.stringify({ test_data: testData }),
    }),

  analyze: (payload: AnalyzePayload) =>
    request<AnalyzeResponse>('/api/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  reports: (params: { limit?: number; offset?: number; q?: string; verdict?: string } = {}) => {
    const search = new URLSearchParams()
    if (params.limit != null) search.set('limit', String(params.limit))
    if (params.offset != null) search.set('offset', String(params.offset))
    if (params.q) search.set('q', params.q)
    if (params.verdict && params.verdict !== 'all') search.set('verdict', params.verdict)
    return request<ReportListResponse>(`/api/reports?${search.toString()}`)
  },

  report: (id: string) => request<ReportDetail>(`/api/reports/${encodeURIComponent(id)}`),

  removeReport: (id: string) =>
    request<{ deleted: boolean; id: string }>(`/api/reports/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),

  trends: (limit = 12) => request<TrendPoint[]>(`/api/trends?limit=${limit}`),

  exportUrl: (id: string, format: ExportFormat) =>
    `/api/reports/${encodeURIComponent(id)}/export?format=${format}`,
}

/**
 * 手工解析 SSE。EventSource 只能 GET，而生成请求需要带 body，
 * 所以用 fetch + ReadableStream 自己拆帧。
 */
export async function streamAnalyze(
  payload: AnalyzePayload,
  handlers: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response
  try {
    response = await fetch('/api/analyze/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
  } catch (error) {
    if ((error as Error).name === 'AbortError') return
    throw new ApiError('无法连接后端服务，请确认 uvicorn 已启动。', 0)
  }

  if (!response.ok) {
    throw new ApiError(await readDetail(response), response.status)
  }
  if (!response.body) {
    throw new ApiError('当前浏览器不支持流式读取。', 0)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const dispatch = (event: string, data: string) => {
    if (!data) return
    let parsed: unknown
    try {
      parsed = JSON.parse(data)
    } catch {
      return
    }
    switch (event) {
      case 'meta':
        handlers.onMeta?.(parsed as Parameters<NonNullable<StreamHandlers['onMeta']>>[0])
        break
      case 'metrics':
        handlers.onMetrics?.(parsed as Parameters<NonNullable<StreamHandlers['onMetrics']>>[0])
        break
      case 'delta':
        handlers.onDelta?.((parsed as { text: string }).text)
        break
      case 'done':
        handlers.onDone?.(parsed as Parameters<NonNullable<StreamHandlers['onDone']>>[0])
        break
      case 'error':
        handlers.onError?.((parsed as { detail: string }).detail)
        break
    }
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf('\n\n')
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      let event = 'message'
      const dataLines: string[] = []
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
      }
      dispatch(event, dataLines.join('\n'))
      boundary = buffer.indexOf('\n\n')
    }
  }
}
