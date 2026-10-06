<script setup lang="ts">
import { onMounted } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import { useSystem } from '@/stores/system'

const { load, loadSamples } = useSystem()

onMounted(() => {
  void load()
  void loadSamples()
})
</script>

<template>
  <div class="app">
    <AppHeader />
    <main class="app__main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--face);
}

.app__main {
  flex: 1;
  min-width: 0;
  padding: var(--space-5) var(--space-5) var(--space-7);
}

@media (max-width: 720px) {
  .app__main {
    padding: var(--space-4) var(--space-3) var(--space-6);
  }
}
</style>
