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
    } else {
      // Session not found: clear current session state
      currentSessionId.value = null
      messages.value = []
      agentSessionId.value = undefined
    }
  }

  function clearSession() {
    currentSessionId.value = null
    messages.value = []
    agentSessionId.value = undefined
  }

  function setAgentSessionId(id: string) {
    agentSessionId.value = id
    // Update matching session in sessions array immutably
    if (currentSessionId.value) {
      sessions.value = sessions.value.map(s =>
        s.id === currentSessionId.value
          ? { ...s, agentSessionId: id }
          : s
      )
    }
  }

  async function loadSessions() {
    const res = await fetch('/api/chat/sessions')
    if (!res.ok) {
      throw new Error(`Failed to load sessions: ${res.status} ${res.statusText}`)
    }
    const data = await res.json()
    sessions.value = data.sessions || []
  }

  async function createSession(engine: string, modelParam?: string) {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ engine, model: modelParam || model.value }),
    })
    if (!res.ok) {
      throw new Error(`Failed to create session: ${res.status} ${res.statusText}`)
    }
    const data = await res.json()
    sessions.value = [data.session, ...sessions.value]
    selectSession(data.session.id)
    return data.session
  }

  async function deleteSession(id: string) {
    const res = await fetch('/api/chat/sessions', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    if (!res.ok) {
      throw new Error(`Failed to delete session: ${res.status} ${res.statusText}`)
    }
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) {
      clearSession()
    }
  }

  return {
    sessions, currentSessionId, messages, isStreaming,
    pendingPermission, model, agentSessionId,
    setSessions, selectSession, clearSession, setAgentSessionId,
    loadSessions, createSession, deleteSession,
  }
})
