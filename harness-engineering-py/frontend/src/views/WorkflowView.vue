<template>
  <div class="workflow-page">
    <ChatLayout
      :sessions="chatStore.sessions"
      :current-session-id="chatStore.currentSessionId"
      :model="chatStore.model"
      :messages="chatMessages"
      :is-streaming="isStreaming"
      @model-change="handleModelChange"
      @send-message="handleSendMessage"
      @resolve-permission="handleResolvePermission"
      @cancel-stream="handleCancelStream"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import ChatLayout from '@/components/workflow/ChatLayout.vue'
import { useChatStore } from '@/stores/chat'
import { useChatStream } from '@/composables/useChatStream'
import type { ChatMessage } from '@/types/chat'

const chatStore = useChatStore()

const {
  messages,
  isStreaming,
  sendMessage,
  resolvePermission,
  cancelStream,
} = useChatStream({
  get sessionId() { return chatStore.currentSessionId || '' },
  get model() { return chatStore.model },
  get agentSessionId() { return chatStore.agentSessionId },
  onAgentSessionIdChange(id: string) {
    chatStore.setAgentSessionId(id)
  },
  async onDone() {
    await chatStore.loadSessions()
  },
})

const chatMessages = ref<ChatMessage[]>(messages.value || [])

watch(messages, (val) => {
  chatMessages.value = val
  chatStore.messages = val
}, { deep: true })

watch(() => chatStore.messages, (val) => {
  if (val !== messages.value) {
    messages.value = val
  }
}, { deep: true })

onMounted(async () => {
  await chatStore.loadSessions()
})

function handleModelChange(model: string) {
  chatStore.setModel(model)
}

async function handleSendMessage(content: string) {
  if (!chatStore.currentSessionId) {
    try {
      await chatStore.createSession()
    } catch (err) {
      console.error('Failed to create session:', err)
      return
    }
  }
  await sendMessage(content)
}

function handleResolvePermission(requestId: string, optionId: string) {
  resolvePermission(requestId, optionId)
}

function handleCancelStream() {
  cancelStream()
}
</script>

<style scoped>
.workflow-page {
  height: 100%;
}
</style>
