<template>
  <div class="chat-input-area" :class="[`variant-${variant}`]">
    <div class="input-wrapper">
      <el-input
        v-model="inputText"
        :type="variant === 'full' ? 'textarea' : 'text'"
        :rows="variant === 'full' ? 3 : 1"
        :placeholder="variant === 'full' ? '输入你想实现的...' : '输入消息... (Enter 发送)'"
        :disabled="isStreaming"
        resize="none"
        class="chat-input-field"
        @keydown.enter.exact.prevent="handleSend"
      />
      <div v-if="variant === 'full'" class="full-actions">
        <el-select
          v-if="models.length > 0"
          :model-value="model"
          size="small"
          class="model-dropdown"
          popper-class="model-dropdown-popper"
          @change="onModelChange"
        >
          <el-option
            v-for="m in models"
            :key="m.id"
            :label="m.name"
            :value="m.id"
          />
        </el-select>
        <el-button
          type="primary"
          :icon="Promotion"
          :disabled="!inputText.trim() || isStreaming"
          circle
          size="large"
          @click="handleSend"
        />
      </div>
      <div v-if="variant === 'compact'" class="input-actions">
        <div v-if="models.length > 0" class="model-select-inline">
          <el-select v-model="selectedModel" size="small" @change="onModelChange">
            <el-option
              v-for="m in models"
              :key="m.id"
              :label="m.name"
              :value="m.id"
            />
          </el-select>
        </div>
        <div class="input-actions-right">
          <el-button
            v-if="isStreaming"
            type="danger"
            :icon="CloseBold"
            @click="$emit('cancel')"
          >
            取消
          </el-button>
          <el-button
            v-else
            type="primary"
            :icon="Promotion"
            :disabled="!inputText.trim()"
            @click="handleSend"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Promotion, CloseBold } from '@element-plus/icons-vue'
import type { ModelInfo } from '@/types/chat'

const props = withDefaults(defineProps<{
  isStreaming: boolean
  variant?: 'compact' | 'full'
  model: string
  models: ModelInfo[]
}>(), {
  variant: 'compact',
  models: () => [],
})

const emit = defineEmits<{
  send: [content: string]
  cancel: []
  modelChange: [model: string]
}>()

const inputText = ref('')
const selectedModel = ref(props.model)

watch(() => props.model, (val) => { selectedModel.value = val })

function handleSend() {
  const content = inputText.value.trim()
  if (!content) return
  emit('send', content)
  inputText.value = ''
}

function onModelChange(val: string) {
  emit('modelChange', val)
}
</script>

<style scoped>
.chat-input-area {
  display: flex;
  justify-content: center;
}

.chat-input-area.variant-compact {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--el-bg-color);
}

.chat-input-area.variant-full {
  padding: 0;
}

.chat-input-area.variant-full .input-wrapper {
  position: relative;
  width: 100%;
  max-width: 680px;
}

.chat-input-area.variant-full .chat-input-field {
  border-radius: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.04);
}

.chat-input-area.variant-full :deep(.el-textarea__inner) {
  border-radius: 24px;
  padding: 16px 110px 16px 22px;
  font-size: 16px;
  line-height: 1.65;
  min-height: 60px;
  border: 1.5px solid #e8e8e2;
  background: #fff;
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
  resize: none;
}

.chat-input-area.variant-full :deep(.el-textarea__inner:hover) {
  border-color: #d4d4cc;
}

.chat-input-area.variant-full :deep(.el-textarea__inner:focus) {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.04);
}

.full-actions {
  position: absolute;
  right: 10px;
  bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.model-dropdown {
  width: auto;
  min-width: 100px;
}

.model-dropdown :deep(.el-input__wrapper) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0 4px;
}

.model-dropdown :deep(.el-input__wrapper:hover),
.model-dropdown :deep(.el-input__wrapper.is-focus) {
  background: transparent;
  box-shadow: none;
}

.model-dropdown :deep(.el-input__inner) {
  font-size: 12px;
  color: #999;
  text-align: right;
}

.chat-input-area.variant-full :deep(.el-button--large.is-circle) {
  width: 40px;
  height: 40px;
}

.chat-input-area.variant-compact .input-wrapper {
  width: 100%;
  max-width: 768px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-actions-right {
  display: flex;
  gap: 8px;
}

.model-select-inline {
  flex-shrink: 0;
}
</style>
