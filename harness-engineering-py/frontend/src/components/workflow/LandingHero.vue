<template>
  <div class="landing-hero">
    <div class="landing-content">
      <div class="brand-section">
        <div class="brand-mark">H</div>
        <h1 class="brand-name">Harness</h1>
      </div>

      <p class="welcome-text">Hi，今天想做什么？</p>

      <div class="hero-input">
        <ChatInput
          :is-streaming="isStreaming"
          variant="full"
          @send="$emit('send', $event)"
          @cancel="$emit('cancel')"
        />
      </div>

      <PromptCards @select="onCardSelect" />
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatInput from './ChatInput.vue'
import PromptCards from './PromptCards.vue'

defineProps<{
  isStreaming: boolean
}>()

const emit = defineEmits<{
  send: [content: string]
  cancel: []
}>()

function onCardSelect(prompt: string) {
  emit('send', prompt)
}
</script>

<style scoped>
.landing-hero {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f7f4;
}

.landing-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 720px;
  padding: 0 24px;
  margin-top: -60px;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
}

.brand-name {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.welcome-text {
  margin: 0 0 28px 0;
  font-size: 18px;
  color: var(--el-text-color-regular);
  font-weight: 450;
}

.hero-input {
  width: 100%;
}
</style>
