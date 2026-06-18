<template>
  <div class="engine-info">
    <span class="engine-label">{{ engineName }}</span>
    <el-divider direction="vertical" />
    <span class="model-label">{{ displayModelName }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ModelInfo } from '@/types/chat'

const props = defineProps<{
  engineName: string
  modelName: string
  models?: ModelInfo[]
}>()

const displayModelName = computed(() => {
  if (props.models && props.models.length > 0) {
    const found = props.models.find(m => m.id === props.modelName)
    if (found) return found.name
  }
  return props.modelName
})
</script>

<style scoped>
.engine-info {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}
.engine-label {
  font-weight: 500;
}
.model-label {
  color: var(--el-text-color-regular);
}
</style>
