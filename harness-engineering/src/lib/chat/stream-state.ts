interface StreamState {
  chatId: string
  frontendSessionId: string
  engine: string
  streamContent: string
  status: "running" | "completed" | "failed" | "killed"
}

const streams = new Map<string, StreamState>()

export function registerStream(chatId: string, frontendSessionId: string, engine: string): void {
  streams.set(chatId, { chatId, frontendSessionId, engine, streamContent: "", status: "running" })
}

export function appendStreamContent(chatId: string, content: string): void {
  const state = streams.get(chatId)
  if (state) state.streamContent += content
}

export function setStreamStatus(chatId: string, status: StreamState["status"]): void {
  const state = streams.get(chatId)
  if (state) state.status = status
}

export function getStream(chatId: string): StreamState | undefined {
  return streams.get(chatId)
}

export function getStreamBySessionId(frontendSessionId: string): StreamState | undefined {
  for (const state of streams.values()) {
    if (state.frontendSessionId === frontendSessionId) return state
  }
  return undefined
}

export function removeStream(chatId: string): void {
  streams.delete(chatId)
}
