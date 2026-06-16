<template>
  <div class="chat-layout">
    <ChatSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId"
      :model="model"
      @select-session="$emit('selectSession', $event)"
      @new-session="$emit('newSession')"
      @delete-session="$emit('deleteSession', $event)"
      @model-change="$emit('modelChange', $event)"
    />
    <div class="chat-main">
      <ChatStream
        :messages="messages"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
      <ChatInput
        :is-streaming="isStreaming"
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession, ChatMessage } from '@/types/chat'
import ChatSidebar from './ChatSidebar.vue'
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
  selectSession: [id: string]
  newSession: []
  deleteSession: [id: string]
  modelChange: [model: string]
  sendMessage: [content: string]
  resolvePermission: [requestId: string, optionId: string]
  cancelStream: []
}>()
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 80px);
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>
