<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Delete, Position, Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import SpecList from '@/components/SpecList.vue'
import { api } from '@/api/client'
import type { LLMSettingsView, LLMTestResult } from '@/api/types'
import { useSystem } from '@/stores/system'

const router = useRouter()
const { status, samples, load: reload, loadSamples } = useSystem()

const view = ref<LLMSettingsView | null>(null)
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const testing = ref(false)

const baseUrl = ref('')
const model = ref('')
const modelList = ref('')
const apiKey = ref('')
const clearKey = ref(false)
const temperature = ref<number | null>(null)
const timeout = ref<number | null>(null)
const maxRetries = ref<number | null>(null)

const probe = ref<LLMTestResult | null>(null)
const probeError = ref<string | null>(null)

function parseModels(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function applyView(value: LLMSettingsView) {
  view.value = value
  baseUrl.value = value.base_url
  model.value = value.model
  modelList.value = value.models.join('\n')
  temperature.value = value.temperature
  timeout.value = value.timeout
  maxRetries.value = value.max_retries
  apiKey.value = ''
  clearKey.value = false
}

async function loadSettings() {
  loading.value = true
  try {
    applyView(await api.settings())
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

function sourceOf(key: string): string {
  return view.value?.sources?.[key] === 'saved' ? '界面保存' : '.env 默认'
}

function isSaved(key: string): boolean {
  return view.value?.sources?.[key] === 'saved'
}

const hasSaved = computed(() =>
  Object.values(view.value?.sources ?? {}).some((origin) => origin === 'saved'),
)

const dirty = computed(() => {
  const value = view.value
  if (!value) return false
  return (
    baseUrl.value.trim() !== value.base_url ||
    model.value.trim() !== value.model ||
    modelList.value.trim() !== value.models.join('\n') ||
    temperature.value !== value.temperature ||
    timeout.value !== value.timeout ||
    maxRetries.value !== value.max_retries ||
    apiKey.value.trim().length > 0 ||
    clearKey.value
  )
})

const keyHint = computed(() => {
  const value = view.value
  if (!value) return ''
  if (value.api_key_stored) return `已保存 ${value.api_key_masked ?? ''}（界面保存的 Key 优先于 .env）`
  if (value.api_key_set) return '当前使用 .env 里的 LLM_API_KEY'
  return '尚未配置 Key：填入后保存，或改用 .env'
})

async function save() {
  if (clearKey.value && !apiKey.value.trim()) {
    // 明确清除，避免"以为只是没填"
    try {
      await ElMessageBox.confirm('将删除已保存的 API Key，并回落到 .env 的 LLM_API_KEY。', '确认清除', {
        confirmButtonText: '清除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
  }

  saving.value = true
  try {
    const payload = {
      base_url: baseUrl.value.trim(),
      model: model.value.trim(),
      models: parseModels(modelList.value),
      temperature: temperature.value,
      timeout: timeout.value,
      max_retries: maxRetries.value,
      api_key: apiKey.value.trim() || null,
      clear_api_key: clearKey.value,
    }
    applyView(await api.saveSettings(payload))
    await reload()
    ElMessage.success('已保存，配置立即生效')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    saving.value = false
  }
}

async function resetToEnv() {
  try {
    await ElMessageBox.confirm('清空界面保存的全部配置，回落到后端 .env 默认。', '恢复默认', {
      confirmButtonText: '恢复',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  resetting.value = true
  try {
    applyView(await api.resetSettings())
    await reload()
    ElMessage.success('已恢复为 .env 默认')
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    resetting.value = false
  }
}

async function runTest() {
  testing.value = true
  probe.value = null
  probeError.value = null
  try {
    probe.value = await api.testSettings({
      base_url: baseUrl.value.trim() || null,
      model: model.value.trim() || null,
      api_key: apiKey.value.trim() || null,
      timeout: timeout.value,
    })
  } catch (error) {
    probeError.value = (error as Error).message
    ElMessage.error(probeError.value)
  } finally {
    testing.value = false
  }
}

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

const envRows = computed(() => {
  const value = view.value?.env
  if (!value) return []
  const models = value.models ?? []
  return [
    {
      label: 'LLM_API_KEY',
      value: value.api_key_set ? '已配置' : '未配置',
      note: '界面未填 Key 时使用',
    },
    {
      label: 'LLM_BASE_URL',
      value: value.base_url ?? '—',
      note: '任何兼容 Chat Completions 的地址',
    },
    { label: 'LLM_MODEL', value: value.model ?? '—' },
    {
      label: 'LLM_MODELS',
      value: models.length ? models.join('、') : '未设置（仅默认模型）',
      note: '逗号分隔，决定界面上的可选模型',
    },
    { label: 'LLM_TIMEOUT', value: `${value.timeout ?? 120}`, note: '秒' },
    {
      label: 'LLM_MAX_RETRIES',
      value: `${value.max_retries ?? 2}`,
      note: '限流与 5xx 时的重试次数',
    },
  ]
})

function useSample(id: string) {
  void router.push({ name: 'workbench', query: { sample: id } })
}

async function refreshAll() {
  await Promise.all([reload(), loadSettings(), loadSamples()])
}

onMounted(refreshAll)
</script>

<template>
  <div class="settings" v-loading="loading">
    <header class="settings__head">
      <div>
        <h1 class="settings__title">设置</h1>
        <p class="settings__sub">
          服务配置可在界面修改并保存，留空即回落到后端 <code>.env</code> 默认值。
        </p>
      </div>
      <el-button size="small" :icon="Refresh" @click="refreshAll">重新读取</el-button>
    </header>

    <section class="panel">
      <header class="panel__head">
        <h2 class="panel__title">模型服务</h2>
        <span class="panel__meta">
          <template v-if="view">当前生效 {{ view.model }} @ {{ view.base_url }}</template>
        </span>
      </header>

      <div class="form">
        <label class="field">
          <span class="field__label">
            接口地址
            <em class="tag" :class="isSaved('base_url') ? 'is-saved' : ''">{{ sourceOf('base_url') }}</em>
          </span>
          <el-input v-model="baseUrl" placeholder="https://api.deepseek.com" spellcheck="false" />
          <span v-if="view" class="field__hint">留空则用 .env：{{ view.env.base_url }}</span>
        </label>

        <label class="field">
          <span class="field__label">
            默认模型
            <em class="tag" :class="isSaved('model') ? 'is-saved' : ''">{{ sourceOf('model') }}</em>
          </span>
          <el-input v-model="model" placeholder="deepseek-chat" spellcheck="false" />
          <span v-if="view" class="field__hint">留空则用 .env：{{ view.env.model }}</span>
        </label>

        <label class="field">
          <span class="field__label">
            可选模型
            <em class="tag" :class="isSaved('models') ? 'is-saved' : ''">{{ sourceOf('models') }}</em>
          </span>
          <el-input
            v-model="modelList"
            type="textarea"
            :rows="3"
            resize="vertical"
            spellcheck="false"
            placeholder="每行一个，决定工作台里的可切换模型"
          />
        </label>

        <label class="field">
          <span class="field__label">
            API Key
            <em class="tag" :class="isSaved('api_key') ? 'is-saved' : ''">{{ sourceOf('api_key') }}</em>
          </span>
          <el-input
            v-model="apiKey"
            type="password"
            show-password
            :disabled="clearKey"
            placeholder="留空表示不改动已保存的 Key"
            autocomplete="off"
          />
          <span class="field__hint">{{ keyHint }}</span>
          <span class="field__check">
            <el-switch v-model="clearKey" size="small" />
            <span class="field__check-label">清除已保存的 Key，回落到 .env</span>
          </span>
        </label>

        <div class="form__row">
          <label class="field">
            <span class="field__label">采样温度</span>
            <el-input-number v-model="temperature" :min="0" :max="2" :step="0.1" :precision="1" controls-position="right" />
            <span class="field__hint">越低越稳定，0.2 适合报告类输出</span>
          </label>

          <label class="field">
            <span class="field__label">请求超时</span>
            <el-input-number v-model="timeout" :min="1" :max="600" :step="5" controls-position="right" />
            <span class="field__hint">秒</span>
          </label>

          <label class="field">
            <span class="field__label">失败重试</span>
            <el-input-number v-model="maxRetries" :min="0" :max="10" :step="1" controls-position="right" />
            <span class="field__hint">限流与 5xx 时</span>
          </label>
        </div>

        <div class="form__actions">
          <el-button type="primary" :icon="Check" :loading="saving" @click="save">保存配置</el-button>
          <el-button :icon="Position" :loading="testing" @click="runTest">测试连接</el-button>
          <el-button :icon="Delete" :loading="resetting" :disabled="!hasSaved" @click="resetToEnv">
            恢复后端默认
          </el-button>
          <span v-if="dirty" class="form__dirty">有未保存的改动</span>
        </div>

        <div v-if="probe" class="probe__result is-ok">
          <span class="probe__latency">{{ probe.latency_ms }} ms</span>
          <span class="probe__detail">{{ probe.model }} · 回复「{{ probe.message }}」</span>
        </div>
        <div v-else-if="probeError" class="probe__result is-fail">
          <span class="probe__detail">{{ probeError }}</span>
        </div>
      </div>
    </section>

    <div class="settings__grid">
      <div class="settings__col">
        <section class="panel">
          <header class="panel__head">
            <h2 class="panel__title">本地存档</h2>
          </header>
          <SpecList :rows="storageRows" />
          <p class="settings__note">
            存档是项目内的单个 SQLite 文件，直接拷贝即可备份，删除即清空。
            界面保存的配置也存在同一个文件里，删掉它就等于回到 .env 默认。
          </p>
        </section>
      </div>

      <div class="settings__col">
        <section class="panel">
          <header class="panel__head">
            <h2 class="panel__title">环境变量默认值</h2>
            <span class="panel__meta">界面留空时回落到这里</span>
          </header>
          <SpecList :rows="envRows" />
          <p class="settings__note">
            这是后端 <code>.env</code> 的实时值。在左侧保存过的字段会覆盖它；把左侧对应项留空再保存，就会回落到这里。
          </p>
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

.settings__sub code {
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
}

.form__row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: var(--space-4);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.field__label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--fs-sm);
  color: var(--ink-2);
}

.field__hint {
  font-size: var(--fs-micro);
  color: var(--ink-3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field__check {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.field__check-label {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.tag {
  padding: 0 5px;
  border: var(--hairline);
  border-radius: 2px;
  font-family: var(--font-data);
  font-size: 10px;
  font-style: normal;
  line-height: 16px;
  color: var(--ink-3);
}

.tag.is-saved {
  border-color: var(--accent);
  color: var(--accent);
}

.form__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
  padding-top: var(--space-3);
  border-top: var(--hairline);
}

.form__dirty {
  font-size: var(--fs-micro);
  color: var(--blocked);
}

.probe__result {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
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

@media (max-width: 720px) {
  .settings__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
