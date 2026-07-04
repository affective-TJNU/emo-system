<template>
  <div class="perf-page">
    <header class="perf-header">
      <div>
        <h1>系统性能看板</h1>
        <p class="perf-sub">后端资源 · 训练耗时 · 接口延迟 · MetaBCI 状态</p>
      </div>
      <div class="actions">
        <el-tag :type="online ? 'success' : 'danger'" effect="dark">
          {{ online ? '后端已连接' : '后端未连接' }}
        </el-tag>
        <el-button type="primary" @click="refresh" :loading="loading">刷新</el-button>
        <el-button @click="router.push('/home')">返回主页</el-button>
      </div>
    </header>

    <el-alert
      v-if="globalError"
      :title="globalError"
      type="error"
      show-icon
      :closable="false"
      class="perf-alert"
    />

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="kpi-card">
          <div class="kpi-label">后端 CPU</div>
          <div class="kpi-value">{{ fmtPct(metrics.process_cpu_percent) }}</div>
          <div class="kpi-sub">进程占用</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="kpi-card">
          <div class="kpi-label">后端内存</div>
          <div class="kpi-value">{{ fmtMb(metrics.process_memory_mb) }}</div>
          <div class="kpi-sub">RSS</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="kpi-card">
          <div class="kpi-label">单 Epoch 耗时</div>
          <div class="kpi-value">{{ fmtMs(training.avg_epoch_ms) }}</div>
          <div class="kpi-sub">均值 · {{ training.sample_count ?? 0 }} 样本</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="kpi-card">
          <div class="kpi-label">训练准确率</div>
          <div class="kpi-value accent">{{ fmtAcc(trainingLog.max_accuracy) }}</div>
          <div class="kpi-sub">{{ String(trainingLog.model || '暂无日志') }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <div class="panel-card">
          <div class="panel-head">
            <span>后端进程</span>
            <el-tag v-if="rtt.metrics != null" size="small" type="info">RTT {{ rtt.metrics.toFixed(1) }} ms</el-tag>
          </div>
          <div class="panel-body">
            <p v-if="errors.metrics" class="panel-error">{{ errors.metrics }}</p>
            <dl v-else class="info-grid">
              <div class="info-row"><dt>进程 ID</dt><dd>{{ metrics.pid || '—' }}</dd></div>
              <div class="info-row"><dt>进程 CPU</dt><dd>{{ fmtPct(metrics.process_cpu_percent) }}</dd></div>
              <div class="info-row"><dt>进程内存</dt><dd>{{ fmtMb(metrics.process_memory_mb) }}</dd></div>
              <div class="info-row"><dt>系统 CPU</dt><dd>{{ fmtPct(metrics.system_cpu_percent) }}</dd></div>
              <div class="info-row"><dt>系统内存占用</dt><dd>{{ fmtPct(metrics.system_memory_percent) }}</dd></div>
              <div class="info-row"><dt>可用内存</dt><dd>{{ fmtMb(metrics.system_memory_available_mb) }}</dd></div>
              <div class="info-row"><dt>监控组件</dt><dd>{{ metrics.psutil ? 'psutil 已启用' : (metrics.note || '未安装 psutil') }}</dd></div>
              <div class="info-row"><dt>采样时间</dt><dd>{{ fmtTime(metrics.timestamp) }}</dd></div>
            </dl>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="panel-card">
          <div class="panel-head">
            <span>训练 Epoch 统计</span>
            <el-tag v-if="rtt.training != null" size="small" type="info">RTT {{ rtt.training.toFixed(1) }} ms</el-tag>
          </div>
          <div class="panel-body">
            <p v-if="errors.training" class="panel-error">{{ errors.training }}</p>
            <template v-else>
              <dl class="info-grid">
                <div class="info-row"><dt>平均耗时</dt><dd>{{ fmtMs(training.avg_epoch_ms) }}</dd></div>
                <div class="info-row"><dt>中位耗时</dt><dd>{{ fmtMs(training.median_epoch_ms) }}</dd></div>
                <div class="info-row"><dt>最近一次</dt><dd>{{ fmtMs(training.last_epoch_ms) }}</dd></div>
                <div class="info-row"><dt>统计样本数</dt><dd>{{ training.sample_count ?? 0 }} 个 epoch 间隔</dd></div>
                <div class="info-row"><dt>数据来源</dt><dd class="path-text" :title="training.log_file">{{ shortPath(training.log_file) }}</dd></div>
              </dl>
              <p v-if="training.message" class="panel-hint">{{ training.message }}</p>
            </template>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <div class="panel-card">
          <div class="panel-head">
            <span>最新训练日志</span>
            <el-tag v-if="rtt.log != null" size="small" type="info">RTT {{ rtt.log.toFixed(1) }} ms</el-tag>
          </div>
          <div class="panel-body">
            <p v-if="errors.log" class="panel-error">{{ errors.log }}</p>
            <template v-else>
              <dl class="info-grid">
                <div class="info-row"><dt>模型</dt><dd>{{ trainingLog.model || '—' }}</dd></div>
                <div class="info-row"><dt>特征类型</dt><dd>{{ trainingLog.feature_type || '—' }}</dd></div>
                <div class="info-row"><dt>最高准确率</dt><dd class="highlight">{{ fmtAcc(trainingLog.max_accuracy) }}</dd></div>
                <div class="info-row"><dt>最终准确率</dt><dd>{{ fmtAcc(trainingLog.final_accuracy) }}</dd></div>
                <div class="info-row"><dt>最佳 Epoch</dt><dd>{{ trainingLog.best_epoch ?? '—' }}</dd></div>
                <div class="info-row"><dt>已完成 Epoch</dt><dd>{{ trainingLog.epoch_count ?? '—' }} / {{ trainingLog.configured_epochs ?? '—' }}</dd></div>
                <div class="info-row"><dt>训练时长</dt><dd>{{ trainingLog.training_duration || '—' }}</dd></div>
                <div class="info-row"><dt>保存路径</dt><dd class="path-text" :title="String(trainingLog.save_path || '')">{{ shortPath(String(trainingLog.save_path || '')) }}</dd></div>
              </dl>
              <div v-if="recentEpochs.length" class="epoch-table-wrap">
                <p class="table-title">最近 5 个 Epoch</p>
                <table class="epoch-table">
                  <thead>
                    <tr><th>Epoch</th><th>准确率</th><th>损失</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in recentEpochs" :key="row.epoch">
                      <td>{{ row.epoch }}</td>
                      <td>{{ fmtAcc(row.accuracy) }}</td>
                      <td>{{ fmtLoss(row.loss) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :lg="12">
        <div class="panel-card">
          <div class="panel-head">
            <span>MetaBCI 状态摘要</span>
            <el-tag v-if="rtt.metabci != null" size="small" type="info">RTT {{ rtt.metabci.toFixed(1) }} ms</el-tag>
          </div>
          <div class="panel-body">
            <p v-if="errors.metabci" class="panel-error">{{ errors.metabci }}</p>
            <template v-else>
              <div class="status-badges">
                <el-tag :type="metabciRaw.module_available ? 'success' : 'danger'" effect="dark">
                  模块 {{ metabciRaw.module_available ? '可用' : '不可用' }}
                </el-tag>
                <el-tag :type="metabciRaw.fallback_supported ? 'warning' : 'info'" effect="dark">
                  降级 {{ metabciRaw.fallback_supported ? '支持' : '不支持' }}
                </el-tag>
                <el-tag :type="braindaMeetsMinimum ? 'success' : 'info'" effect="dark">
                  brainda 严格 API {{ braindaStrictCount }} 项
                </el-tag>
              </div>
              <p class="table-title">子模块状态</p>
              <table class="epoch-table module-table">
                <thead>
                  <tr><th>模块</th><th>状态</th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in moduleRows" :key="item.name">
                    <td>{{ item.label }}</td>
                    <td>
                      <el-tag size="small" :type="item.ok ? 'success' : 'danger'">
                        {{ item.ok ? '正常' : '不可用' }}
                      </el-tag>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p class="table-title">brainda 严格调用（答辩计分口径）</p>
              <ul class="api-list">
                <li v-for="fn in braindaFunctions" :key="fn.id">
                  <strong>{{ fn.name || fn.id }}</strong>
                  <span>{{ fn.description }}</span>
                </li>
              </ul>
            </template>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  api,
  timedApiRequest,
  type SystemMetricsPayload,
  type TrainingEpochStats,
} from '@/api/index';

const MODULE_LABELS: Record<string, string> = {
  brainda: 'brainda 数据处理',
  brainflow: 'brainflow 在线推理',
  brainstim: 'brainstim 范式刺激',
};

const router = useRouter();
const loading = ref(false);
const online = ref(false);
const globalError = ref('');

const metrics = ref<SystemMetricsPayload>({ timestamp: '', pid: 0 });
const training = ref<TrainingEpochStats>({
  success: false,
  sample_count: 0,
  avg_epoch_ms: null,
  median_epoch_ms: null,
  last_epoch_ms: null,
});
const trainingLog = ref<Record<string, unknown>>({});
const metabciRaw = ref<Record<string, unknown>>({});

const errors = reactive({
  metrics: '',
  training: '',
  log: '',
  metabci: '',
});

const rtt = reactive({
  metrics: null as number | null,
  training: null as number | null,
  log: null as number | null,
  metabci: null as number | null,
});

type EpochRow = { epoch: number; accuracy: number; loss: number };

const recentEpochs = computed(() => {
  const rows = (trainingLog.value.epochs as EpochRow[] | undefined) || [];
  return rows.slice(-5);
});

const braindaStrict = computed(() => metabciRaw.value.brainda_strict as Record<string, unknown> | undefined);
const braindaStrictCount = computed(() => Number(braindaStrict.value?.strict_function_count ?? 0));
const braindaMeetsMinimum = computed(() => Boolean(braindaStrict.value?.meets_minimum_three));

const braindaFunctions = computed(() => {
  const list = braindaStrict.value?.strict_functions;
  if (!Array.isArray(list)) return [];
  return list as Array<{ id?: string; name?: string; description?: string }>;
});

const moduleRows = computed(() => {
  const modules = metabciRaw.value.modules as Record<string, boolean> | undefined;
  if (!modules) return [];
  return Object.entries(modules).map(([name, ok]) => ({
    name,
    label: MODULE_LABELS[name] || name,
    ok,
  }));
});

const fmtPct = (v?: number) => (v == null ? '—' : `${v.toFixed(1)}%`);
const fmtMb = (v?: number) => (v == null ? '—' : `${v.toFixed(1)} MB`);
const fmtMs = (v?: number | null) => (v == null ? '—' : `${v.toFixed(1)} ms`);
const fmtAcc = (v?: unknown) => {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? `${n.toFixed(2)}%` : '—';
};
const fmtLoss = (v?: unknown) => {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(4) : '—';
};
const fmtTime = (v?: string) => {
  if (!v) return '—';
  try {
    return new Date(v).toLocaleString('zh-CN');
  } catch {
    return v;
  }
};
const shortPath = (p?: string) => {
  if (!p) return '—';
  const parts = p.split('/');
  return parts.length > 3 ? `…/${parts.slice(-3).join('/')}` : p;
};

function networkHint(err: unknown) {
  const msg = err instanceof Error ? err.message : String(err);
  if (/fetch|network|failed/i.test(msg)) {
    return `${msg}（请确认后端已启动，或通过 5173 端口访问）`;
  }
  return msg;
}

async function loadMetrics() {
  try {
    const res = await timedApiRequest<SystemMetricsPayload>('/api/system-metrics');
    rtt.metrics = res.rttMs;
    if (!res.ok) {
      errors.metrics = `请求失败 (${res.status})`;
      return;
    }
    errors.metrics = '';
    metrics.value = res.data;
  } catch (err) {
    errors.metrics = networkHint(err);
    throw err;
  }
}

async function loadTraining() {
  try {
    const res = await timedApiRequest<TrainingEpochStats>('/api/training-epoch-stats');
    rtt.training = res.rttMs;
    if (!res.ok) {
      errors.training = `请求失败 (${res.status})`;
      return;
    }
    errors.training = '';
    training.value = res.data;
  } catch (err) {
    errors.training = networkHint(err);
    throw err;
  }
}

async function loadLog() {
  try {
    const res = await timedApiRequest<{
      success?: boolean;
      data?: Record<string, unknown>;
      error?: string;
    }>('/api/latest-log-data');
    rtt.log = res.rttMs;
    if (!res.ok || !res.data.success) {
      errors.log = res.data.error || `请求失败 (${res.status})`;
      trainingLog.value = {};
      return;
    }
    errors.log = '';
    trainingLog.value = res.data.data || {};
  } catch (err) {
    errors.log = networkHint(err);
    throw err;
  }
}

async function loadMetabci() {
  try {
    const res = await timedApiRequest<Record<string, unknown>>('/api/metabci/status');
    rtt.metabci = res.rttMs;
    if (!res.ok) {
      errors.metabci = `请求失败 (${res.status})`;
      return;
    }
    errors.metabci = '';
    metabciRaw.value = res.data;
  } catch (err) {
    errors.metabci = networkHint(err);
    throw err;
  }
}

const refresh = async () => {
  loading.value = true;
  globalError.value = '';
  try {
    await api.health();
    online.value = true;
  } catch (err) {
    online.value = false;
    globalError.value = `无法连接后端：${networkHint(err)}`;
  }

  const results = await Promise.allSettled([
    loadMetrics(),
    loadTraining(),
    loadLog(),
    loadMetabci(),
  ]);

  const rejected = results.filter((r) => r.status === 'rejected').length;
  const panelErrors = Object.values(errors).filter(Boolean).length;

  if (!online.value) {
    ElMessage.error('后端未连接，请先运行 start.py');
  } else if (rejected > 0 || panelErrors > 0) {
    ElMessage.warning(`部分性能数据加载失败（${Math.max(rejected, panelErrors)} 项）`);
  }

  loading.value = false;
};

onMounted(refresh);
</script>

<style scoped>
.perf-page {
  padding: 24px;
  min-height: 100vh;
  color: #e0e0ff;
  background: linear-gradient(135deg, #0a0f2b 0%, #1a2a6c 50%, #0a0f2b 100%);
  box-sizing: border-box;
}

.perf-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.perf-header h1 {
  margin: 0;
  font-size: 28px;
  color: #fff;
  text-shadow: 0 0 16px rgba(64, 128, 255, 0.45);
}

.perf-sub {
  margin: 6px 0 0;
  color: #a0d2ff;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  align-items: center;
  flex-wrap: wrap;
}

.perf-alert {
  margin-bottom: 16px;
}

.kpi-row {
  margin-bottom: 8px;
}

.kpi-card,
.panel-card {
  background: rgba(10, 15, 40, 0.92);
  border: 1px solid rgba(64, 128, 255, 0.35);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 40, 0.35);
  margin-bottom: 16px;
}

.kpi-card {
  padding: 18px 20px;
}

.kpi-label {
  font-size: 13px;
  color: #a0d2ff;
}

.kpi-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.kpi-value.accent {
  color: #5efce8;
}

.kpi-sub {
  margin-top: 6px;
  font-size: 12px;
  color: #8b9cb8;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(64, 128, 255, 0.25);
  color: #a0d2ff;
  font-weight: 600;
}

.panel-body {
  padding: 16px 18px;
  max-height: 420px;
  overflow: auto;
}

.panel-error {
  margin: 0;
  color: #ff8e8e;
  font-size: 14px;
  line-height: 1.6;
}

.panel-hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: #8b9cb8;
}

.info-grid {
  margin: 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(64, 128, 255, 0.12);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row dt {
  flex-shrink: 0;
  color: #8b9cb8;
  font-size: 13px;
}

.info-row dd {
  margin: 0;
  text-align: right;
  color: #e8f0ff;
  font-size: 14px;
  word-break: break-all;
}

.info-row dd.highlight {
  color: #5efce8;
  font-weight: 600;
}

.path-text {
  font-size: 12px !important;
  color: #a0d2ff !important;
}

.table-title {
  margin: 16px 0 8px;
  font-size: 13px;
  color: #a0d2ff;
  font-weight: 600;
}

.epoch-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.epoch-table th,
.epoch-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid rgba(64, 128, 255, 0.15);
}

.epoch-table th {
  color: #8b9cb8;
  font-weight: 500;
}

.epoch-table td {
  color: #e8f0ff;
}

.status-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.api-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.api-list li {
  padding: 10px 0;
  border-bottom: 1px solid rgba(64, 128, 255, 0.12);
}

.api-list li:last-child {
  border-bottom: none;
}

.api-list strong {
  display: block;
  color: #5efce8;
  font-size: 13px;
  margin-bottom: 4px;
}

.api-list span {
  display: block;
  color: #8b9cb8;
  font-size: 12px;
  line-height: 1.5;
}
</style>
