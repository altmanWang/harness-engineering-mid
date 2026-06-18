<template>
  <div v-if="content" class="thought-block">
    <div class="thought-header" @click="expanded = !expanded">
      <el-icon :size="14" class="thought-arrow" :class="{ expanded: expanded }"><component :is="ArrowDown" /></el-icon>
      <span class="thought-label">思考过程</span>
    </div>
    <div v-show="expanded" class="thought-content">
      <pre>{{ content }}</pre>
      <div v-if="isStreaming" class="thought-streaming-indicator">...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

defineProps<{
  content: string
  isStreaming: boolean
}>()

const expanded = ref(false)
</script>

<style scoped>
.thought-block {
  margin-top: 8px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  overflow: hidden;
}

.thought-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  font-size: 12px;
  color: #888;
  cursor: pointer;
  background: #f8f8f5;
  user-select: none;
  transition: background 0.15s ease;
}

.thought-header:hover {
  background: #f3f3f0;
}

.thought-header :deep(.el-icon) {
  transition: transform 0.2s ease;
}

.thought-arrow {
  transition: transform 0.2s ease;
}

.thought-arrow:not(.expanded) {
  transform: rotate(-90deg);
}

.thought-label {
  font-weight: 500;
}

.thought-content {
  padding: 10px 12px;
  background: #f8f8f5;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.thought-content pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: #555;
  max-height: 200px;
  overflow-y: auto;
  line-height: 1.6;
}

.thought-streaming-indicator {
  color: #888;
  font-size: 12px;
  margin-top: 4px;
  animation: thought-pulse 1.2s ease-in-out infinite;
}

@keyframes thought-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>
