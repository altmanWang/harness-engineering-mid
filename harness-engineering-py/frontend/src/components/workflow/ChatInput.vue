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
          class="mini-select"
          popper-class="mini-select-popper"
          @change="onModelChange"
        >
          <template #prefix>
            <el-icon class="select-prefix-icon"><Cpu /></el-icon>
          </template>
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
          class="mini-select"
          popper-class="mini-select-popper"
          placeholder="技能"
          clearable
          @change="onSkillChange"
        >
          <template #prefix>
            <el-icon class="select-prefix-icon"><MagicStick /></el-icon>
          </template>
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
        <div class="action-selects">
          <div v-if="models.length > 0" class="mini-select-wrap">
            <el-select v-model="selectedModel" size="small" @change="onModelChange">
              <template #prefix>
                <el-icon class="select-prefix-icon"><Cpu /></el-icon>
              </template>
              <el-option
                v-for="m in models"
                :key="m.id"
                :label="m.name"
                :value="m.id"
              />
            </el-select>
          </div>
          <div class="mini-select-wrap">
            <el-select
              :model-value="selectedSkillId || ''"
              size="small"
              placeholder="技能"
              clearable
              @change="onSkillChange"
            >
              <template #prefix>
                <el-icon class="select-prefix-icon"><MagicStick /></el-icon>
              </template>
              <el-option
                v-for="s in skills"
                :key="s.id"
                :label="s.name"
                :value="s.id"
              />
            </el-select>
          </div>
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
import { ref, watch, computed, nextTick } from 'vue'
import { Promotion, CloseBold, Cpu, MagicStick } from '@element-plus/icons-vue'
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
const prevSkillName = ref('')

const selectedSkillName = computed(() => {
  if (!props.selectedSkillId || !props.skills) return ''
  const skill = props.skills.find(s => s.id === props.selectedSkillId)
  return skill ? skill.name : ''
})

watch(() => props.model, (val) => { selectedModel.value = val })

// Watch selectedSkillId prop to insert/remove skill prefix in input
watch(() => props.selectedSkillId, (newId) => {
  // Remove previous skill prefix first
  if (prevSkillName.value) {
    const oldPrefix = `/${prevSkillName.value} `
    if (inputText.value.startsWith(oldPrefix)) {
      inputText.value = inputText.value.slice(oldPrefix.length)
    }
  }

  if (newId) {
    const skill = props.skills?.find(s => s.id === newId)
    if (skill) {
      prevSkillName.value = skill.name
      const prefix = `/${skill.name} `
      // nextTick ensures el-input internal state picks up the change
      nextTick(() => {
        inputText.value = prefix + inputText.value
      })
    }
  } else {
    prevSkillName.value = ''
  }
})

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
/* ===== Layout ===== */

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

/* ===== Input wrapper ===== */

.chat-input-area.variant-full .input-wrapper {
  position: relative;
  width: 100%;
  max-width: 680px;
}

.chat-input-area.variant-compact .input-wrapper {
  width: 100%;
  max-width: 768px;
}

/* ===== Full variant textarea ===== */

.chat-input-area.variant-full .chat-input-field {
  border-radius: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(0, 0, 0, 0.04);
}

.chat-input-area.variant-full :deep(.el-textarea__inner) {
  border-radius: 24px;
  padding: 18px 120px 18px 24px;
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

/* ===== Compact variant input ===== */

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

/* ===== Full variant action bar (inside textarea) ===== */

.full-actions {
  position: absolute;
  right: 10px;
  bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ===== Send button (full variant) ===== */

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

/* ===== Compact variant action bar ===== */

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.action-selects {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-actions-right {
  display: flex;
  gap: 8px;
}

/* ===== Unified mini-select (pill style, both variants) ===== */

.mini-select {
  width: auto;
  min-width: 86px;
}

.mini-select :deep(.el-input__wrapper) {
  background: transparent;
  border: 1px solid #e8e8e2;
  border-radius: 18px;
  box-shadow: none;
  padding: 2px 8px 2px 4px;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.mini-select :deep(.el-input__wrapper:hover) {
  border-color: #c0c0b8;
  background: #f8f8f5;
}

.mini-select :deep(.el-input__wrapper.is-focus) {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.08);
}

.mini-select :deep(.el-input__inner) {
  font-size: 12px;
  color: #666;
}

.select-prefix-icon {
  font-size: 13px;
  color: #999;
  margin-right: 2px;
}

/* Compact variant: same pill, no extra overrides needed */
.mini-select-wrap {
  flex-shrink: 0;
}

.mini-select-wrap :deep(.el-input__wrapper) {
  background: transparent;
  border: 1px solid #e8e8e2;
  border-radius: 18px;
  box-shadow: none;
  padding: 2px 8px 2px 4px;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.mini-select-wrap :deep(.el-input__wrapper:hover) {
  border-color: #c0c0b8;
  background: #f8f8f5;
}

.mini-select-wrap :deep(.el-input__wrapper.is-focus) {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.08);
}

.mini-select-wrap :deep(.el-input__inner) {
  font-size: 12px;
  color: #666;
}
</style>

<!-- Global popper panel style (unscoped, for both variants) -->
<style>
.mini-select-popper {
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.10), 0 0 0 1px rgba(0, 0, 0, 0.04) !important;
  padding: 4px 0 !important;
  margin-top: 4px !important;
}

.mini-select-popper .el-select-dropdown__item {
  font-size: 13px;
  padding: 7px 14px;
  border-radius: 6px;
  margin: 2px 4px;
  transition: background 0.15s ease;
}

.mini-select-popper .el-select-dropdown__item:hover {
  background: #f5f5f1;
}

.mini-select-popper .el-select-dropdown__item.is-selected {
  color: #1a1a1a;
  font-weight: 600;
  background: #f8f8f5;
}
</style>
