<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Position, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import SpecList from '@/components/SpecList.vue'
import { api } from '@/api/client'
import type { LLMTestResult } from '@/api/types'
import { useSystem } from '@/stores/system'

const router = useRouter()
const { status, samples, load: reload } = useSystem()

const testing = ref(false)
const probe = ref<LLMTestResult | null>(null)
const probeError = ref<string | null>(null)

const serviceRows = computed(() => {
  const value = status.value
  if (!value) return []
  return [
    { label: '应用版本', value: `v${value.app_version}` },
    { label: '服务商', value: value.provider },
    { label: '当前模型', value: value.model, note: `${value.models.length} 个可切换` },
    { label: '接口地址', value: value.base_url },
    { label: '采样温度', value: String(value.temperature) },
    { label: '请求超时', value: `${value.timeout} s` },
    { label: '失败重试', value: `${value.max_retries} 次` },
    { label: 'API Key', value: value.llm_configured ? '已配置' : '未配置' },
  ]
})

const storageRows = computed(() => {
  const value = status.value
  if (!value) return []
  return [
    { label: '存储引擎', value: value.storage_backend },
    { label: '存档数量', value: `${value.report_count} 份` },
    { label: '数据文件', value: value.storage_path },
    { label: '前端产物', value: value.frontend_built ? '已构建（由后端托管）' : '未构建（开发模式）' },
  ]
})

async function runProbe() {
  testing.value = true
  probe.value = null
  probeError.value = null
  try {
    probe.value = await api.llmTest()
  } catch (error) {
    probeError.value = (error as Error).message
    ElMessage.error(probeError.value)
  } finally {
    testing.value = false
  }
}

function useSample(id: string) {
  void router.push({ name: 'workbench', query: { sample: id } })
}

onMounted(reload)
</script>

<template>
  <div class="settings">
    <header class="settings__head">
      <div>
        <h1 class="settings__title">设置</h1>
        <p class="settings__sub">服务配置来自后端 <code>.env</code>，界面只读。</p>
      </div>
      <el-button size="small" :icon="Refresh" @click="reload">重新读取</el-button>
    </header>

    <div class="settings__grid">
      <div class="settings__col">
      <section class="panel">
        <header class="panel__head">
          <h2 class="panel__title">模型服务</h2>
        </header>
        <SpecList :rows="serviceRows" />

        <div class="probe">
          <div class="probe__row">
            <el-button
              type="primary"
              :icon="Position"
              :loading="testing"
              :disabled="!status?.llm_configured"
              @click="runProbe"
            >
              探活模型服务
            </el-button>
            <span class="probe__hint">发送一条最小请求，确认真实可用并测量往返延迟。</span>
          </div>

          <div v-if="probe" class="probe__result is-ok">
            <span class="probe__latency">{{ probe.latency_ms }} ms</span>
            <span class="probe__detail">{{ probe.model }} · 回复「{{ probe.message }}」</span>
          </div>
          <div v-else-if="probeError" class="probe__result is-fail">
            <span class="probe__detail">{{ probeError }}</span>
          </div>
          <div v-else-if="!status?.llm_configured" class="probe__result is-idle">
            <span class="probe__detail">
              未配置 <code>LLM_API_KEY</code>。复制 <code>.env.example</code> 为 <code>.env</code> 并填写 Key 后重启服务。
            </span>
          </div>
        </div>
      </section>

      </div>

      <div class="settings__col">
      <section class="panel">
        <header class="panel__head">
          <h2 class="panel__title">本地存档</h2>
        </header>
        <SpecList :rows="storageRows" />
        <p class="settings__note">
          存档是项目内的单个 SQLite 文件，直接拷贝即可备份，删除即清空。
        </p>
      </section>

      <section class="panel">
        <header class="panel__head">
          <h2 class="panel__title">环境变量</h2>
        </header>
        <SpecList
          :rows="[
            { label: 'LLM_API_KEY', value: '必填', note: '模型服务的密钥' },
            { label: 'LLM_BASE_URL', value: 'https://api.deepseek.com', note: '任何兼容 Chat Completions 的地址' },
            { label: 'LLM_MODEL', value: 'deepseek-chat' },
            { label: 'LLM_MODELS', value: '可选', note: '逗号分隔，决定界面上的可选模型' },
            { label: 'LLM_TIMEOUT', value: '120', note: '秒' },
            { label: 'LLM_MAX_RETRIES', value: '2', note: '限流与 5xx 时的重试次数' },
            { label: 'DATA_DIR', value: './data', note: 'SQLite 存档目录' },
          ]"
        />
      </section>
      </div>
    </div>

    <section class="panel">
      <header class="panel__head">
        <h2 class="panel__title">样例数据</h2>
        <span class="panel__meta">演示值，不是真实项目数据</span>
      </header>
      <ul class="samples">
        <li v-for="sample in samples" :key="sample.id" class="samples__item">
          <div class="samples__text">
            <span class="samples__name">{{ sample.name }}</span>
            <span class="samples__desc">{{ sample.description }}</span>
          </div>
          <el-button size="small" @click="useSample(sample.id)">载入工作台</el-button>
        </li>
      </ul>
    </section>

  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 1100px;
  margin: 0 auto;
}

.settings__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.settings__title {
  font-family: var(--font-doc);
  font-size: var(--fs-xl);
  font-weight: 600;
}

.settings__sub {
  margin-top: 2px;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

.settings__sub code,
.probe__detail code {
  font-family: var(--font-data);
  font-size: 0.92em;
  background: var(--rule-soft);
  padding: 1px 5px;
  border-radius: 2px;
}

.settings__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: var(--space-4);
  align-items: start;
}

.settings__col {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 0;
}

.panel__meta {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.probe {
  padding: var(--space-4);
  border-top: var(--hairline);
}

.probe__row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.probe__hint {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.probe__result {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-top: var(--space-3);
  padding: var(--space-3);
  border: var(--hairline);
  border-radius: var(--radius);
  background: var(--face);
  flex-wrap: wrap;
}

.probe__result.is-ok {
  border-color: var(--pass);
}

.probe__result.is-fail {
  border-color: var(--fail);
}

.probe__latency {
  font-family: var(--font-data);
  font-size: var(--fs-lg);
  font-variant-numeric: tabular-nums;
  color: var(--pass);
}

.probe__detail {
  font-size: var(--fs-sm);
  color: var(--ink-2);
  word-break: break-word;
}

.probe__result.is-fail .probe__detail {
  color: var(--fail);
}

.settings__note {
  padding: var(--space-3) var(--space-4);
  border-top: var(--hairline-soft);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.samples {
  margin: 0;
  padding: 0;
  list-style: none;
}

.samples__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 11px var(--space-4);
  border-bottom: var(--hairline-soft);
}

.samples__item:last-child {
  border-bottom: 0;
}

.samples__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.samples__name {
  font-size: var(--fs-base);
  color: var(--ink);
}

.samples__desc {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}
</style>
