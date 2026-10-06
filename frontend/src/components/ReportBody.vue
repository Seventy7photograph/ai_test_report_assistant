<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps<{ source: string; streaming?: boolean }>()

const html = computed(() => renderMarkdown(props.source))
</script>

<template>
  <article class="doc">
    <div class="doc__body" v-html="html" />
    <span v-if="streaming" class="doc__caret" aria-hidden="true" />
  </article>
</template>

<style scoped>
.doc {
  position: relative;
  padding: var(--space-5) var(--space-5) var(--space-6);
  font-family: var(--font-doc);
  font-size: var(--fs-md);
  line-height: 1.85;
  color: var(--ink);
  max-width: 74ch;
}

.doc__caret {
  display: inline-block;
  width: 8px;
  height: 1.05em;
  margin-left: 2px;
  background: var(--accent);
  vertical-align: -0.16em;
  animation: caret-blink 1.05s steps(1, end) infinite;
}

@keyframes caret-blink {
  0%,
  50% {
    opacity: 1;
  }
  50.01%,
  100% {
    opacity: 0;
  }
}

.doc__body :deep(h1),
.doc__body :deep(h2),
.doc__body :deep(h3) {
  font-family: var(--font-ui);
  letter-spacing: 0.04em;
  color: var(--ink);
}

.doc__body :deep(h2) {
  font-size: var(--fs-base);
  font-weight: 600;
  margin: 30px 0 10px;
  padding-bottom: 6px;
  border-bottom: var(--hairline);
}

.doc__body :deep(h2:first-child) {
  margin-top: 0;
}

.doc__body :deep(h3) {
  font-size: var(--fs-md);
  font-weight: 600;
  margin: 22px 0 6px;
}

.doc__body :deep(p) {
  margin: 0 0 10px;
}

.doc__body :deep(ul),
.doc__body :deep(ol) {
  margin: 0 0 12px;
  padding-left: 1.35em;
}

.doc__body :deep(li) {
  margin-bottom: 4px;
}

.doc__body :deep(li::marker) {
  color: var(--ink-3);
}

.doc__body :deep(strong) {
  font-weight: 600;
}

.doc__body :deep(code) {
  font-family: var(--font-data);
  font-size: 0.86em;
  background: var(--rule-soft);
  padding: 1px 5px;
  border-radius: 2px;
}

.doc__body :deep(pre) {
  margin: 0 0 14px;
  padding: var(--space-3) var(--space-4);
  background: var(--face);
  border: var(--hairline);
  border-radius: var(--radius);
  overflow-x: auto;
}

.doc__body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 12.5px;
  line-height: 1.7;
}

.doc__body :deep(table) {
  width: 100%;
  margin: 0 0 14px;
  border-collapse: collapse;
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
}

.doc__body :deep(th),
.doc__body :deep(td) {
  border-bottom: var(--hairline-soft);
  padding: 7px 10px;
  text-align: left;
}

.doc__body :deep(th) {
  font-size: var(--fs-micro);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-3);
  border-bottom: var(--hairline);
}

.doc__body :deep(blockquote) {
  margin: 0 0 12px;
  padding-left: var(--space-4);
  border-left: 1px solid var(--rule);
  color: var(--ink-2);
}

.doc__body :deep(a) {
  text-decoration: underline;
  text-decoration-color: var(--rule);
}

.doc__body :deep(a:hover) {
  text-decoration-color: var(--accent);
}

.doc__body :deep(hr) {
  border: 0;
  border-top: var(--hairline);
  margin: 24px 0;
}

@media (max-width: 720px) {
  .doc {
    padding: var(--space-4) var(--space-3) var(--space-5);
    font-size: 14px;
  }
}
</style>
