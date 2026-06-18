<template>
  <div class="home-view">
    <Transition name="landing-fade" mode="out-in">
      <LandingHero
        v-if="isLanding"
        key="landing"
        :is-streaming="isStreaming"
        :model="chatStore.model"
        :models="availableModels"
        @send="handleFirstSend"
        @cancel="handleCancelStream"
        @model-change="handleModelChange"
      />
      <ChatLayout
        v-else
        key="chat"
        :sessions="chatStore.sessions"
        :current-session-id="chatStore.currentSessionId"
        :model="chatStore.model"
        :models="availableModels"
        :messages="chatMessages"
        :is-streaming="isStreaming"
        @model-change="handleModelChange"
        @send-message="handleSendMessage"
        @resolve-permission="handleResolvePermission"
        @cancel-stream="handleCancelStream"
      />
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import LandingHero from '@/components/workflow/LandingHero.vue'
import ChatLayout from '@/components/workflow/ChatLayout.vue'
import { useChatStore } from '@/stores/chat'
import { useEngineStore } from '@/stores/engine'
import { useChatStream } from '@/composables/useChatStream'
import type { ChatMessage, ModelInfo } from '@/types/chat'

const chatStore = useChatStore()
const engineStore = useEngineStore()

const availableModels = ref<ModelInfo[]>([])

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

const isLanding = computed(() => {
  return !chatStore.currentSessionId || chatStore.messages.length === 0
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
  await engineStore.fetchAvailability()
  if (engineStore.engineInfo) {
    availableModels.value = engineStore.engineInfo.models || []
    if (engineStore.engineInfo.defaultModel && !chatStore.model) {
      chatStore.setModel(engineStore.engineInfo.defaultModel)
    }
  }
})

async function handleFirstSend(content: string) {
  try {
    await chatStore.createSession()
  } catch (err) {
    console.error('Failed to create session:', err)
    return
  }
  await sendMessage(content)
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

function handleModelChange(model: string) {
  chatStore.setModel(model)
}

function handleResolvePermission(requestId: string, optionId: string) {
  resolvePermission(requestId, optionId)
}

function handleCancelStream() {
  cancelStream()
}
</script>

<style scoped>
.home-view {
  height: 100vh;
  overflow: hidden;
}

.landing-fade-enter-active {
  transition: opacity 0.35s ease;
}

.landing-fade-leave-active {
  transition: opacity 0.2s ease;
}

.landing-fade-enter-from,
.landing-fade-leave-to {
  opacity: 0;
}
</style>
