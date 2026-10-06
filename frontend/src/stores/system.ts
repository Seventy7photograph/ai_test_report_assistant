import { computed, ref } from 'vue'
import { api } from '@/api/client'
import type { SampleDataset, SystemStatus } from '@/api/types'

/** 全局只需要一份：顶栏读数和设置页共用。 */
const status = ref<SystemStatus | null>(null)
const samples = ref<SampleDataset[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

export function useSystem() {
  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      status.value = await api.status()
    } catch (err) {
      error.value = (err as Error).message
    } finally {
      loading.value = false
    }
  }

  async function loadSamples(): Promise<void> {
    if (samples.value.length) return
    try {
      samples.value = await api.samples()
    } catch {
      samples.value = []
    }
  }

  return {
    status,
    samples,
    loading,
    error,
    load,
    loadSamples,
    configured: computed(() => status.value?.llm_configured ?? false),
    models: computed(() => status.value?.models ?? []),
  }
}
