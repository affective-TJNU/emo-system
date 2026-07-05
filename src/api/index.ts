// API服务配置：浏览器端优先同源 /api（Vite 代理），避免远程访问时 localhost 指向访问者本机
function resolveApiBaseUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined') {
    const port = window.location.port;
    if (import.meta.env.DEV || port === '5173' || port === '4173') {
      return '';
    }
    return `${window.location.protocol}//${window.location.hostname}:5001`;
  }
  return 'http://localhost:5001';
}

export const API_BASE_URL = resolveApiBaseUrl();

export async function timedApiRequest<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<{
  data: T;
  rttMs: number;
  serverProcessMs: number | null;
  ok: boolean;
  status: number;
}> {
  const fullUrl = `${API_BASE_URL}${path}`;
  const t0 = performance.now();
  const response = await fetch(fullUrl, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> | undefined),
    },
  });
  const rttMs = performance.now() - t0;
  const h = response.headers.get('X-Process-Time-Ms');
  const sp = h != null ? parseFloat(h) : NaN;
  const serverProcessMs = Number.isFinite(sp) ? sp : null;
  let data: T;
  try {
    data = (await response.json()) as T;
  } catch {
    data = {} as T;
  }
  return { data, rttMs, serverProcessMs, ok: response.ok, status: response.status };
}

// 通用请求函数
async function request<T>(url: string, options: RequestInit = {}, timeoutMs = 0): Promise<T> {
  const fullUrl = `${API_BASE_URL}${url}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const controller = timeoutMs > 0 ? new AbortController() : null;
  const timer = controller
    ? window.setTimeout(() => controller.abort(), timeoutMs)
    : null;

  try {
    const response = await fetch(fullUrl, {
      ...defaultOptions,
      signal: controller?.signal,
    });
    
    if (!response.ok) {
      let errorBody: any = {};
      try {
        errorBody = await response.json();
      } catch {
        errorBody = {};
      }
      const err: any = new Error(errorBody.error || `HTTP error! status: ${response.status}`);
      err.response = { status: response.status, data: errorBody };
      throw err;
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    if (controller?.signal.aborted) {
      throw new Error('请求超时，DE 特征构建可能仍在进行，请稍后刷新重试');
    }
    console.error('API请求失败:', error);
    throw error;
  } finally {
    if (timer != null) {
      window.clearTimeout(timer);
    }
  }
}

// 文件上传函数
async function uploadFile(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  
  const fullUrl = `${API_BASE_URL}/api/upload`;
  
  try {
    const response = await fetch(fullUrl, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('文件上传失败:', error);
    throw error;
  }
}

export interface SystemMetricsPayload {
  timestamp: string;
  pid: number;
  process_cpu_percent?: number;
  process_memory_mb?: number;
  system_cpu_percent?: number;
  system_memory_percent?: number;
  system_memory_available_mb?: number;
  psutil?: boolean;
  note?: string;
  error?: string;
}

export interface TrainingEpochStats {
  success: boolean;
  log_file?: string;
  message?: string;
  error?: string;
  sample_count: number;
  avg_epoch_ms: number | null;
  median_epoch_ms: number | null;
  last_epoch_ms: number | null;
}

// API接口定义
export const api = {
  // 健康检查
  health: () =>
    request<{ status: string; timestamp?: string; service?: string }>('/api/health', {}, 4000),

  systemMetrics: () =>
    request<SystemMetricsPayload>('/api/system-metrics', { method: 'GET' }),

  trainingEpochStats: () =>
    request<TrainingEpochStats>('/api/training-epoch-stats', { method: 'GET' }),

  // 文件管理
  uploadFile: (file: File) => uploadFile(file),
  listFiles: () => request<{message: string; files: Array<{filename: string; size: number; modified: string}>}>('/api/files'),

  // 数据处理（缺 DE 特征时会从 Preprocessed_EEG 自动构建，耗时较长）
  dataPreprocessing: (filename: string, extra: Record<string, unknown> = {}) =>
    request<{
      message: string;
      filename: string;
      processing_steps: Array<{step: number; name: string; status: string}>;
      module?: string;
      module_available?: boolean;
      fallback_used?: boolean;
      metabci_unified?: boolean;
      de_built_from_raw?: boolean;
      de_build_info?: Record<string, unknown>;
      features: Record<string, any>;
      statistics: Record<string, any>;
      metabci?: Record<string, any>;
      acquisition_mode?: string;
      device_source?: string;
      live_probe?: Record<string, unknown>;
    }>(
      '/api/data-preprocessing',
      {
        method: 'POST',
        body: JSON.stringify({
          filename,
          feature_type: 'de_comp_4ch_1p5s',
          auto_build_from_raw: true,
          ...extra,
        }),
      },
      120_000,
    ),

  metabciBuildStatus: () =>
    request<{
      success: boolean;
      message: string;
      build_status: {
        state: 'idle' | 'running' | 'completed' | 'failed';
        message?: string;
        started_at?: string | null;
        finished_at?: string | null;
        error?: string | null;
      };
    }>('/api/metabci/brainda/build-status', {}, 4000),

  metabciStatus: () =>
    request<{
      module_available: boolean;
      modules: Record<string, boolean>;
      fallback_supported: boolean;
    }>('/api/metabci/status'),

  metabciSeedPreprocess: (payload: Record<string, any> = {}) =>
    request<Record<string, any>>('/api/metabci/brainda/seed-preprocess', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  metabciSeedDataset: (payload: Record<string, any> = {}) =>
    request<Record<string, any>>('/api/metabci/brainda/seed-dataset', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  metabciLoso: (payload: Record<string, any> = {}) =>
    request<Record<string, any>>('/api/metabci/brainda/loso', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  metabciEvaluate: (payload: Record<string, any> = {}) =>
    request<Record<string, any>>('/api/metabci/brainda/evaluate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  brainflowStart: (payload: Record<string, any> = {}) =>
    request<Record<string, any>>('/api/metabci/brainflow/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  brainflowStatus: (lite = true) =>
    request<Record<string, any>>(
      `/api/metabci/brainflow/status${lite ? '?lite=1' : ''}`,
      {},
      3000,
    ),

  brainflowStop: () =>
    request<Record<string, any>>('/api/metabci/brainflow/stop', {
      method: 'POST',
    }),

  brainflowDeviceSources: () =>
    request<Record<string, any>>('/api/metabci/brainflow/device-sources'),

  pipelineSessionGet: () =>
    request<Record<string, any>>('/api/pipeline/session', {}, 5000),

  pipelineSessionUpdate: (payload: Record<string, unknown> = {}) =>
    request<Record<string, any>>('/api/pipeline/session', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, 4000),

  pipelineDeviceCheck: (payload: Record<string, unknown> = {}) =>
    request<Record<string, any>>('/api/pipeline/device-check', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  pipelineLiveProbe: (payload: Record<string, unknown> = {}) =>
    request<Record<string, any>>('/api/pipeline/live-probe', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  brainstimParadigm: () =>
    request<Record<string, any>>('/api/metabci/brainstim/paradigm'),

  brainstimSimulate: (payload: { fast?: boolean } = {}) =>
    request<Record<string, any>>('/api/metabci/brainstim/simulate', {
      method: 'POST',
      body: JSON.stringify({ fast: payload.fast ?? true }),
    }),

  brainstimVerify: () =>
    request<Record<string, any>>('/api/metabci/brainstim/verify', {
      method: 'POST',
    }),
  
  // 特征学习
  featureLearning: (
    filename: string,
    model: string = 'CADD_DCCNN',
    featureType: string = 'de_comp_4ch_1p5s'
  ) => 
    request<{
      message: string;
      filename: string;
      learning_steps: Array<{step: number; name: string; status: string}>;
      model_info: Record<string, any>;
      performance: Record<string, number>;
      model_path?: string;
    }>('/api/feature-learning', {
      method: 'POST',
      body: JSON.stringify({ filename, model, feature_type: featureType }),
    }, 960000),

  featureLearningProgress: () =>
    request<{
      success: boolean;
      message: string;
      progress: {
        state: 'idle' | 'running' | 'completed' | 'failed';
        model?: string;
        epoch: number;
        total_epochs: number;
        accuracy: number;
        loss: number;
        percent: number;
        message: string;
        error?: string | null;
      };
    }>('/api/feature-learning/progress'),

  // 获取可用模型列表
  listModels: () =>
    request<{
      models: Array<{ value: string; label: string }>;
      checkpoints?: Record<string, {
        model?: string;
        model_path?: string;
        save_path?: string;
        max_acc?: number;
        feature_type?: string;
      }>;
      default_feature_type: string;
      dataset_path: string;
    }>('/api/models'),
  
  // 情绪识别
  emotionRecognition: (filename: string) => 
    request<{
      message: string;
      filename: string;
      module?: string;
      module_available?: boolean;
      fallback_used?: boolean;
      emotion_results: Record<string, number>;
      primary_emotion: string;
      confidence: number;
      stream_status?: Record<string, any>;
      timestamp: string;
    }>('/api/emotion-recognition', {
      method: 'POST',
      body: JSON.stringify({ filename }),
    }),
  
  // 生成拓扑图
  generateTopomaps: () => 
    request<{
      success: boolean;
      message: string;
      error?: string;
      topomaps?: string[];
    }>('/api/generate-topomaps', {
      method: 'POST',
    }),
  
  // 获取最新log数据
  getLatestLogData: (params?: { model?: string; model_path?: string; save_path?: string }) => {
    const query = new URLSearchParams();
    if (params?.model) query.set('model', params.model);
    if (params?.model_path) query.set('model_path', params.model_path);
    if (params?.save_path) query.set('save_path', params.save_path);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    return request<{
      success: boolean;
      data?: {
        max_accuracy: number;
        final_accuracy: number;
        best_checkpoint_accuracy?: number;
        epoch_count: number;
        training_duration: string;
        epochs: Array<{epoch: number; accuracy: number; loss?: number}>;
        start_time: string;
        end_time: string;
        model?: string;
        feature_type?: string;
        meta_max_acc?: number;
        save_path?: string;
        model_path?: string;
      };
      model?: string;
      feature_type?: string;
      error?: string;
      log_file?: string;
      timestamp?: string;
    }>(`/api/latest-log-data${suffix}`);
  },
  
  // 可视化
  visualization: (filename: string) => 
    request<{
      message: string;
      filename: string;
      visualization_data: {
        training_accuracy: number[];
        training_loss: number[];
        epochs: number[];
        statistics: Record<string, any>;
        tsne_data: Record<string, number[][]>;
      };
    }>('/api/visualization', {
      method: 'POST',
      body: JSON.stringify({ filename }),
    }),
  
  // 日志
  getLogs: () => request<{message: string; logs: string[]}>('/api/logs'),
};

// 错误处理
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// 响应拦截器
export function handleApiResponse<T>(response: T): T {
  // 这里可以添加通用的响应处理逻辑
  return response;
}

// 请求拦截器
export function handleApiRequest(url: string, options: RequestInit): [string, RequestInit] {
  // 这里可以添加通用的请求处理逻辑，比如添加认证头等
  return [url, options];
}

export default api;









