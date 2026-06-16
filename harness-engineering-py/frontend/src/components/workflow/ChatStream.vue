<template>
  <div class="chat-stream" ref="scrollContainer">
    <div v-if="messages.length === 0" class="chat-empty">
      <el-empty description="发送消息开始对话" />
    </div>
    <ChatMessage
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
      @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
    />
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
  padding: 16px;
}
.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
