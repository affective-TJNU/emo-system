<template>
  <DashboardShell
    v-model:active-tab="activeStep"
    :is-fullscreen="isFullscreen"
    :footer-label="footerNextLabel"
    :footer-visible="activeStep === 0 || activeStep === 1"
    :show-right-panel="activeStep === 1"
    :acquisition-mode-label="datasetLabel"
    :acquisition-mode-type="isLiveMode ? 'self' : 'seed'"
    @fullscreen="toggleFullscreen"
    @export="handleExportReport"
    @settings="handleSettings"
    @perf="goPerformance"
    @footer-action="nextStep"
  >
    <template #left>
      <!-- 步骤0：brainstim 情绪实验范式 -->
      <BrainstimExperimentView
        v-if="activeStep === 0"
        :brainstim-paradigm="brainstimParadigmInfo"
        :active="activeStep === 0"
      />

      <!-- 步骤1：数据处理流水线 -->
      <DataPipelineView
        v-else-if="activeStep === 1"
        v-model:selected-feature="selectedFeature"
        :feature-options="dashboardFeatureOptions"
        :process-step="dataProcessStep"
        :loading="dataPreprocessLoading"
        :preprocessing-done="indexs.dataPreprocessing === 1"
        :acquisition-mode="acquisitionMode"
        :dataset-label="datasetLabel"
        :is-live-mode="isLiveMode"
        :live-probe="liveProbe"
        @start="dataPreprocess"
        @reset="resetDataPipeline"
        @batch="batchDataProcess"
      />

                    <!-- 步骤2：特征提取学习 -->
          <div v-else-if="activeStep === 2" class="dash-step-content scrollable">
            <h3 class="section-title">特征提取学习流程</h3>
            <p v-if="isLiveMode" class="workflow-hint live-mode-hint">
              <i class="fas fa-head-side-brain" />
              自采数据集模式：Step1 已完成原始数据→DE 特征提取；将加载预训练 checkpoint，跳过 SEED 离线训练。
            </p>
            <!-- 模型选择区域 -->
            <el-row class="model-selection-bar" type="flex" justify="start" align="middle" style="margin-bottom: 25px;">
              <div class="model-selection-container">
                <div class="model-label-wrapper">
                  <i class="fas fa-project-diagram model-icon"></i>
                  <span class="model-label">模型选择</span>
                  <div class="label-glow"></div>
                </div>
                <div class="model-select-wrapper">
                  <el-select 
                    v-model="selectedModel" 
                    placeholder="请选择模型"
                    class="model-select"
                    :class="modelSelectClass"
                    :data-selected="selectedModel"
                    popper-class="model-select-dropdown"
                  >
                    <el-option
                      v-for="item in modelOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                      :class="['model-option', `model-option-${item.value.toLowerCase()}`]"
                      :data-model="item.value"
                      :data-label="item.label"
                    />
                  </el-select>
                  <div class="select-glow"></div>
                  <div class="select-particles">
                    <div v-for="i in 6" :key="i" class="particle"></div>
                  </div>
                </div>
              </div>
            </el-row>
            
                         <!-- 特征提取学习流程图 -->
             <div class="feature-extraction-flow">
               <!-- 背景装饰元素 -->
               <div class="flow-bg-elements">
                 <div class="bg-circuit-lines"></div>
                 <div class="bg-data-stream"></div>
                 <div class="bg-hologram-grid"></div>
                 <div class="bg-energy-field"></div>
                 <div class="bg-quantum-particles">
                   <div v-for="i in 20" :key="i" class="quantum-particle"></div>
                 </div>
               </div>
               
               <div class="flow-header">
                 <div class="header-glow"></div>
                 <h4 class="flow-title">
                   <span class="title-text">{{ featureFlowStatusText }}</span>
                   <div class="title-scanner"></div>
                 </h4>
                 
                 <div class="header-stats">
                   <div class="stat-item">
                     <span class="stat-number">{{ featureFlowCurrentStepDisplay }}</span>
                     <span class="stat-label">当前步骤</span>
                   </div>
                   <div class="stat-item">
                     <span class="stat-number">{{ FEATURE_FLOW_TOTAL_STEPS }}</span>
                     <span class="stat-label">总步骤</span>
                   </div>
                   <div class="stat-item">
                     <span class="stat-number">{{ featureFlowProgressPercent }}%</span>
                     <span class="stat-label">完成度</span>
                   </div>
                 </div>
               </div>
               
               <div class="flow-container">
                 <template v-for="(step, index) in currentModelFlowSteps" :key="`${selectedModel}-flow-${index}`">
                   <div
                     class="flow-step"
                     :class="{ active: isFeatureStepActive(index), completed: isFeatureStepCompleted(index) }"
                   >
                     <div class="step-hologram"></div>
                     <div class="step-icon">
                       <div class="icon-core"></div>
                       <div class="icon-ring ring-1"></div>
                       <div class="icon-ring ring-2"></div>
                       <div class="icon-ring ring-3"></div>
                       <i :class="['fas', step.icon]"></i>
                     </div>
                     <div class="step-content">
                       <div class="step-title">{{ step.title }}</div>
                       <div class="step-desc">{{ step.desc }}</div>
                       <div class="step-progress">
                         <div class="progress-bar" :style="{ width: getFeatureStepProgress(index) }"></div>
                       </div>
                     </div>
                     <div class="step-glow"></div>
                     <div class="step-particles">
                       <div v-for="i in 8" :key="i" class="particle-dot"></div>
                     </div>
                     <div class="step-energy-beams">
                       <div v-for="i in 12" :key="i" class="energy-beam"></div>
                     </div>
                   </div>

                   <div
                     v-if="index < currentModelFlowSteps.length - 1"
                     class="flow-connector"
                     :class="{ active: isFeatureStepCompleted(index) }"
                   >
                     <div class="connector-core"></div>
                     <div class="connector-line"></div>
                     <div class="connector-pulse"></div>
                     <div class="connector-data-stream">
                       <div v-for="i in 5" :key="i" class="data-bit"></div>
                     </div>
                   </div>
                 </template>
               </div>
               

             </div>
            
            <!-- 主流程控制 -->
            <div class="main-flow-controls">
              <el-button @click="prevStep" class="action-button">
                <i class="fas fa-arrow-left"></i>
                上一步
              </el-button>
              <el-button @click="startFeatureFlow" class="action-button" :loading="featureFlowLoading">
                <i class="fas fa-play"></i>
                开始特征学习
              </el-button>
              <el-button @click="nextStep" class="action-button">
                下一步
                <i class="fas fa-arrow-right"></i>
              </el-button>
            </div>
          </div>

          <!-- 步骤3：情绪识别 -->
          <div v-else-if="activeStep === 3" class="dash-step-content scrollable">
            <h3 class="section-title">情绪识别</h3>
            
            <div class="emotion-recognition-container">
                             <div class="emotion-card positive" :class="{ 'active': emotionResult === 'positive' }">
                 <!-- 背景流动效果 -->
                 <div class="emotion-bg-flow">
                   <div class="flow-particle" v-for="i in 12" :key="i"></div>
                </div>
                 
                 <div class="emotion-icon">
                   <div class="icon-core"></div>
                   <div class="icon-ring ring-1"></div>
                   <div class="icon-ring ring-2"></div>
                   <div class="icon-ring ring-3"></div>
                   <div class="face-expression">
                     <div class="eyes">
                       <div class="eye left-eye happy-eye"></div>
                       <div class="eye right-eye happy-eye"></div>
                        </div>
                     <div class="mouth happy-mouth"></div>
                      </div>
                </div>
                 
                 <div class="emotion-content">
                   <h4 class="emotion-title">
                     正性情绪
                   </h4>
                   <p class="emotion-desc">Positive Emotion</p>
                   <div class="emotion-progress">
                     <div class="progress-container">
                       <div class="progress-bar" :style="{ width: emotionPercentages.positive + '%' }">
                         <div class="progress-glow"></div>
                       </div>
                     </div>
                   </div>
                   <div class="emotion-percentage">
                     {{ emotionPercentages.positive }}%
                   </div>
                 </div>
                 
                 <div class="emotion-glow"></div>
                 <div class="emotion-energy-beams">
                   <div v-for="i in 8" :key="i" class="energy-beam"></div>
                 </div>
               </div>

               <div class="emotion-card neutral" :class="{ 'active': emotionResult === 'neutral' }">
                 <!-- 背景流动效果 -->
                 <div class="emotion-bg-flow">
                   <div class="flow-particle" v-for="i in 12" :key="i"></div>
                 </div>
                 
                 <div class="emotion-icon">
                   <div class="icon-core"></div>
                   <div class="icon-ring ring-1"></div>
                   <div class="icon-ring ring-2"></div>
                   <div class="icon-ring ring-3"></div>
                   <div class="face-expression">
                     <div class="eyes">
                       <div class="eye left-eye"></div>
                       <div class="eye right-eye"></div>
                     </div>
                     <div class="mouth neutral-mouth"></div>
                   </div>
                 </div>
                 
                 <div class="emotion-content">
                   <h4 class="emotion-title">
                     中性情绪
                   </h4>
                   <p class="emotion-desc">Neutral Emotion</p>
                   <div class="emotion-progress">
                     <div class="progress-container">
                       <div class="progress-bar" :style="{ width: emotionPercentages.neutral + '%' }">
                         <div class="progress-glow"></div>
                       </div>
                     </div>
                   </div>
                   <div class="emotion-percentage">
                     {{ emotionPercentages.neutral }}%
                   </div>
                 </div>
                 
                 <div class="emotion-glow"></div>
                 <div class="emotion-energy-beams">
                   <div v-for="i in 8" :key="i" class="energy-beam"></div>
                 </div>
               </div>

               <div class="emotion-card negative" :class="{ 'active': emotionResult === 'negative' }">
                 <!-- 背景流动效果 -->
                 <div class="emotion-bg-flow">
                   <div class="flow-particle" v-for="i in 12" :key="i"></div>
                 </div>
                 
                 <div class="emotion-icon">
                   <div class="icon-core"></div>
                   <div class="icon-ring ring-1"></div>
                   <div class="icon-ring ring-2"></div>
                   <div class="icon-ring ring-3"></div>
                   <div class="face-expression">
                     <div class="eyes">
                       <div class="eye left-eye crying-eye"></div>
                       <div class="eye right-eye crying-eye"></div>
                     </div>
                     <div class="mouth crying-mouth"></div>
                   </div>
                 </div>
                 
                 <div class="emotion-content">
                   <h4 class="emotion-title">
                     负性情绪
                   </h4>
                   <p class="emotion-desc">Negative Emotion</p>
                   <div class="emotion-progress">
                     <div class="progress-container">
                       <div class="progress-bar" :style="{ width: emotionPercentages.negative + '%' }">
                         <div class="progress-glow"></div>
                       </div>
                     </div>
                   </div>
                   <div class="emotion-percentage">
                     {{ emotionPercentages.negative }}%
                   </div>
                 </div>
                 
                 <div class="emotion-glow"></div>
                 <div class="emotion-energy-beams">
                   <div v-for="i in 8" :key="i" class="energy-beam"></div>
                 </div>
               </div>
            </div>
            <el-row class="buttons-bar" type="flex" justify="space-between" align="middle">
              <el-button @click="prevStep" class="action-button">
                <i class="fas fa-arrow-left"></i>
                上一步
              </el-button>
              <el-button
                @click="modelSelection"
                class="action-button"
                :loading="modelSelectionLoading"
                :disabled="!featureLearningCompleted || featureFlowLoading"
              >
                <i class="fas fa-brain"></i>
                {{ featureFlowLoading ? '特征学习中' : '开始情绪识别' }}
              </el-button>
              <el-button @click="nextStep" class="action-button">
                下一步
                <i class="fas fa-arrow-right"></i>
              </el-button>
            </el-row>
            <div v-if="!featureLearningCompleted" class="workflow-hint">
              请先在“特征提取学习”步骤完成 {{ selectedModel }} 训练{{ isLiveMode ? '（或加载 checkpoint）' : '' }}，再启动 brainflow 在线情绪识别。
            </div>
            <div v-if="brainflowPredictionInfo" class="brainflow-status-panel">
              <div class="brainflow-status-item">
                <span>采集模式</span>
                <strong>{{ currentModeLabel }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>MetaBCI模块</span>
                <strong>{{ brainflowPredictionInfo.module || 'brainflow' }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>在线流状态</span>
                <strong>{{ brainflowPredictionInfo.stream_status?.running ? '运行中' : '已停止' }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>数据源</span>
                <strong>{{ brainflowPredictionInfo.stream_status?.source || 'SEED片段回放' }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>设备接入</span>
                <strong>{{
                  brainflowPredictionInfo.stream_status?.device_source
                    || brainflowPredictionInfo.stream_status?.latest_prediction?.device_source
                    || 'seed_replay'
                }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>{{ isLiveMode ? 'Neuroscan 通道' : 'SEED 通道' }}</span>
                <strong>{{
                  isLiveMode
                    ? (brainflowPredictionInfo.stream_status?.latest_prediction?.device_channel_count
                        ? `${brainflowPredictionInfo.stream_status.latest_prediction.device_channel_count} 导 → 4 导`
                        : '40 导 → 4 导')
                    : '4 导 (AF3/AF4/F3/F4)'
                }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>关键导联</span>
                <strong>{{
                  (brainflowPredictionInfo.stream_status?.latest_prediction?.device_key_channels || []).join(', ')
                    || 'AF3, AF4, F3, F4'
                }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>回放范围</span>
                <strong>{{
                  isLiveMode
                    ? (brainflowPredictionInfo.stream_status?.latest_prediction?.replay_scope || 'Neuroscan LSL 实时')
                    : (brainflowPredictionInfo.stream_status?.replay_meta?.replay_scope || '全部15被试')
                }}</strong>
              </div>
              <div v-if="!isLiveMode" class="brainflow-status-item">
                <span>特征类型</span>
                <strong>de_comp_4ch_1p5s</strong>
              </div>
              <div v-if="!isLiveMode" class="brainflow-status-item">
                <span>当前被试</span>
                <strong>S{{ brainflowPredictionInfo.stream_status?.latest_prediction?.subject_id ?? '-' }}</strong>
              </div>
              <div v-if="!isLiveMode" class="brainflow-status-item">
                <span>Session / Trial</span>
                <strong>
                  {{ brainflowPredictionInfo.stream_status?.latest_prediction?.session_id ?? '-' }}
                  /
                  {{ brainflowPredictionInfo.stream_status?.latest_prediction?.trial_id ?? '-' }}
                </strong>
              </div>
              <div class="brainflow-status-item">
                <span>样本序号</span>
                <strong>#{{ brainflowPredictionInfo.stream_status?.latest_prediction?.sample_index ?? '-' }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>输入形状</span>
                <strong>{{ (brainflowPredictionInfo.stream_status?.latest_prediction?.segment_shape || []).join(' x ') || '-' }}</strong>
              </div>
              <div class="brainflow-status-item">
                <span>模式</span>
                <strong>{{
                  brainflowPredictionInfo.stream_status?.latest_prediction?.inference_mode
                    || (brainflowPredictionInfo.stream_status?.model_loaded ? selectedModel : '回放兜底')
                }}</strong>
              </div>
              <div v-if="brainflowPredictionInfo.stream_status?.model_path" class="brainflow-status-item">
                <span>模型</span>
                <strong class="brainflow-model-path">{{ brainflowPredictionInfo.stream_status.model_path }}</strong>
              </div>
            </div>
          </div>

          <!-- 步骤4：结果可视化 -->
          <div v-else-if="activeStep === 4" class="dash-step-content visualization-wrapper">
            <!-- 粒子背景 -->
            <div class="particle-background">
              <div class="particle" v-for="i in 50" :key="i"></div>
            </div>
            
            <!-- 数据流特效 -->
            <div class="data-stream-container">
              <div class="data-stream" v-for="i in 8" :key="i"></div>
            </div>
            
            <!-- 扫描线特效 -->
            <div class="scan-line"></div>
            
            <h3 class="section-title cyberpunk-title">
              <span class="title-glow">可视化展示</span>
              <div class="title-underline"></div>
            </h3>
            <div v-if="visualizationHint" class="workflow-hint visualization-hint">
              {{ visualizationHint }}
            </div>

            <div class="viz-model-bar">
              <span class="viz-model-label"><i class="fas fa-project-diagram" /> 可视化模型</span>
              <el-select
                v-model="visualizationSelectedModel"
                class="viz-model-select"
                placeholder="选择模型"
                @change="onVisualizationModelChange"
              >
                <el-option
                  v-for="item in modelOptions"
                  :key="item"
                  :label="item"
                  :value="item"
                />
              </el-select>
              <span v-if="visualizationGenerated" class="viz-model-log-tag">
                日志：{{ visualizationModelName }}
              </span>
            </div>
            
            <!-- 模型训练过程监控 -->
            <div class="training-monitor-section">
              <h4 class="section-subtitle">
                <i class="fas fa-chart-line"></i>
                模型训练过程监控
              </h4>
              

              
              <!-- 训练统计卡片 -->
              <div class="training-stats-container cyberpunk-stats">
                <div class="stats-glow-effect"></div>
                <div class="stat-card overall">
                  <h3>最高准确率</h3>
                  <div class="stat-value">{{ (maxAccuracy || 0).toFixed(2) }}%</div>
                  
                </div>
                
                <div class="stat-card best">
                  <h3>最终准确率</h3>
                  <div class="stat-value">{{ (finalAccuracy || 0).toFixed(2) }}%</div>
                 
                </div>
                
                <div class="stat-card epoch">
                  <h3>EPOCH数</h3>
                  <div class="stat-value">{{ epochCount }}</div>
                 
                </div>
                
                <div class="stat-card model">
                  <h3>模型名称</h3>
                  <div class="stat-value">{{ visualizationGenerated ? visualizationModelName : visualizationSelectedModel }}</div>
                  
                </div>
              </div>
              

            </div>

            <div v-show="!visualizationGenerated" class="visualization-empty-state">
              <i class="fas fa-chart-pie"></i>
              <p>请点击下方「生成可视化分析」，加载训练过程分析与 t-SNE 特征空间可视化</p>
            </div>

            <!-- 训练过程分析模块 -->
            <div v-show="visualizationGenerated" class="training-analysis-container cyberpunk-analysis">
              <div class="analysis-glow-border"></div>
              <div class="analysis-corner-decor top-left"></div>
              <div class="analysis-corner-decor top-right"></div>
              <div class="analysis-corner-decor bottom-left"></div>
              <div class="analysis-corner-decor bottom-right"></div>
              <div class="analysis-header">
                <h4 class="analysis-title">
                  <i class="fas fa-chart-area"></i>
                  训练过程分析
                </h4>
                <div class="analysis-actions">
                  <button @click="switchAnalysisType('accuracy')" 
                          :class="{ 'active': analysisType === 'accuracy' }" class="analysis-btn">
                    <i class="fas fa-chart-line"></i> 准确率
                  </button>
                  <button @click="switchAnalysisType('loss')" 
                          :class="{ 'active': analysisType === 'loss' }" class="analysis-btn">
                    <i class="fas fa-chart-bar"></i> 损失值
                  </button>
                </div>
              </div>
              
              <div class="analysis-content" v-loading="analysisLoading">
                <div class="analysis-chart-wrapper">
                  <div class="analysis-chart">
                    <div class="analysis-chart-host">
                      <canvas
                        ref="analysisChartCanvas"
                        @mousemove="handleAnalysisChartMouseMove"
                        @mouseleave="handleAnalysisChartMouseLeave"
                      ></canvas>
                      <div
                        v-show="chartTooltip.visible"
                        class="analysis-chart-tooltip"
                        :style="{ left: `${chartTooltip.x}px`, top: `${chartTooltip.y}px` }"
                      >
                        {{ chartTooltip.text }}
                      </div>
                    </div>
                  </div>
                </div>
                <p v-if="chartRenderError" class="analysis-chart-error">{{ chartRenderError }}</p>
              </div>
            </div>

            <!-- t-SNE降维可视化（静态图，进入本步骤即展示） -->
            <div class="tsne-visualization-section cyberpunk-tsne">
              <div class="tsne-glow-border"></div>
              <div class="tsne-corner-decor top-left"></div>
              <div class="tsne-corner-decor top-right"></div>
              <div class="tsne-corner-decor bottom-left"></div>
              <div class="tsne-corner-decor bottom-right"></div>
              <h4 class="section-subtitle">
                <i class="fas fa-project-diagram"></i>
                t-SNE特征空间可视化
              </h4>
              <div class="tsne-container" v-loading="tsneLoading">
                <div class="tsne-images-container">
                  <!-- 左侧图片 -->
                  <div class="tsne-image-wrapper left-image">
                    <div class="tsne-image-title">{{ tsneImageTitles[0] }}</div>
                    <el-image
                      :src="tsneImages[0]"
                      fit="contain"
                      style="width: 100%; height: 100%; object-fit: contain;"
                      @error="handleTsneImageError"
                    />
                  </div>
                  
                  <!-- 右侧图片 -->
                  <div class="tsne-image-wrapper right-image">
                    <div class="tsne-image-title">{{ tsneImageTitles[1] }}</div>
                    <el-image
                      :src="tsneImages[1]"
                      fit="contain"
                      style="width: 100%; height: 100%; object-fit: contain;"
                      @error="handleTsneImageError"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 控制按钮 -->
            <el-row class="buttons-bar" type="flex" justify="space-between" align="middle">
              <el-button @click="prevStep" class="action-button">
                <i class="fas fa-arrow-left"></i>
                上一步
              </el-button>
              <el-button @click="startVisualization" class="action-button">
                <i class="fas fa-chart-pie"></i>
                生成可视化分析
              </el-button>

            </el-row>
          </div>
    </template>

    <template #right>
      <EegPreviewPanel
        :loading="dataPreprocessLoading && activeStep === 1"
        :ready="indexs.dataPreprocessing === 1 || activeStep > 1"
        :images="imageCarousel"
        :current-image-index="currentImageIndex"
        @select-image="(i: number) => (currentImageIndex = i)"
      />
    </template>
  </DashboardShell>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { api } from "@/api/index";
import DashboardShell from '@/components/dashboard/DashboardShell.vue';
import DataPipelineView from '@/components/dashboard/DataPipelineView.vue';
import BrainstimExperimentView from '@/components/dashboard/BrainstimExperimentView.vue';
import EegPreviewPanel from '@/components/dashboard/EegPreviewPanel.vue';
import { usePipelineSession } from '@/composables/usePipelineSession';
import {
  DEFAULT_MODEL,
  FALLBACK_MODEL_OPTIONS,
  MODEL_FLOW_STEPS,
  MODEL_SELECT_SLUG,
  modelOptionClass,
  normalizeAccuracyPercent,
  formatCheckpointLabel,
  getModelTsneImages,
  getModelTsneTitles,
} from "@/constants/models";

const router = useRouter();
const goPerformance = () => router.push("/perf");

const {
  acquisitionMode,
  deviceSource,
  liveProbe,
  isLiveMode,
  currentModeLabel,
  datasetLabel,
  loadSession,
  resetSession,
} = usePipelineSession();

const dashboardFeatureOptions = [
  { label: 'DE / 差分熵', value: 'DE' },
  { label: '功率谱 PSD', value: 'PSD' },
  { label: 'DASM 不对称特征', value: 'DASM' },
  { label: 'RASM 相对不对称', value: 'RASM' },
  { label: 'DCAU 相关特征', value: 'DCAU' },
  { label: '时域波形', value: 'TIME' },
];


const resetDataPipeline = () => {
  dataProcessStep.value = 0;
  indexs.value.dataPreprocessing = 0;
  dataPreprocessLoading.value = false;
  ElMessage.info('数据处理流程已重置');
};

const batchDataProcess = async () => {
  ElMessage.info('开始一键批量处理...');
  await dataPreprocess();
};

const handleExportReport = () => {
  ElMessage.success('报告导出功能即将开放');
};

const handleSettings = () => {
  ElMessage.info('系统设置面板即将开放');
};

interface FileItem {
  name: string;
}
import DEImage from '@/assets/DE.png';

const preprocessingIndex = ref("1");
const modelSelectionIndex = ref("1");
const isFullscreen = ref(false);
const dataProcessStep = ref(0);
const featureFlowStep = ref(0);
const featureWaitingBackend = ref(false);
const featureBackendFinished = ref(false);
const backendTrainingPercent = ref(0);
const backendTrainingEpoch = ref(0);
const backendTrainingTotalEpochs = ref(0);
const FEATURE_FLOW_TOTAL_STEPS = 5;
const FEATURE_PRE_TRAIN_MAX = 12;
const FEATURE_TRAIN_SPAN = 83;
const featureFlowTimers = ref<Array<ReturnType<typeof setTimeout>>>([]);
let featureProgressPollTimer: ReturnType<typeof setInterval> | null = null;

const stopFeatureProgressPoll = () => {
  if (featureProgressPollTimer) {
    clearInterval(featureProgressPollTimer);
    featureProgressPollTimer = null;
  }
};

const syncFeatureFlowStepFromTraining = (trainingPct: number) => {
  if (!featureWaitingBackend.value) return;
  if (trainingPct >= 66 && featureFlowStep.value < 4) {
    featureFlowStep.value = 4;
  } else if (trainingPct >= 33 && featureFlowStep.value < 3) {
    featureFlowStep.value = 3;
  }
};

const pollFeatureTrainingProgress = async () => {
  if (!featureFlowLoading.value || !featureWaitingBackend.value) return;
  try {
    const resp = await api.featureLearningProgress();
    const progress = resp.progress;
    if (!progress) return;

    backendTrainingEpoch.value = Math.max(0, progress.epoch + 1);
    backendTrainingTotalEpochs.value = progress.total_epochs || backendTrainingTotalEpochs.value;

    if (progress.total_epochs > 0 && progress.epoch >= 0) {
      backendTrainingPercent.value = Math.round(
        ((progress.epoch + 1) / progress.total_epochs) * 100,
      );
    } else if (progress.percent > 0) {
      backendTrainingPercent.value = Math.min(100, progress.percent);
    }

    syncFeatureFlowStepFromTraining(backendTrainingPercent.value);
  } catch (error) {
    console.warn('特征学习进度轮询失败:', error);
  }
};

const startFeatureProgressPoll = () => {
  stopFeatureProgressPoll();
  void pollFeatureTrainingProgress();
  featureProgressPollTimer = setInterval(() => {
    void pollFeatureTrainingProgress();
  }, 500);
};

const getStepProgressDuringTraining = (stepIndex: number, trainingPct: number) => {
  if (stepIndex < 2) return 100;
  const segmentSize = 100 / 3;
  const segmentStart = (stepIndex - 2) * segmentSize;
  const segmentEnd = segmentStart + segmentSize;
  if (trainingPct >= segmentEnd) return 100;
  if (trainingPct <= segmentStart) return 0;
  return Math.round(((trainingPct - segmentStart) / segmentSize) * 100);
};

const clearFeatureFlowTimers = () => {
  featureFlowTimers.value.forEach(clearTimeout);
  featureFlowTimers.value = [];
};

const sleep = (ms: number) => new Promise<void>((resolve) => {
  const timer = setTimeout(resolve, ms);
  featureFlowTimers.value.push(timer);
});

const resetFeatureFlowUI = () => {
  clearFeatureFlowTimers();
  stopFeatureProgressPoll();
  featureFlowStep.value = 0;
  featureFlowLoading.value = false;
  featureWaitingBackend.value = false;
  featureBackendFinished.value = false;
  backendTrainingPercent.value = 0;
  backendTrainingEpoch.value = 0;
  backendTrainingTotalEpochs.value = 0;
};

const getPreTrainProgressPercent = (step: number) =>
  Math.round(((Math.min(step, 2) + 1) / 3) * FEATURE_PRE_TRAIN_MAX);

const featureFlowProgressPercent = computed(() => {
  if (featureLearningCompleted.value) return 100;
  if (!featureFlowLoading.value) return 0;
  if (featureBackendFinished.value) {
    const finishIdx = Math.max(0, Math.min(2, featureFlowStep.value - 2));
    return Math.min(100, 95 + Math.round((finishIdx / 2) * 5));
  }
  if (featureWaitingBackend.value) {
    const preTrain = getPreTrainProgressPercent(featureFlowStep.value);
    const trainPart = Math.round((backendTrainingPercent.value / 100) * FEATURE_TRAIN_SPAN);
    return Math.min(95, preTrain + trainPart);
  }
  return Math.round(((featureFlowStep.value + 1) / FEATURE_FLOW_TOTAL_STEPS) * FEATURE_PRE_TRAIN_MAX);
});

const featureFlowStatusText = computed(() => {
  if (featureWaitingBackend.value && backendTrainingTotalEpochs.value > 0) {
    return `${selectedModel.value} 模型训练中 Epoch ${backendTrainingEpoch.value}/${backendTrainingTotalEpochs.value}`;
  }
  return `${selectedModel.value}模型分析脑电信号`;
});

const featureFlowCurrentStepDisplay = computed(() => {
  if (featureLearningCompleted.value) return FEATURE_FLOW_TOTAL_STEPS;
  if (!featureFlowLoading.value) return 0;
  return Math.min(featureFlowStep.value + 1, FEATURE_FLOW_TOTAL_STEPS);
});

const getFeatureStepProgress = (stepIndex: number) => {
  if (featureLearningCompleted.value || featureFlowStep.value > stepIndex) return '100%';
  if (featureWaitingBackend.value) {
    if (stepIndex < 2) return '100%';
    const pct = getStepProgressDuringTraining(stepIndex, backendTrainingPercent.value);
    return `${pct}%`;
  }
  if (featureBackendFinished.value) {
    if (stepIndex < 3) return '100%';
    if (featureFlowStep.value === stepIndex) return '75%';
    return '0%';
  }
  if (featureFlowLoading.value && featureFlowStep.value === stepIndex) {
    return '60%';
  }
  return '0%';
};

const isFeatureStepCompleted = (stepIndex: number) => {
  if (featureLearningCompleted.value) return true;
  return featureFlowStep.value > stepIndex;
};

const isFeatureStepActive = (stepIndex: number) => {
  if (featureLearningCompleted.value || !featureFlowLoading.value) return false;
  return featureFlowStep.value === stepIndex;
};
const navPanelVisible = ref(true); // 新增：导航面板可见性
const selectedFeature = ref("DE"); // 特征选择：DE、PSD、DASM、RASM、DCAU
const featureOptions = [
  { label: "DE", value: "DE" },
  { label: "PSD", value: "PSD" },
  { label: "DASM", value: "DASM" },
  { label: "RASM", value: "RASM" },
  { label: "DCAU", value: "DCAU" }
];

const selectedModel = ref(DEFAULT_MODEL);
const modelOptions = ref([...FALLBACK_MODEL_OPTIONS]);
const modelCheckpoints = ref<Record<string, Record<string, unknown>>>({});
const visualizationSelectedModel = ref(DEFAULT_MODEL);
let visualizationRequestSeq = 0;

const currentModelFlowSteps = computed(() => {
  return MODEL_FLOW_STEPS[selectedModel.value] || MODEL_FLOW_STEPS.ATGRNet;
});

const modelSelectClass = computed(() => {
  const slug = MODEL_SELECT_SLUG[selectedModel.value];
  return {
    ...(slug ? { [`model-select-${slug}`]: true } : {}),
    "model-selected": Boolean(selectedModel.value),
  };
});

async function loadModelOptions() {
  try {
    const resp = await api.listModels();
    if (resp.models?.length) modelOptions.value = resp.models;
    if (resp.checkpoints) modelCheckpoints.value = resp.checkpoints;
  } catch (err) {
    console.warn('加载模型列表失败', err);
  }
}

function resolveVisualizationLogQuery(modelName?: string) {
  const target = modelName || visualizationSelectedModel.value || selectedModel.value;
  const ckpt = modelCheckpoints.value[target] as Record<string, string> | undefined;
  const query: { model: string; model_path?: string; save_path?: string } = { model: target };

  if (trainedModelPath.value && isSameModel(visualizationModelName.value, target)) {
    query.model_path = trainedModelPath.value;
  } else if (ckpt?.save_path) {
    query.save_path = ckpt.save_path;
  } else if (ckpt?.model_path) {
    query.model_path = ckpt.model_path;
  }
  return query;
}

function normalizeModelLabel(name: string) {
  return String(name || '').trim();
}

function isSameModel(a: string, b: string) {
  return normalizeModelLabel(a).toLowerCase() === normalizeModelLabel(b).toLowerCase();
}

async function applyVisualizationFromLog(
  logData: Record<string, any>,
  modelLabel: string,
  targetModel: string,
) {
  if (!isSameModel(modelLabel, targetModel)) {
    console.warn('日志模型与请求模型不一致', modelLabel, targetModel);
    return false;
  }

  visualizationModelName.value = modelLabel;
  visualizationSelectedModel.value = targetModel;
  const epochsRaw = Array.isArray(logData.epochs) ? logData.epochs : [];
  if (epochsRaw.length === 0) {
    return false;
  }

  trainingEpochs.value = epochsRaw.map((e: any) => Number(e.epoch) + 1);
  trainingAccuracies.value = epochsRaw.map((e: any) => Number(e.accuracy || 0));
  trainingLosses.value = epochsRaw.map((e: any) => Number(e.loss ?? 0));

  maxAccuracy.value = Number(logData.max_accuracy) || 0;
  finalAccuracy.value = Number(logData.final_accuracy) || 0;
  avgAccuracy.value = Math.round(
    (trainingAccuracies.value.reduce((a, b) => a + b, 0) / trainingAccuracies.value.length) * 100,
  ) / 100;
  epochCount.value = epochsRaw.length;
  trainingDuration.value = logData.training_duration || trainingDuration.value || '';

  visualizationGenerated.value = true;
  analysisShow.value = true;

  clearAnalysisChartHover();
  (window as any).currentSessions = buildSessionsFromTrainingData();
  await enqueueAnalysisChartRender(buildSessionsFromTrainingData());
  await nextTick();
  if (analysisChartCanvas.value) {
    createAnalysisChart(buildSessionsFromTrainingData());
  }
  return true;
}



const updateLoading = ref(false);
const dataPreprocessLoading = ref(false);

const DEVICE_NOT_CONNECTED_HINT = `请确认：
1. Neuroscan 电极帽已佩戴并开启采集
2. LSL 数据流已发布（默认流名称：Neuroscan）
3. 已完成 Step0 实验范式采集
完成后再点击「启动数据流水线处理」。`;

async function refreshLiveDeviceStatus() {
  if (!isLiveMode.value) return;
  try {
    const status = await api.pipelineDeviceCheck();
    liveProbe.value = {
      ...(status.probe || {}),
      connected: status.device_connected,
      device_connected: status.device_connected,
      connect_message: status.connect_message,
      stream_name: status.stream_name,
    };
  } catch (error) {
    console.warn('设备连接检测失败:', error);
    liveProbe.value = {
      connected: false,
      device_connected: false,
      connect_message: '设备检测失败，请确认后端服务已启动',
    };
  }
}

async function showDeviceNotConnectedDialog(detail?: string) {
  await ElMessageBox.alert(detail || DEVICE_NOT_CONNECTED_HINT, '未连接 Neuroscan 设备', {
    type: 'warning',
    confirmButtonText: '我知道了',
  });
}
const featureFlowLoading = ref(false); // 新增：特征流程loading

// 情绪识别相关变量
const emotionResult = ref(''); // 当前识别的情绪结果
const emotionPercentages = ref({
  positive: 0,
  neutral: 0,
  negative: 0
});



const modelSelectionLoading = ref(false);
const resultLoading1 = ref(false);
const resultLoading2 = ref(false);
const resultLoading3 = ref(false);
const resultLoading4 = ref(false);

// 可视化相关变量
const trainingAccuracyLoading = ref(false);
const trainingAccuracyShow = ref(false);
const trainingLossLoading = ref(false);
const trainingLossShow = ref(false);

const tsneLoading = ref(false);
const visualizationGenerated = ref(false);

// 训练数据
const accuracyData = ref([65, 72, 78, 82, 85, 88, 91, 93, 94, 95]);
const lossData = ref([0.8, 0.6, 0.45, 0.35, 0.28, 0.22, 0.18, 0.15, 0.12, 0.1]);



// t-SNE数据
const tsneData = ref({
  positive: [
    { id: 1, x: 20, y: 30 }, { id: 2, x: 25, y: 35 }, { id: 3, x: 30, y: 25 },
    { id: 4, x: 35, y: 40 }, { id: 5, x: 40, y: 30 }, { id: 6, x: 45, y: 35 }
  ],
  neutral: [
    { id: 7, x: 60, y: 50 }, { id: 8, x: 65, y: 55 }, { id: 9, x: 70, y: 45 },
    { id: 10, x: 75, y: 60 }, { id: 11, x: 80, y: 50 }, { id: 12, x: 85, y: 55 }
  ],
  negative: [
    { id: 13, x: 20, y: 70 }, { id: 14, x: 25, y: 75 }, { id: 15, x: 30, y: 65 },
    { id: 16, x: 35, y: 80 }, { id: 17, x: 40, y: 70 }, { id: 18, x: 45, y: 75 }
  ]
});

// 训练分析相关变量
const maxAccuracy = ref(0);
const finalAccuracy = ref(0);
const avgAccuracy = ref(0);
const trainingDuration = ref('');
const epochCount = ref(30);
const configShow = ref(false);
const modelConfig = ref<Record<string, string>>({});

// 定义类型接口
interface EpochData {
  epoch: number;
  accuracy: number;
  loss: number;
  time?: string;
}

interface SessionData {
  subject: string;
  session: string;
  epochs: EpochData[];
  startTime: string;
  endTime?: string;
  finalAccuracy?: number;
}

interface ConfigParams {
  [key: string]: string;
}

interface ParsedData {
  sessions: SessionData[];
  configParams: ConfigParams;
}

// 获取最新log数据的函数
const loadLatestLogData = async () => {
  try {
    console.log('开始获取最新log数据...');
    const result = await api.getLatestLogData(resolveVisualizationLogQuery());
    
    if (result.success && result.data) {
      console.log('获取到最新log数据:', result.data);
      
      // 更新统计数据
      maxAccuracy.value = Number(result.data.max_accuracy) || 0;
      finalAccuracy.value = Number(result.data.final_accuracy) || 0;
      epochCount.value = Number(result.data.epoch_count) || 0;
      trainingDuration.value = result.data.training_duration || '';
      
      console.log('更新后的数据:', {
        maxAccuracy: maxAccuracy.value,
        finalAccuracy: finalAccuracy.value,
        epochCount: epochCount.value,
        trainingDuration: trainingDuration.value
      });
      
      // 更新训练数据
      if (result.data.epochs && result.data.epochs.length > 0) {
        trainingEpochs.value = result.data.epochs.map(e => Number(e.epoch) + 1);
        trainingAccuracies.value = result.data.epochs.map(e => Number(e.accuracy || 0));
        trainingLosses.value = result.data.epochs.map(e => Number(e.loss || 0));
        
        // 计算平均准确率
        const accuracies = result.data.epochs.map(e => e.accuracy);
        avgAccuracy.value = Math.round((accuracies.reduce((a, b) => a + b, 0) / accuracies.length) * 100) / 100;
      }
      
      console.log('log数据更新完成');
    } else {
      console.warn('获取log数据失败:', result.error);
    }
  } catch (error) {
    console.error('获取最新log数据失败:', error);
  }
};

// 训练数据
const trainingEpochs = ref<number[]>([]);
const trainingAccuracies = ref<number[]>([]);
const trainingLosses = ref<number[]>([]);

// 训练过程分析相关变量
const analysisType = ref('accuracy');
const analysisLoading = ref(false);
const analysisShow = ref(false);
const chartRenderError = ref('');
const chartRenderRetries = ref(0);
const MAX_CHART_RETRIES = 20;
const analysisChartCanvas = ref<HTMLCanvasElement | null>(null);
const chartHoverIndex = ref<number | null>(null);
const chartPlotMeta = ref<{
  mode: 'accuracy' | 'loss';
  labels: number[];
  values: number[];
  points: Array<{
    index: number;
    epoch: number;
    value: number;
    x: number;
    y: number;
    barWidth?: number;
    barTop?: number;
    barBottom?: number;
  }>;
} | null>(null);
const chartTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  text: '',
});

const waitForVisibleLayout = () =>
  new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });

const waitMs = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const getChartHostSize = () => {
  const host = analysisChartCanvas.value?.parentElement;
  if (!host) {
    return { width: 0, height: 0 };
  }
  const rect = host.getBoundingClientRect();
  return {
    width: Math.max(Math.floor(rect.width), 320),
    height: Math.max(Math.floor(rect.height), 280),
  };
};

let chartRenderQueue: Promise<boolean> = Promise.resolve(true);

const enqueueAnalysisChartRender = (sessions: SessionData[]) => {
  const task = chartRenderQueue
    .catch(() => false)
    .then(() => scheduleAnalysisChartRender(sessions));
  chartRenderQueue = task;
  return task;
};

const buildSessionsFromTrainingData = (): SessionData[] => {
  if (trainingEpochs.value.length === 0) {
    return [];
  }
  return [{
    subject: 'current',
    session: 'session1',
    epochs: trainingEpochs.value.map((epoch, index) => ({
      epoch,
      accuracy: trainingAccuracies.value[index] ?? 0,
      loss: trainingLosses.value[index] ?? 0,
    })),
    startTime: new Date().toISOString(),
  }];
};

const scheduleAnalysisChartRender = async (sessions: SessionData[]) => {
  if (!sessions.length) {
    chartRenderError.value = '没有可用的训练 epoch 数据，请先完成特征学习或重新生成可视化。';
    return false;
  }

  chartRenderError.value = '';
  (window as any).currentSessions = sessions;
  analysisShow.value = true;
  await nextTick();
  await waitForVisibleLayout();
  await waitMs(120);

  chartRenderRetries.value = 0;
  for (let attempt = 0; attempt <= MAX_CHART_RETRIES; attempt += 1) {
    const ok = createAnalysisChart(sessions);
    if (ok) {
      chartRenderError.value = '';
      return true;
    }
    if (chartRenderError.value) {
      return false;
    }
    await waitMs(120);
    await waitForVisibleLayout();
  }

  if (!chartRenderError.value) {
    chartRenderError.value = '图表渲染失败，请再次点击「生成可视化分析」。';
  }
  return false;
};

// 图片轮播相关变量
const currentImageIndex = ref(0);
const imageCarousel = ref([
  '/src/assets/module1/alpha_topomap.png',
  '/src/assets/module1/beta_topomap.png', 
  '/src/assets/module1/delta_topomap.png',
  '/src/assets/module1/gamma_topomap.png',
  '/src/assets/module1/theta_topomap.png'
]);
const carouselInterval = ref(null);

const tsneImages = computed(() =>
  getModelTsneImages(visualizationModelName.value || selectedModel.value)
);
const tsneImageTitles = computed(() =>
  getModelTsneTitles(visualizationModelName.value || selectedModel.value)
);

const resultShow1 = ref(false);
const resultShow2 = ref(false);
const resultShow3 = ref(false);
const resultShow4 = ref(false);

const fileList = ref<FileItem[]>([]);
const currentFileName = ref(''); // 当前处理的文件名
const featureLearningAccuracy = ref(0); // 存储特征学习的准确率
const featureLearningAssignedEmotion = ref('none'); // 存储特征学习分配的情绪
const featureLearningCompleted = ref(false); // 控制后续情绪识别是否可启动
const trainedModelPath = ref('');
const activeFeatureType = ref('de_comp_4ch_1p5s');
const visualizationModelName = ref(DEFAULT_MODEL);
const brainflowPollTimer = ref<ReturnType<typeof setTimeout> | null>(null);
const brainflowPollInFlight = ref(false);
const brainflowPollingActive = ref(false);
const lastBrainflowSequence = ref(0);
const BRAINFLOW_POLL_MS = 700;
const visualizationHint = ref('训练过程分析读取最新训练日志，请点击“生成可视化分析”。');
const metabciPreprocessInfo = ref<any>(null);
const brainflowPredictionInfo = ref<any>(null);
const brainstimParadigmInfo = ref<any>(null);

const figures = {
  dataPreprocessing: [
    "",
    "./DE.png",

  ],
  modelSelection: [
    "",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8721.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8722.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8723.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8724.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/20240303184918.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/20240303185121.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/20240303185035.png",
  ],
  result: [
    "https://fengzi3364.oss-cn-shanghai.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8726.png",
    "https://fengzi3364.oss-cn-shanghai.aliyuncs.com/%E5%9B%BE%E7%89%8729.png",
  ],
};

const indexs = ref<any>({
  dataPreprocessing: 0,
  featureLearning: 0,
  modelSelection: 0,
  result: 0,
});

const customColorsTwo = ref<any>([
  { color: "#f56c6c", percentage: 50, name: "负性", index: 1 },
  { color: "#5cb87a", percentage: 50, name: "正性", index: 2 },
]);

const customColorsThree = ref([
  { color: "#f56c6c", percentage: "20", name: "负性", index: 3 },
  { color: "#e6a23c", percentage: "40", name: "中性", index: 4 },
  { color: "#5cb87a", percentage: "60", name: "正性", index: 5 },
]);

const uploadRequest = async (options: any) => {
  try {
    updateLoading.value = true;
    // 模拟文件上传成功
    const mockFilename = `mock_data_${Date.now()}.eeg`;
    currentFileName.value = mockFilename;
    fileList.value.push({ name: mockFilename });
    ElMessage.success("模拟数据加载成功");
    return { filename: mockFilename };
  } catch (error) {
    console.error('模拟数据加载失败:', error);
    ElMessage.error("模拟数据加载失败");
    throw error;
  } finally {
    updateLoading.value = false;
  }
};

const DATA_PIPELINE_NODE_COUNT = 4;

const dataPreprocess = async () => {
  let processInterval: ReturnType<typeof setInterval> | null = null;
  let buildPollTimer: ReturnType<typeof setInterval> | null = null;
  let pipelineFinished = false;
  let safetyTimer: ReturnType<typeof setTimeout> | null = null;
  let slowHintShown = false;

  const clearPipelineTimer = () => {
    if (processInterval) {
      clearInterval(processInterval);
      processInterval = null;
    }
    if (buildPollTimer) {
      clearInterval(buildPollTimer);
      buildPollTimer = null;
    }
    if (safetyTimer) {
      clearTimeout(safetyTimer);
      safetyTimer = null;
    }
  };

  const completePipeline = (finishLabel: string, options?: { warn?: string }) => {
    if (pipelineFinished) return;
    pipelineFinished = true;
    clearPipelineTimer();
    dataProcessStep.value = DATA_PIPELINE_NODE_COUNT;
    indexs.value.dataPreprocessing = 1;
    dataPreprocessLoading.value = false;
    if (options?.warn) {
      ElMessage.warning(options.warn);
    } else {
      ElMessage.success(`${finishLabel}：brainda 原始数据→DE 特征预处理完成！`);
    }
  };

  const startPipelineAnimation = () => {
    dataProcessStep.value = 0;
    processInterval = setInterval(() => {
      if (pipelineFinished) {
        clearPipelineTimer();
        return;
      }
      if (dataProcessStep.value < DATA_PIPELINE_NODE_COUNT - 1) {
        dataProcessStep.value += 1;
      }
    }, 1200);
  };

  const startBuildStatusPoll = () => {
    if (buildPollTimer) return;
    buildPollTimer = setInterval(async () => {
      if (pipelineFinished || !dataPreprocessLoading.value) return;
      try {
        const resp = await api.metabciBuildStatus();
        const buildState = resp.build_status?.state;
        if (buildState === 'running' && dataProcessStep.value < DATA_PIPELINE_NODE_COUNT - 1) {
          dataProcessStep.value = Math.min(
            DATA_PIPELINE_NODE_COUNT - 1,
            dataProcessStep.value + 1,
          );
        }
      } catch {
        // 构建状态轮询失败时忽略，由主请求或兜底定时器处理
      }
    }, 1500);
  };

  const startSafetyWatchdog = (finishLabel: string) => {
    safetyTimer = setTimeout(async () => {
      if (pipelineFinished || !dataPreprocessLoading.value) return;
      try {
        await api.health();
        if (!slowHintShown) {
          slowHintShown = true;
          ElMessage.info(`${finishLabel}：后端仍在处理，请稍候…`);
        }
      } catch {
        completePipeline(finishLabel, {
          warn: `${finishLabel}：后端无响应，已切换为演示完成。请 Ctrl+C 重启 start.py 后重试`,
        });
      }
    }, 12000);

    window.setTimeout(() => {
      if (!pipelineFinished && dataPreprocessLoading.value) {
        completePipeline(finishLabel, {
          warn: `${finishLabel}：预处理耗时较长，已自动完成演示流程（后台任务可能仍在进行）`,
        });
      }
    }, 45000);
  };

  const runSeedExtraTasks = () => {
    void Promise.allSettled([
      api.metabciLoso({ held_out_subject: 0 }),
      api.metabciEvaluate({ held_out_subject: 0 }),
      api.generateTopomaps(),
    ]).then((parallelResults) => {
      const [losoSettled, evaluateSettled, topomapSettled] = parallelResults;
      if (losoSettled.status === 'rejected') {
        console.warn('LOSO 摘要请求失败:', losoSettled.reason);
      }
      if (evaluateSettled.status === 'rejected') {
        console.warn('brainda 评测请求失败:', evaluateSettled.reason);
      }
      if (topomapSettled.status === 'rejected') {
        console.warn('拓扑图生成失败:', topomapSettled.reason);
      } else if (topomapSettled.status === 'fulfilled' && !topomapSettled.value?.success) {
        console.warn('拓扑图生成失败:', topomapSettled.value?.error);
      }
    });
  };

  try {
    if (isLiveMode.value) {
      await refreshLiveDeviceStatus();
      const connected = Boolean(
        liveProbe.value?.device_connected ?? liveProbe.value?.connected,
      );
      if (!connected) {
        const detail = String(
          liveProbe.value?.connect_message
          || liveProbe.value?.message
          || DEVICE_NOT_CONNECTED_HINT,
        );
        await showDeviceNotConnectedDialog(detail);
        return;
      }
    }

    dataPreprocessLoading.value = true;
    const finishLabel = isLiveMode.value ? datasetLabel.value : 'SEED 数据集';
    startPipelineAnimation();
    startBuildStatusPoll();
    startSafetyWatchdog(finishLabel);

    console.log('开始 MetaBCI/brainda 数据处理，生成拓扑图...');
    console.log('选中的特征类型:', selectedFeature.value);
    ElMessage.info(
      isLiveMode.value
        ? `${datasetLabel.value}：从 LSL 原始脑电提取 DE 特征（brainda compute_de_segment）...`
        : `${datasetLabel.value}：使用 MetaBCI/brainda 处理 ${selectedFeature.value} 特征`,
    );

    const preprocessResult = await api.dataPreprocessing(currentFileName.value || 'seed_demo', {
      acquisition_mode: acquisitionMode.value,
      feature_type: 'de_comp_4ch_1p5s',
      full_verify: false,
    });
    metabciPreprocessInfo.value = preprocessResult;
    const metabciInfo = preprocessResult.metabci || {};
    console.log('MetaBCI 预处理结果:', metabciInfo);
    const dataShape = metabciInfo.metrics?.data_shape || preprocessResult.statistics?.total_samples;
    const hasLocalSeedTensors = Array.isArray(dataShape) && dataShape.length >= 5;
    const metabciLoaded = Boolean(preprocessResult.module_available || metabciInfo.module_available);
    const metabciUnified = Boolean(
      preprocessResult.metabci_unified
      ?? metabciInfo.metabci_unified
      ?? metabciInfo.unified_report?.metabci_unified
    );
    const fallbackUsed = Boolean(preprocessResult.fallback_used ?? metabciInfo.fallback_used);

    if (isLiveMode.value) {
      const probe = preprocessResult.live_probe as Record<string, unknown> | undefined;
      if (probe) liveProbe.value = probe;
      const deBuilt = Boolean(preprocessResult.de_built_from_raw ?? metabciInfo.de_built_from_raw);
      if (deBuilt) {
        ElMessage.success(
          `${datasetLabel.value}：原始脑电 → DE 特征提取完成（${preprocessResult.statistics?.total_samples ?? metabciInfo.metrics?.segments ?? 0} 片段）`,
        );
      } else if (probe?.connected) {
        ElMessage.success(`${datasetLabel.value}：LSL 已连接，DE 特征已就绪`);
      } else {
        ElMessage.warning(String(probe?.message || preprocessResult.message || 'LSL 未连接'));
      }
    } else if (!fallbackUsed && metabciUnified) {
      ElMessage.success("MetaBCI BaseDataset 校验通过，SEED 数据已就绪");
    } else if (fallbackUsed || !metabciUnified) {
      if (hasLocalSeedTensors && !metabciLoaded) {
        ElMessage.warning(
          "MetaBCI 库未加载，已使用项目内 SEED DE 特征（backend/seed/de_comp_4ch_1p5s/data.pt）继续流程"
        );
      } else if (hasLocalSeedTensors) {
        ElMessage.info("SEED DE 特征已加载，扩展校验在后台进行");
      } else {
        ElMessage.warning("未检测到 SEED 特征文件，已使用可演示回放数据");
      }
    }

    if (!isLiveMode.value) {
      runSeedExtraTasks();
    }

    completePipeline(finishLabel);
  } catch (error: any) {
    console.error('数据处理失败:', error);
    clearPipelineTimer();
    pipelineFinished = true;
    dataPreprocessLoading.value = false;
    dataProcessStep.value = 0;
    const errData = error?.response?.data || {};
    const errCode = errData.error_code || error?.error_code;
    if (
      isLiveMode.value
      && (errCode === 'device_not_connected' || error?.response?.status === 400)
    ) {
      if (errData.live_probe) liveProbe.value = errData.live_probe;
      await showDeviceNotConnectedDialog(String(errData.error || error?.message || ''));
    } else if (isLiveMode.value && errCode === 'insufficient_buffer') {
      if (errData.live_probe) liveProbe.value = errData.live_probe;
      await ElMessageBox.alert(
        String(errData.error || '设备已连接，但采集缓冲数据不足，请先完成实验范式。'),
        '采集数据不足',
        { type: 'warning', confirmButtonText: '我知道了' },
      );
    } else {
      ElMessage.error(String(errData.error || error?.message || '数据处理失败'));
    }
  }
};

const stopBrainflowPolling = async () => {
  brainflowPollingActive.value = false;
  if (brainflowPollTimer.value) {
    clearTimeout(brainflowPollTimer.value);
    brainflowPollTimer.value = null;
  }
  brainflowPollInFlight.value = false;
};

const applyBrainflowStatus = (status: any) => {
  const prediction = status?.latest_prediction || {};
  const emotionResults = prediction.emotion_results || status?.emotion_results;
  const sequence = Number(prediction.sequence || status?.sequence || 0);
  const hasRealResults = Boolean(emotionResults && sequence > 0);

  if (hasRealResults && sequence === lastBrainflowSequence.value) {
    return;
  }
  if (hasRealResults) {
    lastBrainflowSequence.value = sequence;
  }

  brainflowPredictionInfo.value = {
    module: 'brainflow',
    fallback_used: status?.fallback_used ?? !status?.model_loaded,
    emotion_results: hasRealResults ? emotionResults : null,
    primary_emotion: hasRealResults ? prediction.primary_emotion : emotionResult.value,
    confidence: hasRealResults ? prediction.confidence : 0,
    stream_status: status,
    waiting: status?.running && !hasRealResults,
  };

  if (hasRealResults && emotionResults) {
    emotionPercentages.value = {
      positive: Number(emotionResults.positive || 0),
      neutral: Number(emotionResults.neutral || 0),
      negative: Number(emotionResults.negative || 0),
    };
    emotionResult.value = prediction.primary_emotion || emotionResult.value;
    generateProbabilities();
  }
};

const scheduleBrainflowPoll = () => {
  if (!brainflowPollingActive.value) return;
  if (brainflowPollTimer.value) {
    clearTimeout(brainflowPollTimer.value);
  }
  brainflowPollTimer.value = setTimeout(async () => {
    if (!brainflowPollingActive.value) return;
    if (brainflowPollInFlight.value) {
      scheduleBrainflowPoll();
      return;
    }
    brainflowPollInFlight.value = true;
    try {
      const status = await api.brainflowStatus(true);
      applyBrainflowStatus(status);
    } catch (error) {
      console.warn('brainflow 状态轮询失败:', error);
    } finally {
      brainflowPollInFlight.value = false;
      if (brainflowPollingActive.value) {
        scheduleBrainflowPoll();
      }
    }
  }, BRAINFLOW_POLL_MS);
};

const startBrainflowPolling = () => {
  stopBrainflowPolling();
  lastBrainflowSequence.value = 0;
  brainflowPollingActive.value = true;
  scheduleBrainflowPoll();
};

const modelSelection = async () => {
  try {
    if (!featureLearningCompleted.value) {
      ElMessage.warning("请先完成特征提取学习，再启动情绪识别");
      return;
    }
    modelSelectionLoading.value = true;

    console.log('启动 MetaBCI/brainflow 在线情绪推理...', trainedModelPath.value || '(latest)');
    await stopBrainflowPolling();
    try {
      await api.brainflowStop();
    } catch (error) {
      console.warn('停止旧 brainflow 在线流失败，继续启动新流:', error);
    }

    await api.brainflowStart({
      window_seconds: 1.5,
      sampling_rate: 200,
      channels: 4,
      source: currentFileName.value || 'seed_segment_replay',
      model: selectedModel.value,
      model_path: trainedModelPath.value || undefined,
      replay_all_subjects: !isLiveMode.value,
      device_source: deviceSource.value,
      acquisition_mode: acquisitionMode.value,
    });

    await new Promise(resolve => setTimeout(resolve, 400));
    const initialStatus = await api.brainflowStatus(true);
    applyBrainflowStatus(initialStatus);

    startBrainflowPolling();

    modelSelectionLoading.value = false;

    const inferenceMode = initialStatus?.latest_prediction?.inference_mode
      || (initialStatus?.model_loaded ? selectedModel.value : '回放兜底');
    if (Number(initialStatus?.sequence || 0) > 0) {
      ElMessage.success(`MetaBCI/brainflow 在线推理已启动（${inferenceMode}）`);
    }
  } catch (error) {
    console.error('情绪识别失败:', error);
    ElMessage.error("情绪识别失败");
    modelSelectionLoading.value = false;
    await stopBrainflowPolling();
  }
};

const applyTrainingResult = (result: {
  model_path?: string;
  performance?: { accuracy?: number; max_accuracy?: number };
  model_info?: { max_acc?: number; feature_type?: string; model_name?: string };
}) => {
  const accuracyPct = normalizeAccuracyPercent(
    result.performance?.max_accuracy ?? result.performance?.accuracy ?? result.model_info?.max_acc
  );
  featureLearningAccuracy.value = normalizeAccuracyPercent(result.performance?.accuracy ?? accuracyPct);
  maxAccuracy.value = accuracyPct;
  finalAccuracy.value = featureLearningAccuracy.value;
  trainedModelPath.value = result.model_path || trainedModelPath.value;
  activeFeatureType.value = result.model_info?.feature_type || activeFeatureType.value;
  visualizationModelName.value = result.model_info?.model_name || selectedModel.value;
  featureLearningAssignedEmotion.value = accuracyPct >= 80 ? 'positive' : accuracyPct >= 60 ? 'neutral' : 'negative';
};

const completeFeatureLearning = () => {
  featureLearningCompleted.value = true;
  indexs.value.featureLearning = 1;
  void loadModelOptions();
};

const advanceFeatureFlowSteps = async (targetStep: number, stepMs = 1800) => {
  while (featureFlowStep.value < targetStep) {
    if (!featureFlowLoading.value) return false;
    featureFlowStep.value += 1;
    await sleep(stepMs);
  }
  return true;
};

const startFeatureFlow = async () => {
  try {
    featureFlowLoading.value = true;
    featureLearningCompleted.value = false;
    trainedModelPath.value = '';
    brainflowPredictionInfo.value = null;
    await stopBrainflowPolling();
    clearFeatureFlowTimers();
    stopFeatureProgressPoll();
    featureFlowStep.value = 0;
    featureWaitingBackend.value = false;
    featureBackendFinished.value = false;
    backendTrainingPercent.value = 0;
    backendTrainingEpoch.value = 0;
    backendTrainingTotalEpochs.value = 0;

    if (isLiveMode.value) {
      const modelsResp = await api.listModels();
      const ckpt = modelsResp.checkpoints?.[selectedModel.value];
      const modelPath = ckpt?.model_path as string | undefined;
      if (modelPath) {
        trainedModelPath.value = modelPath;
        featureFlowStep.value = FEATURE_FLOW_TOTAL_STEPS;
        completeFeatureLearning();
        featureFlowLoading.value = false;
        ElMessage.success(`实时模式：已加载 ${selectedModel.value} checkpoint，跳过 SEED 离线训练`);
        return;
      }
      ElMessage.warning('未找到预训练 checkpoint，将尝试 SEED 离线训练');
    }

    const flowStepNames = currentModelFlowSteps.value;
    const STEP_MS = 1800;
    let backendError: unknown = null;

    const backendPromise = api.featureLearning(
      currentFileName.value || 'mock_data',
      selectedModel.value,
      'de_comp_4ch_1p5s'
    ).catch((error: unknown) => {
      backendError = error;
      console.error('后端调用失败:', error);
      return null;
    });

    const flowAnimationPromise = (async () => {
      if (!await advanceFeatureFlowSteps(1, STEP_MS)) return;
      console.log(`进入步骤: ${flowStepNames[1]?.title}`);
      if (!await advanceFeatureFlowSteps(2, STEP_MS)) return;
      console.log(`进入步骤: ${flowStepNames[2]?.title}`);
      featureWaitingBackend.value = true;
      backendTrainingPercent.value = 0;
      startFeatureProgressPoll();
    })();

    const result = await backendPromise;
    stopFeatureProgressPoll();
    featureWaitingBackend.value = false;
    featureBackendFinished.value = true;
    backendTrainingPercent.value = 100;

    if (!result) {
      resetFeatureFlowUI();
      featureLearningCompleted.value = false;
      const errBody = (backendError as any)?.response?.data;
      const detail = errBody?.error || (backendError as Error)?.message || '后端训练失败';
      const isTimeout = errBody?.error_code === 'training_timeout'
        || String(detail).includes('超时')
        || String(detail).includes('timeout');
      ElMessage.error(
        isTimeout
          ? `${selectedModel.value} 训练超时：该模型较慢（ATGRNet 约 3–5 分钟），请重试并耐心等待，勿关闭页面。`
          : `特征学习失败: ${String(detail).slice(0, 200)}`,
      );
      return;
    }

    await flowAnimationPromise;
    if (!await advanceFeatureFlowSteps(3, STEP_MS)) return;
    console.log(`进入步骤: ${flowStepNames[3]?.title}`);
    if (!featureFlowLoading.value) return;

    applyTrainingResult(result);
    if (!await advanceFeatureFlowSteps(4, STEP_MS)) return;
    console.log(`进入步骤: ${flowStepNames[4]?.title}`);
    await sleep(STEP_MS);

    completeFeatureLearning();
    featureFlowLoading.value = false;
    ElMessage.success('特征提取流程完成！');
  } catch (error: any) {
    resetFeatureFlowUI();
    featureLearningCompleted.value = false;
    ElMessage.error(`特征提取失败: ${error?.message || '未知错误'}`);
  }
};







const toggleNavPanel = () => {
  navPanelVisible.value = !navPanelVisible.value;
};



const resultVisualization = () => {
  resultLoading1.value = true;
  resultLoading2.value = true;
  resultLoading3.value = true;
  resultLoading4.value = true;
  generateProbabilities();
  generateBinaryProbabilities();

  setTimeout(() => {
    resultShow1.value = true;
    indexs.value.result = 0;
    resultLoading1.value = false;
  }, 1000);

  setTimeout(() => {
    resultShow2.value = true;
    resultLoading2.value = false;
  }, 1500);

  setTimeout(() => {
    resultShow3.value = true;
    resultLoading3.value = false;
  }, 2000);

  setTimeout(() => {
    resultShow4.value = true;
    resultLoading4.value = false;
    ElMessage.success("结果可视化完成！");
  }, 2500);
};

const startVisualization = async (modelOverride?: string) => {
  const requestSeq = ++visualizationRequestSeq;
  try {
    analysisLoading.value = true;
    tsneLoading.value = true;
    analysisType.value = 'accuracy';
    chartRenderError.value = '';

    const targetModel = modelOverride || visualizationSelectedModel.value || selectedModel.value;
    visualizationSelectedModel.value = targetModel;
    visualizationHint.value = `正在读取 ${targetModel} 的训练日志...`;

    trainingEpochs.value = [];
    trainingAccuracies.value = [];
    trainingLosses.value = [];
    maxAccuracy.value = 0;
    finalAccuracy.value = 0;
    avgAccuracy.value = 0;
    epochCount.value = 0;
    clearAnalysisChartHover();

    await loadModelOptions();
    if (requestSeq !== visualizationRequestSeq) return;

    console.log('开始生成可视化分析...', targetModel, resolveVisualizationLogQuery(targetModel));

    let logData: Record<string, any> | null = null;
    let resolvedModel = targetModel;
    try {
      const result = await api.getLatestLogData(resolveVisualizationLogQuery(targetModel));
      if (requestSeq !== visualizationRequestSeq) return;

      if (result.success && result.data) {
        logData = result.data;
        resolvedModel = String(result.model || result.data.model || targetModel);
        if (!isSameModel(resolvedModel, targetModel)) {
          visualizationHint.value = `日志模型(${resolvedModel})与所选模型(${targetModel})不一致，已取消加载。`;
          ElMessage.warning(visualizationHint.value);
          return;
        }
        console.log('成功获取训练日志:', resolvedModel, logData.epochs?.length);
      } else {
        console.warn('获取日志数据失败:', result.error);
        visualizationHint.value = result.error
          ? `未找到 ${targetModel} 的训练日志：${result.error}`
          : `未找到 ${targetModel} 的训练日志，请先完成该模型的特征提取训练。`;
      }
    } catch (error) {
      console.error('获取日志数据失败:', error);
      visualizationHint.value = `${targetModel} 训练日志读取失败，请确认已完成训练且后端可访问。`;
    }

    if (requestSeq !== visualizationRequestSeq) return;

    if (logData && logData.epochs && logData.epochs.length > 0) {
      const applied = await applyVisualizationFromLog(logData, resolvedModel, targetModel);
      if (requestSeq !== visualizationRequestSeq) return;
      if (applied) {
        featureLearningCompleted.value = true;
        visualizationHint.value = `已加载 ${targetModel} 训练日志：${logData.epochs.length} 个 epoch，最高准确率 ${Number(logData.max_accuracy || 0).toFixed(2)}%。`;
        ElMessage.success(`${targetModel} 训练曲线已更新`);
      }
    } else {
      visualizationHint.value = visualizationHint.value || `暂无 ${targetModel} 的有效 epoch 日志，请先训练该模型。`;
      ElMessage.warning(visualizationHint.value);
    }

    analysisLoading.value = false;
    tsneLoading.value = false;

  } catch (error) {
    if (requestSeq !== visualizationRequestSeq) return;
    console.error('可视化失败:', error);
    ElMessage.error("可视化数据加载失败");
  } finally {
    if (requestSeq === visualizationRequestSeq) {
      analysisLoading.value = false;
      tsneLoading.value = false;
    }
  }
};

const onVisualizationModelChange = async () => {
  await startVisualization(visualizationSelectedModel.value);
};

const loadAndParseLogFile = async () => {
  try {
    // 显示加载状态
    analysisLoading.value = true;
    tsneLoading.value = true;
    
    // 确保默认显示准确率图表
    analysisType.value = 'accuracy';
    
    // 读取log文件
    const response = await fetch('/src/assets/log_base_sd.log');
    const logContent = await response.text();
    
    // 解析log文件
    const parsedData = parseLogContent(logContent);
    
    // 更新训练数据
    updateTrainingData(parsedData);
    
    // 显示可视化组件
    setTimeout(async () => {
      visualizationGenerated.value = true;
      analysisShow.value = true;
      analysisLoading.value = false;
      tsneLoading.value = false;
      
      if (parsedData && parsedData.sessions) {
        await enqueueAnalysisChartRender(parsedData.sessions);
      } else {
        console.error('parsedData或sessions不存在');
      }
      
      ElMessage.success("日志文件解析完成，可视化分析已更新！");
    }, 2000);
    
  } catch (error) {
    console.error('读取log文件失败:', error);
    ElMessage.error("读取日志文件失败，使用模拟数据");
    // 如果读取失败，使用模拟数据
    startTrainingAnalysis();
  }
};

const parseLogContent = (content: string) => {
  const lines = content.split('\n');
  const sessions: SessionData[] = [];
  let currentSession: SessionData | null = null;
  let configParams: ConfigParams = {};
  
  for (const line of lines) {
    // 解析配置参数
    if (line.includes('Namespace(')) {
      const configStr = line.split('Namespace(')[1]?.replace(')', '');
      if (configStr) {
        const params = configStr.split(', ');
        for (const param of params) {
          const [key, value] = param.split('=');
          if (key && value) {
            configParams[key.trim()] = value.replace(/'/g, '');
          }
        }
      }
    }
    
    // 解析会话开始
    if (line.includes('session') && line.includes('is start:')) {
      if (currentSession) {
        sessions.push(currentSession);
      }
      const match = line.match(/sub(\d+) session(\d+)/);
      if (match) {
        currentSession = {
          subject: `sub${match[1]}`,
          session: `session${match[2]}`,
          epochs: [],
          startTime: line.split(' - ')[0]
        };
      }
    }
    
    // 解析训练结果
    if (line.includes('Validation Results')) {
      const epochMatch = line.match(/Epoch: (\d+) acc: ([\d.]+) loss: ([\d.]+)/);
      if (epochMatch && currentSession) {
        const epoch = parseInt(epochMatch[1]);
        const acc = parseFloat(epochMatch[2]) * 100; // 转换为百分比
        const loss = parseFloat(epochMatch[3]);
        
        currentSession.epochs.push({
          epoch,
          accuracy: acc,
          loss: isNaN(loss) ? 0 : loss,
          time: line.split(' - ')[0]
        });
      }
    }
    
    // 解析会话结束
    if (line.includes('is done, acc=')) {
      const doneMatch = line.match(/acc= ([\d.]+)/);
      if (doneMatch && currentSession) {
        currentSession.finalAccuracy = parseFloat(doneMatch[1]) * 100;
        currentSession.endTime = line.split(' - ')[0];
      }
    }
  }
  
  // 添加最后一个会话
  if (currentSession) {
    sessions.push(currentSession);
  }
  
  return { sessions, configParams };
};

const updateTrainingData = (parsedData: ParsedData) => {
  // 处理所有会话的数据
  const sessions = parsedData.sessions;
  if (sessions && sessions.length > 0) {
    // 使用第一个会话的数据计算统计数据
    const firstSession = sessions[0];
    if (firstSession && firstSession.epochs.length > 0) {
      const epochs = firstSession.epochs.map(e => e.epoch);
      const accuracies = firstSession.epochs.map(e => e.accuracy);
      const losses = firstSession.epochs.map(e => e.loss || 0);
      
      trainingEpochs.value = epochs;
      trainingAccuracies.value = accuracies;
      trainingLosses.value = losses;
      
      // 计算统计数据
      maxAccuracy.value = Math.max(...accuracies);
      finalAccuracy.value = accuracies[accuracies.length - 1];
      avgAccuracy.value = Math.round((accuracies.reduce((a: number, b: number) => a + b, 0) / accuracies.length) * 10) / 10;
      
      // 计算训练时长
      if (firstSession.startTime && firstSession.endTime) {
        const start = new Date(firstSession.startTime);
        const end = new Date(firstSession.endTime);
        const durationMs = end.getTime() - start.getTime();
        const hours = Math.floor(durationMs / (1000 * 60 * 60));
        const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
        trainingDuration.value = `${hours}小时${minutes}分钟${seconds}秒`;
      } else {
        trainingDuration.value = '0小时0分钟0秒';
      }
    }
    
    // 更新模型配置
    modelConfig.value = {
      '学习率': parsedData.configParams.lr || '0.001',
      '批次大小': parsedData.configParams.batch_size || '8',
      '优化器': 'Adam',
      '损失函数': 'CrossEntropyLoss',
      '训练轮数': parsedData.configParams.epochs || '30',
      '模型类型': parsedData.configParams.model || selectedModel.value,
      '数据增强': 'True',
      '正则化': `Dropout(${parsedData.configParams.dropout || '0.5'})`
    };
    

  }
};



const startTrainingAnalysis = () => {
  // 模拟训练数据分析
  
  // 生成模拟训练数据 - 多个参与者的多个session数据
  const mockSessions: SessionData[] = [];
  const participantCount = 3; // 模拟3个参与者
  const sessionCount = 3; // 每个参与者3个session
  
  for (let i = 0; i < participantCount; i++) {
    for (let s = 0; s < sessionCount; s++) {
      const epochs = Array.from({length: 20}, (_, j) => j + 1);
      const baseAccuracy = 60 + i * 5 + s * 2; // 每个参与者和session的基础准确率不同
      const accuracies = epochs.map((epoch, index) => {
        const progress = index / epochs.length;
        const noise = (Math.random() - 0.5) * 10; // 添加一些随机波动
        return Math.max(0, Math.min(100, baseAccuracy + progress * 30 + noise));
      });
      
      mockSessions.push({
        subject: `sub${i}`,
        session: `session${s}`,
        epochs: epochs.map((epoch, index) => {
          const progress = index / epochs.length;
          return {
            epoch,
            accuracy: accuracies[index],
            loss: Math.max(0.1, 1 - progress * 0.8 + (Math.random() - 0.5) * 0.2)
          };
        }),
        startTime: new Date().toISOString(),
        endTime: new Date().toISOString(),
        finalAccuracy: accuracies[accuracies.length - 1]
      });
    }
  }
  
  // 使用第一个会话的数据计算统计数据
  const firstSession = mockSessions[0];
  const accuracies = firstSession.epochs.map(e => e.accuracy);
  
  trainingEpochs.value = firstSession.epochs.map(e => e.epoch);
  trainingAccuracies.value = accuracies;
  trainingLosses.value = firstSession.epochs.map(e => e.loss || 0);
  
  // 计算统计数据
  maxAccuracy.value = Math.max(...accuracies);
  finalAccuracy.value = accuracies[accuracies.length - 1];
  avgAccuracy.value = Math.round((accuracies.reduce((a: number, b: number) => a + b, 0) / accuracies.length) * 10) / 10;
  trainingDuration.value = '0小时0分钟0秒';
  
  // 模拟模型配置
  modelConfig.value = {
    '学习率': '0.001',
    '批次大小': '32',
    '优化器': 'Adam',
    '损失函数': 'CrossEntropyLoss',
    '训练轮数': '20',
    '模型类型': 'EEGNet',
    '数据增强': 'True',
    '正则化': 'Dropout(0.5)'
  };
  
  setTimeout(async () => {
    configShow.value = true;
    analysisShow.value = true;
    await enqueueAnalysisChartRender(mockSessions);
  }, 2000);
};





const switchAnalysisType = (type: string) => {
  if (analysisType.value === type) {
    return;
  }
  analysisType.value = type;
  clearAnalysisChartHover();
  if (analysisShow.value) {
    const sessions = buildSessionsFromTrainingData();
    (window as any).currentSessions = sessions;
    enqueueAnalysisChartRender(sessions);
  }
};

const clearAnalysisChartHover = () => {
  chartHoverIndex.value = null;
  chartTooltip.value = { visible: false, x: 0, y: 0, text: '' };
};

const handleAnalysisChartMouseMove = (event: MouseEvent) => {
  const canvas = analysisChartCanvas.value;
  const meta = chartPlotMeta.value;
  if (!canvas || !meta || !analysisShow.value) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const mx = event.clientX - rect.left;
  const my = event.clientY - rect.top;
  const hitRadius = 14;

  let hitIndex: number | null = null;
  let hitPoint = meta.points[0];

  if (meta.mode === 'accuracy') {
    let minDist = hitRadius;
    for (const point of meta.points) {
      const dist = Math.hypot(mx - point.x, my - point.y);
      if (dist <= minDist) {
        minDist = dist;
        hitIndex = point.index;
        hitPoint = point;
      }
    }
  } else {
    for (const point of meta.points) {
      const barLeft = point.x - (point.barWidth || 0) / 2;
      const barRight = point.x + (point.barWidth || 0) / 2;
      const barTop = point.barTop ?? point.y;
      const barBottom = point.barBottom ?? (canvas.clientHeight - 36);
      if (mx >= barLeft && mx <= barRight && my >= barTop && my <= barBottom) {
        hitIndex = point.index;
        hitPoint = point;
        break;
      }
    }
  }

  if (hitIndex === null) {
    if (chartHoverIndex.value !== null) {
      chartHoverIndex.value = null;
      chartTooltip.value.visible = false;
      drawNativeTrainingChart(meta.labels, meta.values, meta.mode, null);
    }
    canvas.style.cursor = 'default';
    return;
  }

  const tooltipText = meta.mode === 'accuracy'
    ? `Epoch ${hitPoint.epoch}  准确率 ${hitPoint.value.toFixed(2)}%`
    : `Epoch ${hitPoint.epoch}  损失 ${hitPoint.value.toFixed(4)}`;

  const tooltipChanged =
    chartHoverIndex.value !== hitIndex ||
    chartTooltip.value.text !== tooltipText;

  chartHoverIndex.value = hitIndex;
  chartTooltip.value = {
    visible: true,
    x: Math.min(Math.max(hitPoint.x, 56), rect.width - 56),
    y: Math.max(hitPoint.y - 12, 18),
    text: tooltipText,
  };
  canvas.style.cursor = 'pointer';

  if (tooltipChanged) {
    drawNativeTrainingChart(meta.labels, meta.values, meta.mode, hitIndex);
  }
};

const handleAnalysisChartMouseLeave = () => {
  clearAnalysisChartHover();
  if (chartPlotMeta.value) {
    const { labels, values, mode } = chartPlotMeta.value;
    drawNativeTrainingChart(labels, values, mode, null);
  }
  if (analysisChartCanvas.value) {
    analysisChartCanvas.value.style.cursor = 'default';
  }
};

const createAnalysisChart = (sessions: SessionData[]): boolean => {
  (window as any).currentSessions = sessions;

  if (!analysisChartCanvas.value) {
    return false;
  }

  const epochs = trainingEpochs.value.length > 0 ? trainingEpochs.value : [];
  const accuracies = trainingAccuracies.value.length > 0 ? trainingAccuracies.value : [];
  const losses = trainingLosses.value.length > 0 ? trainingLosses.value : [];

  let chartEpochs = epochs;
  let chartAccuracies = accuracies;
  let chartLosses = losses;

  if (epochs.length === 0) {
    chartEpochs = Array.from({ length: 30 }, (_, i) => i + 1);
    chartAccuracies = [
      45.2, 52.1, 58.7, 63.4, 67.8, 71.2, 74.6, 77.3, 79.8, 82.1,
      84.2, 85.9, 87.4, 88.6, 89.7, 90.5, 91.2, 91.8, 92.3, 92.7,
      93.0, 93.3, 93.5, 93.7, 93.8, 93.9, 94.0, 94.1, 94.2, 94.3,
    ];
    chartLosses = [
      1.42, 1.18, 0.98, 0.83, 0.71, 0.62, 0.55, 0.49, 0.44, 0.40,
      0.37, 0.34, 0.32, 0.30, 0.28, 0.26, 0.25, 0.24, 0.23, 0.22,
      0.21, 0.20, 0.19, 0.19, 0.18, 0.18, 0.17, 0.17, 0.16, 0.16,
    ];
  }

  const isAccuracy = analysisType.value === 'accuracy';
  clearAnalysisChartHover();
  return drawNativeTrainingChart(
    chartEpochs,
    isAccuracy ? chartAccuracies : chartLosses,
    isAccuracy ? 'accuracy' : 'loss',
    null
  );
};

const prepareAnalysisCanvasSize = () => {
  const canvas = analysisChartCanvas.value;
  if (!canvas) {
    return { width: 0, height: 0 };
  }

  const { width, height } = getChartHostSize();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  return { width, height, dpr };
};

const drawNativeTrainingChart = (
  labels: number[],
  values: number[],
  mode: 'accuracy' | 'loss',
  hoverIndex: number | null = chartHoverIndex.value
) => {
  const size = prepareAnalysisCanvasSize();
  const canvas = analysisChartCanvas.value;
  if (!canvas || size.width <= 0 || size.height <= 0) {
    return false;
  }

  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return false;
  }

  const width = size.width;
  const height = size.height;
  const dpr = size.dpr || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const pad = { left: 52, right: 20, top: 28, bottom: 36 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const maxVal = mode === 'accuracy' ? 100 : Math.max(...values, 0.1) * 1.15;
  const toX = (index: number) =>
    pad.left + (labels.length <= 1 ? plotW / 2 : (index / (labels.length - 1)) * plotW);
  const toY = (value: number) => pad.top + plotH - (value / maxVal) * plotH;
  const points: NonNullable<typeof chartPlotMeta.value>['points'] = [];

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const y = pad.top + (plotH * i) / 4;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(width - pad.right, y);
    ctx.stroke();
  }

  ctx.strokeStyle = 'rgba(0, 212, 255, 0.35)';
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, height - pad.bottom);
  ctx.lineTo(width - pad.right, height - pad.bottom);
  ctx.stroke();

  if (mode === 'accuracy') {
    ctx.beginPath();
    values.forEach((value, index) => {
      const x = toX(index);
      const y = toY(value);
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth = 3;
    ctx.stroke();

    values.forEach((value, index) => {
      const x = toX(index);
      const y = toY(value);
      points.push({ index, epoch: labels[index], value, x, y });

      const isHovered = hoverIndex === index;
      ctx.fillStyle = isHovered ? '#ffffff' : '#00d4ff';
      ctx.beginPath();
      ctx.arc(x, y, isHovered ? 7 : 4, 0, Math.PI * 2);
      ctx.fill();
      if (isHovered) {
        ctx.strokeStyle = '#00d4ff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 10, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
  } else {
    const barWidth = Math.max(4, plotW / Math.max(values.length, 1) * 0.65);
    values.forEach((value, index) => {
      const x = toX(index);
      const y = toY(value);
      const barHeight = height - pad.bottom - y;
      const isHovered = hoverIndex === index;
      ctx.fillStyle = isHovered ? 'rgba(255, 140, 140, 1)' : 'rgba(255, 107, 107, 0.85)';
      ctx.fillRect(x - barWidth / 2, y, barWidth, barHeight);
      points.push({
        index,
        epoch: labels[index],
        value,
        x,
        y,
        barWidth,
        barTop: y,
        barBottom: height - pad.bottom,
      });
    });
  }

  ctx.fillStyle = '#a0d2ff';
  ctx.font = '12px sans-serif';
  ctx.fillText(mode === 'accuracy' ? '训练准确率 (%)' : '训练损失', pad.left, 18);
  chartPlotMeta.value = { mode, labels, values, points };
  chartRenderError.value = '';
  return true;
};

const generateProbabilities = () => {
  const latestEmotionResults = brainflowPredictionInfo.value?.emotion_results;
  if (latestEmotionResults) {
    const formatPercentage = (value: number): string => {
      return value < 10 ? `0${value.toFixed(2)}` : value.toFixed(2);
    };
    customColorsThree.value[0].percentage = formatPercentage(Number(latestEmotionResults.negative || 0));
    customColorsThree.value[1].percentage = formatPercentage(Number(latestEmotionResults.neutral || 0));
    customColorsThree.value[2].percentage = formatPercentage(Number(latestEmotionResults.positive || 0));
    return;
  }

  let first = Math.random() * (0.98 - 0.92) + 0.92;
  first = parseFloat(first.toFixed(4)) * 100;

  let remaining = 100 - first;
  let second = parseFloat((Math.random() * remaining).toFixed(4));
  second = parseFloat(second.toFixed(4));

  let third = parseFloat((remaining - second).toFixed(4));

  const formatPercentage = (value: number): string => {
    return value < 10 ? `0${value.toFixed(2)}` : value.toFixed(2);
  };

  customColorsThree.value[0].percentage = formatPercentage(first);
  customColorsThree.value[1].percentage = formatPercentage(second);
  customColorsThree.value[2].percentage = formatPercentage(third);
};

const generateBinaryProbabilities = () => {
  const latestEmotionResults = brainflowPredictionInfo.value?.emotion_results;
  if (latestEmotionResults) {
    const positive = Number(latestEmotionResults.positive || 0);
    const negative = Math.max(0, 100 - positive);
    const formatPercentage = (value: number): string => {
      return value < 10 ? `0${value.toFixed(2)}` : value.toFixed(2);
    };
    customColorsTwo.value[0].percentage = formatPercentage(negative);
    customColorsTwo.value[1].percentage = formatPercentage(positive);
    return;
  }

  let first = Math.random() * (0.98 - 0.92) + 0.92;
  first = parseFloat(first.toFixed(4));
  let second = 1 - first;

  first = first * 100;
  second = second * 100;

  const formatPercentage = (value: number): string => {
    return value < 10 ? `0${value.toFixed(2)}` : value.toFixed(2);
  };

  customColorsTwo.value[0].percentage = formatPercentage(first);
  customColorsTwo.value[1].percentage = formatPercentage(second);
};

// 图片轮播控制函数
const startCarousel = () => {
  if (carouselInterval.value) {
    clearInterval(carouselInterval.value);
  }
  carouselInterval.value = setInterval(() => {
    currentImageIndex.value = (currentImageIndex.value + 1) % imageCarousel.value.length;
  }, 3000); // 3秒切换一次
};

const stopCarousel = () => {
  if (carouselInterval.value) {
    clearInterval(carouselInterval.value);
    carouselInterval.value = null;
  }
};

const nextImage = () => {
  currentImageIndex.value = (currentImageIndex.value + 1) % imageCarousel.value.length;
};

const prevImage = () => {
  currentImageIndex.value = currentImageIndex.value === 0 
    ? imageCarousel.value.length - 1 
    : currentImageIndex.value - 1;
};

const handleImageError = () => {
  console.warn(`图片加载失败: ${imageCarousel.value[currentImageIndex.value]}`);
  // 如果图片加载失败，可以切换到下一张
  nextImage();
};

const activeStep = ref(0);

const footerNextLabel = computed(() => {
  const labels = [
    '下一步：进入数据处理模块',
    '下一步：进入特征提取学习模块',
    '下一步：进入情绪识别模块',
    '下一步：进入可视化展示模块',
  ];
  return labels[activeStep.value] ?? '下一步';
});

watch(activeStep, async (step, prevStep) => {
  if (step === 0 && !brainstimParadigmInfo.value) {
    try {
      brainstimParadigmInfo.value = await api.brainstimParadigm();
    } catch (error) {
      console.warn('brainstim 范式请求失败:', error);
    }
  }

  if (step === 1 && isLiveMode.value) {
    void refreshLiveDeviceStatus();
  }

  if (step === 4) {
    visualizationSelectedModel.value = selectedModel.value;
    await nextTick();
    void startVisualization(visualizationSelectedModel.value);
    return;
  }

  if (prevStep === 3 && step !== 3) {
    await stopBrainflowPolling();
    try {
      await api.brainflowStop();
    } catch (error) {
      console.warn('离开情绪识别步骤时停止 brainflow 失败:', error);
    }
  }
});

function nextStep() {
  if (activeStep.value < 4) {
    activeStep.value++;
  }
}

function prevStep() {
  if (activeStep.value > 0) {
    activeStep.value--;
  }
}

function beforeUpload(file: { name: string }) {
  // 模拟数据模式，允许任何文件类型
  return true;
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch((err) => {
      console.log(`Error attempting to enable full-screen mode: ${err.message}`);
    });
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }
};

// 监听全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement;
};

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  void loadSession();
  void loadModelOptions();
  startCarousel();
  void (async () => {
    if (activeStep.value !== 0) return;
    try {
      brainstimParadigmInfo.value = await api.brainstimParadigm();
    } catch (error) {
      console.warn('brainstim 范式预加载失败:', error);
    }
  })();
});

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  clearFeatureFlowTimers();
  void stopBrainflowPolling();
  // 清理轮播定时器
  if (carouselInterval.value) {
    clearInterval(carouselInterval.value);
    carouselInterval.value = null;
  }
});

// 生成粒子动画样式
const particleStyle = () => {
  const size = Math.random() * 5 + 2;
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    animationDuration: `${Math.random() * 10 + 10}s`,
    animationDelay: `${Math.random() * 5}s`,
    backgroundColor: `hsl(${Math.random() * 360}, 100%, 70%)`,
  };
};

const handleTsneImageError = () => {
  console.warn(`t-SNE图片加载失败`);
  ElMessage.warning("t-SNE图片加载失败，请检查图片路径");
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Exo+2:wght@300;400;600&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

/* 大屏内步骤内容区：可滚动、适配深色主题 */
.dash-step-content {
  min-height: 100%;
  overflow: visible;
  color: #e0e0ff;
  padding-right: 4px;
  padding-bottom: 16px;
}
.dash-step-content.scrollable {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}
.dash-step-content::-webkit-scrollbar {
  width: 4px;
}
.dash-step-content::-webkit-scrollbar-thumb {
  background: rgba(35, 152, 255, 0.35);
  border-radius: 4px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Exo 2', 'Orbitron', 'Microsoft YaHei', sans-serif;
}

.emotion-recognition-system {
  background: linear-gradient(135deg, #0a0f2b 0%, #1a2a6c 50%, #0a0f2b 100%);
  background-size: 400% 400%;
  animation: gradientBG 15s ease infinite;
  min-height: 100vh;
  overflow-x: hidden;
  color: #e0e0ff;
  position: relative;
  padding: 20px;
  z-index: 10;
}

@keyframes gradientBG {
  0% { background-position: 0% 50% }
  50% { background-position: 100% 50% }
  100% { background-position: 0% 50% }
}

/* 网格背景效果 */
.emotion-recognition-system::before {
  content: "";
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(12, 20, 69, 0.2) 1px, transparent 1px),
    linear-gradient(90deg, rgba(12, 20, 69, 0.2) 1px, transparent 1px);
  background-size: 30px 30px;
  z-index: -1;
  pointer-events: none;
}

/* 头部样式 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 140px;
  background: linear-gradient(90deg, rgba(10, 25, 60, 0.9) 0%, rgba(18, 40, 120, 0.9) 100%);
  border-radius: 15px;
  padding: 20px 30px;
  margin: 20px 0;
  box-shadow: 0 10px 30px rgba(0, 0, 60, 0.6), 0 0 30px rgba(64, 128, 255, 0.3);
  border: 1px solid rgba(64, 128, 255, 0.3);
  position: relative;
  overflow: hidden;
  z-index: 10;
  transform: translateZ(10px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.header:hover {
  transform: translateZ(20px);
  box-shadow: 0 15px 40px rgba(0, 0, 60, 0.8), 0 0 40px rgba(64, 128, 255, 0.5);
}

.header::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 200%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(64, 128, 255, 0.1) 50%,
    transparent 100%);
  animation: scanline 6s linear infinite;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 11;
}

@keyframes scanline {
  0% { transform: translateX(0); }
  100% { transform: translateX(100%); }
}

.title-logo {
  display: flex;
  align-items: center;
  justify-content: start;
  z-index: 1;
}

.logo {
  width: 70px;
  height: 70px;
  margin-right: 25px;
  filter: drop-shadow(0 0 10px rgba(64, 128, 255, 0.7));
  animation: pulse 3s infinite;
  transform: translateZ(5px);
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(1); opacity: 0.9; }
}

.title {
  color: #fff;
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 2px;
  text-shadow: 0 0 20px rgba(64, 128, 255, 0.8);
  background: linear-gradient(to right, #a0d2ff, #7b68ee, #4e54c8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transform: translateZ(5px);
  position: relative;
  z-index: 10;
}

.cyberpunk-title {
  position: relative;
  overflow: hidden;
}

.title-text {
  background: linear-gradient(45deg, #00d4ff, #4b6cb7, #ff6b6b, #00d4ff);
  background-size: 300% 300%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: title-gradient-flow 4s ease-in-out infinite;
  font-size: 38px;
  font-weight: 900;
  letter-spacing: 3px;
  text-shadow: 
    0 0 30px rgba(0, 212, 255, 0.8),
    0 0 60px rgba(0, 212, 255, 0.4),
    0 0 90px rgba(0, 212, 255, 0.2);
  position: relative;
  z-index: 2;
}

@keyframes title-gradient-flow {
  0%, 100% {
    background-position: 0% 50%;
  }
  25% {
    background-position: 100% 50%;
  }
  50% {
    background-position: 100% 100%;
  }
  75% {
    background-position: 0% 100%;
  }
}

.title-glow-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(ellipse at center, rgba(0, 212, 255, 0.3) 0%, transparent 70%);
  animation: title-glow-pulse 3s ease-in-out infinite;
  pointer-events: none;
  z-index: 1;
}

@keyframes title-glow-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

.title-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 3;
}

.title-particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #00d4ff;
  border-radius: 50%;
  animation: title-particle-float 6s infinite linear;
  opacity: 0.7;
}

.title-particle:nth-child(odd) {
  background: #4b6cb7;
  animation-duration: 8s;
}

.title-particle:nth-child(3n) {
  background: #ff6b6b;
  animation-duration: 10s;
}

.title-particle:nth-child(1) { left: 10%; animation-delay: 0s; }
.title-particle:nth-child(2) { left: 20%; animation-delay: 1s; }
.title-particle:nth-child(3) { left: 30%; animation-delay: 2s; }
.title-particle:nth-child(4) { left: 40%; animation-delay: 3s; }
.title-particle:nth-child(5) { left: 50%; animation-delay: 4s; }
.title-particle:nth-child(6) { left: 60%; animation-delay: 5s; }
.title-particle:nth-child(7) { left: 70%; animation-delay: 0s; }
.title-particle:nth-child(8) { left: 80%; animation-delay: 1s; }
.title-particle:nth-child(9) { left: 90%; animation-delay: 2s; }
.title-particle:nth-child(10) { left: 15%; animation-delay: 3s; }
.title-particle:nth-child(11) { left: 25%; animation-delay: 4s; }
.title-particle:nth-child(12) { left: 35%; animation-delay: 5s; }

@keyframes title-particle-float {
  0% {
    transform: translateY(100px) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 0.8;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-50px) translateX(50px);
    opacity: 0;
  }
}

.fullscreen-btn {
  background: linear-gradient(135deg, #4e54c8, #8f94fb);
  border: none;
  border-radius: 12px;
  padding: 12px 25px;
  font-weight: bold;
  letter-spacing: 1px;
  box-shadow: 0 5px 15px rgba(78, 84, 200, 0.5), 0 0 15px rgba(143, 148, 251, 0.5);
  transition: all 0.3s ease;
  z-index: 1;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 8px;
  transform: translateZ(5px);
  font-size: 16px;
}

.fullscreen-btn::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent);
  transition: 0.5s;
}

.fullscreen-btn:hover {
  transform: translateY(-3px) translateZ(10px);
  box-shadow: 0 8px 20px rgba(78, 84, 200, 0.7), 0 0 20px rgba(143, 148, 251, 0.8);
  background: linear-gradient(135deg, #8f94fb, #4e54c8);
}

.fullscreen-btn:hover::before {
  left: 100%;
}

.fullscreen-btn:active {
  transform: translateY(1px) scale(0.98);
}

.fullscreen-btn i {
  transition: transform 0.3s ease;
}

.fullscreen-btn:hover i {
  transform: scale(1.2);
}

/* 酷炫导航栏样式 */
.steps {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 180px;
  margin: 20px 0;
  position: relative;
  z-index: 10;
}

.cyber-nav {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, rgba(10, 15, 40, 0.9) 0%, rgba(20, 35, 80, 0.9) 100%);
  border-radius: 20px;
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 
    0 15px 35px rgba(0, 0, 60, 0.8),
    0 0 30px rgba(64, 128, 255, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  overflow: hidden;
  transform: translateZ(10px);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.cyber-nav:hover {
  transform: translateZ(20px) scale(1.02);
  box-shadow: 
    0 20px 45px rgba(0, 0, 60, 0.9),
    0 0 40px rgba(64, 128, 255, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.nav-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  position: relative;
  z-index: 2;
  padding: 20px;
}

.nav-step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 20px 15px;
  border-radius: 15px;
  background: linear-gradient(145deg, rgba(15, 25, 60, 0.8), rgba(25, 40, 100, 0.8));
  border: 2px solid rgba(64, 128, 255, 0.2);
  box-shadow: 
    0 8px 20px rgba(0, 0, 40, 0.6),
    0 0 15px rgba(64, 128, 255, 0.2);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  min-width: 160px;
  transform: translateZ(5px);
  overflow: hidden;
}

.nav-step:hover {
  transform: translateZ(15px) scale(1.05);
  box-shadow: 
    0 12px 25px rgba(0, 0, 40, 0.8),
    0 0 25px rgba(64, 128, 255, 0.4);
  border-color: rgba(64, 128, 255, 0.5);
}

.nav-step.active {
  background: linear-gradient(145deg, rgba(78, 84, 200, 0.9), rgba(143, 148, 251, 0.9));
  border-color: #8f94fb;
  box-shadow: 
    0 15px 30px rgba(78, 84, 200, 0.6),
    0 0 30px rgba(143, 148, 251, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transform: translateZ(20px) scale(1.1);
}

.nav-step.completed {
  background: linear-gradient(145deg, rgba(94, 252, 232, 0.2), rgba(94, 252, 232, 0.1));
  border-color: #5efce8;
  box-shadow: 
    0 10px 25px rgba(94, 252, 232, 0.3),
    0 0 20px rgba(94, 252, 232, 0.4);
}

.step-number {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 35px;
  height: 35px;
  background: linear-gradient(135deg, #4e54c8, #8f94fb);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: white;
  box-shadow: 0 0 15px rgba(143, 148, 251, 0.7);
  z-index: 3;
}

.nav-step.active .step-number {
  background: linear-gradient(135deg, #8f94fb, #4e54c8);
  box-shadow: 0 0 20px rgba(143, 148, 251, 0.9);
  animation: pulse-glow 2s infinite;
}

.nav-step.completed .step-number {
  background: linear-gradient(135deg, #5efce8, #00d4aa);
  box-shadow: 0 0 20px rgba(94, 252, 232, 0.8);
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(143, 148, 251, 0.9); }
  50% { box-shadow: 0 0 30px rgba(143, 148, 251, 1.2); }
}

.step-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  z-index: 2;
}

.step-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(64, 128, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  border: 2px solid rgba(64, 128, 255, 0.3);
}

.step-icon i {
  font-size: 24px;
  color: #8a9bb4;
  transition: all 0.3s ease;
}

.nav-step:hover .step-icon {
  background: rgba(64, 128, 255, 0.3);
  border-color: rgba(64, 128, 255, 0.6);
  transform: scale(1.1);
}

.nav-step:hover .step-icon i {
  color: #a0d2ff;
  text-shadow: 0 0 10px rgba(160, 210, 255, 0.8);
}

.nav-step.active .step-icon {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
}

.nav-step.active .step-icon i {
  color: white;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
  animation: icon-float 2s ease-in-out infinite;
}

@keyframes icon-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.nav-step.completed .step-icon {
  background: rgba(94, 252, 232, 0.2);
  border-color: #5efce8;
}

.nav-step.completed .step-icon i {
  color: #5efce8;
}

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #c0c9ff;
  text-align: center;
  transition: all 0.3s ease;
  letter-spacing: 1px;
}

.nav-step:hover .step-title {
  color: #a0d2ff;
  text-shadow: 0 0 8px rgba(160, 210, 255, 0.6);
}

.nav-step.active .step-title {
  color: white;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
  font-weight: 700;
}

.nav-step.completed .step-title {
  color: #5efce8;
  text-shadow: 0 0 8px rgba(94, 252, 232, 0.6);
}

.step-subtitle {
  font-size: 10px;
  color: #6d7d9c;
  text-align: center;
  transition: all 0.3s ease;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.nav-step:hover .step-subtitle {
  color: #8a9bb4;
}

.nav-step.active .step-subtitle {
  color: rgba(255, 255, 255, 0.8);
}

.nav-step.completed .step-subtitle {
  color: rgba(94, 252, 232, 0.8);
}

.step-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, rgba(64, 128, 255, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.nav-step:hover .step-glow {
  opacity: 1;
}

.nav-step.active .step-glow {
  opacity: 1;
  background: radial-gradient(circle at center, rgba(143, 148, 251, 0.2) 0%, transparent 70%);
  animation: glow-pulse 2s infinite;
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.step-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle-dot {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #64a0ff;
  border-radius: 50%;
  opacity: 0;
  animation: particle-float 3s infinite;
}

.nav-step.active .particle-dot {
  background: #8f94fb;
  animation: particle-float 2s infinite;
}

.nav-step.completed .particle-dot {
  background: #5efce8;
  animation: particle-float 2.5s infinite;
}

.particle-dot:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
.particle-dot:nth-child(2) { top: 30%; right: 15%; animation-delay: 0.5s; }
.particle-dot:nth-child(3) { bottom: 25%; left: 20%; animation-delay: 1s; }
.particle-dot:nth-child(4) { bottom: 35%; right: 10%; animation-delay: 1.5s; }
.particle-dot:nth-child(5) { top: 50%; left: 5%; animation-delay: 2s; }
.particle-dot:nth-child(6) { top: 60%; right: 5%; animation-delay: 2.5s; }

@keyframes particle-float {
  0% {
    transform: translateY(0) scale(0);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  80% {
    opacity: 1;
  }
  100% {
    transform: translateY(-20px) scale(1);
    opacity: 0;
  }
}

.nav-connector {
  position: relative;
  width: 120px;
  height: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.connector-line {
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, rgba(64, 128, 255, 0.3), rgba(64, 128, 255, 0.1));
  border-radius: 1px;
  position: relative;
  overflow: hidden;
}

.nav-connector.active .connector-line {
  background: linear-gradient(90deg, #5efce8, #64a0ff, #5efce8);
  box-shadow: 0 0 10px rgba(94, 252, 232, 0.6);
}

.connector-pulse {
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #5efce8, transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.nav-connector.active .connector-pulse {
  animation: pulse-flow 2s infinite;
}

@keyframes pulse-flow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.connector-data {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 8px;
  color: #6d7d9c;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.nav-connector.active .connector-data {
  opacity: 1;
  color: #5efce8;
  text-shadow: 0 0 5px rgba(94, 252, 232, 0.6);
}

.connector-data span:first-child {
  font-weight: bold;
  font-size: 10px;
}

.nav-bg-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.bg-circuit {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(90deg, rgba(64, 128, 255, 0.1) 1px, transparent 1px),
    linear-gradient(rgba(64, 128, 255, 0.1) 1px, transparent 1px);
  background-size: 20px 20px;
  animation: circuit-move 20s linear infinite;
}

@keyframes circuit-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(20px, 20px); }
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(64, 128, 255, 0.1) 1px, transparent 1px),
    radial-gradient(circle at 75% 75%, rgba(64, 128, 255, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: grid-pulse 4s ease-in-out infinite;
}

@keyframes grid-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.bg-scanner {
  position: absolute;
  top: 0;
  left: -100%;
  width: 200%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(64, 128, 255, 0.1) 50%,
    transparent 100%);
  animation: scanner-sweep 8s linear infinite;
}

@keyframes scanner-sweep {
  0% { transform: translateX(0); }
  100% { transform: translateX(50%); }
}

/* 数据处理流程图 */
.process-flow-container {
  background: linear-gradient(135deg, rgba(10, 15, 40, 0.95) 0%, rgba(20, 30, 80, 0.95) 100%);
  border-radius: 20px;
  padding: 30px;
  margin: 20px 0;
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(64, 128, 255, 0.2);
  backdrop-filter: blur(10px);
  z-index: 10;
}

.process-flow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  padding: 20px 0;
}

.process-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
  position: relative;
}

.step-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  background: rgba(30, 40, 80, 0.7);
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 0 0 15px rgba(64, 128, 255, 0.2);
  transition: all 0.5s ease;
}

.step-icon i {
  font-size: 28px;
  color: #8a9bb4;
  transition: all 0.5s ease;
}

.step-label {
  font-size: 16px;
  font-weight: 500;
  color: #8a9bb4;
  text-align: center;
  transition: all 0.5s ease;
}

/* 活动状态 */
.process-step.active .step-icon {
  background: rgba(78, 84, 200, 0.8);
  border: 2px solid #8f94fb;
  box-shadow: 0 0 20px rgba(143, 148, 251, 0.6);
  transform: scale(1.1);
}

.process-step.active .step-icon i {
  color: #fff;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.process-step.active .step-label {
  color: #a0d2ff;
  text-shadow: 0 0 8px rgba(160, 210, 255, 0.6);
}

/* 已完成状态 */
.process-step.completed .step-icon {
  background: rgba(94, 252, 232, 0.2);
  border: 2px solid #5efce8;
  box-shadow: 0 0 20px rgba(94, 252, 232, 0.4);
}

.process-step.completed .step-label {
  color: #5efce8;
}

/* 连接线 */
.process-connector {
  flex: 1;
  height: 4px;
  background: rgba(64, 128, 255, 0.2);
  position: relative;
  overflow: hidden;
  border-radius: 2px;
  margin: 0 10px;
}

.process-connector::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #5efce8, transparent);
  transition: all 1s ease;
  transform: translateX(-100%);
}

.process-connector.active::before {
  animation: connectorFlow 1.5s infinite;
}

@keyframes connectorFlow {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(200%);
  }
}

/* ===== 全新的绚丽子导航栏样式 ===== */
.spectacular-nav {
  position: relative;
  background: linear-gradient(135deg, rgba(20, 30, 80, 0.9), rgba(40, 20, 100, 0.9));
  border-radius: 20px;
  padding: 30px;
  margin: 20px 0;
  box-shadow: 
    0 15px 35px rgba(0, 0, 0, 0.8),
    0 0 30px rgba(255, 20, 147, 0.4),
    0 0 60px rgba(0, 255, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 2px solid;
  border-image: linear-gradient(45deg, #ff1493, #00ffff, #ff1493) 1;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.spectacular-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 10;
  gap: 20px;
}

.spectacular-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  cursor: pointer;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 120px;
}

.spectacular-orb {
  position: relative;
  width: 80px;
  height: 80px;
  margin-bottom: 15px;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(255, 20, 147, 0.8), rgba(0, 255, 255, 0.6));
  box-shadow: 
    0 0 30px rgba(255, 20, 147, 0.6),
    0 0 60px rgba(0, 255, 255, 0.4),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
  animation: orb-float 3s ease-in-out infinite;
}

@keyframes orb-float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(180deg); }
}

.orb-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(circle, #fff, rgba(255, 20, 147, 0.8));
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  animation: core-pulse 2s ease-in-out infinite;
}

@keyframes core-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.2); }
}

.orb-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 2px solid transparent;
  animation: ring-rotate 4s linear infinite;
}

.ring-1 {
  width: 60px;
  height: 60px;
  transform: translate(-50%, -50%);
  border-top-color: #ff1493;
  border-right-color: #00ffff;
  animation-duration: 3s;
}

.ring-2 {
  width: 70px;
  height: 70px;
  transform: translate(-50%, -50%);
  border-bottom-color: #ff1493;
  border-left-color: #00ffff;
  animation-duration: 4s;
  animation-direction: reverse;
}

.ring-3 {
  width: 80px;
  height: 80px;
  transform: translate(-50%, -50%);
  border-top-color: #00ffff;
  border-left-color: #ff1493;
  animation-duration: 5s;
}

@keyframes ring-rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.orb-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.orb-particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fff;
  border-radius: 50%;
  animation: particle-orbit 3s linear infinite;
}

.orb-particle:nth-child(1) { top: 10%; left: 50%; animation-delay: 0s; }
.orb-particle:nth-child(2) { top: 20%; right: 10%; animation-delay: 0.5s; }
.orb-particle:nth-child(3) { bottom: 20%; left: 10%; animation-delay: 1s; }
.orb-particle:nth-child(4) { bottom: 10%; left: 50%; animation-delay: 1.5s; }
.orb-particle:nth-child(5) { top: 50%; left: 10%; animation-delay: 2s; }
.orb-particle:nth-child(6) { top: 50%; right: 10%; animation-delay: 2.5s; }
.orb-particle:nth-child(7) { top: 30%; left: 20%; animation-delay: 0.3s; }
.orb-particle:nth-child(8) { bottom: 30%; right: 20%; animation-delay: 0.8s; }

@keyframes particle-orbit {
  0% { transform: rotate(0deg) translateX(30px) rotate(0deg); }
  100% { transform: rotate(360deg) translateX(30px) rotate(-360deg); }
}

.spectacular-content {
  text-align: center;
  z-index: 5;
}

.spectacular-icon {
  font-size: 24px;
  color: #fff;
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.spectacular-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 4px;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
  transition: all 0.3s ease;
}

.spectacular-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  text-shadow: 0 0 5px rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
}

.spectacular-aura {
  position: absolute;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 20, 147, 0.2), transparent 70%);
  opacity: 0;
  transition: all 0.5s ease;
  pointer-events: none;
}

.spectacular-energy {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100px;
  height: 100px;
  pointer-events: none;
}

.energy-beam {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 40px;
  background: linear-gradient(to top, transparent, #ff1493, #00ffff, transparent);
  transform-origin: center bottom;
  opacity: 0;
  transition: all 0.3s ease;
}

.energy-beam:nth-child(1) { transform: translate(-50%, -50%) rotate(0deg); }
.energy-beam:nth-child(2) { transform: translate(-50%, -50%) rotate(30deg); }
.energy-beam:nth-child(3) { transform: translate(-50%, -50%) rotate(60deg); }
.energy-beam:nth-child(4) { transform: translate(-50%, -50%) rotate(90deg); }
.energy-beam:nth-child(5) { transform: translate(-50%, -50%) rotate(120deg); }
.energy-beam:nth-child(6) { transform: translate(-50%, -50%) rotate(150deg); }
.energy-beam:nth-child(7) { transform: translate(-50%, -50%) rotate(180deg); }
.energy-beam:nth-child(8) { transform: translate(-50%, -50%) rotate(210deg); }
.energy-beam:nth-child(9) { transform: translate(-50%, -50%) rotate(240deg); }
.energy-beam:nth-child(10) { transform: translate(-50%, -50%) rotate(270deg); }
.energy-beam:nth-child(11) { transform: translate(-50%, -50%) rotate(300deg); }
.energy-beam:nth-child(12) { transform: translate(-50%, -50%) rotate(330deg); }

/* 活动状态 */
.spectacular-step.active .spectacular-orb {
  transform: scale(1.2);
  box-shadow: 
    0 0 50px rgba(255, 20, 147, 0.8),
    0 0 100px rgba(0, 255, 255, 0.6),
    inset 0 0 30px rgba(255, 255, 255, 0.2);
}

.spectacular-step.active .orb-core {
  background: radial-gradient(circle, #fff, #ff1493);
  box-shadow: 0 0 30px rgba(255, 255, 255, 1);
}

.spectacular-step.active .spectacular-icon {
  color: #ff1493;
  text-shadow: 0 0 15px rgba(255, 20, 147, 0.8);
  transform: scale(1.1);
}

.spectacular-step.active .spectacular-title {
  color: #ff1493;
  text-shadow: 0 0 12px rgba(255, 20, 147, 0.8);
}

.spectacular-step.active .spectacular-subtitle {
  color: rgba(255, 20, 147, 0.8);
}

.spectacular-step.active .spectacular-aura {
  opacity: 1;
  animation: aura-pulse 2s ease-in-out infinite;
}

@keyframes aura-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.6; }
}

.spectacular-step.active .energy-beam {
  opacity: 1;
  animation: beam-rotate 3s linear infinite;
}

@keyframes beam-rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg) scale(1); }
  50% { transform: translate(-50%, -50%) rotate(180deg) scale(1.2); }
  100% { transform: translate(-50%, -50%) rotate(360deg) scale(1); }
}

/* 已完成状态 */
.spectacular-step.completed .spectacular-orb {
  background: radial-gradient(circle at 30% 30%, rgba(0, 255, 255, 0.8), rgba(255, 20, 147, 0.6));
  box-shadow: 
    0 0 40px rgba(0, 255, 255, 0.6),
    0 0 80px rgba(255, 20, 147, 0.4);
}

.spectacular-step.completed .orb-core {
  background: radial-gradient(circle, #fff, #00ffff);
}

.spectacular-step.completed .spectacular-icon {
  color: #00ffff;
  text-shadow: 0 0 15px rgba(0, 255, 255, 0.8);
}

.spectacular-step.completed .spectacular-title {
  color: #00ffff;
  text-shadow: 0 0 12px rgba(0, 255, 255, 0.8);
}

.spectacular-step.completed .spectacular-subtitle {
  color: rgba(0, 255, 255, 0.8);
}

/* 连接器样式 */
.spectacular-connector {
  flex: 1;
  height: 6px;
  position: relative;
  background: linear-gradient(90deg, rgba(255, 20, 147, 0.3), rgba(0, 255, 255, 0.3));
  border-radius: 3px;
  margin: 0 15px;
  overflow: hidden;
}

.connector-core {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.connector-flow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #ff1493, #00ffff, #ff1493);
  transform: translateX(-100%);
  transition: transform 0.5s ease;
}

.connector-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.flow-particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #fff;
  border-radius: 50%;
  animation: flow-particle-move 2s linear infinite;
}

.flow-particle:nth-child(1) { top: 20%; animation-delay: 0s; }
.flow-particle:nth-child(2) { top: 40%; animation-delay: 0.4s; }
.flow-particle:nth-child(3) { top: 60%; animation-delay: 0.8s; }
.flow-particle:nth-child(4) { top: 80%; animation-delay: 1.2s; }
.flow-particle:nth-child(5) { top: 50%; animation-delay: 1.6s; }

@keyframes flow-particle-move {
  0% { left: -10px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
}

.connector-data-stream {
  position: absolute;
  top: -30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.6);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.spectacular-connector.active .connector-core {
  animation: connector-core-flow 2s infinite;
}

.spectacular-connector.active .connector-flow {
  animation: connector-flow-animation 1.5s infinite;
}

.spectacular-connector.active .flow-particle {
  animation: flow-particle-move 1s linear infinite;
}

.spectacular-connector.active .connector-data-stream {
  opacity: 1;
  color: #fff;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
}

@keyframes connector-core-flow {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes connector-flow-animation {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* 背景装饰元素 */
.spectacular-bg-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.bg-neural-network {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 20% 20%, rgba(255, 20, 147, 0.1) 1px, transparent 1px),
    radial-gradient(circle at 80% 80%, rgba(0, 255, 255, 0.1) 1px, transparent 1px);
  background-size: 30px 30px;
  animation: neural-network-move 15s linear infinite;
}

@keyframes neural-network-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(30px, 30px); }
}

.bg-quantum-field {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at 30% 30%, rgba(255, 20, 147, 0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 70%, rgba(0, 255, 255, 0.05) 0%, transparent 50%);
  animation: quantum-field-pulse 8s ease-in-out infinite;
}

@keyframes quantum-field-pulse {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

.bg-hologram {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    linear-gradient(45deg, transparent 40%, rgba(255, 20, 147, 0.1) 50%, transparent 60%),
    linear-gradient(-45deg, transparent 40%, rgba(0, 255, 255, 0.1) 50%, transparent 60%);
  animation: hologram-sweep 6s linear infinite;
}

@keyframes hologram-sweep {
  0% { transform: translateX(-100%) rotate(0deg); }
  100% { transform: translateX(100%) rotate(360deg); }
}

.bg-energy-waves {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.energy-wave {
  position: absolute;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(255, 20, 147, 0.3), rgba(0, 255, 255, 0.3), transparent);
  animation: energy-wave-flow 4s linear infinite;
}

.energy-wave:nth-child(1) { top: 20%; animation-delay: 0s; }
.energy-wave:nth-child(2) { top: 50%; animation-delay: 1.3s; }
.energy-wave:nth-child(3) { top: 80%; animation-delay: 2.6s; }

@keyframes energy-wave-flow {
  0% { transform: translateX(-100%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(100%); opacity: 0; }
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .spectacular-container {
    gap: 15px;
  }
  
  .spectacular-step {
    min-width: 100px;
  }
  
  .spectacular-orb {
    width: 70px;
    height: 70px;
  }
  
  .spectacular-title {
    font-size: 14px;
  }
  
  .spectacular-subtitle {
    font-size: 11px;
  }
}

@media (max-width: 768px) {
  .spectacular-nav {
    padding: 20px;
  }
  
  .spectacular-container {
    flex-direction: column;
    gap: 20px;
  }
  
  .spectacular-step {
    flex-direction: row;
    width: 100%;
    max-width: 300px;
    padding: 15px;
    gap: 15px;
  }
  
  .spectacular-content {
    text-align: left;
  }
  
  .spectacular-orb {
    width: 60px;
    height: 60px;
    margin-bottom: 0;
  }
  
  .spectacular-connector {
    width: 4px;
    height: 40px;
    margin: 0;
    transform: rotate(90deg);
  }
  
  .connector-data-stream {
    display: none;
  }
}

/* 内容区域 */
.content {
  position: relative;
  padding: 30px;
  min-height: 600px;
  background: rgba(10, 15, 40, 0.7);
  border-radius: 15px;
  margin: 20px 0;
  box-shadow: 0 10px 30px rgba(0, 0, 40, 0.7), 0 0 30px rgba(64, 128, 255, 0.3);
  border: 1px solid rgba(64, 128, 255, 0.2);
  backdrop-filter: blur(5px);
  z-index: 10;
  transform: translateZ(5px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.content:hover {
  transform: translateZ(10px);
  box-shadow: 0 15px 40px rgba(0, 0, 40, 0.8), 0 0 40px rgba(64, 128, 255, 0.5);
}

.section-title {
  font-size: 24px;
  margin-bottom: 25px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(64, 128, 255, 0.3);
  color: #a0d2ff;
  text-shadow: 0 0 10px rgba(64, 128, 255, 0.5);
  letter-spacing: 1px;
  position: relative;
  transform: translateZ(5px);
}

.section-title::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 120px;
  height: 2px;
  background: linear-gradient(90deg, #4e54c8, #8f94fb);
  box-shadow: 0 0 10px rgba(143, 148, 251, 0.7);
}

.el-row {
  margin-bottom: 25px;
}

/* 选项面板 */
.options {
  background: rgba(15, 25, 60, 0.6);
  padding: 25px;
  border-radius: 12px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  box-shadow: 0 5px 15px rgba(0, 0, 30, 0.5);
  height: 100%;
  transform: translateZ(5px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.options:hover {
  transform: translateZ(10px);
  box-shadow: 0 8px 20px rgba(0, 0, 30, 0.7), 0 0 20px rgba(64, 128, 255, 0.3);
}

.panel-title {
  font-size: 20px;
  margin-bottom: 20px;
  color: #8f94fb;
  text-shadow: 0 0 8px rgba(143, 148, 251, 0.5);
  position: relative;
  display: inline-block;
}

.panel-title::after {
  content: "";
  position: absolute;
  bottom: -5px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #4e54c8, #8f94fb);
  box-shadow: 0 0 8px rgba(143, 148, 251, 0.7);
}

.radio-group-vertical {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.el-radio {
  margin: 8px 0;
}

.el-radio__label {
  color: #c0c9ff;
  font-size: 16px;
}

.el-radio__input.is-checked + .el-radio__label {
  color: #8f94fb;
  text-shadow: 0 0 8px rgba(143, 148, 251, 0.7);
}

.el-radio__input.is-checked .el-radio__inner {
  background: #4e54c8;
  border-color: #8f94fb;
  box-shadow: 0 0 8px rgba(143, 148, 251, 0.7);
}

/* 可视化区域 */
.visualization {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
  background: rgba(15, 25, 60, 0.6);
  border: 1px solid rgba(64, 128, 255, 0.2);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 30, 0.5);
  position: relative;
  overflow: hidden;
  transform: translateZ(5px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.visualization:hover {
  transform: translateZ(10px);
  box-shadow: 0 8px 20px rgba(0, 0, 30, 0.7), 0 0 20px rgba(64, 128, 255, 0.3);
}

.visualization::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    linear-gradient(90deg, transparent 49%, rgba(64, 128, 255, 0.1) 50%, transparent 51%),
    linear-gradient(transparent 49%, rgba(64, 128, 255, 0.1) 50%, transparent 51%);
  background-size: 20px 20px;
  z-index: 0;
}

.el-image {
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  z-index: 1;
  max-width: 100%;
}

/* 特征选择栏 - 内部版本（在流程图内） */
.feature-selection-inner {
  width: 100%;
  margin-bottom: 25px;
  position: relative;
  z-index: 10;
}

.feature-selection-inner .feature-selection-container {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  padding: 18px 22px;
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.25) 0%, 
    rgba(78, 84, 200, 0.2) 50%, 
    rgba(143, 148, 251, 0.25) 100%);
  border-radius: 14px;
  border: 1px solid rgba(64, 128, 255, 0.5);
  backdrop-filter: blur(15px);
  box-shadow: 
    0 6px 25px rgba(45, 56, 138, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 25px rgba(143, 148, 251, 0.3),
    inset 0 0 30px rgba(143, 148, 251, 0.1);
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 通用特征选择容器样式 */
.feature-selection-container {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  padding: 20px 25px;
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.15) 0%, 
    rgba(78, 84, 200, 0.1) 50%, 
    rgba(143, 148, 251, 0.15) 100%);
  border-radius: 16px;
  border: 1px solid rgba(64, 128, 255, 0.3);
  backdrop-filter: blur(15px);
  box-shadow: 
    0 8px 32px rgba(45, 56, 138, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 0 20px rgba(143, 148, 251, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-selection-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent);
  transition: left 0.6s ease;
}

.feature-selection-container:hover::before {
  left: 100%;
}

.feature-selection-container:hover {
  border-color: rgba(143, 148, 251, 0.6);
  box-shadow: 
    0 12px 40px rgba(45, 56, 138, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 30px rgba(143, 148, 251, 0.4);
  transform: translateY(-2px);
}

/* 标签样式 */
.feature-label-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(78, 84, 200, 0.2), rgba(143, 148, 251, 0.2));
  border-radius: 10px;
  border: 1px solid rgba(143, 148, 251, 0.3);
  box-shadow: 0 4px 15px rgba(78, 84, 200, 0.2);
}

.feature-icon {
  font-size: 18px;
  color: #8f94fb;
  text-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    text-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
    transform: scale(1);
  }
  50% {
    text-shadow: 0 0 20px rgba(143, 148, 251, 1), 0 0 30px rgba(143, 148, 251, 0.6);
    transform: scale(1.1);
  }
}

.feature-label {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.label-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(143, 148, 251, 0.3) 0%, transparent 70%);
  border-radius: 10px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.feature-label-wrapper:hover .label-glow {
  opacity: 1;
}

/* 下拉框容器 */
.select-wrapper {
  position: relative;
  flex: 1;
  max-width: 280px;
}

.select-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(143, 148, 251, 0.2) 0%, transparent 70%);
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
}

.select-wrapper:hover .select-glow {
  opacity: 1;
}

.select-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
  border-radius: 12px;
}

.select-particles .particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(143, 148, 251, 0.6);
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(143, 148, 251, 0.8);
  animation: float-particle 3s ease-in-out infinite;
}

.select-particles .particle:nth-child(1) {
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.select-particles .particle:nth-child(2) {
  top: 50%;
  left: 20%;
  animation-delay: 0.5s;
}

.select-particles .particle:nth-child(3) {
  top: 80%;
  left: 30%;
  animation-delay: 1s;
}

.select-particles .particle:nth-child(4) {
  top: 30%;
  right: 20%;
  animation-delay: 1.5s;
}

.select-particles .particle:nth-child(5) {
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.select-particles .particle:nth-child(6) {
  top: 10%;
  right: 10%;
  animation-delay: 2.5s;
}

@keyframes float-particle {
  0%, 100% {
    transform: translateY(0) translateX(0);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-10px) translateX(5px);
    opacity: 1;
  }
}


/* 下拉框样式 */
.feature-select {
  width: 100%;
  position: relative;
  z-index: 2;
  --el-select-input-focus-border-color: #8f94fb;
  --el-select-border-color-hover: #8f94fb;
}

.feature-select :deep(.el-input__wrapper) {
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.4) 0%, 
    rgba(78, 84, 200, 0.3) 100%);
  border: 2px solid rgba(143, 148, 251, 0.4);
  border-radius: 12px;
  box-shadow: 
    0 4px 15px rgba(45, 56, 138, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 15px rgba(143, 148, 251, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0 15px;
  height: 48px;
  position: relative;
  overflow: hidden;
}

/* 选中后的输入框样式增强 - 当有选中值时 */
.feature-select.feature-selected:not(.feature-select-de) :deep(.el-input__wrapper) {
  border-color: rgba(143, 148, 251, 0.7) !important;
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.5) 0%, 
    rgba(78, 84, 200, 0.4) 100%) !important;
  box-shadow: 
    0 6px 20px rgba(45, 56, 138, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 25px rgba(143, 148, 251, 0.5),
    inset 0 0 30px rgba(143, 148, 251, 0.1) !important;
  animation: selected-pulse 2s ease-in-out infinite;
}

@keyframes selected-pulse {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(45, 56, 138, 0.4),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 25px rgba(143, 148, 251, 0.5),
      inset 0 0 30px rgba(143, 148, 251, 0.1);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(45, 56, 138, 0.5),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 35px rgba(143, 148, 251, 0.7),
      inset 0 0 40px rgba(143, 148, 251, 0.2);
  }
}

/* DE选中后的特殊效果 */
.feature-select-de[data-selected="DE"] :deep(.el-input__wrapper) {
  border-color: rgba(255, 107, 107, 0.8);
  background: linear-gradient(135deg, 
    rgba(255, 107, 107, 0.15) 0%, 
    rgba(255, 215, 0, 0.1) 50%,
    rgba(255, 107, 107, 0.15) 100%);
  box-shadow: 
    0 6px 20px rgba(255, 107, 107, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(255, 107, 107, 0.6),
    0 0 40px rgba(255, 215, 0, 0.4),
    inset 0 0 35px rgba(255, 107, 107, 0.15);
  animation: selected-pulse-de 2s ease-in-out infinite;
}

@keyframes selected-pulse-de {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(255, 107, 107, 0.4),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 30px rgba(255, 107, 107, 0.6),
      0 0 40px rgba(255, 215, 0, 0.4),
      inset 0 0 35px rgba(255, 107, 107, 0.15);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(255, 107, 107, 0.5),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 40px rgba(255, 107, 107, 0.8),
      0 0 50px rgba(255, 215, 0, 0.6),
      inset 0 0 45px rgba(255, 107, 107, 0.2);
  }
}

.feature-select :deep(.el-input__wrapper:hover) {
  border-color: rgba(143, 148, 251, 0.8);
  box-shadow: 
    0 6px 20px rgba(45, 56, 138, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 25px rgba(143, 148, 251, 0.5);
  transform: translateY(-1px);
}

.feature-select :deep(.el-input__wrapper.is-focus) {
  border-color: #8f94fb;
  box-shadow: 
    0 8px 25px rgba(45, 56, 138, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(143, 148, 251, 0.7);
}

.feature-select :deep(.el-input__inner) {
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  height: 48px;
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  transition: all 0.3s ease;
}

/* 选中后的输入框字体优化 - 增强显示效果 */
.feature-select.feature-selected :deep(.el-input__inner) {
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1.8px;
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.4)) 
          drop-shadow(0 0 8px rgba(255, 255, 255, 0.2));
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* DE选中后的字体特殊优化 - 增强显示效果 */
.feature-select-de.feature-selected :deep(.el-input__inner) {
  font-weight: 800;
  font-size: 19px;
  letter-spacing: 2.5px;
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  filter: drop-shadow(0 0 10px rgba(255, 107, 107, 0.9)) 
          drop-shadow(0 0 18px rgba(255, 215, 0, 0.7))
          drop-shadow(0 0 25px rgba(255, 142, 83, 0.5));
}

/* 其他选项渐变样式 - 输入框显示（当选中PSD、DASM、RASM、DCAU时） */
.feature-select:not(.feature-select-de) :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #4e54c8 0%, 
    #8f94fb 25%, 
    #a8b5ff 50%, 
    #8f94fb 75%, 
    #4e54c8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
}

/* 选中后的其他选项字体优化 - 增强显示效果 */
.feature-select.feature-selected:not(.feature-select-de) :deep(.el-input__inner) {
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1.8px;
  filter: drop-shadow(0 0 5px rgba(143, 148, 251, 0.7)) 
          drop-shadow(0 0 10px rgba(143, 148, 251, 0.5))
          drop-shadow(0 0 15px rgba(143, 148, 251, 0.3));
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 根据选中的值设置不同的渐变颜色 */
.feature-select[data-selected="PSD"]:not(.feature-select-de) :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #4e54c8 0%, 
    #8f94fb 30%, 
    #a8b5ff 60%, 
    #8f94fb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
}

.feature-select[data-selected="DASM"]:not(.feature-select-de) :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #667eea 0%, 
    #764ba2 50%, 
    #667eea 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
}

.feature-select[data-selected="RASM"]:not(.feature-select-de) :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #f093fb 0%, 
    #f5576c 50%, 
    #f093fb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
}

.feature-select[data-selected="DCAU"]:not(.feature-select-de) :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #4facfe 0%, 
    #00f2fe 50%, 
    #4facfe 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
}

@keyframes gradient-shift-other {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

/* DE炫彩样式 - 输入框显示 */
.feature-select-de :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de-input 4s ease infinite;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1.5px;
  position: relative;
  filter: drop-shadow(0 0 8px rgba(255, 107, 107, 0.8)) 
          drop-shadow(0 0 15px rgba(255, 215, 0, 0.6))
          drop-shadow(0 0 20px rgba(255, 142, 83, 0.4));
  text-transform: uppercase;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  height: 48px;
  line-height: 48px;
  transition: all 0.3s ease;
}

/* DE选中后的字体优化 */
.feature-select-de.feature-selected :deep(.el-input__inner) {
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 2px;
  filter: drop-shadow(0 0 10px rgba(255, 107, 107, 0.9)) 
          drop-shadow(0 0 18px rgba(255, 215, 0, 0.7))
          drop-shadow(0 0 25px rgba(255, 142, 83, 0.5));
}

.feature-select-de :deep(.el-input__wrapper) {
  box-shadow: 
    0 4px 15px rgba(45, 56, 138, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 20px rgba(255, 107, 107, 0.4),
    0 0 30px rgba(255, 215, 0, 0.3) !important;
  border-color: rgba(255, 107, 107, 0.6) !important;
}

.feature-select-de :deep(.el-input__wrapper.is-focus) {
  box-shadow: 
    0 8px 25px rgba(45, 56, 138, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(255, 107, 107, 0.6),
    0 0 40px rgba(255, 215, 0, 0.5) !important;
  border-color: rgba(255, 107, 107, 0.9) !important;
}

.feature-select-de :deep(.el-input__inner)::before {
  content: "DE";
  position: absolute;
  left: 0;
  top: 0;
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de-input 4s ease infinite reverse;
  z-index: -1;
  filter: blur(4px);
  opacity: 0.6;
  text-transform: uppercase;
}

.feature-select-de :deep(.el-input__inner)::after {
  content: "DE";
  position: absolute;
  left: 0;
  top: 0;
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de-input 4s ease infinite;
  z-index: -2;
  filter: blur(8px);
  opacity: 0.4;
  transform: translate(2px, 2px);
  text-transform: uppercase;
}

@keyframes gradient-shift-de-input {
  0%, 100% {
    background-position: 0% 50%;
  }
  25% {
    background-position: 50% 0%;
  }
  50% {
    background-position: 100% 50%;
  }
  75% {
    background-position: 50% 100%;
  }
}

@keyframes gradient-shift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.feature-select :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
}

.feature-select :deep(.el-select__caret) {
  color: #8f94fb;
  font-size: 16px;
  transition: transform 0.3s ease;
  filter: drop-shadow(0 0 4px rgba(143, 148, 251, 0.8));
}

.feature-select :deep(.el-select__caret.is-reverse) {
  transform: rotate(180deg);
}

/* 下拉选项样式 */
.feature-select-dropdown {
  background: linear-gradient(135deg, 
    rgba(30, 35, 80, 0.98) 0%, 
    rgba(45, 56, 138, 0.98) 100%);
  border: 1px solid rgba(143, 148, 251, 0.4);
  border-radius: 12px;
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(143, 148, 251, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  padding: 8px;
  margin-top: 8px;
}

.feature-select-dropdown .el-select-dropdown__item,
.feature-select-dropdown .feature-option {
  background: transparent !important;
  color: transparent !important;
  border-radius: 8px;
  margin: 4px 0;
  padding: 14px 18px !important;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

/* 其他选项渐变样式 - 下拉选项 */
.feature-select-dropdown .el-select-dropdown__item:not(:first-child) {
  position: relative;
}

/* PSD选项 - 第2个 */
.feature-select-dropdown .el-select-dropdown__item:nth-child(2)::after {
  content: "PSD";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #4e54c8 0%, 
    #8f94fb 30%, 
    #a8b5ff 60%, 
    #8f94fb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  z-index: 2;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

/* DASM选项 - 第3个 */
.feature-select-dropdown .el-select-dropdown__item:nth-child(3)::after {
  content: "DASM";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #667eea 0%, 
    #764ba2 50%, 
    #667eea 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  z-index: 2;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

/* RASM选项 - 第4个 */
.feature-select-dropdown .el-select-dropdown__item:nth-child(4)::after {
  content: "RASM";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #f093fb 0%, 
    #f5576c 50%, 
    #f093fb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  z-index: 2;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

/* DCAU选项 - 第5个 */
.feature-select-dropdown .el-select-dropdown__item:nth-child(5)::after {
  content: "DCAU";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #4facfe 0%, 
    #00f2fe 50%, 
    #4facfe 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  z-index: 2;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

.feature-select-dropdown .el-select-dropdown__item::before,
.feature-select-dropdown .feature-option::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, #8f94fb, #4e54c8);
  transform: scaleY(0);
  transition: transform 0.3s ease;
  z-index: 1;
}

.feature-select-dropdown .el-select-dropdown__item:hover,
.feature-select-dropdown .feature-option:hover {
  background: linear-gradient(90deg, 
    rgba(143, 148, 251, 0.25) 0%, 
    rgba(78, 84, 200, 0.2) 100%) !important;
  transform: translateX(5px);
  box-shadow: 
    0 4px 12px rgba(143, 148, 251, 0.3),
    inset 0 0 20px rgba(143, 148, 251, 0.1);
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

.feature-select-dropdown .el-select-dropdown__item:hover:nth-child(2)::after,
.feature-select-dropdown .el-select-dropdown__item:hover:nth-child(3)::after,
.feature-select-dropdown .el-select-dropdown__item:hover:nth-child(4)::after,
.feature-select-dropdown .el-select-dropdown__item:hover:nth-child(5)::after {
  font-weight: 700;
  animation-duration: 2s;
}

.feature-select-dropdown .el-select-dropdown__item:hover::before,
.feature-select-dropdown .feature-option:hover::before {
  transform: scaleY(1);
}

.feature-select-dropdown .el-select-dropdown__item.is-selected,
.feature-select-dropdown .feature-option.is-selected {
  background: linear-gradient(90deg, 
    rgba(143, 148, 251, 0.4) 0%, 
    rgba(78, 84, 200, 0.35) 50%,
    rgba(143, 148, 251, 0.4) 100%) !important;
  /* 字体样式与普通选项保持一致 */
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
  /* 选中状态的视觉效果 */
  box-shadow: 
    0 6px 20px rgba(143, 148, 251, 0.5),
    inset 0 0 30px rgba(143, 148, 251, 0.2),
    0 0 25px rgba(143, 148, 251, 0.4);
  border: 1px solid rgba(143, 148, 251, 0.6);
  transform: scale(1.02);
  animation: selected-option-pulse 2s ease-in-out infinite;
  position: relative;
}

@keyframes selected-option-pulse {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(143, 148, 251, 0.5),
      inset 0 0 30px rgba(143, 148, 251, 0.2),
      0 0 25px rgba(143, 148, 251, 0.4);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(143, 148, 251, 0.6),
      inset 0 0 35px rgba(143, 148, 251, 0.25),
      0 0 35px rgba(143, 148, 251, 0.5);
  }
}

/* DE选项选中后的特殊效果 */
.feature-select-dropdown .el-select-dropdown__item:first-child.is-selected {
  background: linear-gradient(90deg, 
    rgba(255, 107, 107, 0.3) 0%, 
    rgba(255, 215, 0, 0.25) 50%,
    rgba(255, 107, 107, 0.3) 100%) !important;
  border-color: rgba(255, 107, 107, 0.7);
  box-shadow: 
    0 6px 20px rgba(255, 107, 107, 0.5),
    inset 0 0 30px rgba(255, 107, 107, 0.2),
    0 0 30px rgba(255, 107, 107, 0.6),
    0 0 40px rgba(255, 215, 0, 0.4);
  animation: selected-option-pulse-de 2s ease-in-out infinite;
}

@keyframes selected-option-pulse-de {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(255, 107, 107, 0.5),
      inset 0 0 30px rgba(255, 107, 107, 0.2),
      0 0 30px rgba(255, 107, 107, 0.6),
      0 0 40px rgba(255, 215, 0, 0.4);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(255, 107, 107, 0.6),
      inset 0 0 35px rgba(255, 107, 107, 0.25),
      0 0 40px rgba(255, 107, 107, 0.8),
      0 0 50px rgba(255, 215, 0, 0.6);
  }
}

.feature-select-dropdown .el-select-dropdown__item.is-selected:nth-child(2)::after,
.feature-select-dropdown .el-select-dropdown__item.is-selected:nth-child(3)::after,
.feature-select-dropdown .el-select-dropdown__item.is-selected:nth-child(4)::after,
.feature-select-dropdown .el-select-dropdown__item.is-selected:nth-child(5)::after {
  /* 字体样式与普通选项保持一致 */
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  line-height: 1.5;
  animation-duration: 1.5s;
  filter: drop-shadow(0 0 4px rgba(143, 148, 251, 0.6)) 
          drop-shadow(0 0 8px rgba(143, 148, 251, 0.4));
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
}

/* DE选项选中后的文字效果 - 字体样式与普通选项保持一致 */
.feature-select-dropdown .el-select-dropdown__item:first-child.is-selected::after {
  /* 字体样式与普通DE选项保持一致 */
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1.5px;
  line-height: 1.5;
  filter: drop-shadow(0 0 8px rgba(255, 107, 107, 0.8)) 
          drop-shadow(0 0 15px rgba(255, 215, 0, 0.6))
          drop-shadow(0 0 20px rgba(255, 142, 83, 0.4));
  animation-duration: 1.5s;
  transform: translateY(-50%);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
}

.feature-select-dropdown .el-select-dropdown__item.is-selected::before,
.feature-select-dropdown .feature-option.is-selected::before {
  transform: scaleY(1);
  width: 4px;
  background: linear-gradient(180deg, 
    rgba(143, 148, 251, 1) 0%, 
    rgba(78, 84, 200, 1) 50%,
    rgba(143, 148, 251, 1) 100%);
  box-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
  animation: selected-indicator-pulse 2s ease-in-out infinite;
}

@keyframes selected-indicator-pulse {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 15px rgba(143, 148, 251, 1);
  }
}

/* DE选项选中后的指示器特殊效果 */
.feature-select-dropdown .el-select-dropdown__item:first-child.is-selected::before {
  background: linear-gradient(180deg, 
    rgba(255, 107, 107, 1) 0%, 
    rgba(255, 215, 0, 1) 50%,
    rgba(255, 107, 107, 1) 100%);
  box-shadow: 0 0 15px rgba(255, 107, 107, 0.9);
  animation: selected-indicator-pulse-de 2s ease-in-out infinite;
}

@keyframes selected-indicator-pulse-de {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 15px rgba(255, 107, 107, 0.9);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 20px rgba(255, 107, 107, 1), 0 0 25px rgba(255, 215, 0, 0.8);
  }
}

/* DE选项炫彩样式 - 下拉选项中的DE */
.feature-select-dropdown .feature-option-de,
.feature-select-dropdown .el-select-dropdown__item:first-child {
  color: transparent !important;
  position: relative;
}

/* 针对第一个选项（DE）添加炫彩效果 */
.feature-select-dropdown .el-select-dropdown__item:first-child::after {
  content: "DE";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de 4s ease infinite;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1.5px;
  z-index: 2;
  pointer-events: none;
  filter: drop-shadow(0 0 8px rgba(255, 107, 107, 0.8)) 
          drop-shadow(0 0 15px rgba(255, 215, 0, 0.6))
          drop-shadow(0 0 20px rgba(255, 142, 83, 0.4));
  text-transform: uppercase;
  line-height: 1.5;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  transition: all 0.3s ease;
}

.feature-select-dropdown .el-select-dropdown__item:first-child::before {
  content: "DE";
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de 4s ease infinite reverse;
  z-index: 1;
  pointer-events: none;
  filter: blur(2px);
  opacity: 0.5;
  text-transform: uppercase;
  line-height: 1.5;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1.5px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
}

.feature-select-dropdown .feature-text-de {
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 12%, 
    #ffa500 25%, 
    #ffd700 37%, 
    #ffeb3b 50%, 
    #ff6b9d 62%, 
    #c44569 75%, 
    #ff6b6b 87%, 
    #ff8e53 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de 4s ease infinite;
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1.5px;
  position: relative;
  display: inline-block;
  filter: drop-shadow(0 0 8px rgba(255, 107, 107, 0.8)) 
          drop-shadow(0 0 15px rgba(255, 215, 0, 0.6))
          drop-shadow(0 0 20px rgba(255, 142, 83, 0.4));
  text-transform: uppercase;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

.feature-select-dropdown .feature-text-de::before {
  content: "DE";
  position: absolute;
  left: 0;
  top: 0;
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 15%, 
    #ffa500 30%, 
    #ffd700 45%, 
    #ffeb3b 60%, 
    #ff6b9d 75%, 
    #c44569 90%, 
    #ff6b6b 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de 4s ease infinite reverse;
  z-index: -1;
  filter: blur(3px);
  opacity: 0.6;
}

.feature-select-dropdown .feature-text-de::after {
  content: "DE";
  position: absolute;
  left: 0;
  top: 0;
  background: linear-gradient(135deg, 
    #ff6b6b 0%, 
    #ff8e53 15%, 
    #ffa500 30%, 
    #ffd700 45%, 
    #ffeb3b 60%, 
    #ff6b9d 75%, 
    #c44569 90%, 
    #ff6b6b 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 300% 300%;
  animation: gradient-shift-de 4s ease infinite;
  z-index: -2;
  filter: blur(6px);
  opacity: 0.4;
  transform: translate(1px, 1px);
}

@keyframes gradient-shift-de {
  0%, 100% {
    background-position: 0% 50%;
  }
  25% {
    background-position: 50% 0%;
  }
  50% {
    background-position: 100% 50%;
  }
  75% {
    background-position: 50% 100%;
  }
}

/* DE选项悬停效果增强 */
.feature-select-dropdown .feature-option-de:hover .feature-text-de {
  animation-duration: 2s;
  filter: drop-shadow(0 0 15px rgba(255, 107, 107, 1)) 
          drop-shadow(0 0 25px rgba(255, 215, 0, 0.8));
  transform: scale(1.1);
}

/* DE选项选中状态 */
.feature-select-dropdown .feature-option-de.is-selected .feature-text-de {
  animation-duration: 1.5s;
  filter: drop-shadow(0 0 20px rgba(255, 107, 107, 1)) 
          drop-shadow(0 0 30px rgba(255, 215, 0, 0.9))
          drop-shadow(0 0 40px rgba(255, 142, 83, 0.6));
  transform: scale(1.15);
}

/* 模型选择栏样式 */
.model-selection-bar {
  display: flex;
  justify-content: flex-start;
  width: 100%;
  margin-bottom: 25px;
  padding: 0;
  position: relative;
}

.model-selection-container {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  padding: 18px 22px;
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.25) 0%, 
    rgba(78, 84, 200, 0.2) 50%, 
    rgba(143, 148, 251, 0.25) 100%);
  border-radius: 14px;
  border: 1px solid rgba(64, 128, 255, 0.5);
  backdrop-filter: blur(15px);
  box-shadow: 
    0 6px 25px rgba(45, 56, 138, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 25px rgba(143, 148, 251, 0.3),
    inset 0 0 30px rgba(143, 148, 251, 0.1);
  position: relative;
  overflow: visible;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.model-selection-container::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent);
  transition: left 0.6s ease;
}

.model-selection-container:hover::before {
  left: 100%;
}

.model-selection-container:hover {
  border-color: rgba(143, 148, 251, 0.6);
  box-shadow: 
    0 8px 30px rgba(45, 56, 138, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 0 35px rgba(143, 148, 251, 0.4),
    inset 0 0 40px rgba(143, 148, 251, 0.15);
  transform: translateY(-2px);
}

/* 模型选择标签样式 */
.model-label-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(78, 84, 200, 0.2), rgba(143, 148, 251, 0.2));
  border-radius: 10px;
  border: 1px solid rgba(143, 148, 251, 0.3);
  box-shadow: 0 4px 15px rgba(78, 84, 200, 0.2);
}

.model-icon {
  font-size: 18px;
  color: #8f94fb;
  text-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
  animation: pulse-glow 2s ease-in-out infinite;
}

.model-label {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.model-label-wrapper .label-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(143, 148, 251, 0.3) 0%, transparent 70%);
  border-radius: 10px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.model-label-wrapper:hover .label-glow {
  opacity: 1;
}

/* 模型选择下拉框容器 */
.model-select-wrapper {
  position: relative;
  flex: 1;
  max-width: 280px;
}

.model-select-wrapper .select-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(143, 148, 251, 0.2) 0%, transparent 70%);
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
  border-radius: 12px;
}

.model-select-wrapper:hover .select-glow {
  opacity: 1;
}

.model-select-wrapper .select-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
  overflow: hidden;
  border-radius: 12px;
}

.model-select-wrapper .select-particles .particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: rgba(143, 148, 251, 0.6);
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(143, 148, 251, 0.8);
  animation: float-particle 3s ease-in-out infinite;
}

.model-select-wrapper .select-particles .particle:nth-child(1) {
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.model-select-wrapper .select-particles .particle:nth-child(2) {
  top: 50%;
  left: 20%;
  animation-delay: 0.5s;
}

.model-select-wrapper .select-particles .particle:nth-child(3) {
  top: 80%;
  left: 30%;
  animation-delay: 1s;
}

.model-select-wrapper .select-particles .particle:nth-child(4) {
  top: 30%;
  right: 20%;
  animation-delay: 1.5s;
}

.model-select-wrapper .select-particles .particle:nth-child(5) {
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.model-select-wrapper .select-particles .particle:nth-child(6) {
  top: 10%;
  right: 10%;
  animation-delay: 2.5s;
}

/* 模型选择下拉框样式 */
.model-select {
  width: 100%;
  position: relative;
  z-index: 2;
  --el-select-input-focus-border-color: #8f94fb;
  --el-select-border-color-hover: #8f94fb;
}

.model-select :deep(.el-input__wrapper) {
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.4) 0%, 
    rgba(78, 84, 200, 0.3) 100%);
  border: 2px solid rgba(143, 148, 251, 0.4);
  border-radius: 12px;
  box-shadow: 
    0 4px 15px rgba(45, 56, 138, 0.3),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 15px rgba(143, 148, 251, 0.2);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0 15px;
  height: 48px;
  position: relative;
  overflow: hidden;
}

.model-select :deep(.el-input__wrapper:hover) {
  border-color: rgba(143, 148, 251, 0.8);
  box-shadow: 
    0 6px 20px rgba(45, 56, 138, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 25px rgba(143, 148, 251, 0.5);
  transform: translateY(-1px);
}

.model-select :deep(.el-input__wrapper.is-focus) {
  border-color: #8f94fb;
  box-shadow: 
    0 8px 25px rgba(45, 56, 138, 0.5),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(143, 148, 251, 0.7);
}

.model-select :deep(.el-input__inner) {
  color: #ffffff;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  height: 48px;
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  transition: all 0.3s ease;
}

/* 模型选择选中后的输入框样式增强 */
.model-select.model-selected :deep(.el-input__wrapper) {
  border-color: rgba(143, 148, 251, 0.7) !important;
  background: linear-gradient(135deg, 
    rgba(45, 56, 138, 0.5) 0%, 
    rgba(78, 84, 200, 0.4) 100%) !important;
  box-shadow: 
    0 6px 20px rgba(45, 56, 138, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 25px rgba(143, 148, 251, 0.5),
    inset 0 0 30px rgba(143, 148, 251, 0.1) !important;
  animation: selected-pulse 2s ease-in-out infinite;
}

/* CADD_DCCNN 选中后的特殊效果 */
.model-select-cadd[data-selected="CADD_DCCNN"] :deep(.el-input__wrapper) {
  border-color: rgba(79, 172, 254, 0.8);
  background: linear-gradient(135deg, 
    rgba(79, 172, 254, 0.15) 0%, 
    rgba(0, 242, 254, 0.1) 50%,
    rgba(79, 172, 254, 0.15) 100%);
  box-shadow: 
    0 6px 20px rgba(79, 172, 254, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(79, 172, 254, 0.6),
    0 0 40px rgba(0, 242, 254, 0.4),
    inset 0 0 35px rgba(79, 172, 254, 0.15);
  animation: selected-pulse-cadd 2s ease-in-out infinite;
}

@keyframes selected-pulse-cadd {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(79, 172, 254, 0.4),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 30px rgba(79, 172, 254, 0.6),
      0 0 40px rgba(0, 242, 254, 0.4),
      inset 0 0 35px rgba(79, 172, 254, 0.15);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(79, 172, 254, 0.5),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 40px rgba(79, 172, 254, 0.8),
      0 0 50px rgba(0, 242, 254, 0.6),
      inset 0 0 45px rgba(79, 172, 254, 0.2);
  }
}

/* EEGMatch 选中后的特殊效果 */
.model-select-eegmatch[data-selected="EEGMatch"] :deep(.el-input__wrapper) {
  border-color: rgba(240, 147, 251, 0.8);
  background: linear-gradient(135deg, 
    rgba(240, 147, 251, 0.15) 0%, 
    rgba(245, 87, 108, 0.1) 50%,
    rgba(240, 147, 251, 0.15) 100%);
  box-shadow: 
    0 6px 20px rgba(240, 147, 251, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(240, 147, 251, 0.6),
    0 0 40px rgba(245, 87, 108, 0.4),
    inset 0 0 35px rgba(240, 147, 251, 0.15);
  animation: selected-pulse-eegmatch 2s ease-in-out infinite;
}

@keyframes selected-pulse-eegmatch {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(240, 147, 251, 0.4),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 30px rgba(240, 147, 251, 0.6),
      0 0 40px rgba(245, 87, 108, 0.4),
      inset 0 0 35px rgba(240, 147, 251, 0.15);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(240, 147, 251, 0.5),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 40px rgba(240, 147, 251, 0.8),
      0 0 50px rgba(245, 87, 108, 0.6),
      inset 0 0 45px rgba(240, 147, 251, 0.2);
  }
}

/* ATGRNet 选中后的特殊效果 */
.model-select-atgrnet[data-selected="ATGRNet"] :deep(.el-input__wrapper) {
  border-color: rgba(143, 148, 251, 0.8);
  background: linear-gradient(135deg,
    rgba(143, 148, 251, 0.15) 0%,
    rgba(78, 84, 200, 0.1) 50%,
    rgba(143, 148, 251, 0.15) 100%);
  box-shadow:
    0 6px 20px rgba(143, 148, 251, 0.4),
    inset 0 2px 4px rgba(0, 0, 0, 0.1),
    0 0 30px rgba(143, 148, 251, 0.6),
    0 0 40px rgba(78, 84, 200, 0.4),
    inset 0 0 35px rgba(143, 148, 251, 0.15);
  animation: selected-pulse-atgrnet 2s ease-in-out infinite;
}

@keyframes selected-pulse-atgrnet {
  0%, 100% {
    box-shadow:
      0 6px 20px rgba(143, 148, 251, 0.4),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 30px rgba(143, 148, 251, 0.6),
      0 0 40px rgba(78, 84, 200, 0.4),
      inset 0 0 35px rgba(143, 148, 251, 0.15);
  }
  50% {
    box-shadow:
      0 8px 25px rgba(143, 148, 251, 0.5),
      inset 0 2px 4px rgba(0, 0, 0, 0.1),
      0 0 40px rgba(143, 148, 251, 0.8),
      0 0 50px rgba(78, 84, 200, 0.6),
      inset 0 0 45px rgba(143, 148, 251, 0.2);
  }
}

/* 模型选择选中后的字体优化 */
.model-select.model-selected :deep(.el-input__inner) {
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1.8px;
  filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.4)) 
          drop-shadow(0 0 8px rgba(255, 255, 255, 0.2));
  line-height: 48px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* CADD_DCCNN 选中后的字体优化 */
.model-select-cadd.model-selected :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #4facfe 0%, 
    #00f2fe 50%, 
    #4facfe 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1.8px;
  filter: drop-shadow(0 0 5px rgba(79, 172, 254, 0.7)) 
          drop-shadow(0 0 10px rgba(79, 172, 254, 0.5))
          drop-shadow(0 0 15px rgba(79, 172, 254, 0.3));
}

/* EEGMatch 选中后的字体优化 */
.model-select-eegmatch.model-selected :deep(.el-input__inner) {
  background: linear-gradient(135deg, 
    #f093fb 0%, 
    #f5576c 50%, 
    #f093fb 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 200%;
  animation: gradient-shift-other 3s ease infinite;
  font-weight: 700;
  font-size: 17px;
  letter-spacing: 1.8px;
  filter: drop-shadow(0 0 5px rgba(240, 147, 251, 0.7)) 
          drop-shadow(0 0 10px rgba(240, 147, 251, 0.5))
          drop-shadow(0 0 15px rgba(240, 147, 251, 0.3));
}

.model-select :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
}

.model-select :deep(.el-select__caret) {
  color: #8f94fb;
  font-size: 16px;
  transition: transform 0.3s ease;
  filter: drop-shadow(0 0 4px rgba(143, 148, 251, 0.8));
}

.model-select :deep(.el-select__caret.is-reverse) {
  transform: rotate(180deg);
}

/* 模型选择下拉选项样式 */
.model-select-dropdown {
  background: linear-gradient(135deg, 
    rgba(30, 35, 80, 0.98) 0%, 
    rgba(45, 56, 138, 0.98) 100%);
  border: 1px solid rgba(143, 148, 251, 0.4);
  border-radius: 12px;
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.5),
    0 0 30px rgba(143, 148, 251, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  padding: 8px;
  margin-top: 8px;
}

.model-select-dropdown .el-select-dropdown__item,
.model-select-dropdown .model-option {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.95) !important;
  border-radius: 8px;
  margin: 4px 0;
  padding: 14px 18px !important;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

.model-select-dropdown .model-option-cadd_dccnn,
.model-select-dropdown .el-select-dropdown__item:nth-child(1) {
  color: #4facfe !important;
}

.model-select-dropdown .model-option-eegmatch,
.model-select-dropdown .el-select-dropdown__item:nth-child(2) {
  color: #f093fb !important;
}

.model-select-dropdown .model-option-atgrnet,
.model-select-dropdown .el-select-dropdown__item:nth-child(3) {
  color: #8f94fb !important;
}

.model-select-dropdown .el-select-dropdown__item::before,
.model-select-dropdown .model-option::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, #8f94fb, #4e54c8);
  transform: scaleY(0);
  transition: transform 0.3s ease;
  z-index: 1;
}

.model-select-dropdown .el-select-dropdown__item:hover,
.model-select-dropdown .model-option:hover {
  background: linear-gradient(90deg, 
    rgba(143, 148, 251, 0.25) 0%, 
    rgba(78, 84, 200, 0.2) 100%) !important;
  transform: translateX(5px);
  box-shadow: 
    0 4px 12px rgba(143, 148, 251, 0.3),
    inset 0 0 20px rgba(143, 148, 251, 0.1);
  font-weight: 700;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  line-height: 1.5;
}

.model-select-dropdown .el-select-dropdown__item:hover::before,
.model-select-dropdown .model-option:hover::before {
  transform: scaleY(1);
}

.model-select-dropdown .el-select-dropdown__item.is-selected,
.model-select-dropdown .model-option.is-selected {
  background: linear-gradient(90deg, 
    rgba(143, 148, 251, 0.4) 0%, 
    rgba(78, 84, 200, 0.35) 50%,
    rgba(143, 148, 251, 0.4) 100%) !important;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  font-feature-settings: "kern" 1;
  font-kerning: normal;
  box-shadow: 
    0 6px 20px rgba(143, 148, 251, 0.5),
    inset 0 0 30px rgba(143, 148, 251, 0.2),
    0 0 25px rgba(143, 148, 251, 0.4);
  line-height: 1.5;
  border: 1px solid rgba(143, 148, 251, 0.6);
  transform: scale(1.02);
  animation: selected-option-pulse 2s ease-in-out infinite;
  position: relative;
}

.model-select-dropdown .el-select-dropdown__item.is-selected::before,
.model-select-dropdown .model-option.is-selected::before {
  transform: scaleY(1);
  width: 4px;
  background: linear-gradient(180deg, 
    rgba(143, 148, 251, 1) 0%, 
    rgba(78, 84, 200, 1) 50%,
    rgba(143, 148, 251, 1) 100%);
  box-shadow: 0 0 10px rgba(143, 148, 251, 0.8);
  animation: selected-indicator-pulse 2s ease-in-out infinite;
}

/* CADD_DCCNN 选项选中后的特殊效果 */
.model-select-dropdown .el-select-dropdown__item:first-child.is-selected {
  background: linear-gradient(90deg, 
    rgba(79, 172, 254, 0.3) 0%, 
    rgba(0, 242, 254, 0.25) 50%,
    rgba(79, 172, 254, 0.3) 100%) !important;
  border-color: rgba(79, 172, 254, 0.7);
  box-shadow: 
    0 6px 20px rgba(79, 172, 254, 0.5),
    inset 0 0 30px rgba(79, 172, 254, 0.2),
    0 0 30px rgba(79, 172, 254, 0.6),
    0 0 40px rgba(0, 242, 254, 0.4);
  animation: selected-option-pulse-cadd-dropdown 2s ease-in-out infinite;
}

@keyframes selected-option-pulse-cadd-dropdown {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(79, 172, 254, 0.5),
      inset 0 0 30px rgba(79, 172, 254, 0.2),
      0 0 30px rgba(79, 172, 254, 0.6),
      0 0 40px rgba(0, 242, 254, 0.4);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(79, 172, 254, 0.6),
      inset 0 0 35px rgba(79, 172, 254, 0.25),
      0 0 40px rgba(79, 172, 254, 0.8),
      0 0 50px rgba(0, 242, 254, 0.6);
  }
}

.model-select-dropdown .el-select-dropdown__item:first-child.is-selected::before {
  background: linear-gradient(180deg, 
    rgba(79, 172, 254, 1) 0%, 
    rgba(0, 242, 254, 1) 50%,
    rgba(79, 172, 254, 1) 100%);
  box-shadow: 0 0 15px rgba(79, 172, 254, 0.9);
  animation: selected-indicator-pulse-cadd 2s ease-in-out infinite;
}

@keyframes selected-indicator-pulse-cadd {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 15px rgba(79, 172, 254, 0.9);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 20px rgba(79, 172, 254, 1), 0 0 25px rgba(0, 242, 254, 0.8);
  }
}

/* EEGMatch 选项选中后的特殊效果 */
.model-select-dropdown .el-select-dropdown__item:nth-child(2).is-selected {
  background: linear-gradient(90deg, 
    rgba(240, 147, 251, 0.3) 0%, 
    rgba(245, 87, 108, 0.25) 50%,
    rgba(240, 147, 251, 0.3) 100%) !important;
  border-color: rgba(240, 147, 251, 0.7);
  box-shadow: 
    0 6px 20px rgba(240, 147, 251, 0.5),
    inset 0 0 30px rgba(240, 147, 251, 0.2),
    0 0 30px rgba(240, 147, 251, 0.6),
    0 0 40px rgba(245, 87, 108, 0.4);
  animation: selected-option-pulse-eegmatch-dropdown 2s ease-in-out infinite;
}

@keyframes selected-option-pulse-eegmatch-dropdown {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(240, 147, 251, 0.5),
      inset 0 0 30px rgba(240, 147, 251, 0.2),
      0 0 30px rgba(240, 147, 251, 0.6),
      0 0 40px rgba(245, 87, 108, 0.4);
  }
  50% {
    box-shadow: 
      0 8px 25px rgba(240, 147, 251, 0.6),
      inset 0 0 35px rgba(240, 147, 251, 0.25),
      0 0 40px rgba(240, 147, 251, 0.8),
      0 0 50px rgba(245, 87, 108, 0.6);
  }
}

.model-select-dropdown .el-select-dropdown__item:nth-child(2).is-selected::before {
  background: linear-gradient(180deg, 
    rgba(240, 147, 251, 1) 0%, 
    rgba(245, 87, 108, 1) 50%,
    rgba(240, 147, 251, 1) 100%);
  box-shadow: 0 0 15px rgba(240, 147, 251, 0.9);
  animation: selected-indicator-pulse-eegmatch 2s ease-in-out infinite;
}

@keyframes selected-indicator-pulse-eegmatch {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 15px rgba(240, 147, 251, 0.9);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 20px rgba(240, 147, 251, 1), 0 0 25px rgba(245, 87, 108, 0.8);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feature-selection-container,
  .model-selection-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .select-wrapper,
  .model-select-wrapper {
    max-width: 100%;
  }
}

/* 按钮栏 */
.buttons-bar {
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(64, 128, 255, 0.2);
}

.action-button {
  background: linear-gradient(135deg, #2d388a, #4e54c8, #8f94fb);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 14px 30px;
  font-weight: bold;
  letter-spacing: 1px;
  box-shadow: 0 5px 15px rgba(45, 56, 138, 0.5), 0 0 15px rgba(143, 148, 251, 0.4);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  transform: translateZ(5px);
  font-size: 16px;
}

.action-button::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent);
  transition: 0.5s;
}

.action-button:hover {
  transform: translateY(-5px) scale(1.05) translateZ(10px);
  box-shadow: 0 10px 25px rgba(45, 56, 138, 0.7), 0 0 25px rgba(143, 148, 251, 0.8);
  background: linear-gradient(135deg, #8f94fb, #4e54c8, #2d388a);
}

.action-button:active {
  transform: translateY(2px) scale(0.98);
}

.action-button:hover::before {
  left: 100%;
}

.action-button i {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.action-button:hover i {
  transform: scale(1.2);
}

/* 进度条样式 */
.el-progress {
  margin: 20px 0;
}

.el-progress-bar__outer {
  background: rgba(30, 40, 80, 0.7);
  border-radius: 10px;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.5);
}

.el-progress-bar__inner {
  border-radius: 10px;
  box-shadow: 0 0 10px currentColor;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* 加载动画 */
.el-skeleton {
  background: rgba(20, 30, 70, 0.6);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.el-skeleton::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(64, 128, 255, 0.3),
    transparent);
  animation: loading 1.5s infinite;
}

@keyframes loading {
  100% { left: 100%; }
}

/* 粒子动画 */
.particles {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.particle {
  position: absolute;
  border-radius: 50%;
  animation: float linear infinite;
  z-index: 0;
}

@keyframes float {
  0% {
    transform: translateY(100vh) translateX(0) rotate(0deg);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px) translateX(100px) rotate(360deg);
    opacity: 0;
  }
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .nav-container {
    gap: 30px;
  }
  
  .nav-step {
    min-width: 140px;
    padding: 15px 12px;
  }
  
  .step-icon {
    width: 45px;
    height: 45px;
  }
  
  .step-icon i {
    font-size: 20px;
  }
  
  .step-title {
    font-size: 14px;
  }
  
  .step-subtitle {
    font-size: 9px;
  }
}

@media (max-width: 992px) {
  .title {
    font-size: 28px;
  }
  
  .title-text {
    font-size: 30px;
    letter-spacing: 2px;
  }

  .el-container {
    width: 90%;
  }

  .content {
    padding: 20px;
  }

  .process-flow {
    flex-wrap: wrap;
    justify-content: center;
  }

  .process-step {
    width: 40%;
    margin-bottom: 30px;
  }

  .process-connector {
    display: none;
  }
  
  /* 导航栏响应式 */
  .cyber-nav {
    height: 160px;
  }
  
  .nav-container {
    gap: 20px;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .nav-step {
    min-width: 120px;
    padding: 12px 10px;
  }
  
  .nav-connector {
    width: 80px;
  }
  
  .step-number {
    width: 30px;
    height: 30px;
    font-size: 10px;
  }
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    height: auto;
    padding: 15px;
    text-align: center;
  }

  .title-logo {
    margin-bottom: 15px;
    justify-content: center;
  }

  .title {
    font-size: 24px;
  }
  
  .title-text {
    font-size: 26px;
    letter-spacing: 1px;
  }

  .fullscreen-btn {
    margin-top: 15px;
  }

  .el-col {
    width: 100% !important;
    margin-bottom: 20px;
  }

  .action-button {
    padding: 12px 20px;
    font-size: 14px;
  }

  .buttons-bar {
    flex-wrap: wrap;
    gap: 10px;
  }

  .action-button {
    flex: 1 1 45%;
  }

  .process-step {
    width: 100%;
  }
  
  /* 移动端导航栏 */
  .cyber-nav {
    height: auto;
    min-height: 200px;
    padding: 15px;
  }
  
  .nav-container {
    flex-direction: column;
    gap: 15px;
    width: 100%;
  }
  
  .nav-step {
    width: 100%;
    max-width: 280px;
    min-width: auto;
    flex-direction: row;
    justify-content: flex-start;
    padding: 15px;
    gap: 15px;
  }
  
  .step-content {
    flex-direction: row;
    align-items: center;
    gap: 15px;
  }
  
  .step-icon {
    margin-bottom: 0;
    flex-shrink: 0;
  }
  
  .step-title {
    text-align: left;
    font-size: 16px;
  }
  
  .step-subtitle {
    text-align: left;
    font-size: 10px;
  }
  
  .nav-connector {
    width: 4px;
    height: 30px;
    transform: rotate(90deg);
  }
  
  .connector-line {
    height: 100%;
    width: 2px;
  }
  
  .connector-data {
    display: none;
  }
  
  .step-number {
    top: -5px;
    right: -5px;
    width: 25px;
    height: 25px;
    font-size: 9px;
  }
}



/* DE特征分段显示样式 */
.de-segmentation-display {
  background: linear-gradient(135deg, rgba(0, 20, 40, 0.9) 0%, rgba(0, 40, 80, 0.9) 100%);
  border-radius: 15px;
  padding: 20px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 212, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.de-segmentation-display::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(0, 255, 136, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.de-segmentation-container {
  position: relative;
  z-index: 1;
}

.de-segmentation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
}

.de-segmentation-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  color: #00d4ff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.de-segmentation-title i {
  margin-right: 10px;
  font-size: 20px;
  animation: icon-float 3s ease-in-out infinite;
}

.de-segmentation-stats {
  display: flex;
  gap: 10px;
}

.de-segmentation-content {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.de-segmentation-results {
  width: 100%;
  text-align: center;
}

.de-segmentation-chart {
  background: linear-gradient(135deg, rgba(0, 30, 60, 0.8) 0%, rgba(0, 60, 120, 0.8) 100%);
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  border: 2px solid rgba(0, 212, 255, 0.4);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3), 0 0 10px rgba(0, 212, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.de-segmentation-chart::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.1) 50%, transparent 70%);
  animation: chart-scan 3s linear infinite;
}

.de-segmentation-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.info-item {
  background: linear-gradient(135deg, rgba(0, 40, 80, 0.8) 0%, rgba(0, 80, 160, 0.8) 100%);
  border-radius: 8px;
  padding: 15px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  text-align: center;
  transition: all 0.3s ease;
}

.info-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3), 0 0 10px rgba(0, 212, 255, 0.3);
}

.info-label {
  display: block;
  font-size: 12px;
  color: #a0a0ff;
  margin-bottom: 5px;
  opacity: 0.8;
}

.info-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #00ff88;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.de-segmentation-placeholder {
  text-align: center;
  color: #a0a0ff;
}

.placeholder-icon {
  font-size: 48px;
  color: #00d4ff;
  margin-bottom: 15px;
  opacity: 0.6;
  animation: icon-float 3s ease-in-out infinite;
}

.placeholder-icon i {
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

/* 频域特征显示样式 */
.frequency-display {
  background: linear-gradient(135deg, rgba(40, 0, 80, 0.9) 0%, rgba(80, 0, 160, 0.9) 100%);
  border-radius: 15px;
  padding: 20px;
  border: 2px solid rgba(255, 0, 255, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 0, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.frequency-display::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 30% 30%, rgba(255, 0, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 70% 70%, rgba(0, 255, 255, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.frequency-results {
  width: 100%;
  text-align: center;
}

.frequency-chart {
  background: linear-gradient(135deg, rgba(60, 0, 120, 0.8) 0%, rgba(120, 0, 240, 0.8) 100%);
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  border: 2px solid rgba(255, 0, 255, 0.4);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3), 0 0 10px rgba(255, 0, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.frequency-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.frequency-placeholder {
  text-align: center;
  color: #a0a0ff;
}

/* 时间特征显示样式 */
.temporal-display {
  background: linear-gradient(135deg, rgba(80, 40, 0, 0.9) 0%, rgba(160, 80, 0, 0.9) 100%);
  border-radius: 15px;
  padding: 20px;
  border: 2px solid rgba(255, 165, 0, 0.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 165, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.temporal-display::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 40% 40%, rgba(255, 165, 0, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 60% 60%, rgba(255, 255, 0, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.temporal-results {
  width: 100%;
  text-align: center;
}

.temporal-chart {
  background: linear-gradient(135deg, rgba(120, 60, 0, 0.8) 0%, rgba(240, 120, 0, 0.8) 100%);
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  border: 2px solid rgba(255, 165, 0, 0.4);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3), 0 0 10px rgba(255, 165, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.temporal-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.temporal-placeholder {
  text-align: center;
  color: #a0a0ff;
}



/* 动画效果 */
@keyframes chart-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes icon-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.8; }
}

@keyframes particle-float {
  0%, 100% { 
    transform: translateY(0px) scale(1);
    opacity: 0;
  }
  25% { 
    transform: translateY(-10px) scale(1.2);
    opacity: 1;
  }
  75% { 
    transform: translateY(-20px) scale(0.8);
    opacity: 0.5;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .de-segmentation-info,
  .frequency-info,
  .temporal-info {
    grid-template-columns: 1fr;
  }
  
  .de-segmentation-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  

}



/* 特征提取学习流程图样式 */
.feature-extraction-flow {
  background: linear-gradient(135deg, rgba(10, 15, 40, 0.95) 0%, rgba(20, 30, 80, 0.95) 100%);
  border-radius: 20px;
  padding: 30px;
  margin: 20px 0;
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6), 0 0 20px rgba(64, 128, 255, 0.2);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.feature-extraction-flow::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 20, 147, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(0, 255, 136, 0.05) 0%, transparent 70%);
  pointer-events: none;
  animation: bg-pulse 4s ease-in-out infinite;
}

@keyframes bg-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

/* 背景装饰元素 */
.flow-bg-elements {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.bg-circuit-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(90deg, rgba(0, 212, 255, 0.1) 1px, transparent 1px),
    linear-gradient(rgba(0, 212, 255, 0.1) 1px, transparent 1px);
  background-size: 30px 30px;
  animation: circuit-move 20s linear infinite;
}

@keyframes circuit-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(30px, 30px); }
}

.bg-data-stream {
  position: absolute;
  top: 0;
  left: -100%;
  width: 200%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0, 212, 255, 0.1) 50%,
    transparent 100%);
  animation: data-stream 8s linear infinite;
}

@keyframes data-stream {
  0% { transform: translateX(0); }
  100% { transform: translateX(50%); }
}

.bg-hologram-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(255, 20, 147, 0.1) 1px, transparent 1px),
    radial-gradient(circle at 75% 75%, rgba(0, 255, 136, 0.1) 1px, transparent 1px);
  background-size: 40px 40px;
  animation: hologram-pulse 6s ease-in-out infinite;
}

@keyframes hologram-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.bg-energy-field {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(ellipse at 30% 30%, rgba(0, 212, 255, 0.05) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 70%, rgba(255, 20, 147, 0.05) 0%, transparent 50%);
  animation: energy-field-pulse 10s ease-in-out infinite;
}

@keyframes energy-field-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.1); opacity: 0.6; }
}

.bg-quantum-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.quantum-particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #00d4ff;
  border-radius: 50%;
  animation: quantum-float 8s linear infinite;
}

.quantum-particle:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
.quantum-particle:nth-child(2) { top: 20%; left: 80%; animation-delay: 1s; }
.quantum-particle:nth-child(3) { top: 30%; left: 20%; animation-delay: 2s; }
.quantum-particle:nth-child(4) { top: 40%; left: 70%; animation-delay: 3s; }
.quantum-particle:nth-child(5) { top: 50%; left: 15%; animation-delay: 4s; }
.quantum-particle:nth-child(6) { top: 60%; left: 85%; animation-delay: 5s; }
.quantum-particle:nth-child(7) { top: 70%; left: 25%; animation-delay: 6s; }
.quantum-particle:nth-child(8) { top: 80%; left: 75%; animation-delay: 7s; }
.quantum-particle:nth-child(9) { top: 90%; left: 35%; animation-delay: 0.5s; }
.quantum-particle:nth-child(10) { top: 15%; left: 45%; animation-delay: 1.5s; }
.quantum-particle:nth-child(11) { top: 25%; left: 55%; animation-delay: 2.5s; }
.quantum-particle:nth-child(12) { top: 35%; left: 65%; animation-delay: 3.5s; }
.quantum-particle:nth-child(13) { top: 45%; left: 35%; animation-delay: 4.5s; }
.quantum-particle:nth-child(14) { top: 55%; left: 45%; animation-delay: 5.5s; }
.quantum-particle:nth-child(15) { top: 65%; left: 55%; animation-delay: 6.5s; }
.quantum-particle:nth-child(16) { top: 75%; left: 65%; animation-delay: 7.5s; }
.quantum-particle:nth-child(17) { top: 85%; left: 35%; animation-delay: 0.3s; }
.quantum-particle:nth-child(18) { top: 95%; left: 45%; animation-delay: 1.3s; }
.quantum-particle:nth-child(19) { top: 5%; left: 55%; animation-delay: 2.3s; }
.quantum-particle:nth-child(20) { top: 15%; left: 65%; animation-delay: 3.3s; }

@keyframes quantum-float {
  0% {
    transform: translateY(0) translateX(0) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
    transform: translateY(-10px) translateX(10px) scale(1);
  }
  90% {
    opacity: 1;
    transform: translateY(-30px) translateX(30px) scale(1);
  }
  100% {
    transform: translateY(-50px) translateX(50px) scale(0);
    opacity: 0;
  }
}

.flow-header {
  text-align: center;
  margin-bottom: 40px;
  position: relative;
  z-index: 1;
}

.header-glow {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 60px;
  background: radial-gradient(ellipse, rgba(0, 212, 255, 0.3), transparent 70%);
  border-radius: 50%;
  animation: header-glow-pulse 3s ease-in-out infinite;
}

@keyframes header-glow-pulse {
  0%, 100% { opacity: 0.3; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.6; transform: translateX(-50%) scale(1.1); }
}

.flow-title {
  position: relative;
  font-size: 28px;
  font-weight: 700;
  color: #00d4ff;
  margin-bottom: 15px;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
  display: inline-block;
}

.title-text {
  position: relative;
  z-index: 2;
}

.title-scanner {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: title-scan 4s linear infinite;
}

@keyframes title-scan {
  0% { left: -100%; }
  100% { left: 100%; }
}

.flow-subtitle {
  font-size: 16px;
  color: #a0a0ff;
  opacity: 0.8;
  line-height: 1.5;
  margin-bottom: 20px;
}

.header-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px 20px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  backdrop-filter: blur(5px);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  margin-bottom: 5px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #a0a0ff;
  opacity: 0.8;
}

.flow-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 30px 0;
  position: relative;
  z-index: 1;
  flex-wrap: wrap;
  gap: 20px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 25px;
  background: linear-gradient(135deg, rgba(10, 20, 50, 0.9) 0%, rgba(20, 35, 80, 0.9) 100%);
  border-radius: 20px;
  border: 2px solid rgba(0, 212, 255, 0.2);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  min-width: 140px;
  transform: translateZ(0);
  backdrop-filter: blur(5px);
}

.flow-step:hover {
  transform: translateZ(15px) scale(1.08);
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 
    0 15px 35px rgba(0, 0, 0, 0.6),
    0 0 30px rgba(0, 212, 255, 0.4),
    0 0 60px rgba(255, 20, 147, 0.2);
}

.flow-step.active {
  border-color: #00d4ff;
  box-shadow: 
    0 0 40px rgba(0, 212, 255, 0.6),
    0 0 80px rgba(0, 212, 255, 0.3),
    0 15px 35px rgba(0, 0, 0, 0.6);
  background: linear-gradient(135deg, rgba(0, 100, 150, 0.95) 0%, rgba(0, 150, 200, 0.95) 100%);
  transform: translateZ(20px) scale(1.1);
}

.flow-step.completed {
  border-color: #00ff88;
  background: linear-gradient(135deg, rgba(0, 100, 80, 0.95) 0%, rgba(0, 150, 120, 0.95) 100%);
  box-shadow: 
    0 0 30px rgba(0, 255, 136, 0.5),
    0 0 60px rgba(0, 255, 136, 0.2);
}

.step-hologram {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  border-radius: 25px;
  background: linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.1) 50%, transparent 70%);
  animation: hologram-sweep 3s linear infinite;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.flow-step.active .step-hologram {
  opacity: 1;
}

@keyframes hologram-sweep {
  0% { transform: translateX(-100%) rotate(0deg); }
  100% { transform: translateX(100%) rotate(360deg); }
}

.step-icon {
  width: 70px;
  height: 70px;
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  position: relative;
  box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
  animation: icon-float 3s ease-in-out infinite;
  overflow: hidden;
}

.flow-step.active .step-icon {
  background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
  box-shadow: 
    0 8px 25px rgba(0, 255, 136, 0.5),
    0 0 30px rgba(0, 255, 136, 0.3);
  animation: icon-pulse 2s ease-in-out infinite;
}

.flow-step.completed .step-icon {
  background: linear-gradient(135deg, #00ff88 0%, #00cc66 100%);
  box-shadow: 
    0 8px 25px rgba(0, 255, 136, 0.5),
    0 0 30px rgba(0, 255, 136, 0.3);
}

.icon-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(circle, #fff, rgba(0, 212, 255, 0.8));
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  animation: core-pulse 2s ease-in-out infinite;
}

@keyframes core-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.2); }
}

.icon-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 2px solid transparent;
  animation: ring-rotate 4s linear infinite;
}

.ring-1 {
  width: 50px;
  height: 50px;
  transform: translate(-50%, -50%);
  border-top-color: #00d4ff;
  border-right-color: #ff1493;
  animation-duration: 3s;
}

.ring-2 {
  width: 60px;
  height: 60px;
  transform: translate(-50%, -50%);
  border-bottom-color: #00d4ff;
  border-left-color: #ff1493;
  animation-duration: 4s;
  animation-direction: reverse;
}

.ring-3 {
  width: 70px;
  height: 70px;
  transform: translate(-50%, -50%);
  border-top-color: #ff1493;
  border-left-color: #00d4ff;
  animation-duration: 5s;
}

@keyframes ring-rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.step-icon i {
  font-size: 28px;
  color: white;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
  z-index: 2;
  position: relative;
}

.step-content {
  text-align: center;
}

.step-title {
  font-size: 16px;
  font-weight: 600;
  color: #e0e0ff;
  margin-bottom: 5px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.step-desc {
  font-size: 12px;
  color: #a0a0ff;
  opacity: 0.8;
  margin-bottom: 15px;
}

.step-progress {
  width: 100%;
  height: 4px;
  background: rgba(0, 212, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #ff1493);
  border-radius: 2px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
  animation: progress-shine 2s linear infinite;
}

@keyframes progress-shine {
  0% { left: -100%; }
  100% { left: 100%; }
}

.step-energy-beams {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  pointer-events: none;
}

.energy-beam {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 50px;
  background: linear-gradient(to top, transparent, #00d4ff, #ff1493, transparent);
  transform-origin: center bottom;
  opacity: 0;
  transition: all 0.3s ease;
}

.flow-step.active .energy-beam {
  opacity: 1;
  animation: beam-rotate 3s linear infinite;
}

.energy-beam:nth-child(1) { transform: translate(-50%, -50%) rotate(0deg); }
.energy-beam:nth-child(2) { transform: translate(-50%, -50%) rotate(30deg); }
.energy-beam:nth-child(3) { transform: translate(-50%, -50%) rotate(60deg); }
.energy-beam:nth-child(4) { transform: translate(-50%, -50%) rotate(90deg); }
.energy-beam:nth-child(5) { transform: translate(-50%, -50%) rotate(120deg); }
.energy-beam:nth-child(6) { transform: translate(-50%, -50%) rotate(150deg); }
.energy-beam:nth-child(7) { transform: translate(-50%, -50%) rotate(180deg); }
.energy-beam:nth-child(8) { transform: translate(-50%, -50%) rotate(210deg); }
.energy-beam:nth-child(9) { transform: translate(-50%, -50%) rotate(240deg); }
.energy-beam:nth-child(10) { transform: translate(-50%, -50%) rotate(270deg); }
.energy-beam:nth-child(11) { transform: translate(-50%, -50%) rotate(300deg); }
.energy-beam:nth-child(12) { transform: translate(-50%, -50%) rotate(330deg); }

@keyframes beam-rotate {
  0% { transform: translate(-50%, -50%) rotate(0deg) scale(1); }
  50% { transform: translate(-50%, -50%) rotate(180deg) scale(1.2); }
  100% { transform: translate(-50%, -50%) rotate(360deg) scale(1); }
}

.step-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 15px;
  background: radial-gradient(circle at center, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.flow-step.active .step-glow {
  opacity: 1;
  animation: glow-pulse 2s ease-in-out infinite;
}

.step-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle-dot {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #00d4ff;
  border-radius: 50%;
  opacity: 0;
  animation: particle-float 4s ease-in-out infinite;
}

.particle-dot:nth-child(1) { top: 20%; left: 20%; animation-delay: 0s; }
.particle-dot:nth-child(2) { top: 60%; right: 20%; animation-delay: 1s; }
.particle-dot:nth-child(3) { bottom: 20%; left: 30%; animation-delay: 2s; }
.particle-dot:nth-child(4) { top: 40%; right: 30%; animation-delay: 3s; }
.particle-dot:nth-child(5) { top: 30%; left: 40%; animation-delay: 0.5s; }
.particle-dot:nth-child(6) { bottom: 40%; right: 40%; animation-delay: 1.5s; }

.flow-connector {
  flex: 1;
  height: 6px;
  position: relative;
  opacity: 0.3;
  transition: opacity 0.3s ease;
  min-width: 80px;
}

.flow-connector.active {
  opacity: 1;
}

.connector-core {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #ff1493, #00d4ff);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.connector-line {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.connector-pulse {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, #ffffff 50%, transparent 100%);
  animation: connector-pulse 2s ease-in-out infinite;
}

.flow-connector.active .connector-pulse {
  animation: connector-pulse 1s ease-in-out infinite;
}

.connector-data-stream {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.data-bit {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #fff;
  border-radius: 50%;
  animation: data-bit-flow 2s linear infinite;
  opacity: 0;
}

.flow-connector.active .data-bit {
  opacity: 1;
}

.data-bit:nth-child(1) { top: 20%; animation-delay: 0s; }
.data-bit:nth-child(2) { top: 40%; animation-delay: 0.4s; }
.data-bit:nth-child(3) { top: 60%; animation-delay: 0.8s; }
.data-bit:nth-child(4) { top: 80%; animation-delay: 1.2s; }
.data-bit:nth-child(5) { top: 50%; animation-delay: 1.6s; }

@keyframes data-bit-flow {
  0% { left: -10px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: 100%; opacity: 0; }
}



.main-flow-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(64, 128, 255, 0.3);
  gap: 20px;
}

/* 情绪识别容器样式 */
.emotion-recognition-container {
  display: flex;
  justify-content: space-between;
  gap: 30px;
  margin: 20px 0;
  flex-wrap: wrap;
}

.brainflow-status-panel {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin: 24px 0 8px;
  padding: 18px;
  border: 1px solid rgba(0, 212, 255, 0.28);
  border-radius: 16px;
  background: rgba(4, 18, 42, 0.72);
  box-shadow: 0 0 24px rgba(0, 212, 255, 0.12);
}

.brainflow-status-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(0, 212, 255, 0.08);
}

.brainflow-status-item span {
  color: rgba(210, 235, 255, 0.72);
  font-size: 13px;
}

.brainflow-status-item strong {
  color: #00d4ff;
  font-size: 16px;
  font-weight: 700;
  word-break: break-all;
}

.brainflow-model-path {
  font-size: 11px;
  max-width: 420px;
  display: inline-block;
}

.workflow-hint {
  margin: 16px 0;
  padding: 12px 16px;
  border: 1px solid rgba(230, 162, 60, 0.35);
  border-radius: 12px;
  color: #ffd58a;
  background: rgba(230, 162, 60, 0.12);
  box-shadow: 0 0 18px rgba(230, 162, 60, 0.08);
  font-size: 14px;
}

.visualization-hint {
  margin-bottom: 10px;
}

.viz-model-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid rgba(34, 153, 255, 0.25);
  background: rgba(8, 14, 36, 0.55);
}
.viz-model-label {
  font-size: 12px;
  font-weight: 700;
  color: #88ccff;
  white-space: nowrap;
}
.viz-model-select {
  width: 180px;
}
.viz-model-log-tag {
  font-size: 10px;
  color: #8899bb;
  margin-left: auto;
}

.emotion-card {
  flex: 1;
  min-width: 280px;
  background: linear-gradient(135deg, rgba(10, 20, 50, 0.95) 0%, rgba(20, 35, 80, 0.95) 100%);
  border-radius: 25px;
  padding: 35px;
  border: 2px solid;
  border-image: linear-gradient(45deg, #00d4ff, #ff1493, #00d4ff) 1;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(15px);
  text-align: center;
  box-shadow: 
    0 15px 35px rgba(0, 0, 0, 0.6),
    0 0 20px rgba(0, 212, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.emotion-card:hover {
  transform: translateY(-10px) scale(1.05);
  border-color: rgba(64, 128, 255, 0.6);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.6),
    0 0 30px rgba(64, 128, 255, 0.4);
}

.emotion-card.active {
  transform: translateY(-15px) scale(1.1);
  border-color: #00d4ff;
  box-shadow: 
    0 0 40px rgba(0, 212, 255, 0.6),
    0 0 80px rgba(0, 212, 255, 0.3),
    0 20px 40px rgba(0, 0, 0, 0.6);
}

.emotion-card.positive.active {
  border-color: #52c41a;
  box-shadow: 
    0 0 40px rgba(82, 196, 26, 0.6),
    0 0 80px rgba(82, 196, 26, 0.3);
}

.emotion-card.neutral.active {
  border-color: #1890ff;
  box-shadow: 
    0 0 40px rgba(24, 144, 255, 0.6),
    0 0 80px rgba(24, 144, 255, 0.3);
}

.emotion-card.negative.active {
  border-color: #ff4d4f;
  box-shadow: 
    0 0 40px rgba(255, 77, 79, 0.6),
    0 0 80px rgba(255, 77, 79, 0.3);
}



.emotion-content {
  text-align: center;
  position: relative;
  z-index: 1;
}

.emotion-title {
  font-size: 20px;
  font-weight: 700;
  color: #00d4ff;
  margin-bottom: 8px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.emotion-card.positive .emotion-title {
  color: #52c41a;
  text-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

.emotion-card.neutral .emotion-title {
  color: #1890ff;
  text-shadow: 0 0 10px rgba(24, 144, 255, 0.5);
}

.emotion-card.negative .emotion-title {
  color: #ff4d4f;
  text-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
}

.emotion-desc {
  font-size: 14px;
  color: #a0a0ff;
  opacity: 0.8;
  margin-bottom: 20px;
}

.emotion-progress {
  margin-bottom: 15px;
}

.emotion-percentage {
  font-size: 24px;
  font-weight: 700;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.emotion-card.positive .emotion-percentage {
  color: #52c41a;
  text-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

.emotion-card.neutral .emotion-percentage {
  color: #1890ff;
  text-shadow: 0 0 10px rgba(24, 144, 255, 0.5);
}

.emotion-card.positive .emotion-percentage {
  color: #52c41a;
  text-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

.emotion-card.neutral .emotion-percentage {
  color: #1890ff;
  text-shadow: 0 0 10px rgba(24, 144, 255, 0.5);
}

.emotion-card.negative .emotion-percentage {
  color: #ff4d4f;
  text-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
}

.emotion-card.positive .emotion-percentage {
  color: #52c41a;
  text-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

.emotion-card.neutral .emotion-percentage {
  color: #1890ff;
  text-shadow: 0 0 10px rgba(24, 144, 255, 0.5);
}

.emotion-card.negative .emotion-percentage {
  color: #ff4d4f;
  text-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
}

.emotion-card.negative .emotion-percentage {
  color: #ff4d4f;
  text-shadow: 0 0 10px rgba(255, 77, 79, 0.5);
}

.emotion-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 20px;
  background: radial-gradient(circle at center, rgba(0, 212, 255, 0.1), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.emotion-card.active .emotion-glow {
  opacity: 1;
  animation: glow-pulse 2s ease-in-out infinite;
}

.emotion-card.positive.active .emotion-glow {
  background: radial-gradient(circle at center, rgba(82, 196, 26, 0.1), transparent 70%);
}

.emotion-card.neutral.active .emotion-glow {
  background: radial-gradient(circle at center, rgba(24, 144, 255, 0.1), transparent 70%);
}

.emotion-card.negative.active .emotion-glow {
  background: radial-gradient(circle at center, rgba(255, 77, 79, 0.1), transparent 70%);
}

/* 背景流动效果 */
.emotion-bg-flow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.flow-particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: #00d4ff;
  border-radius: 50%;
  animation: flow-float 6s linear infinite;
  opacity: 0;
}

.emotion-card.positive .flow-particle {
  background: #52c41a;
}

.emotion-card.neutral .flow-particle {
  background: #1890ff;
}

.emotion-card.negative .flow-particle {
  background: #ff4d4f;
}

.flow-particle:nth-child(1) { top: 10%; left: 10%; animation-delay: 0s; }
.flow-particle:nth-child(2) { top: 20%; left: 80%; animation-delay: 1s; }
.flow-particle:nth-child(3) { top: 30%; left: 20%; animation-delay: 2s; }
.flow-particle:nth-child(4) { top: 40%; left: 70%; animation-delay: 3s; }
.flow-particle:nth-child(5) { top: 50%; left: 15%; animation-delay: 4s; }
.flow-particle:nth-child(6) { top: 60%; left: 85%; animation-delay: 5s; }
.flow-particle:nth-child(7) { top: 70%; left: 25%; animation-delay: 0.5s; }
.flow-particle:nth-child(8) { top: 80%; left: 75%; animation-delay: 1.5s; }
.flow-particle:nth-child(9) { top: 90%; left: 35%; animation-delay: 2.5s; }
.flow-particle:nth-child(10) { top: 15%; left: 45%; animation-delay: 3.5s; }
.flow-particle:nth-child(11) { top: 25%; left: 55%; animation-delay: 4.5s; }
.flow-particle:nth-child(12) { top: 35%; left: 65%; animation-delay: 5.5s; }

@keyframes flow-float {
  0% {
    transform: translateY(0) translateX(0) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
    transform: translateY(-10px) translateX(10px) scale(1);
  }
  90% {
    opacity: 1;
    transform: translateY(-30px) translateX(30px) scale(1);
  }
  100% {
    transform: translateY(-50px) translateX(50px) scale(0);
    opacity: 0;
  }
}

/* 新的图标样式 */
.emotion-icon {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 25px;
  position: relative;
  box-shadow: 
    0 15px 35px rgba(0, 212, 255, 0.4),
    0 0 30px rgba(0, 212, 255, 0.2);
  transition: all 0.3s ease;
  overflow: hidden;
}

.emotion-card.positive .emotion-icon {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  box-shadow: 
    0 15px 35px rgba(82, 196, 26, 0.4),
    0 0 30px rgba(82, 196, 26, 0.2);
}

.emotion-card.neutral .emotion-icon {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  box-shadow: 
    0 15px 35px rgba(24, 144, 255, 0.4),
    0 0 30px rgba(24, 144, 255, 0.2);
}

.emotion-card.negative .emotion-icon {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  box-shadow: 
    0 15px 35px rgba(255, 77, 79, 0.4),
    0 0 30px rgba(255, 77, 79, 0.2);
}

.emotion-card.active .emotion-icon {
  transform: scale(1.2);
  animation: icon-pulse 2s ease-in-out infinite;
}

.icon-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle, #fff, rgba(255, 255, 255, 0.8));
  box-shadow: 0 0 25px rgba(255, 255, 255, 0.8);
  animation: core-pulse 2s ease-in-out infinite;
}

.icon-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 2px solid transparent;
  animation: ring-rotate 4s linear infinite;
}

.ring-1 {
  width: 70px;
  height: 70px;
  transform: translate(-50%, -50%);
  border-top-color: currentColor;
  border-right-color: rgba(255, 255, 255, 0.5);
  animation-duration: 3s;
}

.ring-2 {
  width: 85px;
  height: 85px;
  transform: translate(-50%, -50%);
  border-bottom-color: currentColor;
  border-left-color: rgba(255, 255, 255, 0.5);
  animation-duration: 4s;
  animation-direction: reverse;
}

.ring-3 {
  width: 100px;
  height: 100px;
  transform: translate(-50%, -50%);
  border-top-color: rgba(255, 255, 255, 0.5);
  border-left-color: currentColor;
  animation-duration: 5s;
}

/* 表情样式 */
.face-expression {
  position: relative;
  width: 60px;
  height: 60px;
  z-index: 2;
}

.eyes {
  position: absolute;
  top: 15px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  padding: 0 10px;
}

.eye {
  width: 8px;
  height: 8px;
  background: #333;
  border-radius: 50%;
  position: relative;
}

.eye::after {
  content: '';
  position: absolute;
  top: 1px;
  left: 1px;
  width: 3px;
  height: 3px;
  background: #fff;
  border-radius: 50%;
}

/* 大笑脸眼睛 */
.happy-eye {
  transform: scale(0.8);
}

.happy-eye::before {
  content: '';
  position: absolute;
  top: -1px;
  left: -1px;
  width: 10px;
  height: 10px;
  border: 2px solid #333;
  border-bottom: none;
  border-right: none;
  border-radius: 10px 0 0 0;
}

/* 大哭脸眼睛 */
.crying-eye {
  transform: scale(1.2);
}

.crying-eye::before {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  width: 14px;
  height: 14px;
  border: 2px solid #333;
  border-top: none;
  border-left: none;
  border-radius: 0 0 14px 0;
}

.crying-eye::after {
  content: '';
  position: absolute;
  top: 8px;
  left: 2px;
  width: 2px;
  height: 6px;
  background: #333;
  border-radius: 1px;
  animation: tear-drop 2s ease-in-out infinite;
}

@keyframes tear-drop {
  0%, 100% { opacity: 0; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(4px); }
}

.mouth {
  position: absolute;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 10px;
  border: 2px solid #333;
  border-top: none;
  border-radius: 0 0 20px 20px;
}

.happy-mouth {
  border-radius: 0 0 25px 25px;
  border-bottom: 3px solid #333;
  border-top: 3px solid transparent;
  height: 12px;
  width: 25px;
}

.neutral-mouth {
  width: 16px;
  height: 2px;
  border: none;
  background: #333;
  border-radius: 1px;
}

.crying-mouth {
  border-radius: 25px 25px 0 0;
  border-top: 3px solid #333;
  border-bottom: 3px solid transparent;
  height: 12px;
  width: 25px;
}

/* 进度条样式 */
.progress-container {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #ff1493);
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}

.emotion-card.positive .progress-bar {
  background: linear-gradient(90deg, #52c41a, #73d13d);
}

.emotion-card.neutral .progress-bar {
  background: linear-gradient(90deg, #1890ff, #40a9ff);
}

.emotion-card.negative .progress-bar {
  background: linear-gradient(90deg, #ff4d4f, #ff7875);
}

.progress-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: progress-shine 2s linear infinite;
}

/* 能量光束 */
.emotion-energy-beams {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 150px;
  height: 150px;
  pointer-events: none;
}

.emotion-card.active .energy-beam {
  opacity: 1;
  animation: beam-rotate 3s linear infinite;
}

.energy-beam {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 60px;
  background: linear-gradient(to top, transparent, currentColor, transparent);
  transform-origin: center bottom;
  opacity: 0;
  transition: all 0.3s ease;
}

.emotion-card.positive .energy-beam {
  color: #52c41a;
}

.emotion-card.neutral .energy-beam {
  color: #1890ff;
}

.emotion-card.negative .energy-beam {
  color: #ff4d4f;
}

.energy-beam:nth-child(1) { transform: translate(-50%, -50%) rotate(0deg); }
.energy-beam:nth-child(2) { transform: translate(-50%, -50%) rotate(45deg); }
.energy-beam:nth-child(3) { transform: translate(-50%, -50%) rotate(90deg); }
.energy-beam:nth-child(4) { transform: translate(-50%, -50%) rotate(135deg); }
.energy-beam:nth-child(5) { transform: translate(-50%, -50%) rotate(180deg); }
.energy-beam:nth-child(6) { transform: translate(-50%, -50%) rotate(225deg); }
.energy-beam:nth-child(7) { transform: translate(-50%, -50%) rotate(270deg); }
.energy-beam:nth-child(8) { transform: translate(-50%, -50%) rotate(315deg); }

/* 动画定义 */
@keyframes icon-float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
}

@keyframes icon-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes glow-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

@keyframes particle-float {
  0%, 100% { 
    transform: translateY(0px) scale(1);
    opacity: 0;
  }
  25% { 
    transform: translateY(-10px) scale(1.2);
    opacity: 1;
  }
  75% { 
    transform: translateY(-20px) scale(0.8);
    opacity: 0.5;
  }
}

@keyframes connector-pulse {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .feature-learning-nav {
    flex-direction: column;
    gap: 15px;
  }
  
  .feature-step {
    width: 100%;
    max-width: 300px;
  }
  
  .feature-connector {
    width: 4px;
    height: 30px;
    transform: rotate(90deg);
  }
  
  .feature-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .main-flow-controls {
    flex-direction: column;
    gap: 15px;
    align-items: center;
  }
  
  .emotion-recognition-container {
    flex-direction: column;
    gap: 20px;
  }
  
  .emotion-card {
    min-width: auto;
    width: 100%;
  }
}

/* 全局导航控制面板样式 */
.global-nav-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 280px;
  background: linear-gradient(135deg, rgba(10, 15, 40, 0.95) 0%, rgba(20, 30, 80, 0.95) 100%);
  border-radius: 12px;
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.6), 0 0 15px rgba(64, 128, 255, 0.3);
  backdrop-filter: blur(10px);
  z-index: 1000;
  transition: all 0.3s ease;
  transform: translateZ(10px);
}

.global-nav-panel:hover {
  transform: translateZ(15px) scale(1.02);
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(64, 128, 255, 0.5);
}

.nav-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(64, 128, 255, 0.2);
  background: linear-gradient(90deg, rgba(64, 128, 255, 0.1), rgba(143, 148, 251, 0.1));
  border-radius: 10px 10px 0 0;
}

.nav-panel-header h4 {
  color: #a0d2ff;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  text-shadow: 0 0 8px rgba(160, 210, 255, 0.5);
}

.nav-toggle-btn {
  background: rgba(64, 128, 255, 0.2);
  border: 1px solid rgba(64, 128, 255, 0.3);
  color: #a0d2ff;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-toggle-btn:hover {
  background: rgba(64, 128, 255, 0.3);
  border-color: rgba(64, 128, 255, 0.5);
  transform: scale(1.05);
}

.nav-panel-content {
  padding: 16px;
}

.nav-quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.nav-action-btn {
  background: rgba(15, 25, 60, 0.6);
  border: 1px solid rgba(64, 128, 255, 0.2);
  color: #c0c9ff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 11px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.nav-action-btn:hover {
  background: rgba(64, 128, 255, 0.2);
  border-color: rgba(64, 128, 255, 0.4);
  transform: translateY(-2px);
}

.nav-action-btn.active {
  background: linear-gradient(135deg, #4e54c8, #8f94fb);
  border-color: #8f94fb;
  color: white;
  box-shadow: 0 0 15px rgba(143, 148, 251, 0.5);
}

.nav-action-btn i {
  font-size: 14px;
}

.nav-controls {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.nav-control-btn {
  background: linear-gradient(135deg, #2d388a, #4e54c8);
  border: none;
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-control-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4e54c8, #8f94fb);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(78, 84, 200, 0.4);
}

.nav-control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.nav-control-btn.reset-btn {
  background: linear-gradient(135deg, #d63031, #e17055);
}

.nav-control-btn.reset-btn:hover {
  background: linear-gradient(135deg, #e17055, #d63031);
}

/* 可视化展示样式 */
.section-subtitle {
  font-size: 18px;
  margin-bottom: 15px;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-subtitle i {
  font-size: 18px;
}



.training-monitor-section,
.tsne-visualization-section {
  margin-bottom: 25px;
  padding: 20px;
  background: rgba(15, 25, 60, 0.6);
  border-radius: 15px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 10;
}

.cyberpunk-tsne {
  position: relative;
  overflow: hidden;
}

.tsne-glow-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 15px;
  background: linear-gradient(45deg, transparent 30%, rgba(75, 108, 183, 0.3) 50%, transparent 70%);
  animation: tsne-border-glow 4s ease-in-out infinite;
  pointer-events: none;
}

@keyframes tsne-border-glow {
  0%, 100% {
    opacity: 0.2;
  }
  50% {
    opacity: 0.6;
  }
}

.tsne-corner-decor {
  position: absolute;
  width: 25px;
  height: 25px;
  border: 2px solid #4b6cb7;
  opacity: 0.7;
}

.tsne-corner-decor.top-left {
  top: 15px;
  left: 15px;
  border-right: none;
  border-bottom: none;
}

.tsne-corner-decor.top-right {
  top: 15px;
  right: 15px;
  border-left: none;
  border-bottom: none;
}

.tsne-corner-decor.bottom-left {
  bottom: 15px;
  left: 15px;
  border-right: none;
  border-top: none;
}

.tsne-corner-decor.bottom-right {
  bottom: 15px;
  right: 15px;
  border-left: none;
  border-top: none;
}

.chart-container {
  background: rgba(10, 15, 40, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  height: 300px;
  position: relative;
}

.chart-title {
  font-size: 16px;
  color: #a0d2ff;
  margin-bottom: 15px;
  text-align: center;
}





/* 可视化展示科技感特效 */
.visualization-wrapper {
  position: relative;
  overflow: visible;
  min-height: 100%;
  padding-bottom: 24px;
}

/* 粒子背景 */
.particle-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: #00d4ff;
  border-radius: 50%;
  animation: particle-float 8s infinite linear;
  opacity: 0.6;
}

.particle:nth-child(odd) {
  background: #4b6cb7;
  animation-duration: 12s;
}

.particle:nth-child(3n) {
  background: #ff6b6b;
  animation-duration: 10s;
}

@keyframes particle-float {
  0% {
    transform: translateY(100vh) translateX(0);
    opacity: 0;
  }
  10% {
    opacity: 0.8;
  }
  90% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100px) translateX(100px);
    opacity: 0;
  }
}

/* 数据流特效 */
.data-stream-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

.data-stream {
  position: absolute;
  width: 1px;
  height: 100px;
  background: linear-gradient(to bottom, transparent, #00d4ff, transparent);
  animation: data-stream-flow 4s infinite linear;
  opacity: 0.4;
}

.data-stream:nth-child(1) { left: 10%; animation-delay: 0s; }
.data-stream:nth-child(2) { left: 20%; animation-delay: 0.5s; }
.data-stream:nth-child(3) { left: 30%; animation-delay: 1s; }
.data-stream:nth-child(4) { left: 40%; animation-delay: 1.5s; }
.data-stream:nth-child(5) { left: 50%; animation-delay: 2s; }
.data-stream:nth-child(6) { left: 60%; animation-delay: 2.5s; }
.data-stream:nth-child(7) { left: 70%; animation-delay: 3s; }
.data-stream:nth-child(8) { left: 80%; animation-delay: 3.5s; }

@keyframes data-stream-flow {
  0% {
    transform: translateY(-100px);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(100vh);
    opacity: 0;
  }
}

/* 扫描线特效 */
.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
  animation: scan-line-sweep 3s infinite linear;
  z-index: 3;
  pointer-events: none;
}

@keyframes scan-line-sweep {
  0% {
    transform: translateY(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(100vh);
    opacity: 0;
  }
}

/* 赛博朋克标题 */
.cyberpunk-title {
  position: relative;
  z-index: 10;
}

.title-glow {
  background: linear-gradient(45deg, #00d4ff, #4b6cb7, #ff6b6b);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: title-glow-shift 3s ease-in-out infinite;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
}

@keyframes title-glow-shift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.title-underline {
  width: 0;
  height: 3px;
  background: linear-gradient(90deg, #00d4ff, #4b6cb7);
  margin-top: 10px;
  animation: title-underline-expand 2s ease-out forwards;
}

@keyframes title-underline-expand {
  to {
    width: 100%;
  }
}

/* 训练过程分析模块样式 */
.training-analysis-container {
  background: rgba(10, 15, 40, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  margin-bottom: 20px;
  position: relative;
  z-index: 10;
}

.cyberpunk-analysis {
  position: relative;
  overflow: hidden;
}

.analysis-glow-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  background: linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.3) 50%, transparent 70%);
  animation: analysis-border-glow 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes analysis-border-glow {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.8;
  }
}

.analysis-corner-decor {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid #00d4ff;
  opacity: 0.6;
}

.analysis-corner-decor.top-left {
  top: 10px;
  left: 10px;
  border-right: none;
  border-bottom: none;
}

.analysis-corner-decor.top-right {
  top: 10px;
  right: 10px;
  border-left: none;
  border-bottom: none;
}

.analysis-corner-decor.bottom-left {
  bottom: 10px;
  left: 10px;
  border-right: none;
  border-top: none;
}

.analysis-corner-decor.bottom-right {
  bottom: 10px;
  right: 10px;
  border-left: none;
  border-top: none;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.analysis-title {
  color: #a0d2ff;
  font-size: 1.3rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.analysis-actions {
  display: flex;
  gap: 10px;
}

.analysis-btn {
  background: rgba(64, 128, 255, 0.2);
  border: 1px solid rgba(64, 128, 255, 0.3);
  color: #a0d2ff;
  padding: 8px 15px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
}

.analysis-btn:hover {
  background: rgba(64, 128, 255, 0.3);
  border-color: rgba(64, 128, 255, 0.5);
  transform: translateY(-2px);
}

.analysis-btn.active {
  background: linear-gradient(90deg, #4b6cb7, #182848);
  border-color: #4b6cb7;
  color: white;
  box-shadow: 0 0 15px rgba(75, 108, 183, 0.5);
}

.analysis-content {
  position: relative;
  height: 350px;
}

.visualization-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  margin: 20px 0;
  padding: 40px 24px;
  border-radius: 12px;
  border: 1px dashed rgba(64, 128, 255, 0.35);
  background: rgba(8, 12, 28, 0.55);
  color: #8a9bb4;
  text-align: center;
}

.visualization-empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.55;
  color: #409eff;
}

.visualization-empty-state p {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  opacity: 0.85;
}

.analysis-placeholder {
  position: absolute;
  inset: 0;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #8a9bb4;
  background: rgba(8, 12, 28, 0.72);
}

.analysis-placeholder i {
  font-size: 48px;
  margin-bottom: 15px;
  opacity: 0.5;
}

.analysis-placeholder p {
  font-size: 16px;
  margin: 0;
  opacity: 0.8;
}

.analysis-chart-wrapper {
  height: 100%;
  min-height: 300px;
}

.analysis-chart {
  height: 100%;
  min-height: 300px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.3) 0%, rgba(10, 15, 40, 0.4) 100%);
  border-radius: 12px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  overflow: hidden;
  position: relative;
  box-shadow: 
    0 0 20px rgba(0, 212, 255, 0.2),
    inset 0 0 20px rgba(0, 212, 255, 0.1);
}

.analysis-chart-host {
  position: relative;
  width: 100%;
  height: 300px;
}

.analysis-chart-tooltip {
  position: absolute;
  z-index: 6;
  pointer-events: none;
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(10, 15, 40, 0.95);
  border: 1px solid rgba(0, 212, 255, 0.45);
  color: #c0c9ff;
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
  transform: translate(-50%, -100%);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}

.analysis-chart canvas {
  position: relative;
  z-index: 2;
  display: block;
  max-width: 100%;
  cursor: crosshair;
}

.analysis-chart::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(75, 108, 183, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

.analysis-chart-error {
  margin-top: 12px;
  text-align: center;
  color: #ff8e8e;
  font-size: 14px;
}

.analysis-chart:hover {
  border-color: rgba(0, 212, 255, 0.6);
  box-shadow: 
    0 0 30px rgba(0, 212, 255, 0.4),
    inset 0 0 30px rgba(0, 212, 255, 0.2);
  transform: scale(1.02);
}

.analysis-chart:hover canvas {
  filter: brightness(1.1) contrast(1.1);
}

/* 图表加载动画 */
.analysis-chart.loading {
  animation: chart-loading-pulse 2s ease-in-out infinite;
}

@keyframes chart-loading-pulse {
  0%, 100% {
    box-shadow: 
      0 0 20px rgba(0, 212, 255, 0.2),
      inset 0 0 20px rgba(0, 212, 255, 0.1);
  }
  50% {
    box-shadow: 
      0 0 40px rgba(0, 212, 255, 0.4),
      inset 0 0 40px rgba(0, 212, 255, 0.2);
  }
}

/* 图片轮播样式 */
.image-carousel-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: linear-gradient(135deg, rgba(10, 15, 40, 0.8) 0%, rgba(20, 30, 60, 0.6) 100%);
  border-radius: 12px;
  border: 2px solid rgba(0, 212, 255, 0.3);
  padding: 20px;
  min-height: 300px;
}

.carousel-image-wrapper {
  position: relative;
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.4) 0%, rgba(10, 15, 40, 0.6) 100%);
  border: 2px solid rgba(0, 212, 255, 0.3);
  min-height: 250px;
  box-shadow: inset 0 0 20px rgba(0, 212, 255, 0.1);
}

.carousel-image-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.05) 50%, transparent 70%);
  pointer-events: none;
  z-index: 1;
}

.carousel-image-wrapper .el-image {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.carousel-image-wrapper .el-image img {
  position: relative;
  z-index: 2;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.carousel-indicators {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}

.indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid rgba(0, 212, 255, 0.3);
}

.indicator.active {
  background: rgba(0, 212, 255, 0.8);
  border-color: rgba(0, 212, 255, 1);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.indicator:hover {
  background: rgba(0, 212, 255, 0.6);
  transform: scale(1.2);
}

.carousel-controls {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 10;
}

.carousel-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 212, 255, 0.8);
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
  z-index: 10;
}

.carousel-btn:hover {
  background: rgba(0, 212, 255, 1);
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.5);
}

.carousel-btn:active {
  transform: scale(0.95);
}

.carousel-btn i {
  font-size: 16px;
  font-weight: bold;
}

/* 外部轮播按钮样式 */
.carousel-btn.external-btn {
  position: relative;
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  background: rgba(0, 212, 255, 0.9);
  border: 2px solid rgba(0, 212, 255, 0.5);
  box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
}

.carousel-btn.external-btn:hover {
  background: rgba(0, 212, 255, 1);
  transform: scale(1.1);
  box-shadow: 0 8px 25px rgba(0, 212, 255, 0.6);
  border-color: rgba(0, 212, 255, 0.8);
}

.carousel-btn.external-btn i {
  font-size: 18px;
  font-weight: bold;
}

.prev-btn {
  left: 20px;
}

.next-btn {
  right: 20px;
}

.tsne-container {
  background: rgba(10, 15, 40, 0.8);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  height: 450px;
  position: relative;
}

.tsne-images-container {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 20px;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
}

.tsne-image-wrapper {
  position: relative;
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(10, 15, 40, 0.8);
  border: 2px solid rgba(64, 128, 255, 0.3);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
  transition: all 0.3s ease;
  padding: 15px;
  min-height: 350px;
}

.tsne-image-wrapper:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6);
  border-color: rgba(64, 128, 255, 0.6);
}

.tsne-image-title {
  position: absolute;
  top: 10px;
  left: 10px;
  right: 10px;
  background: linear-gradient(135deg, rgba(64, 128, 255, 0.9), rgba(78, 84, 200, 0.9));
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  color: white;
  padding: 8px 12px;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.tsne-image-wrapper .el-image {
  width: 100%;
  height: calc(100% - 60px);
  border-radius: 8px;
  overflow: hidden;
  margin-top: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

.tsne-image-wrapper img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  width: auto;
  height: auto;
  display: block;
}

.tsne-chart {
  position: relative;
  width: 100%;
  height: 220px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(64, 128, 255, 0.2);
  overflow: hidden;
}

.tsne-point {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: tsne-float 3s ease-in-out infinite;
}

.tsne-point.positive {
  background: #52c41a;
  box-shadow: 0 0 10px rgba(82, 196, 26, 0.8);
}

.tsne-point.neutral {
  background: #1890ff;
  box-shadow: 0 0 10px rgba(24, 144, 255, 0.8);
}

.tsne-point.negative {
  background: #ff4d4f;
  box-shadow: 0 0 10px rgba(255, 77, 79, 0.8);
}

.tsne-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #8a9bb4;
  font-size: 14px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-color.positive {
  background: #52c41a;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.6);
}

.legend-color.neutral {
  background: #1890ff;
  box-shadow: 0 0 8px rgba(24, 144, 255, 0.6);
}

.legend-color.negative {
  background: #ff4d4f;
  box-shadow: 0 0 8px rgba(255, 77, 79, 0.6);
}

@keyframes tsne-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

/* 训练分析样式 */
.training-stats-container {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  position: relative;
  z-index: 10;
}

.cyberpunk-stats {
  position: relative;
}

.stats-glow-effect {
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 70%);
  border-radius: 15px;
  animation: stats-glow-pulse 4s ease-in-out infinite;
  pointer-events: none;
}

@keyframes stats-glow-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.02);
  }
}

.stat-card {
  flex: 1;
  min-width: 180px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  text-align: center;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(64, 128, 255, 0.2);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-5px) scale(1.02);
  box-shadow: 0 15px 30px rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.5);
}

.stat-card:hover .stat-value {
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.8);
  animation: stat-value-pulse 0.6s ease-in-out;
}

@keyframes stat-value-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
}

.stat-card.overall::before {
  background: linear-gradient(90deg, #4b6cb7, #182848);
}

.stat-card.best::before {
  background: #28a745;
}

.stat-card.avg::before {
  background: #ffc107;
}

.stat-card.epoch::before {
  background: #17a2b8;
}

.stat-card.model::before {
  background: #6f42c1;
}

.stat-card.samples::before {
  background: #dc3545;
}

.stat-card h3 {
  color: #a0d2ff;
  margin-bottom: 10px;
  font-size: 1rem;
  font-weight: 600;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #00d4ff;
  line-height: 1.2;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.stat-desc {
  font-size: 0.9rem;
  color: #8a9bb4;
  margin-top: 5px;
}

/* 特征学习准确率显示样式 */
.feature-accuracy-info {
  margin-top: 8px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(255, 20, 147, 0.1));
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0, 212, 255, 0.2);
  animation: accuracy-fade-in 0.5s ease-in-out;
}

.accuracy-label {
  font-size: 0.75rem;
  color: #00d4ff;
  font-weight: 500;
  opacity: 0.9;
}

.accuracy-value {
  font-size: 0.85rem;
  color: #ff1493;
  font-weight: 600;
  text-shadow: 0 0 5px rgba(255, 20, 147, 0.5);
}

@keyframes accuracy-fade-in {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}







.training-config-container {
  background: rgba(10, 15, 40, 0.8);
  border-radius: 12px;
  padding: 25px;
  border: 1px solid rgba(64, 128, 255, 0.2);
}

.config-title {
  color: #a0d2ff;
  margin-bottom: 20px;
  font-size: 1.3rem;
  font-weight: 600;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
}

.config-item {
  background: rgba(15, 25, 60, 0.6);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid rgba(64, 128, 255, 0.2);
}

.config-key {
  font-weight: 600;
  color: #00d4ff;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.config-value {
  color: #c0c9ff;
  word-break: break-all;
  font-size: 0.9rem;
}

/* 响应式设计更新 */
@media (max-width: 768px) {
  .global-nav-panel {
    width: 85%;
    right: 7.5%;
    bottom: 10px;
  }
  
  .nav-quick-actions {
    grid-template-columns: 1fr;
  }
  
  .nav-controls {
    flex-direction: column;
  }
  
  .flow-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .flow-step {
    width: 100%;
    max-width: 280px;
    flex-direction: row;
    justify-content: flex-start;
    padding: 15px;
    gap: 15px;
  }
  
  .step-content {
    text-align: left;
  }
  
  .step-icon {
    margin-bottom: 0;
    flex-shrink: 0;
  }
  
  .step-title {
    text-align: left;
    font-size: 16px;
  }
  
  .step-desc {
    text-align: left;
    font-size: 12px;
  }
  
  .training-stats-container {
    flex-direction: column;
  }
  
  .stat-card {
    min-width: auto;
  }
  
  .analysis-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .analysis-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .analysis-content {
    height: 300px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .chart-actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .single-chart {
    min-height: 250px;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .emotion-recognition-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .emotion-card {
    min-width: auto;
    width: 100%;
  }
  
  .flow-connector {
    width: 4px;
    height: 30px;
    transform: rotate(90deg);
  }
  
  .connector-line {
    height: 100%;
    width: 2px;
  }
}

</style>