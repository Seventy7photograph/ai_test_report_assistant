import type { Verdict } from '@/api/types'

export function percent(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

export function integer(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return String(value)
}

/** ISO 字符串 → 本地可读时间。后端返回带时区的时间戳。 */
export function datetime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  const diff = Date.now() - date.getTime()
  const minutes = Math.round(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days} 天前`
  return datetime(iso)
}

export function duration(ms: number | null | undefined): string {
  if (ms == null) return '—'
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

export const VERDICT_TONE: Record<Verdict, string> = {
  pass: 'var(--pass)',
  conditional: 'var(--blocked)',
  reject: 'var(--fail)',
  unknown: 'var(--ink-3)',
}

export const VERDICT_FILL: Record<Verdict, string> = {
  pass: 'var(--pass-fill)',
  conditional: 'var(--blocked-fill)',
  reject: 'var(--fail-fill)',
  unknown: 'var(--skipped-fill)',
}

export function verdictLabel(verdict: Verdict, fallback = '无法判定'): string {
  const map: Record<Verdict, string> = {
    pass: '建议发版',
    conditional: '有条件通过',
    reject: '不建议发版',
    unknown: '无法判定',
  }
  return map[verdict] ?? fallback
}

/** 缺陷状态 → 展示用中文标签与色调。 */
export function defectStatusLabel(status: string | null): string {
  switch (status) {
    case 'open':
      return '未关闭'
    case 'resolved':
      return '已修复'
    case 'rejected':
      return '已驳回'
    case 'unknown':
      return '状态未标注'
    default:
      return status || '—'
  }
}

export function defectStatusColor(status: string | null): string {
  switch (status) {
    case 'open':
      return 'var(--fail)'
    case 'resolved':
      return 'var(--pass)'
    // 未标注按未关闭计入判定，颜色要跟上，别让人误以为已关闭。
    case 'unknown':
      return 'var(--blocked)'
    case 'rejected':
      return 'var(--ink-3)'
    default:
      return 'var(--ink-3)'
  }
}

/** 归一化丢掉了原文（待复核 → unknown），有原文时补在标签后面。 */
export function defectStatusDetail(status: string | null, raw: string | null): string {
  const label = defectStatusLabel(status)
  const text = (raw ?? '').trim()
  if (!text) return label
  const normalized = text.toLowerCase()
  if (normalized === (status ?? '').toLowerCase() || normalized === label.toLowerCase()) return label
  return `${label}（原文：${text}）`
}

export function priorityColor(priority: string | null): string {
  switch (priority) {
    case 'P0':
      return 'var(--fail)'
    case 'P1':
      return 'var(--blocked)'
    default:
      return 'var(--ink-2)'
  }
}
