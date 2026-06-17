<template>
  <div class="chat-layout">
    <header class="workflow-topbar">
      <div class="session-meta">
        <h1 class="session-title">{{ currentSessionTitle }}</h1>
        <span class="session-subtitle">OpenCode 工作流</span>
      </div>
      <div class="model-select">
        <span class="model-label">模型</span>
        <el-select v-model="modelValue" size="small" @change="onModelChange" class="model-selector">
          <el-option
            v-for="m in (engineInfo?.models || [])"
            :key="m.id"
            :label="m.name"
            :value="m.id"
          />
        </el-select>
      </div>
    </header>

    <div class="chat-main">
      <ChatStream
        :messages="messages"
        @resolve-permission="(reqId, optId) => $emit('resolvePermission', reqId, optId)"
      />
      <ChatInput
        :is-streaming="isStreaming"
        @send="$emit('sendMessage', $event)"
        @cancel="$emit('cancelStream')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { ChatSession, ChatMessage, EngineAvailability } from '@/types/chat'
import { useEngineStore } from '@/stores/engine'
import ChatStream from './ChatStream.vue'
import ChatInput from './ChatInput.vue'

const props = defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
  messages: ChatMessage[]
  isStreaming: boolean
}>()

const emit = defineEmits<{
  modelChange: [model: string]
  sendMessage: [content: string]
  resolvePermission: [requestId: string, optionId: string]
  cancelStream: []
}>()

const engineStore = useEngineStore()
const engineInfo = ref<EngineAvailability | null>(null)
const modelValue = ref(props.model)

const currentSessionTitle = computed(() => {
  const session = props.sessions.find(s => s.id === props.currentSessionId)
  return session?.title || '新对话'
})

watch(() => props.model, (val) => { modelValue.value = val })

onMounted(async () => {
  await engineStore.fetchAvailability()
  engineInfo.value = engineStore.engineInfo
  if (engineInfo.value?.defaultModel && !props.model) {
    emit('modelChange', engineInfo.value.defaultModel)
  }
})

function onModelChange(val: string) {
  emit('modelChange', val)
}
</script>

<style scoped>
.chat-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f7f7f4;
}
.workflow-topbar {
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 24px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(10px);
}
.session-meta {
  min-width: 0;
}
.session-title {
  margin: 0;
  font-size: 16px;
  font-weight: 650;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-subtitle {
  display: block;
  margin-top: 2px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.model-select {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.model-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.model-selector {
  width: 220px;
}
.chat-main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
@media (max-width: 900px) {
  .workflow-topbar {
    padding: 0 14px;
  }
  .model-selector {
    width: 160px;
  }
}
</style>
