<template>
  <!-- 大屏全局布局壳：顶栏 + 70/30 主体 + 底部固定按钮 -->
  <div class="dash-root relative flex h-screen w-screen flex-col overflow-hidden bg-gradient-to-br from-dash-bg-from to-dash-bg-to">
    <!-- 科技网格纹理背景 -->
    <div
      class="pointer-events-none absolute inset-0 opacity-[0.07]"
      :style="gridBgStyle"
    />
    <!-- 微弱粒子层 -->
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        v-for="i in 24"
        :key="i"
        class="absolute h-1 w-1 rounded-full bg-dash-blue opacity-30"
        :style="particleStyle(i)"
      />
    </div>

    <!-- ===== 顶部导航栏 ===== -->
    <header class="relative z-20 flex h-[64px] shrink-0 items-center justify-between border-b border-[rgba(35,152,255,0.2)] px-6 backdrop-blur-md">
      <!-- 左侧：Logo + 标题 -->
      <div class="flex min-w-[280px] items-center gap-3">
        <div class="eeg-logo relative flex h-10 w-10 items-center justify-center">
          <svg viewBox="0 0 40 40" class="h-full w-full">
            <circle cx="20" cy="20" r="18" fill="none" stroke="rgba(35,152,255,0.4)" stroke-width="1" />
            <path
              class="eeg-wave"
              d="M4,20 Q10,8 16,20 T28,20 T36,20"
              fill="none"
              stroke="#2398ff"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </div>
        <h1 class="title-gradient whitespace-nowrap text-sm font-bold md:text-base lg:text-lg">
          基于时空频特征融合的脑电情绪识别系统
        </h1>
      </div>

      <!-- 中间：全局功能导航 -->
      <nav class="flex flex-1 items-center justify-center gap-1 px-4">
        <span
          v-if="acquisitionModeLabel"
          class="mode-badge"
          :class="acquisitionModeType === 'self' ? 'mode-badge-self' : 'mode-badge-seed'"
          :title="`当前数据源：${acquisitionModeLabel}（在实验范式页切换）`"
        >
          <i :class="acquisitionModeType === 'self' ? 'fas fa-head-side-brain' : 'fas fa-database'" />
          {{ acquisitionModeLabel }}
        </span>
        <button
          v-for="tab in navTabs"
          :key="tab.key"
          class="dash-nav-tab"
          :class="{ active: activeTab === tab.key }"
          @click="onTabClick(tab.key)"
        >
          {{ tab.label }}
        </button>
      </nav>

      <!-- 右侧：功能按钮组 -->
      <div class="flex min-w-[280px] items-center justify-end gap-2">
        <button class="dash-action-btn primary" @click="$emit('fullscreen')">
          <i class="fas fa-expand mr-1" />{{ isFullscreen ? '退出全屏' : '全屏报告' }}
        </button>
        <button class="dash-action-btn" @click="$emit('export')">
          <i class="fas fa-file-export mr-1" />导出报告
        </button>
        <button class="dash-action-btn" @click="$emit('settings')">
          <i class="fas fa-cog mr-1" />系统设置
        </button>
        <button class="dash-action-btn" title="用户信息">
          <i class="fas fa-user-circle mr-1" />用户
        </button>
      </div>
    </header>

    <!-- ===== 主体分栏：数据处理步骤左 2/3 + 右 1/3，其余步骤左侧全宽 ===== -->
    <main class="relative z-10 flex min-h-0 flex-1 gap-4 px-5 py-4">
      <section
        class="glass-panel flex min-h-0 min-w-0 flex-col overflow-hidden p-4"
        :class="showRightPanel ? 'flex-[2] dash-col-data' : 'flex-1'"
      >
        <div class="dash-slot-inner" :class="showRightPanel ? 'dash-slot-fill' : 'min-h-0 flex-1 overflow-y-auto overflow-x-hidden'">
          <slot name="left" />
        </div>
      </section>

      <aside
        v-if="showRightPanel"
        class="glass-panel dash-col-data flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden p-4"
      >
        <div class="dash-slot-fill">
          <slot name="right" />
        </div>
      </aside>
    </main>

    <!-- ===== 底部固定下一步按钮 ===== -->
    <button
      v-if="footerVisible"
      class="dash-footer-btn"
      @click="$emit('footer-action')"
    >
      {{ footerLabel }}
      <i class="fas fa-arrow-right ml-2" />
    </button>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    activeTab: number;
    isFullscreen?: boolean;
    footerLabel?: string;
    footerVisible?: boolean;
    /** 是否显示右侧预览栏（仅数据处理步骤为 true） */
    showRightPanel?: boolean;
    /** 当前采集模式标签（顶栏展示，非导航 Tab） */
    acquisitionModeLabel?: string;
    /** seed | self — 顶栏徽章配色 */
    acquisitionModeType?: 'seed' | 'self';
  }>(),
  {
    isFullscreen: false,
    footerLabel: '下一步：进入特征提取学习模块',
    footerVisible: true,
    showRightPanel: true,
    acquisitionModeLabel: '',
    acquisitionModeType: 'seed',
  }
);

const emit = defineEmits<{
  'update:activeTab': [value: number];
  'tab-change': [value: number];
  fullscreen: [];
  export: [];
  settings: [];
  perf: [];
  'footer-action': [];
}>();

const navTabs = [
  { key: 0, label: '实验范式' },
  { key: 1, label: '数据处理' },
  { key: 2, label: '特征提取' },
  { key: 3, label: '情绪识别' },
  { key: 4, label: '可视化展示' },
  { key: 5, label: '模型性能' },
];

const gridBgStyle = computed(() => ({
  backgroundImage: `
    linear-gradient(rgba(35,152,255,0.5) 1px, transparent 1px),
    linear-gradient(90deg, rgba(35,152,255,0.5) 1px, transparent 1px)
  `,
  backgroundSize: '40px 40px',
}));

function particleStyle(i: number) {
  const x = (i * 17 + 13) % 100;
  const y = (i * 23 + 7) % 100;
  const delay = (i % 8) * 0.5;
  return {
    left: `${x}%`,
    top: `${y}%`,
    animation: `pulseSoft 3s ease-in-out ${delay}s infinite`,
  };
}

function onTabClick(key: number) {
  if (key === 5) {
    emit('perf');
    return;
  }
  emit('update:activeTab', key);
  emit('tab-change', key);
}
</script>

<style scoped>
.title-gradient {
  background: linear-gradient(135deg, #ffffff 0%, #2398ff 50%, #914cff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 30px rgba(35, 152, 255, 0.3);
}

.eeg-wave {
  animation: waveMove 2s ease-in-out infinite;
}

@keyframes waveMove {
  0%,
  100% {
    d: path('M4,20 Q10,8 16,20 T28,20 T36,20');
  }
  50% {
    d: path('M4,20 Q10,32 16,20 T28,12 T36,20');
  }
}

.dash-slot-fill {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.dash-col-data {
  --data-step-top-h: 96px;
}

.mode-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  white-space: nowrap;
  margin-right: 8px;
  display: none;
  align-items: center;
  gap: 4px;
}
@media (min-width: 1024px) {
  .mode-badge {
    display: inline-flex;
  }
}
.mode-badge-seed {
  color: #66ccff;
  border: 1px solid rgba(0, 180, 255, 0.4);
  background: rgba(0, 100, 200, 0.15);
}
.mode-badge-self {
  color: #ffaa66;
  border: 1px solid rgba(255, 140, 60, 0.4);
  background: rgba(255, 120, 40, 0.12);
}
</style>
