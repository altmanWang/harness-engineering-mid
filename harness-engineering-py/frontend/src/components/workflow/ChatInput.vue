<template>
  <div class="chat-input-area">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
      :disabled="isStreaming"
      resize="none"
      @keydown.enter.exact.prevent="handleSend"
    />
    <div class="input-actions">
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
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion, CloseBold } from '@element-plus/icons-vue'

defineProps<{ isStreaming: boolean }>()
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
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}
.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}
</style>
