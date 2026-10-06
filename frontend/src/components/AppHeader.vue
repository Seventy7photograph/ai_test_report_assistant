<script setup lang="ts">
import { useSystem } from '@/stores/system'

const { status, configured } = useSystem()

const modes = [
  { to: '/', label: '工作台' },
  { to: '/archive', label: '档案' },
  { to: '/settings', label: '设置' },
]
</script>

<template>
  <header class="case">
    <RouterLink to="/" class="case__plate">
      <svg class="case__mark" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <path d="M1 15.5h20" stroke="currentColor" stroke-width="1" />
        <path d="M2 15.5v-3" stroke="currentColor" stroke-width="1" />
        <path d="M5 15.5v-5" stroke="currentColor" stroke-width="1" />
        <path d="M8 15.5v-3" stroke="currentColor" stroke-width="1" />
        <path d="M11 15.5v-9" stroke="currentColor" stroke-width="1" />
        <path d="M14 15.5v-3" stroke="currentColor" stroke-width="1" />
        <path d="M17 15.5v-5" stroke="currentColor" stroke-width="1" />
        <path d="M20 15.5v-3" stroke="currentColor" stroke-width="1" />
        <path d="M11 1.5V5.4" stroke="currentColor" stroke-width="1.4" />
        <path d="M9.3 5.4h3.4L11 8.3z" fill="currentColor" />
      </svg>
      <span class="case__name">{{ status?.app_name ?? 'AI 测试报告助手' }}</span>
      <span class="case__version">v{{ status?.app_version ?? '2.0.0' }}</span>
    </RouterLink>

    <nav class="case__modes" aria-label="主导航">
      <RouterLink v-for="mode in modes" :key="mode.to" :to="mode.to" class="case__mode">
        {{ mode.label }}
      </RouterLink>
    </nav>

    <dl class="case__readouts">
      <div class="case__readout">
        <dt>模型</dt>
        <dd class="case__readout-value"><span class="case__readout-text">{{ status?.model ?? '——' }}</span></dd>
      </div>
      <div class="case__readout">
        <dt>存档</dt>
        <dd class="case__readout-value">{{ status?.report_count ?? '——' }}</dd>
      </div>
      <div class="case__readout">
        <dt>服务</dt>
        <dd class="case__readout-value">
          <span class="case__led" :class="configured ? 'is-on' : 'is-off'" aria-hidden="true" />
          {{ configured ? '就绪' : '未配置' }}
        </dd>
      </div>
    </dl>
  </header>
</template>

<style scoped>
.case {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: var(--space-5);
  height: var(--shell-height);
  padding: 0 var(--space-5);
  background: var(--case);
  border-bottom: 1px solid var(--case-line);
  color: var(--case-ink);
}

/* 铭牌 */
.case__plate {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  color: inherit;
  text-decoration: none;
  flex-shrink: 0;
}

.case__plate:hover {
  text-decoration: none;
}

.case__mark {
  width: 20px;
  height: 20px;
  color: var(--case-accent);
  align-self: center;
  flex-shrink: 0;
  transition: color 160ms ease-out;
}

.case__plate:hover .case__mark {
  color: var(--case-ink);
}

.case__name {
  font-size: var(--fs-base);
  font-weight: 500;
  letter-spacing: 0.06em;
}

.case__version {
  font-family: var(--font-data);
  font-size: var(--fs-micro);
  color: var(--case-ink-2);
  letter-spacing: 0.04em;
}

/* 模式选择：标准页签，指示块而非描边 */
.case__modes {
  display: flex;
  align-items: stretch;
  height: 100%;
  gap: var(--space-1);
}

.case__mode {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 0 var(--space-3);
  color: var(--case-ink-2);
  font-size: var(--fs-sm);
  letter-spacing: 0.08em;
  text-decoration: none;
  transition: color 140ms ease-out;
}

.case__mode:hover {
  color: var(--case-ink);
  text-decoration: none;
}

.case__mode::after {
  content: "";
  position: absolute;
  left: var(--space-3);
  right: var(--space-3);
  bottom: 0;
  height: 2px;
  background: var(--case-accent);
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
}

.case__mode:hover::after {
  transform: scaleX(0.4);
}

.case__mode.router-link-active {
  color: var(--case-ink);
}

.case__mode.router-link-active::after {
  transform: scaleX(1);
}

/* 实时读数 */
.case__readouts {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  margin: 0;
  margin-left: auto;
}

.case__readout {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.case__readout dt {
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--case-ink-2);
}

.case__readout-value {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-family: var(--font-data);
  font-size: var(--fs-sm);
  font-variant-numeric: tabular-nums;
  color: var(--case-ink);
  min-width: 0;
}

.case__readout-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 18ch;
}

.case__led {
  width: 7px;
  height: 7px;
  border-radius: 1px;
  border: 1px solid var(--case-ink-2);
  flex-shrink: 0;
}

.case__led.is-on {
  border-color: var(--pass-fill);
  background: var(--pass-fill);
}

.case__led.is-off {
  border-color: var(--blocked-fill);
}

@media (max-width: 1080px) {
  .case__readout:first-child {
    display: none;
  }
}

@media (max-width: 860px) {
  .case__readouts {
    display: none;
  }
}

@media (max-width: 560px) {
  .case {
    gap: var(--space-3);
    padding: 0 var(--space-3);
  }

  .case__version {
    display: none;
  }

  .case__mode {
    padding: 0 var(--space-2);
    letter-spacing: 0.04em;
  }

  .case__mode::after {
    left: var(--space-2);
    right: var(--space-2);
  }
}
</style>
