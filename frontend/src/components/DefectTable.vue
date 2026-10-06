<script setup lang="ts">
import { computed } from 'vue'
import type { Defect } from '@/api/types'
import { defectStatusColor, defectStatusDetail, priorityColor } from '@/utils/format'

const props = defineProps<{ defects: Defect[] }>()

const sorted = computed(() => {
  const rank = (priority: string | null) => {
    if (!priority) return 9
    const match = /^P(\d)$/.exec(priority)
    return match ? Number(match[1]) : 8
  }
  const statusRank = (status: string | null) => (status === 'open' ? 0 : 1)
  return [...props.defects].sort(
    (a, b) => statusRank(a.status) - statusRank(b.status) || rank(a.priority) - rank(b.priority),
  )
})
</script>

<template>
  <table class="defects">
    <caption class="u-visually-hidden">缺陷清单</caption>
    <thead>
      <tr>
        <th scope="col" class="defects__col-id">编号</th>
        <th scope="col" class="defects__col-pri">优先级</th>
        <th scope="col">模块</th>
        <th scope="col">状态</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(defect, index) in sorted" :key="defect.id ?? index">
        <td class="defects__id">{{ defect.id ?? '—' }}</td>
        <td>
          <span class="defects__pri" :style="{ color: priorityColor(defect.priority) }">
            {{ defect.priority ?? '—' }}
          </span>
        </td>
        <td class="defects__module">
          <span class="defects__title">{{ defect.title ?? defect.module ?? '—' }}</span>
          <span v-if="defect.title && defect.module" class="defects__sub">{{ defect.module }}</span>
        </td>
        <td>
          <span class="defects__status" :style="{ color: defectStatusColor(defect.status) }">
            <i
              class="defects__dot"
              :style="{ background: defectStatusColor(defect.status) }"
              aria-hidden="true"
            />
            {{ defectStatusDetail(defect.status, defect.status_raw) }}
          </span>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.defects {
  width: 100%;
  border-collapse: collapse;
}

.defects th {
  padding: 7px var(--space-4);
  white-space: nowrap;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-3);
  text-align: left;
  border-bottom: var(--hairline);
  background: var(--face);
}

.defects td {
  padding: 9px var(--space-4);
  font-size: var(--fs-sm);
  color: var(--ink-2);
  border-bottom: var(--hairline-soft);
  vertical-align: top;
}

.defects tr:last-child td {
  border-bottom: 0;
}

.defects__col-id {
  width: 13ch;
}

.defects__col-pri {
  width: 9ch;
}

.defects__id {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
  color: var(--ink);
  white-space: nowrap;
}

.defects__pri {
  font-family: var(--font-data);
  font-weight: 500;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.defects__module {
  min-width: 0;
}

.defects__title {
  display: block;
  color: var(--ink);
}

.defects__sub {
  display: block;
  margin-top: 2px;
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.defects__status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.defects__dot {
  width: 6px;
  height: 6px;
  border-radius: 1px;
  flex-shrink: 0;
}

@media (max-width: 720px) {
  .defects th,
  .defects td {
    padding: 8px var(--space-3);
  }

  .defects__col-id,
  .defects__col-pri {
    width: auto;
  }
}
</style>
