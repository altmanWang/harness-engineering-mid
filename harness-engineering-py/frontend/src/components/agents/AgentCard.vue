<template>
  <el-card shadow="hover" class="agent-card">
    <div class="agent-header">
      <div class="agent-icon">
        <el-icon :size="20"><component :is="iconComponent" /></el-icon>
      </div>
      <div class="agent-info">
        <h3 class="agent-name">{{ agent.name }}</h3>
        <p class="agent-desc">{{ agent.description }}</p>
      </div>
    </div>
    <div class="agent-tags">
      <el-tag v-for="tag in agent.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'
import type { Agent } from '@/types'

const props = defineProps<{ agent: Agent }>()

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    Bot: Icons.Service,
    FlaskConical: Icons.Orange,
    Server: Icons.Monitor,
    BookOpen: Icons.Reading,
    ShieldCheck: Icons.Checked,
    BarChart3: Icons.DataAnalysis,
    Blocks: Icons.Grid,
    GitBranch: Icons.Connection,
  }
  return iconMap[props.agent.icon] || Icons.Service
})
</script>

<style scoped>
.agent-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.agent-card:hover {
  transform: translateY(-2px);
}
.agent-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.agent-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  flex-shrink: 0;
}
.agent-info {
  min-width: 0;
  flex: 1;
}
.agent-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
}
.agent-desc {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.agent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
</style>
