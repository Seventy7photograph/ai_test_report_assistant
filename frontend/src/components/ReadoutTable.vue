<script setup lang="ts">
import { computed } from 'vue'
import type { Metrics } from '@/api/types'
import { percent } from '@/utils/format'

type Phase = 'idle' | 'pending' | 'pressed'

const props = defineProps<{
  metrics: Metrics | null
  phase: Phase
}>()

interface Row {
  key: string
  label: string
  value: string
  unit?: string
  note?: string
  mark?: string
}

const rows = computed<Row[]>(() => {
  const m = props.metrics
  if (!m) {
    return [
      { key: 'total', label: '用例总数', value: '——', unit: '条' },
      { key: 'passed', label: '通过', value: '——', unit: '条', mark: 'var(--pass-fill)' },
      { key: 'failed', label: '失败', value: '——', unit: '条', mark: 'var(--fail-fill)' },
      { key: 'blocked', label: '阻塞', value: '——', unit: '条', mark: 'var(--blocked-fill)' },
      { key: 'skipped', label: '未执行', value: '——', unit: '条', mark: 'var(--skipped-fill)' },
      { key: 'execution', label: '执行率', value: '——' },
      { key: 'effective', label: '有效通过率', value: '——' },
      { key: 'defects', label: '缺陷 · 未关闭 / 总数', value: '——' },
    ]
  }
  return [
    { key: 'total', label: '用例总数', value: String(m.total), unit: '条' },
    {
      key: 'passed',
      label: '通过',
      value: String(m.passed),
      unit: '条',
      note: percent(m.pass_rate),
      mark: 'var(--pass-fill)',
    },
    {
      key: 'failed',
      label: '失败',
      value: String(m.failed),
      unit: '条',
      note: percent(m.fail_rate),
      mark: 'var(--fail-fill)',
    },
    { key: 'blocked', label: '阻塞', value: String(m.blocked), unit: '条', mark: 'var(--blocked-fill)' },
    { key: 'skipped', label: '未执行', value: String(m.skipped), unit: '条', mark: 'var(--skipped-fill)' },
    { key: 'execution', label: '执行率', value: percent(m.execution_rate) },
    {
      key: 'effective',
      label: '有效通过率',
      value: percent(m.effective_pass_rate),
      note: `分母 ${m.executed}`,
    },
    {
      key: 'defects',
      label: '缺陷 · 未关闭 / 总数',
      value: `${m.defects_open} / ${m.defects_total}`,
      unit: '条',
    },
  ]
})

const isEmpty = computed(() => props.metrics === null)
const isLocked = computed(() => props.metrics !== null && props.phase === 'pressed')
</script>

<template>
  <dl class="readout">
    <div v-for="row in rows" :key="row.key" class="readout__row">
      <dt class="readout__label">
        <span v-if="row.mark" class="readout__mark" :style="{ background: row.mark }" aria-hidden="true" />
        {{ row.label }}
      </dt>
      <dd class="readout__cell">
        <span
          class="readout__value"
          :class="{
            'readout__value--locked': isLocked,
            'readout__value--empty': isEmpty,
          }"
        >{{ row.value }}</span>
        <span v-if="row.unit" class="readout__unit">{{ row.unit }}</span>
        <span class="readout__note">{{ row.note ?? '' }}</span>
      </dd>
    </div>
  </dl>

  <p v-if="metrics" class="readout__legend">
    通过率 = 通过 ÷ 用例总数（{{ metrics.total }} 条，未执行计入分母）；有效通过率 = 通过 ÷ 已执行条数。
  </p>
</template>

<style scoped>
.readout {
  display: flex;
  flex-direction: column;
  margin: 0;
}

.readout__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 9px var(--space-4);
  border-bottom: var(--hairline-soft);
}

.readout__row:last-child {
  border-bottom: 0;
}

.readout__legend {
  margin: 0;
  padding: 10px var(--space-4) 0;
  border-top: var(--hairline-soft);
  font-size: var(--fs-micro);
  line-height: 1.6;
  color: var(--ink-3);
}

.readout__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--ink-2);
  letter-spacing: 0.02em;
}

.readout__mark {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  flex-shrink: 0;
  transform: translateY(-1px);
}

.readout__cell {
  display: grid;
  grid-template-columns: minmax(48px, auto) 2.2em minmax(52px, auto);
  align-items: baseline;
  gap: 6px;
  margin: 0;
  text-align: right;
}

.readout__cell :deep(span) {
  white-space: nowrap;
}

.readout__value {
  font-family: var(--font-data);
  font-size: var(--fs-readout);
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
  letter-spacing: -0.01em;
  justify-self: end;
}

.readout__unit,
.readout__note {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
  justify-self: end;
}

/* 空态：还没有数据，读数不存在，不用青色假装它在读数 */
.readout__value--empty {
  color: var(--ink-3);
  border-bottom: 1px dashed var(--rule);
}

/* 定值：墨色 + 基线由左向右画实（见 base.css 的签名动作） */
.readout__value--locked {
  color: var(--ink);
}

@media (max-width: 560px) {
  .readout__row {
    padding: 8px var(--space-3);
  }

  .readout__value {
    font-size: 18px;
  }
}
</style>
