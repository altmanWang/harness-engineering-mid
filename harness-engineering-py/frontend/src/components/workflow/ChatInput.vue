<template>
  <div class="chat-input-area" :class="[`variant-${variant}`]">
    <div v-if="selectedSkillName" class="skill-tag-row">
      <el-tag size="small" closable type="warning" @close="onSkillChange('')">
        {{ selectedSkillName }}
      </el-tag>
    </div>
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
        <el-select
          :model-value="selectedSkillId || ''"
          size="small"
          class="skill-dropdown"
          popper-class="skill-dropdown-popper"
          placeholder="技能"
          clearable
          @change="onSkillChange"
        >
          <el-option
            v-for="s in skills"
            :key="s.id"
            :label="s.name"
            :value="s.id"
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
        <div class="skill-select-inline">
          <el-select
            :model-value="selectedSkillId || ''"
            size="small"
            placeholder="技能"
            clearable
            @change="onSkillChange"
          >
            <el-option
              v-for="s in skills"
              :key="s.id"
              :label="s.name"
              :value="s.id"
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
import { ref, watch, computed } from 'vue'
import { Promotion, CloseBold } from '@element-plus/icons-vue'
import type { ModelInfo } from '@/types/chat'
import type { Skill } from '@/types'

const props = withDefaults(defineProps<{
  isStreaming: boolean
  variant?: 'compact' | 'full'
  model: string
  models: ModelInfo[]
  skills?: Skill[]
  selectedSkillId?: string
}>(), {
  variant: 'compact',
  models: () => [],
  skills: () => [],
  selectedSkillId: '',
})

const emit = defineEmits<{
  send: [content: string]
  cancel: []
  modelChange: [model: string]
  skillChange: [skillId: string]
}>()

const inputText = ref('')
const selectedModel = ref(props.model)

const selectedSkillName = computed(() => {
  if (!props.selectedSkillId || !props.skills) return ''
  const skill = props.skills.find(s => s.id === props.selectedSkillId)
  return skill ? skill.name : ''
})

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

function onSkillChange(val: string) {
  emit('skillChange', val || '')
}
</script>

<style scoped>
.chat-input-area {
  display: flex;
  justify-content: center;
}

.chat-input-area.variant-compact {
  padding: 16px 20px;
  background: #fff;
  box-shadow: 0 -1px 4px rgba(0, 0, 0, 0.03);
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.04);
}

.chat-input-area.variant-full :deep(.el-textarea__inner) {
  border-radius: 24px;
  padding: 18px 110px 18px 24px;
  font-size: 16px;
  line-height: 1.65;
  min-height: 60px;
  border: 1.5px solid transparent;
  background: #fff;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
  resize: none;
}

.chat-input-area.variant-full :deep(.el-textarea__inner:hover) {
  border-color: #d4d4cc;
}

.chat-input-area.variant-full :deep(.el-textarea__inner:focus) {
  border-color: #1a1a1a;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06), 0 4px 20px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.06);
  transform: translateY(-1px);
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.chat-input-area.variant-full :deep(.el-button--large.is-circle:hover) {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.22);
  transform: scale(1.05);
}

.chat-input-area.variant-compact .input-wrapper {
  width: 100%;
  max-width: 768px;
}

.chat-input-area.variant-compact :deep(.el-input__wrapper) {
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease;
}

.chat-input-area.variant-compact :deep(.el-input__wrapper:hover) {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.06);
}

.chat-input-area.variant-compact :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06), 0 0 0 1px rgba(0, 0, 0, 0.08);
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

.model-select-inline :deep(.el-input__wrapper) {
  background: transparent;
  border: 1px solid #e8e8e2;
  border-radius: 18px;
  box-shadow: none;
  padding: 2px 10px;
  transition: border-color 0.2s ease;
}

.model-select-inline :deep(.el-input__wrapper:hover) {
  border-color: #c0c0b8;
}

.model-select-inline :deep(.el-input__inner) {
  font-size: 12px;
  color: #666;
}

.skill-tag-row {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.chat-input-area.variant-compact .skill-tag-row {
  padding: 0;
  margin-bottom: 8px;
}

.skill-dropdown {
  width: auto;
  min-width: 80px;
}

.skill-dropdown :deep(.el-input__wrapper) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0 4px;
}

.skill-dropdown :deep(.el-input__wrapper:hover),
.skill-dropdown :deep(.el-input__wrapper.is-focus) {
  background: transparent;
  box-shadow: none;
}

.skill-dropdown :deep(.el-input__inner) {
  font-size: 12px;
  color: #999;
  text-align: right;
}

.skill-select-inline {
  flex-shrink: 0;
}

.skill-select-inline :deep(.el-input__wrapper) {
  background: transparent;
  border: 1px solid #e8e8e2;
  border-radius: 18px;
  box-shadow: none;
  padding: 2px 10px;
  transition: border-color 0.2s ease;
}

.skill-select-inline :deep(.el-input__wrapper:hover) {
  border-color: #c0c0b8;
}

.skill-select-inline :deep(.el-input__inner) {
  font-size: 12px;
  color: #666;
}
</style>
