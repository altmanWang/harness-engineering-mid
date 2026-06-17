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

  async function loadSessions() {
    const res = await fetch('/api/chat/sessions')
    const data = await res.json()
    setSessions(data.sessions || [])
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

  async function createSession() {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine: 'opencode', model: model.value }),
    })
    const data = await res.json()
    const session = data.session as ChatSession
    setSessions([session, ...sessions.value])
    selectSession(session.id)
    messages.value = []
    return session
  }

  async function deleteSession(id: string) {
    await fetch('/api/chat/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    setSessions(sessions.value.filter(s => s.id !== id))
    if (currentSessionId.value === id) {
      clearSession()
    }
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
    agentSessionId.value = undefined
  }

  function setModel(nextModel: string) {
    model.value = nextModel
  }

  function setAgentSessionId(id: string) {
    agentSessionId.value = id
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      session.agentSessionId = id
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    pendingPermission,
    model,
    agentSessionId,
    setSessions,
    loadSessions,
    selectSession,
    createSession,
    deleteSession,
    clearSession,
    setModel,
    setAgentSessionId,
  }
})
