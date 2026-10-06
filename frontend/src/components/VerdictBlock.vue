<script setup lang="ts">
import { computed } from 'vue'
import type { Metrics, Verdict } from '@/api/types'
import { VERDICT_TONE } from '@/utils/format'

const props = defineProps<{
  metrics: Metrics | null
  /** pressed = 已定值并盖章；pending = 有数据但报告尚未生成 */
  phase: 'idle' | 'pending' | 'pressed'
}>()

const verdict = computed<Verdict>(() => props.metrics?.verdict ?? 'unknown')

const label = computed(() => {
  if (props.metrics) return props.metrics.verdict_label
  return '尚未判定'
})

const reasons = computed(() => props.metrics?.verdict_reasons ?? [])
</script>

<template>
  <section class="verdict" :aria-label="`系统判定：${label}`">
    <div class="verdict__stamp">
      <span
        class="stamp"
        :class="[`stamp--${verdict}`, { 'stamp--pressed': phase === 'pressed' }]"
        :style="{ color: VERDICT_TONE[verdict] }"
      >
        {{ label }}
      </span>
    </div>

    <div class="verdict__reasons">
      <p class="rule-label">判定依据</p>
      <ul v-if="reasons.length" class="verdict__list">
        <li v-for="reason in reasons" :key="reason">{{ reason }}</li>
      </ul>
      <p v-else class="verdict__hint">
        贴入测试数据后，这里会列出判定所依据的具体条件。
      </p>
    </div>
  </section>
</template>

<style scoped>
.verdict {
  display: flex;
  align-items: flex-start;
  gap: var(--space-5);
  padding: var(--space-4);
  border-bottom: var(--hairline-soft);
}

.verdict__stamp {
  flex-shrink: 0;
  padding-top: 2px;
}

.verdict__reasons {
  min-width: 0;
  flex: 1;
}

.verdict__list {
  margin: var(--space-2) 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.verdict__list li {
  position: relative;
  padding-left: 14px;
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.verdict__list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.62em;
  width: 5px;
  height: 1px;
  background: var(--ink-3);
}

.verdict__hint {
  margin-top: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

@media (max-width: 560px) {
  .verdict {
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>
