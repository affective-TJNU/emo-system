<template>
  <div class="preview-panel">
    <div class="preview-header">
      <h2 class="preview-title">实时脑电特征预览</h2>
    </div>

    <div class="preview-body">
      <div class="topomap-wrap">
        <template v-if="ready && images.length">
          <img :src="images[currentImageIndex]" alt="" class="topo-img" @error="onImageError" />
          <div class="topo-dots">
            <span
              v-for="(_, i) in images"
              :key="i"
              class="dot"
              :class="{ on: i === currentImageIndex }"
              @click="$emit('select-image', i)"
            />
          </div>
        </template>
        <p v-else class="topo-empty">完成数据处理后显示脑地形图</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
defineProps<{
  loading: boolean;
  ready: boolean;
  images: string[];
  currentImageIndex: number;
}>();

defineEmits<{
  'select-image': [number];
}>();

function onImageError() {}
</script>

<style scoped>
.preview-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  min-height: var(--data-step-top-h, 96px);
  margin-bottom: 8px;
  flex-shrink: 0;
}

.preview-title {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

.preview-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
}

.topomap-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  border: 1px solid rgba(0, 150, 255, 0.2);
  border-radius: 8px;
  background: rgba(6, 10, 26, 0.8);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}
.topo-img {
  max-width: 96%;
  max-height: 85%;
  object-fit: contain;
}
.topo-empty {
  color: #8aa8cc;
  font-size: 12px;
}
.topo-dots {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(0, 150, 255, 0.3);
  cursor: pointer;
}
.dot.on {
  width: 14px;
  border-radius: 3px;
  background: #00aaff;
}
</style>
