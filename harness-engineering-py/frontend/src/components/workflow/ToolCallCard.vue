<template>
  <div class="tool-call-card">
    <div class="tool-header" @click="expanded = !expanded">
      <el-icon :size="14"><Tools /></el-icon>
      <span class="tool-name">{{ name }}</span>
      <el-icon :size="12" class="expand-icon"><component :is="expanded ? ArrowDown : ArrowRight" /></el-icon>
    </div>
    <div v-show="expanded" class="tool-body">
      <div v-if="input" class="tool-section">
        <div class="tool-label">Input:</div>
        <pre>{{ input }}</pre>
      </div>
      <div v-if="output" class="tool-section">
        <div class="tool-label">Output:</div>
        <pre>{{ output }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Tools, ArrowDown, ArrowRight } from '@element-plus/icons-vue'

defineProps<{
  name: string
  input?: string
  output?: string
}>()

const expanded = ref(false)
</script>

<style scoped>
.tool-call-card {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
.tool-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  background: var(--el-fill-color-light);
}
.tool-name {
  font-weight: 500;
  flex: 1;
}
.expand-icon {
  color: var(--el-text-color-secondary);
}
.tool-body {
  padding: 10px;
  background: var(--el-bg-color);
}
.tool-section {
  margin-bottom: 8px;
}
.tool-section:last-child {
  margin-bottom: 0;
}
.tool-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}
.tool-body pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 150px;
  overflow-y: auto;
}
</style>
