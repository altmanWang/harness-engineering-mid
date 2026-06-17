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
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession, ChatMessage } from '@/types/chat'
import ChatStream from './ChatStream.vue'
import ChatInput from './ChatInput.vue'

defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
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
  background: #f7f7f4;
}

.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
