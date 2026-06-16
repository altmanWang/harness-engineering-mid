<template>
  <div v-if="content" class="thought-block">
    <div class="thought-header" @click="expanded = !expanded">
      <el-icon :size="14"><component :is="expanded ? ArrowDown : ArrowRight" /></el-icon>
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
import { ArrowDown, ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  content: string
  isStreaming: boolean
}>()

const expanded = ref(false)
</script>

<style scoped>
.thought-block {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
.thought-header {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  cursor: pointer;
  background: var(--el-fill-color-light);
}
.thought-label {
  font-weight: 500;
}
.thought-content {
  padding: 10px;
  background: var(--el-bg-color);
}
.thought-content pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--el-text-color-regular);
  max-height: 200px;
  overflow-y: auto;
}
.thought-streaming-indicator {
  color: var(--el-color-primary);
  font-size: 12px;
  margin-top: 4px;
}
</style>
