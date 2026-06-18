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
        <span v-if="message.isStreaming" class="streaming-cursor" />
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
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>')
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
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
  margin-bottom: 28px;
  padding: 0 16px;
}

.chat-message.user {
  justify-content: flex-end;
}

.chat-message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 14.5px;
  line-height: 1.75;
  word-break: break-word;
}

.user-bubble {
  background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
  color: #fff;
  border-bottom-right-radius: 6px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.user-bubble p {
  margin: 0;
}

.assistant-bubble {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-bottom-left-radius: 6px;
  color: #333;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 2px 8px rgba(0, 0, 0, 0.04);
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(p + p) {
  margin-top: 8px;
}

.message-text :deep(code) {
  background: #f0f0e8;
  color: #c7254e;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
}

.message-text :deep(pre) {
  background: #f8f8f5;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-left: 3px solid #e0e0d8;
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 10px 0;
}

.message-text :deep(pre code) {
  background: none;
  color: #333;
  padding: 0;
  font-size: 13px;
  line-height: 1.6;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #1a1a1a;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursor-blink 0.8s infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
