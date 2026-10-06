<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Position, Printer, VideoPause } from '@element-plus/icons-vue'
import DefectTable from '@/components/DefectTable.vue'
import OutcomeBar from '@/components/OutcomeBar.vue'
import ReadoutTable from '@/components/ReadoutTable.vue'
import ReportBody from '@/components/ReportBody.vue'
import VerdictBlock from '@/components/VerdictBlock.vue'
import { useRoute } from 'vue-router'
import { api, ApiError, streamAnalyze } from '@/api/client'
import type { Defect, ExportFormat, Metrics } from '@/api/types'
import { useSystem } from '@/stores/system'
import { datetime, duration } from '@/utils/format'

const route = useRoute()
const { status, samples } = useSystem()

const testData = ref('')
const instruction = ref('重点分析高优先级缺陷、版本风险，并给出回归建议。')
const model = ref('')
const useStream = ref(true)
const archive = ref(true)

const liveMetrics = ref<Metrics | null>(null)
const liveDefects = ref<Defect[]>([])
const liveVersion = ref<string | null>(null)

const report = ref('')
const reportMeta = ref<{ model: string; elapsed: number; createdAt: string } | null>(null)
const reportId = ref<string | null>(null)
const generating = ref(false)
const warnings = ref<string[]>([])

const sourceRevision = ref(0)
const lockedRevision = ref(-1)
let controller: AbortController | null = null
let metricsTimer: number | undefined
let lastPayload = ''

const phase = computed<'idle' | 'pending' | 'pressed'>(() => {
  if (!liveMetrics.value) return 'idle'
  return lockedRevision.value === sourceRevision.value ? 'pressed' : 'pending'
})

const sourceFormat = computed(() => (liveMetrics.value ? 'json' : testData.value.trim() ? 'text' : 'empty'))

const parseNote = computed(() => {
  if (!testData.value.trim()) return '等待送检数据'
  if (liveMetrics.value) {
    const version = liveVersion.value ? ` · 版本 ${liveVersion.value}` : ''
    return `已识别结构化数据${version} · ${liveMetrics.value.total} 条用例`
  }
  return '非 JSON 输入 · 无法计算指标，将按原文分析'
})

const canGenerate = computed(() => testData.value.trim().length > 0 && !generating.value)

const exportedAt = computed(() => (reportMeta.value ? datetime(reportMeta.value.createdAt) : ''))

const PRESETS = [
  { label: '发版评估', text: '重点分析高优先级缺陷与本版本风险，给出是否可发版的判断依据。' },
  { label: '回归建议', text: '总结本轮失败用例的分布特征，给出下一轮回归的范围与优先级建议。' },
  { label: '缺陷复盘', text: '按模块归纳缺陷，指出缺陷密度最高的模块并分析可能的原因。' },
]

watch(testData, () => {
  sourceRevision.value += 1
  scheduleMetrics()
})

async function refreshMetrics() {
  const payload = testData.value
  if (payload === lastPayload) return
  lastPayload = payload

  if (!payload.trim()) {
    liveMetrics.value = null
    liveDefects.value = []
    liveVersion.value = null
    return
  }
  try {
    const result = await api.metrics(payload)
    if (payload !== testData.value) return
    liveMetrics.value = result.metrics
    liveDefects.value = result.defects
    liveVersion.value = result.version
  } catch {
    /* 实时读数失败不应该打断输入 */
  }
}

function scheduleMetrics() {
  window.clearTimeout(metricsTimer)
  metricsTimer = window.setTimeout(() => void refreshMetrics(), 320)
}

function applySample(id: string) {
  const sample = samples.value.find((item) => item.id === id)
  if (!sample) return
  testData.value = sample.content
  ElMessage.success(`已载入「${sample.name}」`)
}

function clearAll() {
  testData.value = ''
  report.value = ''
  reportMeta.value = null
  reportId.value = null
  lockedRevision.value = -1
  warnings.value = []
}

async function generate() {
  if (!canGenerate.value) return
  generating.value = true
  report.value = ''
  reportId.value = null
  reportMeta.value = null
  warnings.value = []

  const payload = {
    test_data: testData.value,
    instruction: instruction.value,
    model: model.value || null,
    save: archive.value,
  }

  if (useStream.value) {
    controller = new AbortController()
    let buffer = ''
    try {
      await streamAnalyze(
        payload,
        {
          onMeta: (meta) => {
            reportMeta.value = { model: meta.model, elapsed: 0, createdAt: meta.created_at }
            warnings.value = [...meta.warnings]
          },
          onMetrics: (metrics) => {
            liveMetrics.value = metrics
          },
          onDelta: (text) => {
            buffer += text
            report.value = buffer
          },
          onDone: (info) => {
            reportMeta.value = {
              model: reportMeta.value?.model ?? status.value?.model ?? '—',
              elapsed: info.elapsed_ms,
              createdAt: reportMeta.value?.createdAt ?? new Date().toISOString(),
            }
            reportId.value = info.id
            warnings.value = [...info.warnings]
            lockedRevision.value = sourceRevision.value
          },
          onError: (detail) => {
            warnings.value = [detail]
            ElMessage.error(detail)
          },
        },
        controller.signal,
      )
    } catch (error) {
      const message = error instanceof ApiError ? error.message : (error as Error).message
      warnings.value = [message]
      ElMessage.error(message)
    } finally {
      controller = null
    }
  } else {
    try {
      const result = await api.analyze(payload)
      report.value = result.report
      reportId.value = result.id
      reportMeta.value = { model: result.model, elapsed: result.elapsed_ms, createdAt: result.created_at }
      if (result.metrics) liveMetrics.value = result.metrics
      warnings.value = result.warnings
      lockedRevision.value = sourceRevision.value
    } catch (error) {
      const message = error instanceof ApiError ? error.message : (error as Error).message
      warnings.value = [message]
      ElMessage.error(message)
    }
  }

  generating.value = false
}

function stop() {
  controller?.abort()
  controller = null
  generating.value = false
}

function download(format: ExportFormat) {
  if (!reportId.value) return
  window.location.href = api.exportUrl(reportId.value, format)
}

function printReport() {
  window.print()
}

function onKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    void generate()
  }
}

// 路由是懒加载的：组件挂载时样例可能已经取回来了，
// 所以要 immediate 跑一次，而不是只等后续变化。
watch(
  samples,
  () => {
    if (!testData.value && samples.value.length) {
      testData.value = samples.value[0].content
    }
  },
  { immediate: true },
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  const requested = route.query.sample
  if (typeof requested === 'string') {
    applySample(requested)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  window.clearTimeout(metricsTimer)
  controller?.abort()
})
</script>

<template>
  <div class="workbench">
    <section class="intake panel" aria-label="送检">
      <header class="panel__head">
        <h2 class="panel__title">送检</h2>
        <el-select
          :model-value="''"
          placeholder="载入样例"
          size="small"
          class="intake__samples"
          @change="applySample"
        >
          <el-option v-for="sample in samples" :key="sample.id" :label="sample.name" :value="sample.id" />
        </el-select>
      </header>

      <div class="intake__body">
        <label class="field">
          <span class="field__label">测试数据</span>
          <el-input v-model="testData" type="textarea" :rows="14" resize="vertical" spellcheck="false" />
        </label>

        <p class="intake__note" :class="`is-${sourceFormat}`">
          <span class="intake__note-mark" aria-hidden="true" />
          {{ parseNote }}
        </p>

        <label class="field">
          <span class="field__label">分析要求</span>
          <el-input v-model="instruction" type="textarea" :rows="3" resize="none" />
        </label>

        <div class="intake__presets">
          <button
            v-for="preset in PRESETS"
            :key="preset.label"
            type="button"
            class="preset"
            @click="instruction = preset.text"
          >
            {{ preset.label }}
          </button>
        </div>

        <label class="field">
          <span class="field__label">模型</span>
          <el-select v-model="model" placeholder="使用默认模型" clearable>
            <el-option v-for="name in status?.models ?? []" :key="name" :label="name" :value="name" />
          </el-select>
        </label>

        <div class="intake__switches">
          <el-switch v-model="useStream" size="small" />
          <span class="intake__switch-label">流式输出</span>
          <el-switch v-model="archive" size="small" class="intake__switch-gap" />
          <span class="intake__switch-label">存入档案</span>
        </div>

        <div class="intake__actions">
          <el-button
            type="primary"
            size="large"
            :icon="Position"
            :loading="generating"
            :disabled="!canGenerate"
            class="intake__generate"
            @click="generate"
          >
            {{ generating ? '正在生成' : '生成报告' }}
          </el-button>
          <el-button v-if="generating" :icon="VideoPause" size="large" @click="stop">停止</el-button>
          <el-button v-else :icon="Delete" size="large" :disabled="!testData" @click="clearAll">清空</el-button>
        </div>

        <p class="intake__hint">
          Ctrl / ⌘ + Enter 生成
          <span v-if="status && !status.llm_configured" class="intake__hint-warn">
            · 尚未配置 LLM_API_KEY，只能查看读数
          </span>
        </p>
      </div>
    </section>

    <section class="panel" aria-label="读数">
      <header class="panel__head">
        <h2 class="panel__title">读数</h2>
        <span class="panel__meta">
          <template v-if="liveVersion">受检对象 {{ liveVersion }} · </template>由服务端计算
        </span>
      </header>

      <VerdictBlock :metrics="liveMetrics" :phase="phase" />
      <ReadoutTable :metrics="liveMetrics" :phase="phase" />
      <OutcomeBar :metrics="liveMetrics" />

      <template v-if="liveDefects.length">
        <p class="rule-label panel__subhead">缺陷清单 · {{ liveDefects.length }} 条</p>
        <DefectTable :defects="liveDefects" />
      </template>
    </section>

    <section class="panel report" aria-label="报告">
      <header class="panel__head">
        <h2 class="panel__title">报告</h2>
        <span class="panel__meta">
          <template v-if="reportMeta">
            {{ reportMeta.model }} 撰写 · {{ duration(reportMeta.elapsed) }} · {{ exportedAt }}
          </template>
          <template v-else>由模型撰写</template>
        </span>
      </header>

      <ul v-if="warnings.length" class="warn-list">
        <li v-for="warning in warnings" :key="warning">{{ warning }}</li>
      </ul>

      <ReportBody v-if="report" :source="report" :streaming="generating" />

      <div v-else-if="generating" class="report__waiting">
        <span class="report__pulse" aria-hidden="true" />
        正在生成报告…
      </div>

      <div v-else class="report__empty">
        <p class="report__empty-title">报告尚未生成</p>
        <p class="report__empty-text">
          左侧读数已经在你粘贴数据时算好了。点「生成报告」让模型补上归纳、风险判断与建议。
        </p>
      </div>

      <footer v-if="reportId" class="report__actions">
        <span class="report__saved">已存入档案 · {{ reportId }}</span>
        <div class="report__exports">
          <el-button size="small" @click="download('md')">Markdown</el-button>
          <el-button size="small" @click="download('html')">HTML</el-button>
          <el-button size="small" @click="download('docx')">Word</el-button>
          <el-button size="small" @click="download('json')">JSON</el-button>
          <el-button size="small" :icon="Printer" @click="printReport">打印</el-button>
        </div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.workbench {
  display: grid;
  grid-template-columns: minmax(320px, 400px) minmax(0, 1fr);
  align-items: start;
  gap: var(--space-4);
  max-width: var(--page-max);
  margin: 0 auto;
}

.intake {
  position: sticky;
  top: calc(var(--shell-height) + var(--space-4));
  max-height: calc(100vh - var(--shell-height) - var(--space-6));
  display: flex;
  flex-direction: column;
}

.intake__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  overflow-y: auto;
}

.intake__samples {
  width: 118px;
}

.field {
  display: block;
}

.field__label {
  display: block;
  margin-bottom: 5px;
  font-size: var(--fs-micro);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.intake__note {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: -4px;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.intake__note-mark {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  background: var(--skipped-fill);
  flex-shrink: 0;
}

.intake__note.is-json .intake__note-mark {
  background: var(--pass-fill);
}

.intake__presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.preset {
  padding: 3px 10px;
  border: 1px solid var(--rule);
  border-radius: 2px;
  background: var(--sheet);
  color: var(--ink-2);
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: border-color 120ms ease-out, color 120ms ease-out;
}

.preset:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.intake__switches {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.intake__switch-label {
  font-size: var(--fs-micro);
  color: var(--ink-2);
  letter-spacing: 0.04em;
}

.intake__switch-gap {
  margin-left: var(--space-3);
}

.intake__actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.intake__generate {
  flex: 1;
}

.intake__hint {
  font-size: var(--fs-micro);
  color: var(--ink-3);
  letter-spacing: 0.02em;
}

.intake__hint-warn {
  color: var(--blocked);
}

.panel__meta {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
  text-align: right;
}

.panel__subhead {
  padding: var(--space-3) var(--space-4) var(--space-2);
}

.report {
  grid-column: 2;
}

.report__waiting {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: var(--space-5);
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.report__pulse {
  width: 8px;
  height: 8px;
  border-radius: 1px;
  background: var(--accent);
  animation: pulse 1.1s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.25;
  }
  50% {
    opacity: 1;
  }
}

.report__empty {
  padding: var(--space-6) var(--space-5);
  max-width: 46ch;
}

.report__empty-title {
  font-family: var(--font-ui);
  font-size: var(--fs-md);
  font-weight: 500;
  color: var(--ink);
}

.report__empty-text {
  margin-top: 6px;
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.warn-list {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  list-style: none;
  border-bottom: var(--hairline-soft);
  background: #fbf7ee;
}

.warn-list li {
  position: relative;
  padding-left: 14px;
  font-size: var(--fs-sm);
  color: var(--blocked);
}

.warn-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.68em;
  width: 5px;
  height: 1px;
  background: var(--blocked);
}

.report__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-3) var(--space-4);
  border-top: var(--hairline);
  background: var(--face);
}

.report__saved {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.report__exports {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

@media (max-width: 1000px) {
  .intake__hint {
    display: none;
  }
}

@media (max-width: 1080px) {
  .workbench {
    grid-template-columns: minmax(0, 1fr);
  }

  .intake {
    position: static;
    max-height: none;
  }

  .report {
    grid-column: 1;
  }
}

@media print {
  .intake {
    display: none;
  }
}
</style>
