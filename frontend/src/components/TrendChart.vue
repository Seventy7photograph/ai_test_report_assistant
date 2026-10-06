<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { TrendPoint, Verdict } from '@/api/types'
import { datetime, percent, VERDICT_FILL } from '@/utils/format'

const props = defineProps<{ points: TrendPoint[] }>()

const THRESHOLD = 0.95

/**
 * 画布几何随视口切换，而不是把一块 1000 单位的画布等比压扁。
 * 压扁到 390px 时 10 单位字号只剩约 3px，刻度、点标签和判定色块都读不出来；
 * 改用窄画布后单位密度下降，但字号仍按作者尺寸渲染。
 */
const NARROW_QUERY = '(max-width: 720px)'
const WIDE_GEO = {
  width: 1000,
  height: 224,
  pad: { top: 16, right: 26, bottom: 42, left: 56 },
  tickCount: 4,
}
const NARROW_GEO = {
  width: 360,
  height: 240,
  pad: { top: 14, right: 12, bottom: 48, left: 38 },
  tickCount: 2,
}

const narrow = ref(false)
let media: MediaQueryList | null = null

function syncNarrow(event: MediaQueryList | MediaQueryListEvent) {
  narrow.value = event.matches
}

onMounted(() => {
  media = window.matchMedia(NARROW_QUERY)
  syncNarrow(media)
  media.addEventListener('change', syncNarrow)
})

onBeforeUnmount(() => {
  media?.removeEventListener('change', syncNarrow)
})

const geo = computed(() => (narrow.value ? NARROW_GEO : WIDE_GEO))
const plotWidth = computed(() => geo.value.width - geo.value.pad.left - geo.value.pad.right)
const plotHeight = computed(() => geo.value.height - geo.value.pad.top - geo.value.pad.bottom)

/**
 * 纵轴不写死 0–100%：全量程下 90% 与 99% 会挤成一条线，看不出发布风险。
 * 下界按实际数据自适应，并把实际数值标在轴上，读者看到的就是真实刻度。
 */
const domain = computed(() => {
  const rates = props.points.map((point) => point.pass_rate)
  const lowest = rates.length ? Math.min(...rates) : 0
  const low = Math.max(0, Math.min(0.8, Math.floor((lowest - 0.04) * 10) / 10))
  return { low, high: 1 }
})

const yFor = (rate: number) => {
  const { low, high } = domain.value
  const ratio = (rate - low) / (high - low)
  return geo.value.pad.top + (1 - Math.min(Math.max(ratio, 0), 1)) * plotHeight.value
}

const ticks = computed(() => {
  const { low, high } = domain.value
  const count = geo.value.tickCount
  return Array.from({ length: count + 1 }, (_, index) => low + ((high - low) * index) / count)
})

const coordinates = computed(() =>
  props.points.map((point, index) => {
    const ratio = props.points.length > 1 ? index / (props.points.length - 1) : 0.5
    return {
      point,
      x: geo.value.pad.left + ratio * plotWidth.value,
      y: yFor(point.pass_rate),
    }
  }),
)

const path = computed(() =>
  coordinates.value
    .map((item, index) => `${index === 0 ? "M" : "L"}${item.x.toFixed(1)} ${item.y.toFixed(1)}`)
    .join(" "),
)

function pointAnchor(index: number): string {
  if (index === 0) return "start"
  if (index === props.points.length - 1) return "end"
  return "middle"
}

const thresholdVisible = computed(
  () => THRESHOLD >= domain.value.low && THRESHOLD <= domain.value.high,
)

const showEveryLabel = computed(() => (narrow.value || props.points.length > 8 ? 2 : 1))

const legend: { verdict: Verdict; label: string }[] = [
  { verdict: 'pass', label: '建议发版' },
  { verdict: 'conditional', label: '有条件通过' },
  { verdict: 'reject', label: '不建议发版' },
  { verdict: 'unknown', label: '无法判定' },
]

const description = computed(() => {
  if (!props.points.length) return '通过率趋势：暂无数据'
  const latest = props.points[props.points.length - 1]
  return `通过率趋势：共 ${props.points.length} 个存档，最新一轮 ${latest.label} 通过率 ${percent(latest.pass_rate)}（${latest.verdict_label}）`
})
</script>

<template>
  <div class="trend">
    <p v-if="points.length < 2" class="trend__empty">
      至少需要两份带指标的存档才能画出趋势。当前 {{ points.length }} 份。
    </p>

    <template v-else>
      <svg
        class="trend__svg"
        :viewBox="`0 0 ${geo.width} ${geo.height}`"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        :aria-label="description"
      >
        <!-- 刻度网格：0 / 25 / 50 / 75 / 100 -->
        <g>
          <template v-for="tick in ticks" :key="`grid-${tick}`">
            <line
              :x1="geo.pad.left"
              :x2="geo.width - geo.pad.right"
              :y1="yFor(tick)"
              :y2="yFor(tick)"
              stroke="var(--rule-soft)"
              stroke-width="1"
            />
            <text
              :x="geo.pad.left - 10"
              :y="yFor(tick) + 3"
              text-anchor="end"
              class="trend__tick"
            >
              {{ (tick * 100).toFixed(tick < 0.995 ? 1 : 0) }}%
            </text>
          </template>
        </g>

        <!-- 判定线：失败率 5% 的边界，即通过率 95% -->
        <template v-if="thresholdVisible">
          <line
            :x1="geo.pad.left"
            :x2="geo.width - geo.pad.right"
            :y1="yFor(THRESHOLD)"
            :y2="yFor(THRESHOLD)"
            stroke="var(--ink-3)"
            stroke-width="1"
            stroke-dasharray="3 4"
          />
          <text :x="geo.width - geo.pad.right" :y="yFor(THRESHOLD) - 7" text-anchor="end" class="trend__threshold">
            95% 判定线
          </text>
        </template>

        <path :d="path" fill="none" stroke="var(--ink)" stroke-width="1.5" stroke-linejoin="round" />

        <!-- 每个点按判定着色：色块即数据 -->
        <g v-for="(item, index) in coordinates" :key="item.point.id">
          <rect
            :x="item.x - 3.5"
            :y="item.y - 3.5"
            width="7"
            height="7"
            :fill="VERDICT_FILL[item.point.verdict]"
            stroke="var(--sheet)"
            stroke-width="1.5"
          />
          <rect :x="item.x - 16" :y="geo.pad.top" width="32" :height="plotHeight" fill="transparent">
            <title>
              {{ item.point.label }} · {{ percent(item.point.pass_rate) }} · {{ item.point.verdict_label }}
              （{{ datetime(item.point.created_at) }}）
            </title>
          </rect>
          <text
            v-if="index % showEveryLabel === 0"
            :x="item.x"
            :y="geo.height - geo.pad.bottom + 18"
            :text-anchor="pointAnchor(index)"
            class="trend__label"
          >
            {{ item.point.label }}
          </text>
        </g>
      </svg>

      <ul class="trend__legend">
        <li v-for="entry in legend" :key="entry.verdict">
          <i class="trend__swatch" :style="{ background: VERDICT_FILL[entry.verdict] }" aria-hidden="true" />
          {{ entry.label }}
        </li>
        <li class="trend__legend-rule">
          <i class="trend__dash" aria-hidden="true" />
          95% 判定线
        </li>
        <li class="trend__legend-rule">
          <i class="trend__line" aria-hidden="true" />
          通过率
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.trend {
  padding: var(--space-4);
}

.trend__empty {
  padding: var(--space-5) 0;
  text-align: center;
  font-size: var(--fs-sm);
  color: var(--ink-3);
}

.trend__svg {
  display: block;
  width: 100%;
  max-width: 1000px;
  height: auto;
  margin: 0 auto;
}

.trend__tick,
.trend__label,
.trend__threshold {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
  fill: var(--ink-3);
  font-size: 10px;
}

.trend__threshold {
  font-size: 10px;
  letter-spacing: 0.04em;
}

.trend__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
  margin: var(--space-3) 0 0;
  padding: 0;
  list-style: none;
  font-size: var(--fs-micro);
  color: var(--ink-2);
}

.trend__legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.trend__swatch {
  width: 7px;
  height: 7px;
  border-radius: 1px;
}

.trend__dash {
  width: 16px;
  height: 0;
  border-top: 1px dashed var(--ink-3);
}

.trend__line {
  width: 16px;
  height: 0;
  border-top: 1.5px solid var(--ink);
}
</style>
