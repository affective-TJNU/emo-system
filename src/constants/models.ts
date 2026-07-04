/** Shared model definitions — keep in sync with backend/models/registry.py */

import caddTsne1 from '@/assets/module4/D3CC1.png';
import caddTsne2 from '@/assets/module4/D3CC2.png';
import ccaTsne1 from '@/assets/module4/CCA_RMPG1.png';
import ccaTsne2 from '@/assets/module4/CCA_RMPG2.png';
import dgcTsne1 from '@/assets/module4/DGConformer1.png';
import dgcTsne2 from '@/assets/module4/DGConformer2.png';
import eegTsne1 from '@/assets/module4/EEGMatch1.png';
import eegTsne2 from '@/assets/module4/EEGMatch2.png';
import atgrTsne1 from '@/assets/module4/tsne1.png';
import atgrTsne2 from '@/assets/module4/tsne2.png';

export type ModelOption = { label: string; value: string };

export type ModelFlowStep = { title: string; desc: string; icon: string };

export const DEFAULT_MODEL = 'CADD_DCCNN';

export const FALLBACK_MODEL_OPTIONS: ModelOption[] = [
  { label: 'CADD_DCCNN', value: 'CADD_DCCNN' },
  { label: 'CCA-RMPG', value: 'CCA_RMPG' },
  { label: 'DGConformer', value: 'DGConformer' },
  { label: 'EEGMatch', value: 'EEGMatch' },
  { label: 'ATGRNet', value: 'ATGRNet' },
];

/** CSS slug for model-select-* classes */
export const MODEL_SELECT_SLUG: Record<string, string> = {
  CADD_DCCNN: 'cadd',
  CCA_RMPG: 'cca_rmpg',
  DGConformer: 'dgconformer',
  EEGMatch: 'eegmatch',
  ATGRNet: 'atgrnet',
};

export const MODEL_FLOW_STEPS: Record<string, ModelFlowStep[]> = {
  CADD_DCCNN: [
    { title: 'DE特征', desc: '4导联差分熵输入', icon: 'fa-brain' },
    { title: '数据分段', desc: '1.5s非重叠窗分段', icon: 'fa-cut' },
    { title: '跨注意力', desc: 'CrissCross空间-频带注意力', icon: 'fa-th' },
    { title: '膨胀因果卷积', desc: 'DCCNN时序特征提取', icon: 'fa-wave-square' },
    { title: '域对齐分类', desc: '全局+局部域自适应', icon: 'fa-globe' },
  ],
  CCA_RMPG: [
    { title: 'DE特征', desc: '4导联差分熵输入', icon: 'fa-brain' },
    { title: '数据分段', desc: '1.5s非重叠窗分段', icon: 'fa-cut' },
    { title: 'CrissCross注意力', desc: '空间-频带交叉注意力', icon: 'fa-th' },
    { title: 'RMPG图卷积', desc: '多邻接图消息传递', icon: 'fa-project-diagram' },
    { title: '情绪分类', desc: '全连接层三分类输出', icon: 'fa-smile' },
  ],
  DGConformer: [
    { title: 'DE特征', desc: '4导联差分熵输入', icon: 'fa-brain' },
    { title: '数据分段', desc: '1.5s时序片段构建', icon: 'fa-cut' },
    { title: 'DGCNN空间编码', desc: 'KNN图卷积空间建模', icon: 'fa-globe' },
    { title: 'Conformer时序', desc: '多头自注意力+卷积', icon: 'fa-clock' },
    { title: 'CLS分类', desc: 'CLS token情绪识别', icon: 'fa-smile' },
  ],
  EEGMatch: [
    { title: 'DE特征', desc: '4导联差分熵输入', icon: 'fa-brain' },
    { title: '数据分段', desc: '时序片段构建', icon: 'fa-cut' },
    { title: '双分支特征', desc: 'f/g特征提取器', icon: 'fa-code-branch' },
    { title: '低秩原型对齐', desc: '跨被试原型匹配', icon: 'fa-project-diagram' },
    { title: '半监督对比', desc: 'SupCon情绪匹配', icon: 'fa-link' },
  ],
  ATGRNet: [
    { title: 'DE特征', desc: '4导联差分熵输入', icon: 'fa-brain' },
    { title: '数据分段', desc: '信号分段处理', icon: 'fa-cut' },
    { title: '频带特征学习', desc: '频段注意力机制', icon: 'fa-wave-square' },
    { title: '空间特征学习', desc: '图卷积空间建模', icon: 'fa-globe' },
    { title: '时序特征学习', desc: 'TCN时序推理', icon: 'fa-clock' },
  ],
};

export const MODEL_TSNE_IMAGES: Record<string, [string, string]> = {
  CADD_DCCNN: [caddTsne1, caddTsne2],
  CCA_RMPG: [ccaTsne1, ccaTsne2],
  DGConformer: [dgcTsne1, dgcTsne2],
  EEGMatch: [eegTsne1, eegTsne2],
  ATGRNet: [atgrTsne1, atgrTsne2],
};

export const MODEL_TSNE_TITLES: Record<string, [string, string]> = {
  CADD_DCCNN: ['CADD_DCCNN 特征 t-SNE', 'CADD_DCCNN 分类 t-SNE'],
  CCA_RMPG: ['CCA-RMPG 特征 t-SNE', 'CCA-RMPG 分类 t-SNE'],
  DGConformer: ['DGConformer 特征 t-SNE', 'DGConformer 分类 t-SNE'],
  EEGMatch: ['EEGMatch 特征 t-SNE', 'EEGMatch 分类 t-SNE'],
  ATGRNet: ['ATGRNet 特征 t-SNE', 'ATGRNet 分类 t-SNE'],
};

export function getModelTsneImages(model: string): [string, string] {
  return MODEL_TSNE_IMAGES[model] || MODEL_TSNE_IMAGES.ATGRNet;
}

export function getModelTsneTitles(model: string): [string, string] {
  return MODEL_TSNE_TITLES[model] || MODEL_TSNE_TITLES.ATGRNet;
}

export function modelOptionClass(value: string): string {
  return `model-option-${value.toLowerCase()}`;
}

/** 0.85 → 85，已是百分数则原样返回 */
export function normalizeAccuracyPercent(value: number | string | undefined | null): number {
  const num = Number(value);
  if (!Number.isFinite(num) || num < 0) return 0;
  return num <= 1 ? num * 100 : num;
}

/** 展示用短路径，如 seed/20260703_204214/model_best.pth */
export function formatCheckpointLabel(modelPath?: string): string {
  if (!modelPath) return '-';
  const normalized = modelPath.replace(/\\/g, '/');
  const seedIdx = normalized.indexOf('/seed/');
  if (seedIdx >= 0) {
    return normalized.slice(seedIdx + 1);
  }
  const parts = normalized.split('/');
  return parts.length >= 2 ? `${parts[parts.length - 2]}/${parts[parts.length - 1]}` : normalized;
}
