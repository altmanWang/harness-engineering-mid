<template>
  <el-card shadow="hover" class="skill-card">
    <div class="skill-header">
      <div class="skill-icon">
        <el-icon :size="20"><component :is="iconComponent" /></el-icon>
      </div>
      <div class="skill-info">
        <h3 class="skill-name">{{ skill.name }}</h3>
        <p class="skill-desc">{{ skill.description }}</p>
      </div>
    </div>
    <div class="skill-tags">
      <el-tag v-for="tag in skill.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'
import type { Skill } from '@/types'

const props = defineProps<{ skill: Skill }>()

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    Code: Icons.Document,
    TestTube: Icons.Orange,
    Search: Icons.Search,
    FileText: Icons.Document,
    Rocket: Icons.Promotion,
    Database: Icons.Coin,
    Gauge: Icons.Odometer,
    Webhook: Icons.Link,
    Shield: Icons.Lock,
    ScrollText: Icons.Tickets,
    Package: Icons.Box,
    Settings: Icons.Setting,
  }
  return iconMap[props.skill.icon] || Icons.MagicStick
})
</script>

<style scoped>
.skill-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.skill-card:hover {
  transform: translateY(-2px);
}
.skill-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.skill-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  flex-shrink: 0;
}
.skill-info {
  min-width: 0;
  flex: 1;
}
.skill-name {
  margin: 0 0 4px;
  font-size: 14px;
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
</style>
