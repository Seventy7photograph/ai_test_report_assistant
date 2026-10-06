<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import SpecList from '@/components/SpecList.vue'
import TrendChart from '@/components/TrendChart.vue'
import { api } from '@/api/client'
import type { ExportFormat, ReportSummary, TrendPoint } from '@/api/types'
import { useSystem } from '@/stores/system'
import { datetime, duration, percent, relativeTime, VERDICT_TONE } from '@/utils/format'

const router = useRouter()
const { status, load: reloadStatus } = useSystem()

const items = ref<ReportSummary[]>([])
const trends = ref<TrendPoint[]>([])
const total = ref(0)
const loading = ref(false)
const query = ref('')
const verdict = ref('all')
const page = ref(1)
const pageSize = ref(20)

/** 宽表固定列合计 1138px，在 390px 上只能横向滚动；窄屏改用卡片式记录单。 */
const NARROW_QUERY = '(max-width: 720px)'
const narrowMedia = typeof window === 'undefined' ? null : window.matchMedia(NARROW_QUERY)
const narrow = ref(narrowMedia?.matches ?? false)

function syncNarrow(event: MediaQueryListEvent) {
  narrow.value = event.matches
}

narrowMedia?.addEventListener('change', syncNarrow)

onBeforeUnmount(() => {
  narrowMedia?.removeEventListener('change', syncNarrow)
})

const compareOptions = ref<ReportSummary[]>([])
const baselineId = ref('')
const compareId = ref('')

const verdictOptions = [
  { value: 'all', label: '全部判定' },
  { value: 'pass', label: '建议发版' },
  { value: 'conditional', label: '有条件通过' },
  { value: 'reject', label: '不建议发版' },
  { value: 'unknown', label: '无法判定' },
]

async function loadReports() {
  loading.value = true
  try {
    const response = await api.reports({
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
      q: query.value || undefined,
      verdict: verdict.value,
    })
    items.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadTrends() {
  try {
    trends.value = await api.trends(12)
  } catch {
    trends.value = []
  }
}

function search() {
  page.value = 1
  void loadReports()
}

function resetFilters() {
  query.value = ''
  verdict.value = 'all'
  search()
}

async function loadCompareOptions() {
  try {
    const response = await api.reports({ limit: 100 })
    compareOptions.value = response.items
  } catch {
    compareOptions.value = []
  }
}

function openReport(id: string) {
  void router.push({ name: 'report', params: { id } })
}

function exportReport(id: string, format: ExportFormat) {
  window.location.href = api.exportUrl(id, format)
}

async function remove(report: ReportSummary) {
  try {
    await ElMessageBox.confirm(
      `删除后不可恢复。确认删除「${report.title ?? report.id}」？`,
      '删除存档',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await api.removeReport(report.id)
    ElMessage.success('已删除')
    await Promise.all([loadReports(), loadTrends(), loadCompareOptions(), reloadStatus()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

const comparison = computed(() => {
  const a = compareOptions.value.find((item) => item.id === baselineId.value)
  const b = compareOptions.value.find((item) => item.id === compareId.value)
  if (!a || !b || a.id === b.id) return null

  const rows = [
    {
      label: '受检版本',
      value: `${a.version ?? a.title ?? '—'} → ${b.version ?? b.title ?? '—'}`,
    },
    {
      label: '用例总数',
      value: `${a.total ?? '—'} → ${b.total ?? '—'}`,
      note: delta(a.total, b.total),
    },
    {
      label: '通过率',
      value: `${percent(a.pass_rate)} → ${percent(b.pass_rate)}`,
      note: deltaPoint(a.pass_rate, b.pass_rate),
    },
    {
      label: '失败用例',
      value: `${a.failed ?? '—'} → ${b.failed ?? '—'}`,
      note: delta(a.failed, b.failed),
    },
    {
      label: '阻塞用例',
      value: `${a.blocked ?? '—'} → ${b.blocked ?? '—'}`,
      note: delta(a.blocked, b.blocked),
    },
    {
      label: '系统判定',
      value: `${a.verdict_label} → ${b.verdict_label}`,
      note: a.verdict === b.verdict ? '未变化' : '有变化',
    },
  ]
  return { a, b, rows }
})

function delta(from: number | null, to: number | null): string {
  if (from == null || to == null) return ''
  const diff = to - from
  if (diff === 0) return '持平'
  return `${diff > 0 ? '+' : '−'}${Math.abs(diff)}`
}

function deltaPoint(from: number | null, to: number | null): string {
  if (from == null || to == null) return ''
  const diff = (to - from) * 100
  if (Math.abs(diff) < 0.05) return '持平'
  return `${diff > 0 ? '+' : '−'}${Math.abs(diff).toFixed(1)}pp`
}

onMounted(() => {
  void loadReports()
  void loadTrends()
  void loadCompareOptions()
})
</script>

<template>
  <div class="archive">
    <header class="archive__head">
      <div>
        <h1 class="archive__title">报告档案</h1>
        <p class="archive__sub">共 {{ total }} 份存档 · 本地 SQLite</p>
      </div>
      <el-button :icon="Refresh" @click="() => { void loadReports(); void loadTrends(); void loadCompareOptions() }">刷新</el-button>
    </header>

    <section class="panel">
      <header class="panel__head">
        <h2 class="panel__title">通过率趋势</h2>
        <span class="panel__meta">最近 {{ trends.length }} 份带指标的存档</span>
      </header>
      <TrendChart :points="trends" :pass-line="status?.thresholds?.pass_line ?? 0.95" />
    </section>

    <section class="panel">
      <header class="panel__head filters">
        <el-input
          v-model="query"
          placeholder="搜索标题、版本、模型或正文"
          :prefix-icon="Search"
          clearable
          class="filters__search"
          @keyup.enter="search"
          @clear="search"
        />
        <el-select v-model="verdict" class="filters__verdict" @change="search">
          <el-option v-for="option in verdictOptions" :key="option.value" :label="option.label" :value="option.value" />
        </el-select>
        <el-button @click="search">筛选</el-button>
        <el-button text @click="resetFilters">重置</el-button>
      </header>

      <div v-if="!loading && !items.length" class="archive__empty">
        <p class="archive__empty-title">还没有存档</p>
        <p class="archive__empty-text">在工作台生成报告并勾选「存入档案」，这里就会出现记录。</p>
        <el-button size="small" @click="router.push('/')">去工作台</el-button>
      </div>

      <ul v-else-if="narrow" v-loading="loading" class="slips">
        <li v-for="row in items" :key="row.id" class="slip">
          <header class="slip__head">
            <span class="slip__stamp">
              <span class="cell-time">{{ datetime(row.created_at) }}</span>
              <span class="cell-sub">{{ relativeTime(row.created_at) }}</span>
            </span>
            <span
              class="cell-verdict"
              :style="{ color: VERDICT_TONE[row.verdict as keyof typeof VERDICT_TONE] }"
            >
              <i
                class="cell-verdict__mark"
                :style="{ background: VERDICT_TONE[row.verdict as keyof typeof VERDICT_TONE] }"
                aria-hidden="true"
              />
              {{ row.verdict_label }}
            </span>
          </header>

          <button type="button" class="cell-link slip__title" @click="openReport(row.id)">
            {{ row.title ?? '未命名报告' }}
          </button>
          <p class="slip__excerpt">{{ row.excerpt }}</p>

          <dl class="slip__readouts">
            <div class="slip__field">
              <dt>模型</dt>
              <dd class="cell-mono">{{ row.model }}</dd>
            </div>
            <div class="slip__field">
              <dt>通过率</dt>
              <dd class="cell-num">{{ percent(row.pass_rate) }}</dd>
            </div>
            <div class="slip__field">
              <dt>失败</dt>
              <dd class="cell-num">{{ row.failed ?? '—' }}</dd>
            </div>
            <div class="slip__field">
              <dt>阻塞</dt>
              <dd class="cell-num">{{ row.blocked ?? '—' }}</dd>
            </div>
            <div class="slip__field">
              <dt>耗时</dt>
              <dd class="cell-num">{{ duration(row.elapsed_ms) }}</dd>
            </div>
          </dl>

          <div class="row-actions slip__actions">
            <el-button size="small" text @click="openReport(row.id)">查看</el-button>
            <el-button size="small" text @click="exportReport(row.id, 'md')">MD</el-button>
            <el-button size="small" text @click="exportReport(row.id, 'docx')">Word</el-button>
            <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
          </div>
        </li>
      </ul>

      <el-table
        v-else
        v-loading="loading"
        :data="items"
        row-key="id"
        class="archive__table"
      >
        <el-table-column label="生成时间" width="150">
          <template #default="{ row }">
            <span class="cell-time">{{ datetime(row.created_at) }}</span>
            <span class="cell-sub">{{ relativeTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="受检对象" min-width="180">
          <template #default="{ row }">
            <button type="button" class="cell-link" @click="openReport(row.id)">
              {{ row.title ?? '未命名报告' }}
            </button>
            <span class="cell-sub">{{ row.excerpt }}</span>
          </template>
        </el-table-column>
        <el-table-column label="模型" width="150">
          <template #default="{ row }">
            <span class="cell-mono">{{ row.model }}</span>
          </template>
        </el-table-column>
        <el-table-column label="通过率" width="96" align="right">
          <template #default="{ row }">
            <span class="cell-num">{{ percent(row.pass_rate) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="失败" width="72" align="right">
          <template #default="{ row }">
            <span class="cell-num">{{ row.failed ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阻塞" width="72" align="right">
          <template #default="{ row }">
            <span class="cell-num">{{ row.blocked ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="判定" width="110">
          <template #default="{ row }">
            <span class="cell-verdict" :style="{ color: VERDICT_TONE[row.verdict as keyof typeof VERDICT_TONE] }">
              <i
                class="cell-verdict__mark"
                :style="{ background: VERDICT_TONE[row.verdict as keyof typeof VERDICT_TONE] }"
                aria-hidden="true"
              />
              {{ row.verdict_label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="80" align="right">
          <template #default="{ row }">
            <span class="cell-num">{{ duration(row.elapsed_ms) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="228" align="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" text @click="openReport(row.id)">查看</el-button>
              <el-button size="small" text @click="exportReport(row.id, 'md')">MD</el-button>
              <el-button size="small" text @click="exportReport(row.id, 'docx')">Word</el-button>
              <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>

      </el-table>

      <footer v-if="total > pageSize" class="archive__pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          background
          @current-change="loadReports"
        />
      </footer>
    </section>

    <section class="panel compare">
      <header class="panel__head">
        <h2 class="panel__title">两轮对比</h2>
        <span class="panel__meta">只读取已算好的指标，不重新调用模型</span>
      </header>

      <div class="compare__pickers">
        <label class="compare__pick">
          <span class="compare__pick-label">基准</span>
          <el-select v-model="baselineId" placeholder="选择较早的一轮" filterable clearable>
            <el-option
              v-for="option in compareOptions"
              :key="option.id"
              :label="`${option.version ?? option.title ?? option.id} · ${datetime(option.created_at)}`"
              :value="option.id"
            />
          </el-select>
        </label>
        <span class="compare__arrow" aria-hidden="true">→</span>
        <label class="compare__pick">
          <span class="compare__pick-label">对比</span>
          <el-select v-model="compareId" placeholder="选择较新的一轮" filterable clearable>
            <el-option
              v-for="option in compareOptions"
              :key="option.id"
              :label="`${option.version ?? option.title ?? option.id} · ${datetime(option.created_at)}`"
              :value="option.id"
            />
          </el-select>
        </label>
      </div>

      <SpecList v-if="comparison" :rows="comparison.rows" />
      <p v-else class="compare__hint">
        选择两份存档后，这里会列出版本、用例数、通过率、失败与阻塞的逐项变化。
      </p>
    </section>
  </div>
</template>

<style scoped>
.archive {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: var(--page-max);
  margin: 0 auto;
}

.archive__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.archive__title {
  font-family: var(--font-doc);
  font-size: var(--fs-xl);
  font-weight: 600;
  letter-spacing: 0.01em;
}

.archive__sub {
  margin-top: 2px;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

.panel__meta {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
}

.filters {
  gap: var(--space-2);
  flex-wrap: wrap;
}

.filters__search {
  flex: 1;
  min-width: 220px;
}

.filters__verdict {
  width: 140px;
}

.archive__table :deep(.cell) {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.archive__table :deep(td .cell) {
  align-items: flex-start;
}

.archive__table :deep(.is-right .cell) {
  align-items: flex-end;
}

.cell-time {
  font-family: var(--font-data);
  font-size: var(--fs-sm);
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}

.cell-sub {
  font-size: var(--fs-micro);
  color: var(--ink-3);
  max-width: 42ch;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: var(--fs-base);
  text-align: left;
  cursor: pointer;
  text-underline-offset: 3px;
}

.cell-link:hover {
  color: var(--accent);
  text-decoration: underline;
}

.cell-mono {
  font-family: var(--font-data);
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.cell-num {
  font-family: var(--font-data);
  font-size: var(--fs-base);
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}

.cell-verdict {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-sm);
}

.cell-verdict__mark {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  flex-shrink: 0;
}

.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 2px;
}

/* 窄屏记录单：同一条数据换成卡片式读法，替掉 1138px 固定列的横向滚动 */
.slips {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin: 0;
  padding: var(--space-4);
  list-style: none;
}

.slip {
  padding: var(--space-3);
  border: var(--hairline);
  border-radius: var(--radius);
}

.slip__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.slip__stamp {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.slip__title {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--fs-md);
}

.slip__excerpt {
  margin-top: 4px;
  font-size: var(--fs-micro);
  line-height: 1.6;
  color: var(--ink-3);
}

.slip__readouts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3) var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: var(--hairline);
}

.slip__field {
  min-width: 0;
}

.slip__field:first-child {
  grid-column: 1 / -1;
}

.slip__field dt {
  font-size: var(--fs-micro);
  letter-spacing: 0.12em;
  color: var(--ink-3);
}

.slip__field dd {
  margin: 3px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slip__actions {
  margin-top: var(--space-3);
  justify-content: flex-start;
  gap: var(--space-2);
}

.archive__empty {
  padding: var(--space-6) var(--space-4);
}

.archive__empty-title {
  font-size: var(--fs-md);
  color: var(--ink);
}

.archive__empty-text {
  margin: 6px 0 var(--space-4);
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.archive__pager {
  display: flex;
  justify-content: flex-end;
  padding: var(--space-3) var(--space-4);
  border-top: var(--hairline-soft);
}

.compare__pickers {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: var(--hairline-soft);
  flex-wrap: wrap;
}

.compare__pick {
  flex: 1;
  min-width: 220px;
}

.compare__pick-label {
  display: block;
  margin-bottom: 5px;
  font-size: var(--fs-micro);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-3);
}

.compare__arrow {
  padding-bottom: 8px;
  font-family: var(--font-data);
  color: var(--ink-3);
}

.compare__hint {
  padding: var(--space-4);
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

@media (max-width: 720px) {
  .archive__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
