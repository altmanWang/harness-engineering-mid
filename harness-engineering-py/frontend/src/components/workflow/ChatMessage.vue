<template>
  <div class="chat-message" :class="[message.role]">
    <template v-if="message.role === 'user'">
      <div class="message-bubble user-bubble">
        <p>{{ message.content }}</p>
      </div>
    </template>

    <template v-else-if="message.role === 'assistant' && message.permissionRequest">
      <PermissionCard
        :request="message.permissionRequest"
        :decision="message.permissionDecision"
        @resolve="onResolvePermission"
      />
    </template>

    <template v-else-if="message.role === 'assistant'">
      <div class="message-bubble assistant-bubble">
        <ThoughtBlock
          v-if="message.thoughtContent"
          :content="message.thoughtContent"
          :is-streaming="message.isStreaming ?? false"
        />
        <div v-if="message.content" class="message-text" v-html="renderedContent" />
        <div v-if="message.isStreaming" class="streaming-cursor">|</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage as ChatMessageType } from '@/types/chat'
import ThoughtBlock from './ThoughtBlock.vue'
import PermissionCard from './PermissionCard.vue'

const props = defineProps<{
  message: ChatMessageType
}>()

const emit = defineEmits<{
  resolvePermission: [requestId: string, optionId: string]
}>()

const renderedContent = computed(() => {
  let text = props.message.content
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
  text = text.replace(/\n/g, '<br/>')
  return text
})

function onResolvePermission(requestId: string, optionId: string) {
  emit('resolvePermission', requestId, optionId)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 16px;
}
.chat-message.user {
  justify-content: flex-end;
}
.chat-message.assistant {
  justify-content: flex-start;
}
.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}
.user-bubble {
  background: var(--el-color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}
.user-bubble p {
  margin: 0;
}
.assistant-bubble {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-bottom-left-radius: 4px;
}
.message-text {
  word-break: break-word;
}
.message-text :deep(code) {
  background: var(--el-fill-color);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.message-text :deep(pre) {
  background: var(--el-fill-color);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}
.message-text :deep(pre code) {
  background: none;
  padding: 0;
}
.streaming-cursor {
  display: inline;
  animation: blink 1s infinite;
  color: var(--el-color-primary);
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
