<template>
  <div class="pipeline-root flex h-full min-h-0 flex-col">
    <div class="pipeline-top shrink-0">
      <!-- 流程标题栏 -->
      <div class="mb-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="title-accent h-6 w-1 rounded-full" />
          <div>
            <h2 class="text-lg font-bold text-white">数据处理流水线</h2>
            <p class="mt-0.5 text-xs text-[#8aa8d8]">
              当前数据源：<span class="dataset-inline" :class="datasetBannerClass">{{ datasetLabel }}</span>
            </p>
          </div>
        </div>
        <div class="flex gap-2">
          <button class="dash-action-btn" @click="$emit('reset')">
            <i class="fas fa-redo mr-1" />重置流程
          </button>
          <button class="dash-action-btn" @click="$emit('batch')">
            <i class="fas fa-layer-group mr-1" />一键批量处理
          </button>
        </div>
      </div>

    <!-- 数据集标识 -->
    <div class="dataset-banner mb-3 flex items-center gap-3 px-4 py-2" :class="datasetBannerClass">
      <span class="dataset-badge">{{ datasetLabel }}</span>
      <span class="dataset-desc">{{ datasetDesc }}</span>
      <span
        v-if="isLiveMode"
        class="live-probe-tag ml-auto"
        :class="{ ok: isDeviceConnected, warn: !isDeviceConnected }"
      >
        {{ isDeviceConnected ? '设备已连接' : '设备未连接' }}
      </span>
    </div>

    <!-- 特征类型选择（两种模式统一布局） -->
    <div class="feature-bar flex items-center gap-3 px-4 py-2.5">
      <span class="feature-bar-label">DE特征类型选择：</span>
      <span class="channel-tag">4导 · AF3 / AF4 / F3 / F4</span>
      <template v-if="!isLiveMode">
        <el-select
          :model-value="selectedFeature"
          placeholder="DE微分熵"
          class="feature-glass-select feature-inline-select"
          popper-class="feature-glass-dropdown"
          @update:model-value="$emit('update:selectedFeature', $event)"
        >
          <el-option
            v-for="item in featureOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </template>
      <span v-else class="de-fixed-tag">差分熵 DE · de_comp_4ch_1p5s</span>
      <span v-if="isLiveMode && liveProbe?.stream_name" class="live-stream-name">{{ liveProbe.stream_name }}</span>
    </div>
    </div>

    <!-- 霓虹环形光球流水线 -->
    <div class="pipeline-flow-wrap min-h-0 flex-1">
      <NeonPipelineFlow
        class="h-full w-full"
        :process-step="processStep"
        :loading="loading"
        :preprocessing-done="preprocessingDone"
        :dataset-label="datasetLabel"
        :is-live-mode="isLiveMode"
        @node-click="openConfig"
        @start="$emit('start')"
      />
    </div>

    <!-- 节点配置弹窗 -->
    <el-dialog
      v-model="configVisible"
      :title="activeNode?.title + ' — 步骤配置'"
      width="480px"
      class="pipeline-config-dialog"
      destroy-on-close
    >
      <div v-if="activeNode" class="space-y-4 text-sm text-[#9cb8e8]">
        <p><strong class="text-white">步骤说明：</strong>{{ activeNode.description }}</p>
        <el-form label-width="100px">
          <el-form-item label="输入源">
            <el-select v-model="configForm.input" class="w-full" :disabled="isLiveMode">
              <el-option :label="isLiveMode ? '自采 LSL 原始数据' : 'SEED 数据集'" :value="isLiveMode ? 'self_collected' : 'seed'" />
              <el-option v-if="!isLiveMode" label="本地 EEG 文件" value="local" />
              <el-option v-if="!isLiveMode" label="BrainFlow 实时流" value="brainflow" />
            </el-select>
          </el-form-item>
          <el-form-item label="采样率">
            <el-input-number v-model="configForm.sampleRate" :min="128" :max="512" :step="1" />
          </el-form-item>
          <el-form-item label="通道数">
            <el-input-number v-model="configForm.channels" :min="1" :max="64" :disabled="!isLiveMode" />
            <span v-if="!isLiveMode" class="form-hint">SEED 固定 4 导（AF3/AF4/F3/F4）</span>
            <span v-else class="form-hint">自采：Neuroscan 40 导映射至 4 导</span>
          </el-form-item>
          <el-form-item v-if="activeNodeIndex === 1" label="特征算法">
            <el-select v-model="configForm.algorithm" class="w-full">
              <el-option label="差分熵 (DE)" value="DE" />
              <el-option label="功率谱 (PSD)" value="PSD" />
              <el-option label="时域波形" value="TIME" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="configVisible = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import NeonPipelineFlow from '@/components/dashboard/NeonPipelineFlow.vue';
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';

interface FeatureOption {
  label: string;
  value: string;
}

const props = defineProps<{
  selectedFeature: string;
  featureOptions: FeatureOption[];
  processStep: number;
  loading: boolean;
  preprocessingDone: boolean;
  acquisitionMode?: string;
  datasetLabel?: string;
  isLiveMode?: boolean;
  liveProbe?: Record<string, unknown> | null;
}>();

defineEmits<{
  'update:selectedFeature': [value: string];
  start: [];
  reset: [];
  batch: [];
}>();

const seedPipelineNodes = [
  { title: '原始脑电数据导入', description: '从 SEED Preprocessed_EEG 导入原始脑电，完成格式校验与 4 导通道映射。' },
  { title: '时空频联合特征提取', description: '基于 brainda loadmat + compute_de_segment 提取 DE 差分熵特征矩阵。' },
  { title: '频段分割滤波', description: 'Delta/Theta/Alpha/Beta/Gamma 五频段带通滤波与差分熵计算。' },
  { title: '特征可视化输出', description: '生成脑地形图与频谱热力图，供后续情绪识别模块使用。' },
];

const livePipelineNodes = [
  { title: '原始脑电数据导入', description: '从 Neuroscan LSL 缓冲读取自采原始脑电，完成 40 导格式校验。' },
  { title: '时空频联合特征提取', description: '40 导映射至 AF3/AF4/F3/F4 后，复用 brainda compute_de_segment 提取 DE。' },
  { title: '频段分割滤波', description: '与 SEED 路径一致的五频段带通滤波与差分熵计算。' },
  { title: '特征可视化输出', description: '保存自采 DE 张量 (data.pt/label.pt)，供在线推理使用。' },
];

const pipelineNodes = computed(() => (props.isLiveMode ? livePipelineNodes : seedPipelineNodes));

const datasetLabel = computed(() => props.datasetLabel || (props.isLiveMode ? '自采数据集' : 'SEED 数据集'));

const datasetBannerClass = computed(() => (props.isLiveMode ? 'dataset-self' : 'dataset-seed'));

const datasetDesc = computed(() =>
  props.isLiveMode
    ? '范式采集后的 LSL 原始数据 → brainda DE 特征提取（需连接 Neuroscan 设备）'
    : '从 SEED Preprocessed_EEG 原始 .mat → brainda DE 特征构建',
);

const isDeviceConnected = computed(() =>
  Boolean(props.liveProbe?.device_connected ?? props.liveProbe?.connected),
);

const configVisible = ref(false);
const activeNodeIndex = ref(0);
const configForm = ref({
  input: 'seed',
  sampleRate: 200,
  channels: 4,
  algorithm: 'DE',
});

const activeNode = computed(() => pipelineNodes.value[activeNodeIndex.value]);

function openConfig(idx: number) {
  activeNodeIndex.value = idx;
  configVisible.value = true;
}

function saveConfig() {
  configVisible.value = false;
  ElMessage.success(`${activeNode.value?.title} 配置已保存`);
}
</script>

<style scoped>
.title-accent {
  background: linear-gradient(180deg, #2299ff, #9944ff);
  box-shadow: 0 0 14px rgba(34, 153, 255, 0.7);
}

.dataset-banner {
  border-radius: 10px;
  border: 1px solid rgba(34, 153, 255, 0.22);
  background: rgba(6, 12, 32, 0.72);
  backdrop-filter: blur(8px);
}
.dataset-banner.dataset-seed {
  border-color: rgba(0, 180, 255, 0.35);
  background: linear-gradient(90deg, rgba(0, 120, 255, 0.12), rgba(8, 14, 36, 0.65));
}
.dataset-banner.dataset-self {
  border-color: rgba(255, 140, 60, 0.35);
  background: linear-gradient(90deg, rgba(255, 120, 40, 0.1), rgba(8, 14, 36, 0.65));
}
.dataset-badge {
  font-size: 12px;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 14px;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.dataset-seed .dataset-badge {
  color: #66ccff;
  border: 1px solid rgba(0, 180, 255, 0.5);
  background: rgba(0, 120, 255, 0.15);
}
.dataset-self .dataset-badge {
  color: #ffaa66;
  border: 1px solid rgba(255, 140, 60, 0.5);
  background: rgba(255, 120, 40, 0.12);
}
.dataset-desc {
  font-size: 11px;
  color: #8aa8d8;
}
.dataset-inline {
  font-weight: 700;
}
.dataset-inline.dataset-seed,
.dataset-seed .dataset-inline {
  color: #66ccff;
}
.dataset-inline.dataset-self,
.dataset-self .dataset-inline {
  color: #ffaa66;
}

.channel-tag,
.de-fixed-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(0, 200, 120, 0.4);
  color: #66eebb;
  background: rgba(0, 200, 120, 0.1);
  white-space: nowrap;
}
.de-fixed-tag {
  border-color: rgba(255, 140, 60, 0.4);
  color: #ffcc88;
  background: rgba(255, 120, 40, 0.1);
}

.feature-bar {
  border-radius: 10px;
  border: 1px solid rgba(34, 153, 255, 0.25);
  background: rgba(8, 14, 36, 0.65);
  backdrop-filter: blur(10px);
}

.feature-bar-label {
  font-size: 13px;
  color: #b0c4e8;
  white-space: nowrap;
}

.pipeline-flow-wrap {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.pipeline-top {
  min-height: var(--data-step-top-h, 96px);
  margin-bottom: 8px;
}

:deep(.feature-glass-select .el-input__wrapper) {
  background: rgba(12, 22, 48, 0.75) !important;
  border: 1px solid rgba(34, 153, 255, 0.35) !important;
  box-shadow: inset 0 0 10px rgba(34, 153, 255, 0.06) !important;
  backdrop-filter: blur(8px);
}
:deep(.feature-glass-select .el-input__inner) {
  color: #94b8f2 !important;
}
:deep(.feature-inline-select) {
  width: 160px;
}

.live-probe-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255, 180, 0, 0.4);
  color: #ffcc66;
  background: rgba(255, 180, 0, 0.1);
}
.live-probe-tag.ok {
  border-color: rgba(0, 200, 120, 0.45);
  color: #66eebb;
  background: rgba(0, 200, 120, 0.12);
}
.live-stream-name {
  font-size: 10px;
  color: #8899bb;
}

.form-hint {
  margin-left: 8px;
  font-size: 10px;
  color: #778899;
}
</style>

<style>
.feature-glass-dropdown {
  background: rgba(5, 12, 34, 0.96) !important;
  border: 1px solid rgba(34, 153, 255, 0.4) !important;
}
.feature-glass-dropdown .el-select-dropdown__item {
  color: #9cb8e8;
}
.feature-glass-dropdown .el-select-dropdown__item.hover,
.feature-glass-dropdown .el-select-dropdown__item:hover {
  background: rgba(34, 153, 255, 0.15) !important;
}
.pipeline-config-dialog .el-dialog {
  background: rgba(5, 12, 34, 0.96) !important;
  border: 1px solid rgba(34, 153, 255, 0.4);
  border-radius: 16px;
  box-shadow: 0 0 30px rgba(153, 68, 255, 0.3);
}
.pipeline-config-dialog .el-dialog__title {
  color: #fff;
}
</style>
