<template>
  <el-card shadow="hover" class="skill-card">
    <div class="skill-info">
      <h3 class="skill-name">{{ skill.name }}</h3>
      <p class="skill-desc">{{ skill.description }}</p>
    </div>
    <div class="skill-tags">
      <el-tag v-for="tag in skill.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
    </div>
    <div class="skill-meta">
      <span class="skill-size">{{ formatFileSize(skill.fileSize) }}</span>
      <span class="skill-date">{{ formatDate(skill.createdAt) }}</span>
    </div>
    <div class="skill-actions">
      <el-button size="small" :icon="Download" type="primary" plain @click="onDownload">
        下载
      </el-button>
      <el-button size="small" :icon="Delete" type="danger" plain @click="onDelete">
        删除
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { Download, Delete } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { Skill } from '@/types'

const props = defineProps<{ skill: Skill }>()

const emit = defineEmits<{
  deleted: [id: string]
}>()

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function onDownload() {
  window.open(`/api/skills/${props.skill.id}/download`, '_blank')
}

async function onDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除 "${props.skill.name}" 吗？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    const res = await fetch(`/api/skills/${props.skill.id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('删除失败')
    ElMessage.success('删除成功')
    emit('deleted', props.skill.id)
  } catch {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.skill-card {
  transition: transform 0.2s;
}
.skill-card:hover {
  transform: translateY(-2px);
}
.skill-info {
  min-width: 0;
}
.skill-name {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
}
.skill-desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
.skill-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}
.skill-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
