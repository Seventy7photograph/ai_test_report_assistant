import DOMPurify from 'dompurify'
import { Marked } from 'marked'

const marked = new Marked({ gfm: true, breaks: false })

/**
 * 报告正文来自模型输出，属不可信内容：渲染后必须过一遍 DOMPurify。
 */
export function renderMarkdown(source: string): string {
  if (!source) return ''
  const html = marked.parse(source, { async: false }) as string
  return DOMPurify.sanitize(html, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ['style', 'form', 'input', 'iframe'],
    FORBID_ATTR: ['style', 'onerror', 'onload'],
  })
}
