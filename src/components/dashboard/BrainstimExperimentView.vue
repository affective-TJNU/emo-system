<template>
  <div class="brainstim-page flex h-full min-h-0 flex-col">
    <div class="mb-4 flex shrink-0 items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="title-accent h-6 w-1 rounded-full" />
        <h2 class="text-lg font-bold text-white">brainstim 情绪实验范式</h2>
        <span class="page-tag">MetaBCI · PsychoPy ImageStim</span>
      </div>
    </div>

    <p class="page-intro shrink-0">
      {{ isLiveMode ? liveIntro : seedIntro }}
    </p>

    <!-- 双模式选择 -->
    <div class="mode-switch-bar mb-3 shrink-0">
      <div class="mode-switch-header">
        <span class="mode-switch-label"><i class="fas fa-route" /> 采集模式（点击切换）</span>
        <span class="mode-current-pill" :class="isLiveMode ? 'pill-self' : 'pill-seed'">
          当前：{{ isLiveMode ? '自采数据集' : 'SEED 数据集' }}
        </span>
      </div>
      <div class="mode-switch-buttons">
        <button
          type="button"
          class="mode-btn mode-btn-seed"
          :class="{ active: isSeedMode }"
          @click="selectMode('seed_offline')"
        >
          <i class="fas fa-database" />
          <span class="mode-btn-title">SEED 数据集</span>
          <span class="mode-btn-sub">无电极帽 · 跳过范式</span>
        </button>
        <button
          type="button"
          class="mode-btn mode-btn-self"
          :class="{ active: isLiveMode }"
          @click="selectMode('neuroscan_live')"
        >
          <i class="fas fa-head-side-brain" />
          <span class="mode-btn-title">自采数据集</span>
          <span class="mode-btn-sub">Neuroscan 40导 · 范式+LSL</span>
        </button>
      </div>
      <p class="mode-switch-hint">{{ currentModeLabel }} · {{ isLiveMode ? '范式 → 原始数据 DE 提取 → 在线推理' : '可跳过范式，直接进入数据处理' }}</p>
    </div>

    <!-- 操作指引 -->
    <div class="ops-guide mb-3 shrink-0" :class="isLiveMode ? 'ops-self' : 'ops-seed'">
      <div class="ops-guide-title">
        <i class="fas fa-list-ol" />
        {{ isLiveMode ? '自采数据集操作流程' : 'SEED 数据集操作流程' }}
      </div>
      <ol class="ops-steps">
        <template v-if="isLiveMode">
          <li>确认 Neuroscan 电极帽与 LSL 流已开启（流名称默认 <code>Neuroscan</code>）</li>
          <li>点击下方「范式运行」，完成基线十字 + 情绪图片刺激（同步 Marker）</li>
          <li>点击底部「下一步：进入数据处理模块」，启动流水线（LSL 原始 → DE 特征）</li>
          <li>特征提取加载 checkpoint → 情绪识别在线推理</li>
        </template>
        <template v-else>
          <li>本步可跳过，直接点底部「下一步：进入数据处理模块」</li>
          <li>数据处理将使用 SEED Preprocessed_EEG 原始 .mat 构建 DE 特征</li>
          <li>完成特征提取训练 → 情绪识别 seed_replay 回放</li>
        </template>
      </ol>
    </div>

    <!-- SEED 离线 / Neuroscan 实时 设备信息 -->
    <div v-if="isSeedMode" class="device-reserve-bar mb-3 shrink-0 seed-mode-bar">
      <div class="device-reserve-title">
        <i class="fas fa-database" />
        SEED 离线数据集
        <span class="device-vendor">de_comp_4ch_1p5s</span>
      </div>
      <p class="device-note">
        4 导关键电极 AF3 / AF4 / F3 / F4 · 采样率 200Hz · 窗长 1.5s · 可跳过本步直接进入数据处理
      </p>
    </div>
    <div v-else-if="deviceCatalog" class="device-reserve-bar mb-3 shrink-0">
      <div class="device-reserve-title">
        <i class="fas fa-head-side-brain" />
        Neuroscan 40 导设备接入
        <span class="device-vendor">{{ deviceCatalog.device_vendor }}</span>
      </div>
      <div class="device-source-row">
        <span
          v-for="src in deviceCatalog.sources"
          :key="src.id"
          class="device-chip"
          :class="deviceChipClass(src.id)"
        >
          {{ src.label }}
          <span v-if="src.id === 'neuroscan_lsl'" class="chip-tag">
            {{ src.lsl_available ? 'LSL 就绪' : '待接帽' }}
          </span>
        </span>
      </div>
      <p class="device-note">
        关键导联 {{ (deviceCatalog.key_channels || []).join(' / ') }} → 与 brainstim marker 对齐后进入数据处理与在线推理
      </p>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <BrainstimParadigmPanel :external-data="brainstimParadigm" />
    </div>

    <div class="demo-hint shrink-0">
      <i class="fas fa-book" />
      刺激图片来源：<strong>OASIS</strong> 公开情绪图片库（900 张效价评分图，研究可免费使用）
      · <a href="https://osf.io/6pnd7/" target="_blank" rel="noopener">osf.io/6pnd7</a>
    </div>
  </div>
</template>

<script lang="ts" setup>
import BrainstimParadigmPanel from '@/components/dashboard/BrainstimParadigmPanel.vue';
import { onMounted, ref, watch } from 'vue';
import { api } from '@/api/index';
import { ElMessage } from 'element-plus';
import { usePipelineSession, type AcquisitionMode } from '@/composables/usePipelineSession';

const seedIntro =
  'SEED 离线演示：可跳过本步，直接进入数据处理；或使用 brainstim 模拟范式 + LSL Marker 录视频。';
const liveIntro =
  'Neuroscan 实时链路：基线十字 → 情绪图片 → LSL Marker 同步 → 40 导 LSL 采集 → 在线 DE → brainflow 推理。';

const {
  isLiveMode,
  isSeedMode,
  currentModeLabel,
  applyModeLocal,
  syncModeToBackend,
  loadSession,
} = usePipelineSession();

const props = defineProps<{
  brainstimParadigm?: Record<string, unknown> | null;
  active?: boolean;
}>();

const deviceCatalog = ref<Record<string, any> | null>(null);
const localParadigm = ref<Record<string, unknown> | null>(null);

const brainstimParadigm = ref<Record<string, unknown> | null>(props.brainstimParadigm ?? null);

watch(
  () => props.brainstimParadigm,
  (val) => {
    if (val) brainstimParadigm.value = val;
  },
);

async function selectMode(mode: AcquisitionMode) {
  if ((mode === 'seed_offline' && isSeedMode.value) || (mode === 'neuroscan_live' && isLiveMode.value)) {
    return;
  }
  applyModeLocal(mode);
  ElMessage.success(mode === 'neuroscan_live' ? '已切换：自采数据集' : '已切换：SEED 数据集');
  void syncModeToBackend(mode);
}

function deviceChipClass(srcId: string) {
  if (isSeedMode.value) {
    return { active: srcId === 'seed_replay' };
  }
  return {
    active: srcId === 'neuroscan_lsl' || srcId === 'neuroscan_sim',
    reserved: srcId === 'neuroscan_lsl',
  };
}

async function loadDeviceCatalog() {
  try {
    deviceCatalog.value = await api.brainflowDeviceSources();
  } catch {
    deviceCatalog.value = null;
  }
}

async function loadParadigmIfNeeded() {
  if (brainstimParadigm.value?.success !== false && brainstimParadigm.value?.steps) {
    return;
  }
  try {
    localParadigm.value = await api.brainstimParadigm();
    brainstimParadigm.value = localParadigm.value;
  } catch {
    /* panel handles error state */
  }
}

onMounted(() => {
  void loadDeviceCatalog();
  if (props.active !== false) {
    void loadParadigmIfNeeded();
  }
});

watch(
  () => props.active,
  (val) => {
    if (val) void loadParadigmIfNeeded();
  },
);
</script>

<style scoped>
.title-accent {
  background: linear-gradient(180deg, #9944ff, #ff66aa);
  box-shadow: 0 0 14px rgba(153, 68, 255, 0.7);
}

.page-tag {
  font-size: 10px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(153, 68, 255, 0.22);
  color: #cc99ff;
  border: 1px solid rgba(153, 68, 255, 0.4);
}

.page-intro {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.55;
  color: #9cb8e8;
}

.mode-switch-bar {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(34, 153, 255, 0.28);
  background: rgba(8, 14, 36, 0.72);
}
.mode-switch-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.mode-switch-label {
  font-size: 11px;
  font-weight: 700;
  color: #66bbff;
}
.mode-current-pill {
  font-size: 10px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
}
.mode-current-pill.pill-seed {
  color: #66ccff;
  border: 1px solid rgba(0, 180, 255, 0.45);
  background: rgba(0, 120, 255, 0.12);
}
.mode-current-pill.pill-self {
  color: #ffaa66;
  border: 1px solid rgba(255, 140, 60, 0.45);
  background: rgba(255, 120, 40, 0.12);
}
.mode-switch-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  border: 2px solid rgba(100, 130, 200, 0.35);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 700;
  color: #b0c4e8;
  background: rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}
.mode-btn i {
  font-size: 14px;
  margin-bottom: 2px;
}
.mode-btn-title {
  font-size: 12px;
  font-weight: 800;
}
.mode-btn-sub {
  font-size: 9px;
  font-weight: 500;
  color: #8899bb;
  line-height: 1.3;
}
.mode-btn:not(.active):hover {
  border-color: rgba(0, 180, 255, 0.5);
  color: #e0eeff;
  background: rgba(0, 100, 200, 0.18);
  box-shadow: 0 0 10px rgba(0, 150, 255, 0.15);
}
.mode-btn.active {
  color: #fff;
  box-shadow: 0 0 14px rgba(0, 150, 255, 0.28);
}
.mode-btn-seed.active {
  border-color: rgba(0, 180, 255, 0.65);
  background: linear-gradient(135deg, rgba(0, 120, 255, 0.55), rgba(60, 100, 220, 0.4));
}
.mode-btn-self.active {
  border-color: rgba(255, 140, 60, 0.65);
  background: linear-gradient(135deg, rgba(255, 120, 40, 0.5), rgba(180, 60, 200, 0.35));
}

.mode-switch-hint {
  margin: 8px 0 0;
  font-size: 10px;
  color: #778899;
}

.ops-guide {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(34, 153, 255, 0.22);
  background: rgba(6, 12, 32, 0.65);
}
.ops-guide.ops-seed {
  border-color: rgba(0, 180, 255, 0.3);
}
.ops-guide.ops-self {
  border-color: rgba(255, 140, 60, 0.3);
}
.ops-guide-title {
  font-size: 11px;
  font-weight: 700;
  color: #99ccee;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.ops-steps {
  margin: 0;
  padding-left: 18px;
  font-size: 10px;
  color: #8899bb;
  line-height: 1.55;
}
.ops-steps code {
  color: #aaccff;
  font-size: 9px;
}

.device-reserve-bar {
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(153, 68, 255, 0.28);
  background: rgba(12, 8, 32, 0.72);
}
.seed-mode-bar {
  border-color: rgba(0, 200, 120, 0.35);
  background: rgba(8, 28, 20, 0.55);
}
.device-reserve-title {
  font-size: 12px;
  font-weight: 700;
  color: #cc99ff;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.device-vendor {
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(153, 68, 255, 0.2);
  color: #ddbbff;
}
.device-source-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}
.device-chip {
  font-size: 10px;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(100, 120, 180, 0.35);
  color: #8899bb;
  background: rgba(0, 0, 0, 0.25);
}
.device-chip.reserved {
  border-color: rgba(255, 180, 0, 0.45);
  color: #ffdd88;
}
.device-chip.active {
  border-color: rgba(0, 200, 120, 0.45);
  color: #66eebb;
}
.chip-tag {
  margin-left: 4px;
  font-size: 9px;
  opacity: 0.85;
}
.device-note {
  margin: 0;
  font-size: 10px;
  color: #667799;
  line-height: 1.4;
}

.demo-hint {
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 10px;
  color: #778899;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(153, 68, 255, 0.15);
  line-height: 1.5;
}
.demo-hint code {
  display: block;
  margin-top: 4px;
  color: #aaccff;
  word-break: break-all;
  font-size: 9px;
}
</style>
