import { ref, computed } from 'vue';
import { api } from '@/api/index';

export type AcquisitionMode = 'seed_offline' | 'neuroscan_live';

const acquisitionMode = ref<AcquisitionMode>('seed_offline');
const deviceSource = ref('seed_replay');
const liveProbe = ref<Record<string, unknown> | null>(null);
const sessionLoaded = ref(false);
/** 本地模式切换版本号，防止 stale 的 loadSession 覆盖用户刚选的模式 */
let localModeRevision = 0;

const modeMeta = computed(() => ({
  seed_offline: {
    label: 'SEED 数据集演示',
    datasetLabel: 'SEED 数据集',
    hint: '无电极帽：SEED 离线预处理 → 训练 → seed_replay 推理',
    icon: 'fa-database',
  },
  neuroscan_live: {
    label: 'Neuroscan 实时采集',
    datasetLabel: '自采数据集',
    hint: '有电极帽：范式 + LSL 40 导 → 原始数据 DE 提取 → brainflow 推理',
    icon: 'fa-head-side-brain',
  },
}));

const isLiveMode = computed(() => acquisitionMode.value === 'neuroscan_live');
const isSeedMode = computed(() => acquisitionMode.value === 'seed_offline');
const currentModeLabel = computed(() => modeMeta.value[acquisitionMode.value]?.label ?? '');
const datasetLabel = computed(() => modeMeta.value[acquisitionMode.value]?.datasetLabel ?? 'SEED 数据集');

function applySession(data: Record<string, unknown>) {
  const mode = String(data.acquisition_mode || 'seed_offline') as AcquisitionMode;
  acquisitionMode.value = mode === 'neuroscan_live' ? 'neuroscan_live' : 'seed_offline';
  deviceSource.value = String(data.device_source || (isLiveMode.value ? 'neuroscan_lsl' : 'seed_replay'));
  liveProbe.value = (data.live_probe as Record<string, unknown>) || null;
  sessionLoaded.value = true;
}

function applyModeLocal(mode: AcquisitionMode) {
  localModeRevision += 1;
  acquisitionMode.value = mode;
  deviceSource.value = mode === 'neuroscan_live' ? 'neuroscan_lsl' : 'seed_replay';
  if (mode === 'seed_offline') {
    liveProbe.value = null;
  }
}

async function loadSession() {
  const revisionAtStart = localModeRevision;
  const data = await api.pipelineSessionGet();
  if (revisionAtStart !== localModeRevision) {
    return data;
  }
  applySession(data);
  return data;
}

async function syncModeToBackend(mode: AcquisitionMode) {
  const revisionAtStart = localModeRevision;
  try {
    const data = await api.pipelineSessionUpdate({ acquisition_mode: mode });
    if (revisionAtStart !== localModeRevision) {
      return data;
    }
    applySession(data);
    return data;
  } catch (error) {
    console.warn('pipeline session update failed, keeping local mode:', error);
    return null;
  }
}

async function setMode(mode: AcquisitionMode) {
  applyModeLocal(mode);
  return syncModeToBackend(mode);
}

async function resetSession() {
  const data = await api.pipelineSessionUpdate({ reset: true });
  applySession(data);
  return data;
}

export function usePipelineSession() {
  return {
    acquisitionMode,
    deviceSource,
    liveProbe,
    sessionLoaded,
    modeMeta,
    isLiveMode,
    isSeedMode,
    currentModeLabel,
    datasetLabel,
    loadSession,
    setMode,
    resetSession,
    applySession,
    applyModeLocal,
    syncModeToBackend,
  };
}
