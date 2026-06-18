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
  margin-top: 40px;
  display: flex;
  justify-content: center;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  max-width: 640px;
  width: 100%;
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid #e8e8e2;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
  font-family: inherit;
  color: #3d3d3a;
  -webkit-tap-highlight-color: transparent;
}

.prompt-card:hover {
  background: rgba(255, 255, 255, 0.95);
  border-color: #c8c8c0;
  transform: translateY(-1px);
}

.prompt-card:active {
  transform: translateY(0);
  background: #f0f0ec;
}

.prompt-card:focus-visible {
  outline: 2px solid #1a1a1a;
  outline-offset: 2px;
}

.card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #f0f0ea;
  color: #5a5a55;
  flex-shrink: 0;
  font-size: 14px;
}

.card-title {
  font-size: 13px;
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
