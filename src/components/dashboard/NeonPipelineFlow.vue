<template>
  <!-- 数据处理流水线 — 霓虹环形光球 + 能量流 -->
  <div class="pipeline-stage" :class="{ active: loading || preprocessingDone }">
    <!-- 背景装饰 -->
    <div class="stage-bg-decor" aria-hidden="true">
      <div class="decor-grid" />
      <div class="decor-glow decor-glow--center" />
      <div class="decor-glow decor-glow--left" />
      <div class="decor-glow decor-glow--right" />
      <span class="decor-corner decor-corner--tl" />
      <span class="decor-corner decor-corner--tr" />
      <span class="decor-corner decor-corner--bl" />
      <span class="decor-corner decor-corner--br" />
      <div class="decor-particles">
        <span v-for="i in 12" :key="i" class="decor-dot" :style="{ left: `${(i * 17) % 100}%`, top: `${(i * 29) % 100}%`, animationDelay: `${i * 0.35}s` }" />
      </div>
    </div>

    <div class="pipeline-visual-align">
      <div class="pipeline-stage-body">
      <!-- 能量流背景层 -->
      <div class="energy-track">
      <svg class="energy-svg" viewBox="0 0 1200 100" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <linearGradient id="waveG1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#2299ff" stop-opacity="0" />
            <stop offset="30%" stop-color="#44ccff" stop-opacity="0.55" />
            <stop offset="70%" stop-color="#8866ff" stop-opacity="0.5" />
            <stop offset="100%" stop-color="#9944ff" stop-opacity="0" />
          </linearGradient>
          <linearGradient id="beamG" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.3" />
            <stop offset="50%" stop-color="#00f0ff" stop-opacity="1" />
            <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.3" />
          </linearGradient>
          <filter id="waveBlur"><feGaussianBlur stdDeviation="3" /></filter>
          <filter id="beamGlow"><feGaussianBlur stdDeviation="3" /></filter>
        </defs>
        <path
          v-for="(d, i) in wavePaths"
          :key="i"
          :d="d"
          fill="none"
          stroke="url(#waveG1)"
          stroke-width="2.5"
          :opacity="0.35 + i * 0.08"
          filter="url(#waveBlur)"
        />
        <line x1="0" y1="50" x2="1200" y2="50" stroke="url(#beamG)" stroke-width="4" filter="url(#beamGlow)" />
      </svg>
      <div class="beam-dots">
        <span v-for="i in 5" :key="i" class="beam-dot-el" :style="{ animationDelay: `${(i - 1) * 0.6}s` }" />
      </div>
    </div>

    <!-- 4 节点 -->
    <div class="nodes-grid">
      <div
        v-for="(node, idx) in nodes"
        :key="node.id"
        class="node-col"
        @click="$emit('node-click', idx)"
      >
        <div class="status-pill" :class="getStatus(idx)">
          {{ statusText(getStatus(idx)) }}
        </div>

        <div class="sphere-unit">
          <div class="sphere-glow cyan" />
          <div class="sphere-glow pink" />
          <svg class="sphere-rings" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1" stroke-dasharray="6 10" class="ring-spin" />
            <circle cx="60" cy="60" r="44" fill="none" stroke="rgba(0,220,255,0.45)" stroke-width="1.5" />
            <path d="M20,60 A40,40 0 0,1 100,60" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.2" />
            <path d="M25,60 A35,35 0 0,0 95,60" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1" />
            <circle
              v-for="d in 5"
              :key="d"
              :cx="orbitDot(d, 48).x"
              :cy="orbitDot(d, 48).y"
              r="2"
              fill="#fff"
              class="orbit-dot"
              :style="{ animationDelay: `${d * 0.35}s` }"
            />
          </svg>
          <div class="sphere-core">
            <div class="core-inner" />
          </div>
        </div>

        <div class="icon-square" />
        <p class="node-name">{{ node.titleCn }}</p>
      </div>
    </div>
    </div>
    </div>

    <div class="stage-footer">
      <button class="btn-start" :disabled="loading" @click="$emit('start')">
        <span class="btn-shine" />
        {{ loading ? '处理中...' : '启动数据流水线处理' }}
      </button>
      <span class="stage-meta">{{ stageMetaText }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';

export type NodeStatus = 'pending' | 'running' | 'completed';

const props = defineProps<{
  processStep?: number;
  loading?: boolean;
  preprocessingDone?: boolean;
  statuses?: NodeStatus[];
  datasetLabel?: string;
  isLiveMode?: boolean;
}>();

defineEmits<{ 'node-click': [number]; start: [] }>();

const stageMetaText = computed(() => {
  const base = '采样率 200Hz | 4导 (AF3/AF4/F3/F4) | de_comp_4ch_1p5s | 窗长 1.5s';
  const label = props.datasetLabel || (props.isLiveMode ? '自采数据集' : 'SEED 数据集');
  if (props.isLiveMode) {
    return `${label} · Neuroscan 40导→4导 · ${base}`;
  }
  return `${label} · ${base}`;
});

const nodes = [
  { id: '1', titleCn: '原始脑电数据导入' },
  { id: '2', titleCn: '时空频联合特征提取' },
  { id: '3', titleCn: '频段分割滤波' },
  { id: '4', titleCn: '特征可视化输出' },
];

const wavePaths = [
  'M0,55 C150,25 250,75 400,50 C550,25 650,70 800,48 C950,30 1050,65 1200,50',
  'M0,65 C180,35 280,80 450,58 C620,38 720,72 900,52 C1020,38 1100,62 1200,55',
];

function getStatus(idx: number): NodeStatus {
  if (props.statuses?.length === 4) return props.statuses[idx];
  if (props.preprocessingDone || (props.processStep ?? 0) > idx) return 'completed';
  if (props.loading && (props.processStep ?? 0) === idx) return 'running';
  if (props.loading && (props.processStep ?? 0) >= 4) return 'completed';
  return 'pending';
}

function statusText(s: NodeStatus) {
  return { pending: '待执行', running: '进行中', completed: '完成' }[s];
}

function orbitDot(i: number, r: number) {
  const a = ((i - 1) / 5) * Math.PI * 2 - Math.PI / 2;
  return { x: 60 + r * Math.cos(a), y: 60 + r * Math.sin(a) };
}
</script>

<style scoped>
.pipeline-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: 0;
  overflow: hidden;
}

.stage-bg-decor {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.decor-grid {
  position: absolute;
  inset: 8% 4%;
  border-radius: 16px;
  background-image:
    linear-gradient(rgba(34, 153, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 153, 255, 0.06) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, #000 20%, transparent 100%);
}

.decor-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
}
.decor-glow--center {
  width: 55%;
  height: 45%;
  left: 22%;
  top: 28%;
  background: radial-gradient(circle, rgba(100, 60, 255, 0.12) 0%, transparent 70%);
}
.decor-glow--left {
  width: 28%;
  height: 35%;
  left: 0;
  top: 20%;
  background: radial-gradient(circle, rgba(0, 180, 255, 0.1) 0%, transparent 70%);
}
.decor-glow--right {
  width: 28%;
  height: 35%;
  right: 0;
  top: 20%;
  background: radial-gradient(circle, rgba(255, 80, 180, 0.08) 0%, transparent 70%);
}

.decor-corner {
  position: absolute;
  width: 28px;
  height: 28px;
  border-color: rgba(34, 153, 255, 0.35);
  border-style: solid;
}
.decor-corner--tl { top: 12px; left: 12px; border-width: 2px 0 0 2px; }
.decor-corner--tr { top: 12px; right: 12px; border-width: 2px 2px 0 0; }
.decor-corner--bl { bottom: 12px; left: 12px; border-width: 0 0 2px 2px; }
.decor-corner--br { bottom: 12px; right: 12px; border-width: 0 2px 2px 0; }

.decor-particles {
  position: absolute;
  inset: 0;
}
.decor-dot {
  position: absolute;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(0, 200, 255, 0.45);
  animation: decorFloat 4s ease-in-out infinite;
}

@keyframes decorFloat {
  0%, 100% { opacity: 0.25; transform: translateY(0); }
  50% { opacity: 0.85; transform: translateY(-6px); }
}

.pipeline-visual-align {
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 0;
}

.pipeline-stage-body {
  position: relative;
  width: 100%;
  height: 312px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.energy-track {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 150px;
  transform: translateY(-50%);
  z-index: 1;
  pointer-events: none;
}

.energy-svg {
  width: 100%;
  height: 100%;
}

.beam-dots {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 0;
  transform: translateY(-50%);
}
.beam-dot-el {
  position: absolute;
  top: -3px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 8px #00eeff;
  animation: dotFlow 3s linear infinite;
  opacity: 0;
}
.pipeline-stage.active .beam-dot-el { opacity: 1; }

@keyframes dotFlow {
  0% { left: 0%; opacity: 0; }
  8% { opacity: 1; }
  92% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
}

.nodes-grid {
  position: relative;
  z-index: 5;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 0 12px;
  align-items: center;
}

.node-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.3s ease;
}
.node-col:hover {
  transform: translateY(-4px);
}

.status-pill {
  height: 32px;
  padding: 0 18px;
  margin-bottom: 10px;
  border-radius: 20px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  display: flex;
  align-items: center;
  white-space: nowrap;
  z-index: 10;
}
.status-pill.pending {
  background: rgba(20, 40, 80, 0.85);
  color: #a8c4e8;
  border: 1px solid rgba(168, 196, 232, 0.25);
}
.status-pill.running {
  background: linear-gradient(90deg, #0088ee, #00bbff);
  box-shadow: 0 0 12px rgba(0, 170, 255, 0.6);
}
.status-pill.completed {
  background: linear-gradient(135deg, #7733ee, #9955ff);
  box-shadow: 0 0 12px rgba(130, 60, 255, 0.55);
}

.sphere-unit {
  position: relative;
  width: 132px;
  height: 132px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.sphere-glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}
.sphere-glow.cyan {
  width: 118px;
  height: 118px;
  background: radial-gradient(circle, rgba(0, 200, 255, 0.35) 0%, transparent 70%);
  animation: breathe 3s ease-in-out infinite;
}
.sphere-glow.pink {
  width: 64px;
  height: 64px;
  background: radial-gradient(circle, rgba(255, 60, 150, 0.5) 0%, transparent 70%);
  animation: breathe 3s ease-in-out infinite 0.5s;
}

.sphere-rings {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 2;
}

.ring-spin {
  transform-origin: 60px 60px;
  animation: spin 14s linear infinite;
}

.orbit-dot {
  animation: twinkle 2s ease-in-out infinite;
}

.sphere-core {
  position: relative;
  z-index: 4;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #fff 0%, #ff66aa 40%, #ee1177 75%, #aa0055 100%);
  box-shadow:
    0 0 16px rgba(255, 50, 130, 0.9),
    0 0 32px rgba(255, 100, 180, 0.5),
    0 0 48px rgba(0, 200, 255, 0.3);
  animation: corePulse 4s ease-in-out infinite;
}

.core-inner {
  position: absolute;
  top: 20%;
  left: 22%;
  width: 30%;
  height: 25%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  filter: blur(1px);
}

.icon-square {
  width: 16px;
  height: 16px;
  border: 1.5px solid rgba(255, 255, 255, 0.7);
  border-radius: 2px;
  margin-bottom: 10px;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.2);
}

.node-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  text-align: center;
  white-space: nowrap;
  margin: 0;
  text-shadow: 0 0 8px rgba(0, 180, 255, 0.2);
}

.stage-footer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 8px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 0 12px;
  pointer-events: none;
}
.stage-footer .btn-start {
  pointer-events: auto;
}

.btn-start {
  position: relative;
  overflow: hidden;
  border: none;
  border-radius: 28px;
  padding: 13px 36px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  background: linear-gradient(135deg, #0088ff, #6644ff, #9933ff);
  box-shadow: 0 0 20px rgba(100, 80, 255, 0.5);
  transition: transform 0.25s, box-shadow 0.25s;
}
.btn-start:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 0 30px rgba(100, 80, 255, 0.7);
}
.btn-start:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%);
  animation: shine 3s ease-in-out infinite;
}

.stage-meta {
  font-size: 13px;
  color: #8aa8cc;
  text-align: center;
}

@keyframes breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.06); }
}
@keyframes corePulse {
  0%, 100% { transform: scale(1); filter: brightness(1); }
  50% { transform: scale(1.1); filter: brightness(1.2); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
@keyframes shine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@media (max-width: 1100px) {
  .sphere-unit { width: 100px; height: 100px; }
  .sphere-core { width: 34px; height: 34px; }
  .node-name { font-size: 13px; }
  .status-pill { font-size: 13px; height: 28px; padding: 0 14px; }
}
</style>
