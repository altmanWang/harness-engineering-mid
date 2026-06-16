<template>
  <div class="workflow-page">
    <ChatLayout
      :sessions="chatStore.sessions"
      :current-session-id="chatStore.currentSessionId"
      :model="chatStore.model"
      :messages="chatMessages"
      :is-streaming="isStreaming"
      @select-session="handleSelectSession"
      @new-session="handleNewSession"
      @delete-session="handleDeleteSession"
      @model-change="handleModelChange"
      @send-message="handleSendMessage"
      @resolve-permission="handleResolvePermission"
      @cancel-stream="handleCancelStream"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, ref } from 'vue'
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
    chatStore.agentSessionId = id
  },
})

const chatMessages = ref<ChatMessage[]>(messages.value || [])

watch(messages, (val) => { chatMessages.value = val }, { deep: true })

async function loadSessions() {
  try {
    const res = await fetch('/api/chat/sessions')
    const data = await res.json()
    chatStore.setSessions(data.sessions || [])
  } catch (err) {
    console.error('Failed to load sessions:', err)
  }
}

onMounted(() => {
  loadSessions()
})

function handleSelectSession(id: string) {
  chatStore.selectSession(id)
  messages.value = chatStore.messages
}

async function handleNewSession() {
  try {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine: 'opencode', model: chatStore.model }),
    })
    const data = await res.json()
    chatStore.setSessions([data.session, ...chatStore.sessions])
    chatStore.selectSession(data.session.id)
    messages.value = []
  } catch (err) {
    console.error('Failed to create session:', err)
  }
}

async function handleDeleteSession(id: string) {
  try {
    await fetch('/api/chat/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    chatStore.setSessions(chatStore.sessions.filter(s => s.id !== id))
    if (chatStore.currentSessionId === id) {
      chatStore.clearSession()
      messages.value = []
    }
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

function handleModelChange(model: string) {
  chatStore.model = model
}

function handleSendMessage(content: string) {
  sendMessage(content)
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
  margin: -24px;
}
</style>
