<template>
  <div class="brainstim-panel" :class="{ running: simRunning }">
    <div class="panel-header">
      <div class="header-left">
        <span class="header-dot" :class="{ pulse: simRunning }" />
        <h3 class="panel-title">brainstim 情绪实验范式</h3>
        <span class="paradigm-tag">{{ paradigmName }}</span>
      </div>
      <div class="header-right">
        <span class="status-badge" :class="statusClass">{{ statusLabel }}</span>
        <button
          class="run-btn"
          :disabled="simRunning || loading || verifyRunning"
          @click="startSimulation(false)"
        >
          <i class="fas" :class="simRunning ? 'fa-spinner fa-spin' : 'fa-play'" />
          {{ simRunning ? '运行中...' : '模拟范式运行' }}
        </button>
        <button
          class="verify-btn"
          :disabled="verifyRunning || simRunning"
          @click="runStrictVerify"
        >
          <i class="fas" :class="verifyRunning ? 'fa-spinner fa-spin' : 'fa-check-double'" />
          {{ verifyRunning ? '验证中...' : '验证 brainstim API' }}
        </button>
        <button class="refresh-btn" :disabled="loading || simRunning" @click="loadParadigm">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }" />
        </button>
      </div>
    </div>

    <!-- 刺激呈现：Step1 十字 + Step2 三类情绪图片 -->
    <div class="stimulus-preview">
      <div class="stimulus-preview-header">
        <span><i class="fas fa-image" /> 刺激序列：基线十字 → 积极 / 中性 / 消极 图片（ImageStim）</span>
        <span class="stimulus-mode-tag">{{ simRunning ? '演示同步中' : stimuliReady ? '9 张图片就绪' : '加载中' }}</span>
      </div>

      <!-- 主舞台：运行提示（实际刺激在全屏弹层呈现） -->
      <div class="stimulus-stage">
        <div v-if="simRunning && stimulusOverlayVisible" class="stimulus-running-hint">
          <i class="fas fa-expand" />
          <p>全屏刺激呈现中 — 请注视弹出窗口</p>
          <span v-if="overlayLabel">{{ overlayLabel }}</span>
        </div>
        <div v-else-if="showBaseline" class="baseline-cross baseline-cross--inline">
          <span class="cross-v" />
          <span class="cross-h" />
          <p>Step 1 · 基线注视十字 · marker #1</p>
        </div>
        <div v-else class="stimulus-placeholder">
          <p v-if="!simRunning">点击下方「模拟范式运行」：先十字 3s，再九张情绪图片逐张呈现（每张约 1.8s）</p>
          <p v-else>{{ currentStimulusLabel || '情绪刺激块过渡…' }}</p>
        </div>
      </div>
      <p v-if="currentStimulusLabel && !stimulusOverlayVisible" class="stimulus-caption">{{ currentStimulusLabel }}</p>

      <!-- 三类情绪图片库（始终可见，运行时会高亮当前类） -->
      <div v-if="stimuliBlocks.length" class="emotion-gallery">
        <div
          v-for="block in stimuliBlocks"
          :key="block.emotion"
          class="emotion-block"
          :class="{ active: activeEmotion === block.emotion, done: completedEmotions.has(block.emotion) }"
        >
          <div class="emotion-block-head">
            <span class="emotion-name">{{ block.label }}</span>
            <code class="emotion-marker">#{{ block.marker }}</code>
          </div>
          <div class="emotion-images">
            <img
              v-for="img in block.images"
              :key="img.filename"
              :src="resolveStimulusUrl(img.url)"
              :alt="img.filename"
              class="emotion-img"
              :class="{ 'emotion-img--active': activeStimulusFilename === img.filename && activeEmotion === block.emotion }"
            />
          </div>
        </div>
      </div>
    </div>

    <p v-if="description" class="panel-desc">{{ description }}</p>

    <!-- 当前阶段进度 -->
    <div v-if="simRunning || lastMessage" class="progress-block">
      <div class="progress-label">
        <span>{{ currentPhaseLabel }}</span>
        <span v-if="simRunning" class="phase-timer">{{ phaseCountdown }}s</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: phaseProgress + '%' }" />
      </div>
      <p v-if="lastMessage" class="sim-message">{{ lastMessage }}</p>
    </div>

    <div v-if="loading && !steps.length" class="panel-loading">
      <i class="fas fa-spinner fa-spin" /> 加载范式配置...
    </div>

    <div v-else-if="error" class="panel-error">
      <i class="fas fa-exclamation-triangle" /> {{ error }}
      <button class="retry-link" @click="loadParadigm">重试</button>
    </div>

    <template v-else>
      <div class="steps-grid">
        <div
          v-for="step in steps"
          :key="step.step"
          class="step-card"
          :class="stepStateClass(step.step)"
        >
          <div class="step-num-row">
            <span class="step-num">Step {{ step.step }}</span>
            <span v-if="stepStatus(step.step) === 'running'" class="step-live">进行中</span>
            <span v-else-if="stepStatus(step.step) === 'done'" class="step-done">✓</span>
          </div>
          <div class="step-name">{{ step.name }}</div>
          <div class="marker-row">
            <span class="marker-label">Marker</span>
            <code class="marker-code" :class="{ flash: lastMarkerStep === step.step }">
              #{{ activeMarkerForStep(step.step) ?? step.marker_code }}
            </code>
            <span class="marker-name">{{ step.marker }}</span>
          </div>
          <div class="step-dur">
            <i class="fas fa-clock" />
            {{ step.duration_seconds ? `${step.duration_seconds}s` : '事件触发' }}
          </div>
          <p class="step-desc">{{ step.description }}</p>
        </div>
      </div>

      <!-- Marker 事件流 -->
      <div v-if="markerLog.length" class="marker-log">
        <div class="log-title">
          <i class="fas fa-broadcast-tower" /> LSL Marker 事件流
          <span class="log-channel">{{ lslAvailable ? 'brainstim LsLPort' : '模拟通道' }}</span>
        </div>
        <ul class="log-list">
          <li v-for="(ev, i) in markerLog.slice().reverse().slice(0, 6)" :key="i" class="log-item">
            <span class="log-time">{{ formatTime(ev.timestamp) }}</span>
            <code class="log-marker">#{{ ev.marker_code }}</code>
            <span class="log-detail">{{ ev.detail }}</span>
            <span class="log-ch">{{ ev.channel }}</span>
          </li>
        </ul>
      </div>

      <div v-if="runtimeInfo || strictVerifiedCount != null" class="runtime-bar">
        <span><i class="fas fa-cube" /> PsychoPy: {{ runtimeInfo?.psychopy_available ? '✓' : '✗' }}</span>
        <span><i class="fas fa-brain" /> brainstim: {{ runtimeReady ? '✓ 就绪' : '模块已集成' }}</span>
        <span class="strict-count" :class="{ ok: strictVerifiedCount >= 3, partial: strictVerifiedCount >= 1 && strictVerifiedCount < 3 }">
          严格 API {{ strictVerifiedCount ?? 0 }}/{{ strictRegisteredCount }}
        </span>
        <span v-if="apisCalled.length">已调用: {{ apisCalled.length }} 项</span>
      </div>

      <div v-if="verifyChecks.length" class="verify-list">
        <div v-for="chk in verifyChecks" :key="chk.id" class="verify-item" :class="{ ok: chk.verified }">
          <i class="fas" :class="chk.verified ? 'fa-check-circle' : 'fa-times-circle'" />
          <code>{{ chk.brainstim_api }}</code>
          <span>{{ chk.message }}</span>
        </div>
      </div>
    </template>
  </div>

  <!-- 全屏刺激弹层：播放时弹出，结束后消失 -->
  <Teleport to="body">
    <Transition name="stimulus-overlay">
      <div
        v-if="stimulusOverlayVisible"
        class="stimulus-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="情绪刺激呈现"
      >
        <div class="stimulus-overlay-backdrop" />
        <div class="stimulus-overlay-content">
          <div v-if="overlayShowBaseline" class="overlay-baseline">
            <div class="overlay-cross">
              <span class="cross-v cross-v--large" />
              <span class="cross-h cross-h--large" />
            </div>
            <p class="overlay-caption">基线采集 · 请注视十字</p>
            <span class="overlay-marker">Marker #1</span>
          </div>
          <div v-else-if="overlayImageUrl" class="overlay-image-wrap">
            <img
              :key="overlayImageUrl"
              :src="overlayImageUrl"
              :alt="overlayLabel"
              class="overlay-image"
            />
            <p class="overlay-caption">{{ overlayLabel }}</p>
            <span v-if="overlayMarker" class="overlay-marker">Marker #{{ overlayMarker }}</span>
          </div>
          <div v-if="simRunning && phaseCountdown > 0" class="overlay-countdown">{{ phaseCountdown }}s</div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script lang="ts" setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { api, API_BASE_URL } from '@/api/index';
import { ElMessage } from 'element-plus';

export interface ParadigmStep {
  step: number;
  name: string;
  marker: string;
  marker_code: number;
  duration_seconds: number;
  description: string;
}

interface StimulusInfo {
  emotion?: string;
  label?: string;
  marker?: number;
  filename?: string;
  url?: string;
}

interface MarkerEvent {
  step: number;
  marker_code: number;
  marker_label: string;
  detail: string;
  duration_ms: number;
  timestamp: string;
  channel: string;
  sent: boolean;
  stimulus?: StimulusInfo | null;
}

interface StimuliBlock {
  emotion: string;
  label: string;
  marker: number;
  images?: Array<{ filename: string; url: string }>;
}

const props = defineProps<{
  externalData?: Record<string, unknown> | null;
  /** 数据处理流水线启动时自动触发范式模拟 */
  autoRun?: boolean;
}>();

const loading = ref(false);
const error = ref('');
const paradigmName = ref('SEEDPassiveEmotion');
const description = ref('');
const steps = ref<ParadigmStep[]>([]);
const moduleAvailable = ref(false);
const runtimeReady = ref(false);
const runtimeInfo = ref<Record<string, unknown> | null>(null);

const simRunning = ref(false);
const markerLog = ref<MarkerEvent[]>([]);
const lastMessage = ref('');
const lslAvailable = ref(false);
const apisCalled = ref<string[]>([]);
const verifyRunning = ref(false);
const strictVerifiedCount = ref<number | null>(null);
const strictRegisteredCount = ref(3);
const verifyChecks = ref<Array<Record<string, unknown>>>([]);
const stimuliReady = ref(false);
const stimuliBlocks = ref<StimuliBlock[]>([]);
const currentStimulusUrl = ref('');
const currentStimulusLabel = ref('');
const showBaseline = ref(false);
const stimulusOverlayVisible = ref(false);
const overlayShowBaseline = ref(false);
const overlayImageUrl = ref('');
const overlayLabel = ref('');
const overlayMarker = ref<number | null>(null);
const activeStimulusFilename = ref('');
const activeEmotion = ref('');
const completedEmotions = ref(new Set<string>());

const activeStep = ref(0);
const lastMarkerStep = ref(0);
const activeMarkerCode = ref<number | null>(null);
const phaseCountdown = ref(0);
const phaseProgress = ref(0);
const currentPhaseLabel = ref('等待启动范式模拟');

let simTimers: ReturnType<typeof setTimeout>[] = [];
let countdownTimer: ReturnType<typeof setInterval> | null = null;

const statusClass = computed(() => {
  if (simRunning.value) return 'running';
  if (runtimeReady.value || lslAvailable.value) return 'ready';
  if (moduleAvailable.value) return 'partial';
  return 'fallback';
});

const statusLabel = computed(() => {
  if (simRunning.value) return '范式运行中';
  if (lslAvailable.value) return 'LSL 已发送';
  if (runtimeReady.value) return 'brainstim 就绪';
  if (moduleAvailable.value) return '模块已集成';
  return '待模拟';
});

function stepStatus(stepNum: number): 'pending' | 'running' | 'done' {
  if (activeStep.value > stepNum) return 'done';
  if (activeStep.value === stepNum && simRunning.value) return 'running';
  if (!simRunning.value && markerLog.value.some((e) => e.step === stepNum)) return 'done';
  return 'pending';
}

function stepStateClass(stepNum: number) {
  return stepStatus(stepNum);
}

function activeMarkerForStep(stepNum: number): number | null {
  if (lastMarkerStep.value === stepNum && activeMarkerCode.value != null) {
    return activeMarkerCode.value;
  }
  return null;
}

function resolveStimulusUrl(path: string) {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${API_BASE_URL}${path}`;
}

function clearStimulusOverlay() {
  stimulusOverlayVisible.value = false;
  overlayShowBaseline.value = false;
  overlayImageUrl.value = '';
  overlayLabel.value = '';
  overlayMarker.value = null;
  activeStimulusFilename.value = '';
  showBaseline.value = false;
  currentStimulusUrl.value = '';
}

function applyStimulusFromEvent(event: MarkerEvent) {
  const emotionFromMarker: Record<number, string> = { 21: 'positive', 22: 'neutral', 23: 'negative' };

  if (event.marker_code === 1) {
    showBaseline.value = true;
    activeEmotion.value = '';
    currentStimulusLabel.value = 'Step 1 · 基线采集 — 注视十字';
    stimulusOverlayVisible.value = true;
    overlayShowBaseline.value = true;
    overlayImageUrl.value = '';
    overlayLabel.value = '基线采集 · 请注视十字';
    overlayMarker.value = 1;
    return;
  }

  if ([21, 22, 23].includes(event.marker_code)) {
    showBaseline.value = false;
    activeEmotion.value = emotionFromMarker[event.marker_code];
    const stim = event.stimulus;
    const block = stimuliBlocks.value.find((b) => b.marker === event.marker_code);
    const url = stim?.url
      ? resolveStimulusUrl(stim.url)
      : block?.images?.[0]
        ? resolveStimulusUrl(block.images[0].url)
        : '';
    if (url) {
      currentStimulusUrl.value = url;
      activeStimulusFilename.value = stim?.filename || '';
      currentStimulusLabel.value = stim?.label
        ? `${stim.label} · ${stim.filename || event.detail}`
        : event.detail;
      stimulusOverlayVisible.value = true;
      overlayShowBaseline.value = false;
      overlayImageUrl.value = url;
      overlayLabel.value = currentStimulusLabel.value;
      overlayMarker.value = event.marker_code;
    }
    return;
  }

  clearStimulusOverlay();
  if (event.marker_code === 2) {
    currentStimulusLabel.value = 'Step 2 · 情绪刺激块开始 · marker #2';
  } else {
    currentStimulusLabel.value = event.detail;
  }
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false });
  } catch {
    return ts.slice(11, 19);
  }
}

function clearSimTimers() {
  simTimers.forEach(clearTimeout);
  simTimers = [];
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

function runPhase(event: MarkerEvent, index: number, allEvents: MarkerEvent[]) {
  return new Promise<void>((resolve) => {
    activeStep.value = event.step;
    lastMarkerStep.value = event.step;
    activeMarkerCode.value = event.marker_code;
    currentPhaseLabel.value = `Step ${event.step}: ${event.detail}`;
    lastMessage.value = event.detail;
    applyStimulusFromEvent(event);

    const durMs = event.duration_ms || 1000;
    const durSec = Math.ceil(durMs / 1000);
    phaseCountdown.value = durSec;
    phaseProgress.value = 0;

    if (countdownTimer) clearInterval(countdownTimer);
    const start = Date.now();
    countdownTimer = setInterval(() => {
      const elapsed = Date.now() - start;
      phaseProgress.value = Math.min(100, (elapsed / durMs) * 100);
      phaseCountdown.value = Math.max(0, durSec - Math.floor(elapsed / 1000));
    }, 100);

    const t = setTimeout(() => {
      if (event.marker_code === 1 || [21, 22, 23].includes(event.marker_code)) {
        clearStimulusOverlay();
        currentStimulusLabel.value = '';
      }
      if ([21, 22, 23].includes(event.marker_code)) {
        const map: Record<number, string> = { 21: 'positive', 22: 'neutral', 23: 'negative' };
        completedEmotions.value = new Set([...completedEmotions.value, map[event.marker_code]]);
      }
      if (index === allEvents.length - 1) {
        activeStep.value = 5;
      }
      resolve();
    }, durMs);
    simTimers.push(t);
  });
}

async function startSimulation(fromAuto = false) {
  if (simRunning.value) return;
  clearSimTimers();
  simRunning.value = true;
  markerLog.value = [];
  activeStep.value = 0;
  lastMarkerStep.value = 0;
  activeMarkerCode.value = null;
  phaseProgress.value = 0;
  clearStimulusOverlay();
  currentStimulusLabel.value = '';
  activeEmotion.value = '';
  completedEmotions.value = new Set();

  try {
    const data = await api.brainstimSimulate({ fast: true });
    lslAvailable.value = Boolean(data.lsl_available);
    apisCalled.value = (data.apis_called as string[]) || [];
    lastMessage.value = String(data.message || '');
    if (data.stimuli) {
      stimuliReady.value = Boolean((data.stimuli as Record<string, unknown>).stimuli_ready);
      stimuliBlocks.value = ((data.stimuli as Record<string, unknown>).blocks as StimuliBlock[]) || [];
    }
    const events = (data.events as MarkerEvent[]) || [];
    markerLog.value = events;

    for (let i = 0; i < events.length; i++) {
      await runPhase(events[i], i, events);
    }

    currentPhaseLabel.value = '范式模拟完成';
    phaseProgress.value = 100;
    phaseCountdown.value = 0;
    clearStimulusOverlay();
    if (!fromAuto) {
      ElMessage.success(lslAvailable.value ? 'brainstim 范式完成，LSL marker 已发送' : 'brainstim 范式模拟完成');
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '范式模拟失败';
    ElMessage.error(error.value);
  } finally {
    simRunning.value = false;
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }
}

function applyData(data: Record<string, unknown>) {
  paradigmName.value = String(data.paradigm_name || 'SEEDPassiveEmotion');
  description.value = String(data.description || '');
  steps.value = (data.steps as ParadigmStep[]) || [];
  moduleAvailable.value = Boolean(data.module_available);
  runtimeReady.value = Boolean(data.runtime_ready);
  runtimeInfo.value = (data.runtime as Record<string, unknown>) || null;
  const strict = (data.brainstim_strict as Record<string, unknown>) || null;
  if (data.stimuli) {
    stimuliReady.value = Boolean((data.stimuli as Record<string, unknown>).stimuli_ready);
    stimuliBlocks.value = ((data.stimuli as Record<string, unknown>).blocks as StimuliBlock[]) || [];
  }
  if (strict) {
    strictRegisteredCount.value = Number(strict.strict_function_count || 3);
    strictVerifiedCount.value = Number(strict.runtime_verified_count ?? 0);
  }
}

async function runStrictVerify() {
  verifyRunning.value = true;
  try {
    const data = await api.brainstimVerify();
    strictVerifiedCount.value = Number(data.runtime_verified_count ?? 0);
    strictRegisteredCount.value = Number(data.strict_function_count ?? 3);
    verifyChecks.value = (data.checks as Array<Record<string, unknown>>) || [];
    apisCalled.value = (data.apis_called as string[]) || [];
    lslAvailable.value = apisCalled.value.some((a) => a.includes('LsLPort'));
    const n = strictVerifiedCount.value;
    if (n >= 3) {
      ElMessage.success('brainstim 严格 API 验证 3/3 通过');
    } else if (n >= 1) {
      ElMessage.warning(`brainstim 已验证 ${n}/3；本地桌面录视频时可再点一次拿满 3 项`);
    } else {
      ElMessage.error('brainstim API 验证未通过');
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'brainstim 验证失败';
    if (msg.includes('500')) {
      ElMessage.error('验证失败：后端 500，请确认 backend/run.py 已启动 (端口 5001)');
    } else if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
      ElMessage.error('验证失败：无法连接后端，请先启动 python run.py');
    } else {
      ElMessage.error(msg);
    }
  } finally {
    verifyRunning.value = false;
  }
}

async function loadParadigm() {
  loading.value = true;
  error.value = '';
  try {
    const data = await api.brainstimParadigm();
    applyData(data);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载 brainstim 范式失败';
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.externalData,
  (val) => {
    if (val && val.success !== false) applyData(val);
  },
  { immediate: true },
);

watch(
  () => props.autoRun,
  (val) => {
    if (val && steps.value.length) void startSimulation(true);
  },
);

onMounted(() => {
  if (!steps.value.length) void loadParadigm();
});

onUnmounted(() => clearSimTimers());
</script>

<style scoped>
.brainstim-panel {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(153, 68, 255, 0.35);
  background: rgba(12, 8, 32, 0.65);
  flex-shrink: 0;
  transition: box-shadow 0.3s, border-color 0.3s;
}
.brainstim-panel.running {
  border-color: rgba(153, 68, 255, 0.7);
  box-shadow: 0 0 20px rgba(153, 68, 255, 0.25);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
  flex-wrap: wrap;
}

.header-left { display: flex; align-items: center; gap: 8px; }

.header-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #9944ff; box-shadow: 0 0 8px #9944ff;
}
.header-dot.pulse { animation: dot-pulse 1s ease-in-out infinite; }

@keyframes dot-pulse {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.3); }
}

.panel-title { font-size: 13px; font-weight: 700; color: #fff; margin: 0; }

.paradigm-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px;
  background: rgba(153, 68, 255, 0.25); color: #cc99ff;
  border: 1px solid rgba(153, 68, 255, 0.4);
}

.header-right { display: flex; align-items: center; gap: 6px; }

.status-badge {
  font-size: 11px; padding: 3px 10px; border-radius: 12px; font-weight: 600;
}
.status-badge.ready { background: rgba(0,200,120,0.2); color: #44eeaa; border: 1px solid rgba(0,200,120,0.4); }
.status-badge.partial { background: rgba(0,150,255,0.2); color: #66bbff; border: 1px solid rgba(0,150,255,0.4); }
.status-badge.fallback { background: rgba(255,180,0,0.15); color: #ffcc44; border: 1px solid rgba(255,180,0,0.35); }
.status-badge.running { background: rgba(153,68,255,0.3); color: #eeccff; border: 1px solid rgba(153,68,255,0.6); animation: dot-pulse 1.5s infinite; }

.run-btn {
  border: none; border-radius: 16px; padding: 5px 14px;
  font-size: 11px; font-weight: 700; color: #fff; cursor: pointer;
  background: linear-gradient(135deg, #7733ee, #9944ff);
  box-shadow: 0 0 12px rgba(153, 68, 255, 0.4);
}
.run-btn:hover:not(:disabled) { filter: brightness(1.15); }
.run-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.verify-btn {
  border: 1px solid rgba(0, 200, 120, 0.55); border-radius: 16px; padding: 5px 12px;
  font-size: 11px; font-weight: 700; color: #44eeaa; cursor: pointer;
  background: rgba(0, 200, 120, 0.12);
}
.verify-btn:hover:not(:disabled) { background: rgba(0, 200, 120, 0.22); }
.verify-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.refresh-btn {
  background: transparent; border: 1px solid rgba(153, 68, 255, 0.4);
  border-radius: 6px; color: #cc99ff; padding: 4px 8px; cursor: pointer; font-size: 12px;
}

.panel-desc { font-size: 11px; color: #9cb8e8; margin: 0 0 8px; line-height: 1.5; }

.stimulus-preview {
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 120, 180, 0.35);
  background: rgba(20, 8, 28, 0.55);
}
.stimulus-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #ff99cc;
  margin-bottom: 8px;
}
.stimulus-mode-tag {
  font-size: 9px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255, 100, 180, 0.2);
  color: #ffccee;
}
.stimulus-stage {
  min-height: 100px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.stimulus-running-hint {
  text-align: center;
  padding: 20px 16px;
  color: #cc99ff;
}
.stimulus-running-hint i {
  font-size: 22px;
  margin-bottom: 8px;
  display: block;
  animation: dot-pulse 1.2s ease-in-out infinite;
}
.stimulus-running-hint p {
  margin: 0 0 6px;
  font-size: 12px;
  color: #ddeeff;
}
.stimulus-running-hint span {
  font-size: 10px;
  color: #8899bb;
}
.baseline-cross {
  position: relative;
  color: #aaccff;
  text-align: center;
}
.baseline-cross p {
  position: absolute;
  bottom: -28px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 10px;
  margin: 0;
  color: #8899bb;
}
.cross-v, .cross-h {
  position: absolute;
  background: #ffffff;
  box-shadow: 0 0 10px rgba(255,255,255,0.6);
}
.cross-v { width: 4px; height: 48px; left: 38px; top: 16px; }
.cross-h { width: 48px; height: 4px; left: 16px; top: 38px; }
.baseline-cross--inline { width: 80px; height: 80px; }
.cross-v--large { width: 6px; height: 72px; left: 57px; top: 24px; }
.cross-h--large { width: 72px; height: 6px; left: 24px; top: 57px; }

.stimulus-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.stimulus-overlay-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.88);
  backdrop-filter: blur(6px);
}
.stimulus-overlay-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  max-width: 92vw;
  max-height: 92vh;
  animation: overlay-pop-in 0.38s cubic-bezier(0.22, 1, 0.36, 1);
}
.overlay-baseline {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.overlay-cross {
  position: relative;
  width: 120px;
  height: 120px;
}
.overlay-image-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.overlay-image {
  max-width: min(85vw, 960px);
  max-height: min(72vh, 720px);
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 10px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.08);
  animation: overlay-image-in 0.42s cubic-bezier(0.22, 1, 0.36, 1);
}
.overlay-caption {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #eef4ff;
  text-align: center;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
}
.overlay-marker {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
  background: rgba(153, 68, 255, 0.35);
  color: #eeccff;
  border: 1px solid rgba(153, 68, 255, 0.5);
  font-family: monospace;
}
.overlay-countdown {
  position: absolute;
  top: -36px;
  right: 0;
  font-size: 13px;
  font-family: monospace;
  color: #ff99cc;
  background: rgba(0, 0, 0, 0.5);
  padding: 4px 10px;
  border-radius: 8px;
}
@keyframes overlay-pop-in {
  from { opacity: 0; transform: scale(0.88); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes overlay-image-in {
  from { opacity: 0; transform: scale(0.92) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.stimulus-overlay-enter-active,
.stimulus-overlay-leave-active {
  transition: opacity 0.28s ease;
}
.stimulus-overlay-enter-active .stimulus-overlay-content,
.stimulus-overlay-leave-active .stimulus-overlay-content {
  transition: transform 0.28s ease, opacity 0.28s ease;
}
.stimulus-overlay-enter-from,
.stimulus-overlay-leave-to {
  opacity: 0;
}
.stimulus-overlay-enter-from .stimulus-overlay-content,
.stimulus-overlay-leave-to .stimulus-overlay-content {
  opacity: 0;
  transform: scale(0.94);
}
.stimulus-placeholder {
  text-align: center;
  padding: 12px;
  font-size: 10px;
  color: #778899;
}
.thumb-row {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}
.stimulus-thumb {
  width: 72px;
  height: 54px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.15);
}
.stimulus-caption {
  margin: 6px 0 0;
  font-size: 10px;
  color: #cc99ff;
  text-align: center;
}

.emotion-gallery {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}
.emotion-block {
  padding: 8px;
  border-radius: 8px;
  border: 1px solid rgba(100, 80, 180, 0.3);
  background: rgba(0, 0, 0, 0.2);
  transition: border-color 0.25s, box-shadow 0.25s;
}
.emotion-block.active {
  border-color: rgba(255, 100, 180, 0.7);
  box-shadow: 0 0 14px rgba(255, 100, 180, 0.25);
}
.emotion-block.done {
  border-color: rgba(0, 200, 120, 0.5);
}
.emotion-block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 10px;
}
.emotion-name { color: #cc99ff; font-weight: 700; }
.emotion-marker { color: #ff66aa; font-size: 9px; }
.emotion-images {
  display: flex;
  gap: 4px;
}
.emotion-img {
  flex: 1;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.1);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}
.emotion-img--active {
  border-color: rgba(255, 120, 200, 0.9);
  box-shadow: 0 0 12px rgba(255, 100, 180, 0.55);
  transform: scale(1.06);
  z-index: 1;
}

.progress-block {
  margin-bottom: 10px; padding: 8px 10px; border-radius: 8px;
  background: rgba(0, 0, 0, 0.25); border: 1px solid rgba(153, 68, 255, 0.2);
}
.progress-label {
  display: flex; justify-content: space-between; font-size: 11px; color: #cc99ff; margin-bottom: 4px;
}
.phase-timer { font-family: monospace; color: #ff88cc; }
.progress-track {
  height: 4px; border-radius: 2px; background: rgba(255,255,255,0.1); overflow: hidden;
}
.progress-fill {
  height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, #7733ee, #ff66aa);
  transition: width 0.1s linear;
}
.sim-message { font-size: 10px; color: #8899bb; margin: 4px 0 0; }

.steps-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }

.step-card {
  padding: 10px; border-radius: 8px;
  border: 1px solid rgba(100, 80, 200, 0.3);
  background: rgba(8, 12, 28, 0.8);
  transition: all 0.3s;
}
.step-card.running {
  border-color: rgba(153, 68, 255, 0.8);
  background: rgba(30, 15, 60, 0.9);
  box-shadow: 0 0 16px rgba(153, 68, 255, 0.35);
  transform: translateY(-2px);
}
.step-card.done {
  border-color: rgba(0, 200, 120, 0.45);
  background: rgba(8, 28, 20, 0.85);
}

.step-num-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.step-num { font-size: 10px; color: #8866cc; font-weight: 700; }
.step-live { font-size: 9px; color: #ff88cc; animation: dot-pulse 1s infinite; }
.step-done { font-size: 11px; color: #44eeaa; font-weight: 700; }

.step-name { font-size: 12px; font-weight: 700; color: #fff; margin-bottom: 6px; }

.marker-code.flash {
  animation: marker-flash 0.6s ease;
  background: rgba(255, 100, 180, 0.45);
}
@keyframes marker-flash {
  0%, 100% { box-shadow: none; }
  50% { box-shadow: 0 0 12px rgba(255, 100, 180, 0.8); }
}

.marker-row { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; flex-wrap: wrap; }
.marker-label { font-size: 10px; color: #667799; }
.marker-code {
  font-size: 13px; font-weight: 700; color: #ff66aa;
  background: rgba(255, 80, 150, 0.15); padding: 1px 6px; border-radius: 4px; font-family: monospace;
}
.marker-name { font-size: 10px; color: #8899bb; font-family: monospace; }
.step-dur { font-size: 10px; color: #66aacc; margin-bottom: 4px; }
.step-desc {
  font-size: 10px; color: #778899; margin: 0; line-height: 1.4;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.marker-log {
  margin-top: 10px; padding: 8px 10px; border-radius: 8px;
  background: rgba(0, 0, 0, 0.35); border: 1px solid rgba(100, 80, 200, 0.25);
}
.log-title { font-size: 11px; color: #aaccff; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.log-channel {
  font-size: 9px; padding: 1px 6px; border-radius: 8px;
  background: rgba(153, 68, 255, 0.25); color: #cc99ff;
}
.log-list { list-style: none; margin: 0; padding: 0; max-height: 120px; overflow-y: auto; }
.log-item {
  display: flex; align-items: center; gap: 8px; font-size: 10px;
  padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
  animation: log-in 0.3s ease;
}
@keyframes log-in {
  from { opacity: 0; transform: translateX(-6px); }
  to { opacity: 1; transform: translateX(0); }
}
.log-time { color: #667788; font-family: monospace; min-width: 52px; }
.log-marker { color: #ff66aa; font-weight: 700; min-width: 28px; }
.log-detail { flex: 1; color: #99aabb; }
.log-ch { color: #66bbff; font-size: 9px; }

.runtime-bar {
  display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; padding-top: 8px;
  border-top: 1px solid rgba(100, 80, 200, 0.2); font-size: 11px; color: #8899bb;
}
.strict-count { font-weight: 700; color: #ffcc44; }
.strict-count.partial { color: #66bbff; }
.strict-count.ok { color: #44eeaa; }

.verify-list {
  margin-top: 8px; padding: 8px 10px; border-radius: 8px;
  background: rgba(0, 0, 0, 0.28); border: 1px solid rgba(0, 200, 120, 0.2);
  font-size: 10px;
}
.verify-item {
  display: flex; align-items: flex-start; gap: 6px; padding: 4px 0;
  color: #ff8866; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.verify-item.ok { color: #44eeaa; }
.verify-item code { color: #cc99ff; font-size: 9px; white-space: nowrap; }
.verify-item span { flex: 1; color: #99aabb; line-height: 1.4; }

.panel-loading, .panel-error { font-size: 12px; color: #8aa8cc; padding: 12px 0; text-align: center; }
.panel-error { color: #ff8866; }
.retry-link { margin-left: 8px; background: none; border: none; color: #66bbff; cursor: pointer; text-decoration: underline; }

@media (max-width: 1100px) {
  .steps-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
