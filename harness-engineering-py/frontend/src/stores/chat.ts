import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage, PermissionRequest } from '@/types/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const pendingPermission = ref<PermissionRequest | null>(null)
  const model = ref('claude-sonnet-4-6')
  const agentSessionId = ref<string | undefined>(undefined)

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  function selectSession(id: string) {
    currentSessionId.value = id
    const session = sessions.value.find(s => s.id === id)
    if (session) {
      messages.value = session.messages
      agentSessionId.value = session.agentSessionId
      model.value = session.model
    }
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
    agentSessionId.value = undefined
  }

  return {
    sessions, currentSessionId, messages, isStreaming,
    pendingPermission, model, agentSessionId,
    setSessions, selectSession, clearSession,
  }
})
