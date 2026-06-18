<template>
  <div class="chat-stream" ref="scrollContainer">
    <div v-if="messages.length === 0" class="chat-empty">
      <div class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          <path d="M8 9h8M8 13h6"/>
        </svg>
        <p class="empty-text">发送消息开始对话</p>
      </div>
    </div>
    <div v-else class="messages-container">
      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import ChatMessage from './ChatMessage.vue'

const props = defineProps<{
  messages: ChatMessageType[]
}>()

defineEmits<{
  resolvePermission: [requestId: string, optionId: string]
}>()

const scrollContainer = ref<HTMLElement>()

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-stream {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.messages-container {
  max-width: 768px;
  margin: 0 auto;
  padding: 28px 0 16px;
}

.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  width: 36px;
  height: 36px;
  color: #ccc;
}

.empty-text {
  font-size: 14px;
  color: #bbb;
}
</style>
