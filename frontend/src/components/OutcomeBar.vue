<script setup lang="ts">
import { computed } from 'vue'
import type { Metrics } from '@/api/types'

const props = defineProps<{ metrics: Metrics | null }>()

const segments = computed(() => {
  const m = props.metrics
  if (!m || m.total <= 0) return []
  return [
    { key: 'passed', label: '通过', count: m.passed, color: 'var(--pass-fill)' },
    { key: 'failed', label: '失败', count: m.failed, color: 'var(--fail-fill)' },
    { key: 'blocked', label: '阻塞', count: m.blocked, color: 'var(--blocked-fill)' },
    { key: 'skipped', label: '未执行', count: m.skipped, color: 'var(--skipped-fill)' },
  ]
    .filter((segment) => segment.count > 0)
    .map((segment) => ({
      ...segment,
      percent: (segment.count / m.total) * 100,
    }))
})

const description = computed(() => {
  if (!segments.value.length) return '用例分布：暂无数据'
  return `用例分布：${segments.value.map((s) => `${s.label} ${s.count} 条`).join('，')}`
})
</script>

<template>
  <figure class="dist" role="img" :aria-label="description">
    <div class="dist__track" :class="{ 'is-empty': !segments.length }">
      <span
        v-for="segment in segments"
        :key="segment.key"
        class="dist__seg"
        :style="{ width: `${segment.percent}%`, background: segment.color }"
        :title="`${segment.label} ${segment.count} 条 · ${segment.percent.toFixed(1)}%`"
      />
    </div>
    <figcaption class="dist__caption">
      <span>{{ metrics ? `共 ${metrics.total} 条` : '等待送检' }}</span>
      <span v-if="metrics">执行 {{ metrics.total - metrics.blocked - metrics.skipped }} 条</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.dist {
  margin: 0;
  padding: var(--space-3) var(--space-4) var(--space-4);
}

.dist__track {
  display: flex;
  height: 10px;
  border: 1px solid var(--rule);
  border-radius: 2px;
  overflow: hidden;
  background: var(--sheet);
}

.dist__track.is-empty {
  background: repeating-linear-gradient(
    90deg,
    var(--rule-soft) 0 6px,
    transparent 6px 12px
  );
  border-style: dashed;
}

.dist__seg {
  display: block;
  height: 100%;
}

.dist__seg + .dist__seg {
  border-left: 1px solid var(--sheet);
}

.dist__caption {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  margin-top: var(--space-2);
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  font-variant-numeric: tabular-nums;
  color: var(--ink-3);
}
</style>
