<template>
  <div class="stock-input">
    <div class="input-row">
      <div class="tag-input-wrapper">
        <el-tag
          v-for="code in modelValue"
          :key="code"
          closable
          :disable-transitions="false"
          class="stock-tag"
          @close="removeCode(code)"
        >
          {{ code }}
        </el-tag>
        <el-input
          v-if="inputVisible"
          ref="inputRef"
          v-model="inputValue"
          size="small"
          class="tag-input"
          placeholder="输入代码，回车添加"
          @keyup.enter="addCode"
          @blur="addCode"
        />
        <el-button
          v-else
          size="small"
          class="add-tag-btn"
          @click="showInput"
        >
          + 添加股票
        </el-button>
      </div>
    </div>

    <div class="input-row options-row">
      <el-select
        :model-value="days"
        placeholder="日期范围"
        style="width: 140px"
        @update:model-value="$emit('update:days', $event)"
      >
        <el-option label="近30天" :value="30" />
        <el-option label="近60天" :value="60" />
        <el-option label="近90天" :value="90" />
        <el-option label="近180天" :value="180" />
      </el-select>

      <el-select
        :model-value="selectedSkills"
        multiple
        placeholder="选择 Skills"
        style="width: 240px"
        @update:model-value="$emit('update:selectedSkills', $event)"
      >
        <el-option
          v-for="skill in skills"
          :key="skill.id"
          :label="skill.name"
          :value="skill.id"
        />
      </el-select>

      <el-button
        type="primary"
        :loading="isAnalyzing"
        :disabled="modelValue.length === 0"
        @click="$emit('start')"
      >
        {{ isAnalyzing ? '分析中...' : '开始诊股' }}
      </el-button>

      <el-button
        v-if="modelValue.length > 0 && !isAnalyzing"
        @click="$emit('clear')"
      >
        清空
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import type { Skill } from '@/types'

const props = defineProps<{
  modelValue: string[]
  days: number
  skills: Skill[]
  selectedSkills: string[]
  isAnalyzing: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [codes: string[]]
  'update:days': [days: number]
  'update:selectedSkills': [skills: string[]]
  start: []
  clear: []
}>()

const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

function showInput() {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function addCode() {
  const code = inputValue.value.trim().toUpperCase()
  if (code && !props.modelValue.includes(code)) {
    emit('update:modelValue', [...props.modelValue, code])
  }
  inputValue.value = ''
  inputVisible.value = false
}

function removeCode(code: string) {
  emit('update:modelValue', props.modelValue.filter(c => c !== code))
}
</script>

<style scoped>
.stock-input {
  margin-bottom: 20px;
}
.input-row {
  margin-bottom: 12px;
}
.options-row {
  display: flex;
  gap: 10px;
  align-items: center;
}
.tag-input-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  min-height: 36px;
  padding: 6px 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: #fff;
}
.stock-tag {
  font-family: monospace;
}
.tag-input {
  width: 160px;
}
.add-tag-btn {
  border-style: dashed;
}
</style>
