<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Delete, Printer } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import DefectTable from '@/components/DefectTable.vue'
import OutcomeBar from '@/components/OutcomeBar.vue'
import ReadoutTable from '@/components/ReadoutTable.vue'
import ReportBody from '@/components/ReportBody.vue'
import SpecList from '@/components/SpecList.vue'
import VerdictBlock from '@/components/VerdictBlock.vue'
import { api } from '@/api/client'
import type { ExportFormat, ReportDetail } from '@/api/types'
import { useSystem } from '@/stores/system'
import { datetime, duration } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const { load: reloadStatus } = useSystem()

const detail = ref<ReportDetail | null>(null)
const loading = ref(false)
const missing = ref(false)

const spec = computed(() => {
  const record = detail.value
  if (!record) return []
  return [
    { label: '报告编号', value: record.id },
    { label: '受检对象', value: record.version ?? '—' },
    { label: '生成时间', value: datetime(record.created_at) },
    { label: '执行模型', value: record.model, note: record.provider },
    { label: '推理耗时', value: duration(record.elapsed_ms) },
    { label: '系统判定', value: record.metrics?.verdict_label ?? record.verdict_label },
  ]
})

async function load() {
  const id = String(route.params.id ?? '')
  if (!id) return
  loading.value = true
  missing.value = false
  try {
    detail.value = await api.report(id)
  } catch {
    detail.value = null
    missing.value = true
  } finally {
    loading.value = false
  }
}

function printReport() {
  window.print()
}

function download(format: ExportFormat) {
  if (!detail.value) return
  window.location.href = api.exportUrl(detail.value.id, format)
}

async function remove() {
  const record = detail.value
  if (!record) return
  try {
    await ElMessageBox.confirm(`删除后不可恢复。确认删除「${record.title ?? record.id}」？`, '删除存档', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await api.removeReport(record.id)
    ElMessage.success('已删除')
    await reloadStatus()
    void router.push({ name: 'archive' })
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div class="report-view">
    <header class="report-view__head">
      <button type="button" class="back" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </button>
      <div class="report-view__title-wrap">
        <h1 class="report-view__title">{{ detail?.title ?? (missing ? '存档不存在' : '载入中…') }}</h1>
        <p v-if="detail" class="report-view__sub">
          {{ detail.version ?? '未标注版本' }} · {{ datetime(detail.created_at) }} · 由 {{ detail.model }} 撰写
        </p>
      </div>
      <div v-if="detail" class="report-view__actions">
        <el-button size="small" @click="download('md')">Markdown</el-button>
        <el-button size="small" @click="download('html')">HTML</el-button>
        <el-button size="small" @click="download('docx')">Word</el-button>
        <el-button size="small" :icon="Printer" @click="printReport">打印</el-button>
        <el-button size="small" type="danger" plain :icon="Delete" @click="remove">删除</el-button>
      </div>
    </header>

    <div v-if="missing" class="panel report-view__missing">
      <p class="report-view__missing-title">找不到这份存档</p>
      <p class="report-view__missing-text">它可能已被删除。档案里的记录都是本地文件，删除后无法恢复。</p>
      <el-button size="small" @click="router.push({ name: 'archive' })">回到档案</el-button>
    </div>

    <template v-else-if="detail">
      <div class="report-view__grid">
        <section class="panel" aria-label="读数">
          <header class="panel__head">
            <h2 class="panel__title">读数</h2>
            <span class="panel__meta">由服务端计算</span>
          </header>
          <SpecList :rows="spec" />
          <VerdictBlock :metrics="detail.metrics" phase="pressed" />
          <ReadoutTable :metrics="detail.metrics" phase="pressed" />
          <OutcomeBar :metrics="detail.metrics" />
        </section>

        <section class="panel" aria-label="报告">
          <header class="panel__head">
            <h2 class="panel__title">报告</h2>
            <span class="panel__meta">{{ detail.model }} 撰写</span>
          </header>
          <ul v-if="detail.warnings.length" class="warn-list">
            <li v-for="warning in detail.warnings" :key="warning">{{ warning }}</li>
          </ul>
          <ReportBody :source="detail.report" />
        </section>
      </div>

      <section v-if="detail.defects.length" class="panel">
        <header class="panel__head">
          <h2 class="panel__title">缺陷清单</h2>
          <span class="panel__meta">{{ detail.defects.length }} 条</span>
        </header>
        <DefectTable :defects="detail.defects" />
      </section>

      <details class="panel source">
        <summary class="source__summary">送检原始数据</summary>
        <pre class="source__body">{{ detail.source_data }}</pre>
        <p class="source__note">报告里的每个指标都可以在这份输入里找到出处。</p>
      </details>
    </template>
  </div>
</template>

<style scoped>
.report-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: var(--page-max);
  margin: 0 auto;
}

.report-view__head {
  display: flex;
  align-items: flex-end;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  border: 0;
  background: none;
  color: var(--ink-2);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  cursor: pointer;
}

.back:hover {
  color: var(--accent);
}

.report-view__title-wrap {
  flex: 1;
  min-width: 220px;
}

.report-view__title {
  font-family: var(--font-doc);
  font-size: var(--fs-xl);
  font-weight: 600;
}

.report-view__sub {
  margin-top: 2px;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

.report-view__actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.report-view__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr);
  align-items: start;
  gap: var(--space-4);
}

.panel__meta {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.warn-list {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  list-style: none;
  border-bottom: var(--hairline-soft);
  background: #fbf7ee;
}

.warn-list li {
  font-size: var(--fs-sm);
  color: var(--blocked);
}

.report-view__missing {
  padding: var(--space-6) var(--space-5);
  max-width: 52ch;
}

.report-view__missing-title {
  font-size: var(--fs-md);
  color: var(--ink);
}

.report-view__missing-text {
  margin: 6px 0 var(--space-4);
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.source__summary {
  padding: 12px var(--space-4);
  font-size: var(--fs-sm);
  color: var(--ink-2);
  cursor: pointer;
  letter-spacing: 0.02em;
}

.source__summary:hover {
  color: var(--accent);
}

.source__body {
  margin: 0;
  padding: var(--space-4);
  border-top: var(--hairline-soft);
  background: var(--face);
  font-family: var(--font-data);
  font-size: 12.5px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 420px;
  overflow: auto;
}

.source__note {
  padding: var(--space-2) var(--space-4) var(--space-3);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

@media (max-width: 1080px) {
  .report-view__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media print {
  .report-view__actions,
  .back {
    display: none;
  }
}
</style>
