import { ref } from 'vue'
import type { ChatMessage, PermissionRequest } from '@/types/chat'

interface UseChatStreamOptions {
  sessionId: string
  model: string
  agentSessionId?: string
  onAgentSessionIdChange?: (id: string) => void
}

export function useChatStream(options: UseChatStreamOptions) {
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const currentChatId = ref<string | null>(null)
  const pendingPermission = ref<PermissionRequest | null>(null)
  let eventSource: EventSource | null = null

  async function sendMessage(content: string) {
    if (!content.trim() || isStreaming.value) return

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMsg)
    isStreaming.value = true

    const assistantMsgId = `msg-assistant-${Date.now()}`
    messages.value.push({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    })

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          model: options.model,
          sessionId: options.sessionId,
          agentSessionId: options.agentSessionId || undefined,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        updateAssistant(assistantMsgId, { content: `错误: ${err.detail || err.error}`, isStreaming: false })
        isStreaming.value = false
        return
      }

      const { chatId } = await res.json()
      currentChatId.value = chatId

      const es = new EventSource(`/api/chat/stream?id=${chatId}`)
      eventSource = es

      es.addEventListener('delta', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + data.content }
            : m
        )
      })

      es.addEventListener('thinking', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, thoughtContent: (m.thoughtContent || '') + data.content }
            : m
        )
      })

      es.addEventListener('permission_request', (e) => {
        const data = JSON.parse(e.data)
        pendingPermission.value = data.request
        messages.value.push({
          id: `perm-msg-${data.request.id}`,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          permissionRequest: data.request,
        })
      })

      es.addEventListener('done', (e) => {
        const data = JSON.parse(e.data)
        if (data.sessionId && options.onAgentSessionIdChange) {
          options.onAgentSessionIdChange(data.sessionId)
        }
        updateAssistant(assistantMsgId, { isStreaming: false })
        isStreaming.value = false
        es.close()
        eventSource = null
      })

      es.addEventListener('failed', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false }
            : m
        )
        isStreaming.value = false
        es.close()
        eventSource = null
      })

      es.addEventListener('engine_error', (e) => {
        const data = JSON.parse(e.data)
        messages.value = messages.value.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + `\n\n❌ ${data.message}`, isStreaming: false }
            : m
        )
      })

      es.onerror = () => {
        updateAssistant(assistantMsgId, { isStreaming: false })
        isStreaming.value = false
        es.close()
        eventSource = null
      }
    } catch (error) {
      updateAssistant(assistantMsgId, { content: `连接失败: ${error}`, isStreaming: false })
      isStreaming.value = false
    }
  }

  function updateAssistant(id: string, updates: Partial<ChatMessage>) {
    messages.value = messages.value.map(m =>
      m.id === id ? { ...m, ...updates } : m
    )
  }

  async function resolvePermission(requestId: string, optionId: string) {
    pendingPermission.value = null
    messages.value = messages.value.map(m =>
      m.permissionRequest?.id === requestId
        ? { ...m, permissionDecision: { optionId, label: optionId } }
        : m
    )
    await fetch('/api/chat/permission', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requestId, optionId }),
    })
  }

  async function cancelStream() {
    if (currentChatId.value) {
      await fetch(`/api/chat/stream?id=${currentChatId.value}`, { method: 'DELETE' })
    }
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isStreaming.value = false
  }

  return {
    messages,
    isStreaming,
    pendingPermission,
    sendMessage,
    resolvePermission,
    cancelStream,
  }
}
