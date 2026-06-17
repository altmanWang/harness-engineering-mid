<template>
  <div class="prompt-cards-section">
    <div class="prompt-grid">
      <button
        v-for="card in cards"
        :key="card.title"
        type="button"
        class="prompt-card"
        @click="$emit('select', card.prompt)"
      >
        <span class="card-icon" aria-hidden="true">
          <el-icon><component :is="card.icon" /></el-icon>
        </span>
        <span class="card-title">{{ card.title }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Connection,
  User,
  Lock,
  DataAnalysis,
  Document,
  Upload,
} from '@element-plus/icons-vue'
import type { Component } from 'vue'

interface PromptCard {
  title: string
  prompt: string
  icon: Component
}

const cards: PromptCard[] = [
  { title: '创建工作流', prompt: '帮我创建一个自动化工作流', icon: Connection },
  { title: '推荐 Agent', prompt: '推荐适合我需求的 Agent', icon: User },
  { title: '安全审查', prompt: '帮我审查这段代码的安全性', icon: Lock },
  { title: '数据分析', prompt: '帮我分析数据并生成可视化报告', icon: DataAnalysis },
  { title: '生成文档', prompt: '帮我生成项目 API 文档', icon: Document },
  { title: '部署上线', prompt: '帮我规划部署上线流程', icon: Upload },
]

defineEmits<{
  select: [prompt: string]
}>()
</script>

<style scoped>
.prompt-cards-section {
  margin-top: 32px;
  display: flex;
  justify-content: center;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  max-width: 640px;
  width: 100%;
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 14px;
  background: var(--el-bg-color);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  font-family: inherit;
  color: var(--el-text-color-primary);
}

.prompt-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: var(--el-color-primary-light-5);
}

.prompt-card:active {
  transform: translateY(0);
}

.prompt-card:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  flex-shrink: 0;
  font-size: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .prompt-grid {
    grid-template-columns: repeat(2, 1fr);
    padding: 0 16px;
  }
}
</style>
