<template>
  <div class="chat-layout">
    <div class="chat-main">
      <ChatStream
        :messages="messages"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
      <ChatInput
        :is-streaming="isStreaming"
        variant="compact"
        :model="model"
        :models="models"
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
        @model-change="$emit('modelChange', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession, ChatMessage, ModelInfo } from '@/types/chat'
import ChatStream from './ChatStream.vue'
import ChatInput from './ChatInput.vue'

defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
  models: ModelInfo[]
  messages: ChatMessage[]
  isStreaming: boolean
}>()

defineEmits<{
  modelChange: [model: string]
  sendMessage: [content: string]
  resolvePermission: [requestId: string, optionId: string]
  cancelStream: []
}>()
</script>

<style scoped>
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f5f5f1;
}

.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
