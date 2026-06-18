<template>
  <div class="landing-hero">
    <div class="landing-content">
      <!-- 极简品牌标识 -->
      <div class="brand-row">
        <button class="brand-dot" type="button" aria-label="Harness" />
      </div>

      <!-- 大号问候 -->
      <h1 class="greeting">Hi，今天想做什么？</h1>

      <!-- 核心输入区 -->
      <div class="hero-input">
        <ChatInput
          :is-streaming="isStreaming"
          variant="full"
          :model="model"
          :models="models"
          :skills="skills"
          :selected-skill-id="selectedSkillId"
          @send="$emit('send', $event)"
          @cancel="$emit('cancel')"
          @model-change="$emit('modelChange', $event)"
          @skill-change="$emit('skillChange', $event)"
        />
      </div>

      <!-- 提示卡片 -->
      <PromptCards @select="onCardSelect" />
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatInput from './ChatInput.vue'
import PromptCards from './PromptCards.vue'
import type { ModelInfo } from '@/types/chat'
import type { Skill } from '@/types'

defineProps<{
  isStreaming: boolean
  model: string
  models: ModelInfo[]
  skills?: Skill[]
  selectedSkillId?: string
}>()

const emit = defineEmits<{
  send: [content: string]
  cancel: []
  modelChange: [model: string]
  skillChange: [skillId: string]
}>()

function onCardSelect(prompt: string) {
  emit('send', prompt)
}
</script>

<style scoped>
.landing-hero {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f1;
}

.landing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 680px;
  padding: 0 32px;
  margin-top: -80px;
}

/* 极简品牌点 */
.brand-row {
  margin-bottom: 40px;
}

.brand-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: none;
  background: #1a1a1a;
  cursor: pointer;
  padding: 0;
  transition: transform 0.2s ease;
}

.brand-dot:hover {
  transform: scale(1.3);
}

/* 问候语 */
.greeting {
  margin: 0 0 36px 0;
  font-size: 32px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.02em;
  text-align: center;
}

/* 核心输入区 */
.hero-input {
  width: 100%;
}

@media (max-width: 640px) {
  .landing-content {
    padding: 0 20px;
    margin-top: -60px;
  }

  .greeting {
    font-size: 26px;
    margin-bottom: 28px;
  }

  .brand-row {
    margin-bottom: 28px;
  }
}
</style>
