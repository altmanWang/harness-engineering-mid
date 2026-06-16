<template>
  <el-card class="permission-card" :class="{ 'is-resolved': !!decision }">
    <div class="perm-header">
      <el-icon :size="16"><WarningFilled /></el-icon>
      <span class="perm-type">{{ request.type }}</span>
    </div>
    <p class="perm-desc">{{ request.description }}</p>
    <p v-if="request.detail" class="perm-detail">{{ request.detail }}</p>
    <div v-if="!decision" class="perm-actions">
      <el-button
        v-for="option in request.options"
        :key="option.id"
        :type="option.style === 'danger' ? 'danger' : option.style === 'primary' ? 'primary' : 'default'"
        size="small"
        @click="onResolve(option.id)"
      >
        {{ option.label }}
      </el-button>
    </div>
    <div v-else class="perm-resolved">
      <el-tag type="info">已选择: {{ decision.label }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'
import type { PermissionRequest } from '@/types/chat'

const props = defineProps<{
  request: PermissionRequest
  decision?: { optionId: string; label: string }
}>()

const emit = defineEmits<{
  resolve: [requestId: string, optionId: string]
}>()

function onResolve(optionId: string) {
  emit('resolve', props.request.id, optionId)
}
</script>

<style scoped>
.permission-card {
  max-width: 400px;
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-5);
}
.permission-card.is-resolved {
  opacity: 0.7;
}
.perm-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.perm-type {
  font-weight: 600;
  font-size: 14px;
}
.perm-desc {
  margin: 0 0 4px;
  font-size: 13px;
}
.perm-detail {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
.perm-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.perm-resolved {
  margin-top: 8px;
}
</style>
