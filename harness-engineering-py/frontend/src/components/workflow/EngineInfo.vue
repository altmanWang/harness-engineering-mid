<template>
  <div class="engine-info">
    <span class="engine-label">{{ engineName }}</span>
    <el-divider direction="vertical" />
    <span class="model-label">{{ modelName }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  engineName: string
  modelName: string
}>()
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
