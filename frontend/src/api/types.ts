export type Verdict = 'pass' | 'conditional' | 'reject' | 'unknown'

export interface CountItem {
  key: string
  label: string
  count: number
}

export interface Metrics {
  total: number
  passed: number
  failed: number
  blocked: number
  skipped: number
  pass_rate: number
  fail_rate: number
  execution_rate: number
  defects_total: number
  defects_open: number
  open_p0: number
  open_p1: number
  by_priority: CountItem[]
  by_status: CountItem[]
  by_module: CountItem[]
  verdict: Verdict
  verdict_label: string
  verdict_reasons: string[]
}

export interface Defect {
  id: string | null
  title: string | null
  priority: string | null
  module: string | null
  status: string | null
}

export interface MetricsResult {
  metrics: Metrics | null
  defects: Defect[]
  version: string | null
  source_format: 'json' | 'text'
  warnings: string[]
}

export interface AnalyzePayload {
  test_data: string
  instruction: string
  model?: string | null
  temperature?: number | null
  title?: string | null
  save?: boolean
}

export interface AnalyzeResponse {
  id: string | null
  report: string
  model: string
  provider: string
  metrics: Metrics | null
  warnings: string[]
  version: string | null
  created_at: string
  elapsed_ms: number
  usage: Record<string, unknown> | null
}

export interface ReportSummary {
  id: string
  title: string | null
  version: string | null
  model: string
  provider: string
  created_at: string
  elapsed_ms: number
  verdict: Verdict
  verdict_label: string
  pass_rate: number | null
  total: number | null
  failed: number | null
  blocked: number | null
  excerpt: string
}

export interface ReportDetail extends ReportSummary {
  instruction: string
  source_data: string
  report: string
  metrics: Metrics | null
  defects: Defect[]
  usage: Record<string, unknown> | null
  warnings: string[]
}

export interface ReportListResponse {
  items: ReportSummary[]
  total: number
}

export interface TrendPoint {
  id: string
  label: string
  created_at: string
  pass_rate: number
  total: number
  failed: number
  blocked: number
  verdict: Verdict
  verdict_label: string
}

export interface SystemStatus {
  app_name: string
  app_version: string
  llm_configured: boolean
  provider: string
  base_url: string
  model: string
  models: string[]
  temperature: number
  timeout: number
  max_retries: number
  storage_backend: string
  storage_path: string
  report_count: number
  frontend_built: boolean
}

export interface SampleDataset {
  id: string
  name: string
  description: string
  content: string
}

export interface LLMTestResult {
  ok: boolean
  model: string
  provider: string
  latency_ms: number
  message: string
}

export type ExportFormat = 'md' | 'html' | 'docx' | 'json'

export interface LLMSettingsView {
  base_url: string
  model: string
  models: string[]
  temperature: number
  timeout: number
  max_retries: number
  api_key_set: boolean
  api_key_masked: string | null
  api_key_stored: boolean
  sources: Record<string, 'env' | 'saved'>
  env: {
    base_url?: string
    model?: string
    models?: string[]
    temperature?: number
    timeout?: number
    max_retries?: number
    api_key_set?: boolean
  }
}

export interface LLMSettingsUpdate {
  base_url?: string | null
  model?: string | null
  models?: string[] | null
  temperature?: number | null
  timeout?: number | null
  max_retries?: number | null
  api_key?: string | null
  clear_api_key?: boolean
}

export interface SettingsTestPayload {
  base_url?: string | null
  model?: string | null
  api_key?: string | null
  timeout?: number | null
}

export interface StreamHandlers {
  onMeta?: (meta: { model: string; provider: string; created_at: string; version: string | null; warnings: string[] }) => void
  onMetrics?: (metrics: Metrics) => void
  onDelta?: (text: string) => void
  onDone?: (info: { id: string | null; elapsed_ms: number; warnings: string[]; saved: boolean }) => void
  onError?: (detail: string) => void
}
