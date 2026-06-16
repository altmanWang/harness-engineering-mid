<template>
  <div class="chat-sidebar">
    <div class="sidebar-header">
      <el-button type="primary" :icon="Plus" size="small" @click="$emit('newSession')" class="new-session-btn">
        新建会话
      </el-button>
    </div>

    <div class="sidebar-sessions">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === currentSessionId }"
        @click="$emit('selectSession', session.id)"
      >
        <span class="session-title">{{ session.title || '新会话' }}</span>
        <el-button
          :icon="Delete"
          size="small"
          text
          type="danger"
          @click.stop="$emit('deleteSession', session.id)"
        />
      </div>
      <el-empty v-if="sessions.length === 0" description="暂无会话，点击新建" :image-size="60" />
    </div>

    <div class="sidebar-footer">
      <EngineInfo
        :engine-name="engineInfo?.name || 'OpenCode'"
        :model-name="model"
      />
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { ChatSession, EngineAvailability } from '@/types/chat'
import EngineInfo from './EngineInfo.vue'
import { useEngineStore } from '@/stores/engine'

const props = defineProps<{
  sessions: ChatSession[]
  currentSessionId: string | null
  model: string
}>()

const emit = defineEmits<{
  selectSession: [id: string]
  newSession: []
  deleteSession: [id: string]
  modelChange: [model: string]
}>()

const engineStore = useEngineStore()
const engineInfo = ref<EngineAvailability | null>(null)
const modelValue = ref(props.model)

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
.chat-sidebar {
  width: 260px;
  border-right: 1px solid var(--el-border-color-light);
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color);
}
.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.new-session-btn {
  width: 100%;
}
.sidebar-sessions {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  margin-bottom: 2px;
}
.session-item:hover {
  background: var(--el-fill-color-light);
}
.session-item.active {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sidebar-footer {
  border-top: 1px solid var(--el-border-color-lighter);
}
.model-select {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
}
.model-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
.model-selector {
  flex: 1;
}
</style>
