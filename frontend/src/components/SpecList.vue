<script setup lang="ts">
defineProps<{ rows: { label: string; value: string; note?: string }[] }>()
</script>

<template>
  <dl class="spec">
    <div v-for="row in rows" :key="row.label" class="spec__row">
      <dt>{{ row.label }}</dt>
      <dd>
        <span class="spec__value">{{ row.value }}</span>
        <span v-if="row.note" class="spec__note">{{ row.note }}</span>
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.spec {
  margin: 0;
}

.spec__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 9px var(--space-4);
  border-bottom: var(--hairline-soft);
}

.spec__row:last-child {
  border-bottom: 0;
}

.spec__row dt {
  flex-shrink: 0;
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.spec__row dd {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin: 0;
  min-width: 0;
  text-align: right;
}

.spec__value {
  font-family: var(--font-data);
  font-size: var(--fs-base);
  font-variant-numeric: tabular-nums;
  color: var(--ink);
  overflow-wrap: anywhere;
}

.spec__note {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  color: var(--ink-3);
  white-space: nowrap;
}
</style>
