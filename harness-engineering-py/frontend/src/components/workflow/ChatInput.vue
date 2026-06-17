<template>
  <div class="chat-input-area" :class="[`variant-${variant}`]">
    <div class="input-wrapper">
      <el-input
        v-model="inputText"
        :type="variant === 'full' ? 'textarea' : 'text'"
        :rows="variant === 'full' ? 3 : 1"
        :placeholder="variant === 'full' ? '输入你想实现的...' : '输入消息... (Enter 发送)'"
        :disabled="isStreaming"
        resize="none"
        class="chat-input-field"
        @keydown.enter.exact.prevent="handleSend"
      >
        <template v-if="variant === 'full'" #suffix>
          <el-button
            type="primary"
            :icon="Promotion"
            :disabled="!inputText.trim() || isStreaming"
            circle
            size="large"
            @click="handleSend"
          />
        </template>
      </el-input>
      <div v-if="variant === 'compact'" class="input-actions">
        <el-button
          v-if="isStreaming"
          type="danger"
          :icon="CloseBold"
          @click="$emit('cancel')"
        >
          取消
        </el-button>
        <el-button
          v-else
          type="primary"
          :icon="Promotion"
          :disabled="!inputText.trim()"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion, CloseBold } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  isStreaming: boolean
  variant?: 'compact' | 'full'
}>(), {
  variant: 'compact',
})

const emit = defineEmits<{
  send: [content: string]
  cancel: []
}>()

const inputText = ref('')

function handleSend() {
  const content = inputText.value.trim()
  if (!content) return
  emit('send', content)
  inputText.value = ''
}
</script>

<style scoped>
.chat-input-area {
  display: flex;
  justify-content: center;
}

.chat-input-area.variant-compact {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.chat-input-area.variant-full {
  padding: 0;
}

.chat-input-area.variant-full .input-wrapper {
  width: 100%;
  max-width: 640px;
}

.chat-input-area.variant-full .chat-input-field {
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
}

.chat-input-area.variant-full :deep(.el-textarea__inner) {
  border-radius: 16px;
  padding: 14px 48px 14px 18px;
  font-size: 15px;
  line-height: 1.6;
  min-height: 56px;
  border: 1.5px solid var(--el-border-color);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-input-area.variant-full :deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 3px rgba(var(--el-color-primary-rgb, 64 158 255), 0.12);
}

.chat-input-area.variant-full :deep(.el-input__suffix) {
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
}

.chat-input-area.variant-compact .input-wrapper {
  width: 100%;
  max-width: 768px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
