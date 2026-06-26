<template>
  <div class="stock-input">
    <!-- 关键字搜索股票 -->
    <div class="input-row">
      <div class="option-item" style="flex: 1;">
        <label class="option-label">股票搜索</label>
        <div class="search-row">
          <el-input
            v-model="searchKeyword"
            placeholder="输入关键字搜索股票..."
            clearable
            :loading="searchLoading"
            style="flex: 1;"
            @keydown="onSearchKeydown"
            @clear="clearSearch"
            @focus="showDropdown = searchResults.length > 0"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button
            :loading="searchLoading"
            :disabled="!searchKeyword.trim()"
            @click="handleSearchEnter"
          >
            搜索
          </el-button>
        </div>
        <!-- 搜索结果下拉面板 -->
        <div
          v-if="showDropdown && (searchResults.length > 0 || searchLoading)"
          class="search-dropdown"
        >
          <div v-if="searchLoading" class="search-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>搜索中...</span>
          </div>
          <template v-else>
            <div class="search-actions">
              <el-checkbox
                :model-value="isAllSelected"
                :indeterminate="isIndeterminate"
                @change="handleSelectAll"
              >
                全选
              </el-checkbox>
              <span class="search-count">共 {{ searchResults.length }} 条结果</span>
            </div>
            <div class="search-results">
              <el-checkbox-group v-model="checkedStocks">
                <div
                  v-for="stock in searchResults"
                  :key="stock.code"
                  class="search-result-item"
                >
                  <el-checkbox :value="stock.code" :disabled="isCodeAdded(stock.code)">
                    <span class="stock-code">{{ stock.code }}</span>
                    <span class="stock-name">{{ stock.name }}</span>
                    <el-tag v-if="stock.type" size="small" type="info" class="stock-type-tag">
                      {{ stock.type }}
                    </el-tag>
                    <el-tag v-if="isCodeAdded(stock.code)" size="small" type="success">
                      已添加
                    </el-tag>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>
            <div class="search-footer">
              <el-button size="small" type="primary" :disabled="checkedStocks.length === 0" @click="addCheckedStocks">
                添加选中 ({{ checkedStocks.length }})
              </el-button>
              <el-button size="small" @click="showDropdown = false">取消</el-button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 股票代码标签输入器（始终显示） -->
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
          @keydown="onTagKeydown"
          @keydown.backspace="handleBackspace"
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
      <span class="input-helper">搜索股票后勾选添加，或直接输入代码按回车添加。按 Backspace 删除最后一个标签</span>
    </div>

    <div class="input-row options-row">
      <div class="option-item">
        <label class="option-label">日期范围</label>
        <el-select
          :model-value="days"
          placeholder="选择天数"
          style="width: 140px"
          @update:model-value="$emit('update:days', $event)"
        >
          <el-option label="近30天" :value="30" />
          <el-option label="近60天" :value="60" />
          <el-option label="近90天" :value="90" />
          <el-option label="近180天" :value="180" />
        </el-select>
      </div>

      <div class="option-item">
        <label class="option-label">Skills</label>
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
      </div>

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
import { ref, computed, nextTick } from 'vue'
import { Search, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { Skill } from '@/types'
import type { StockSearchResult } from '@/types/stock'

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

// 手动输入标签
const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

// 搜索相关
const searchKeyword = ref('')
const searchLoading = ref(false)
const searchResults = ref<StockSearchResult[]>([])
const checkedStocks = ref<string[]>([])
const showDropdown = ref(false)

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

function onTagKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    addCode()
  }
}

function removeCode(code: string) {
  emit('update:modelValue', props.modelValue.filter(c => c !== code))
}

function handleBackspace() {
  if (inputValue.value === '' && props.modelValue.length > 0) {
    removeCode(props.modelValue[props.modelValue.length - 1])
  }
}

// ---- 搜索逻辑 ----
function onSearchKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    handleSearchEnter()
  }
}

function handleSearchEnter() {
  const keyword = searchKeyword.value.trim()
  if (!keyword || searchLoading.value) return
  doSearch(keyword)
}

async function doSearch(keyword: string) {
  searchLoading.value = true
  try {
    const res = await fetch(`/api/stock/search?keyword=${encodeURIComponent(keyword)}`)
    if (!res.ok) {
      ElMessage.error('搜索失败')
      searchResults.value = []
      return
    }
    const data = await res.json()
    searchResults.value = (data.stocks || []) as StockSearchResult[]
    checkedStocks.value = []
    showDropdown.value = true
  } catch (e: any) {
    ElMessage.error('搜索请求失败: ' + (e.message || '网络错误'))
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

function clearSearch() {
  searchKeyword.value = ''
  searchResults.value = []
  checkedStocks.value = []
  showDropdown.value = false
}

function isCodeAdded(code: string): boolean {
  return props.modelValue.includes(code)
}

const isAllSelected = computed(() => {
  if (searchResults.value.length === 0) return false
  const available = searchResults.value.filter(s => !isCodeAdded(s.code))
  if (available.length === 0) return false
  return available.every(s => checkedStocks.value.includes(s.code))
})

const isIndeterminate = computed(() => {
  if (searchResults.value.length === 0) return false
  const available = searchResults.value.filter(s => !isCodeAdded(s.code))
  const selected = available.filter(s => checkedStocks.value.includes(s.code))
  return selected.length > 0 && selected.length < available.length
})

function handleSelectAll(checked: boolean) {
  if (checked) {
    checkedStocks.value = searchResults.value
      .filter(s => !isCodeAdded(s.code))
      .map(s => s.code)
  } else {
    checkedStocks.value = []
  }
}

function addCheckedStocks() {
  if (checkedStocks.value.length === 0) return
  const newCodes = checkedStocks.value.filter(c => !props.modelValue.includes(c))
  if (newCodes.length > 0) {
    emit('update:modelValue', [...props.modelValue, ...newCodes])
  }
  checkedStocks.value = []
  showDropdown.value = false
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
  max-height: 200px;
  overflow-y: auto;
  padding: 6px 10px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: var(--el-bg-color);
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
.input-helper {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.option-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.option-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}
.search-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 搜索结果下拉 */
.search-dropdown {
  position: absolute;
  z-index: 1000;
  margin-top: 4px;
  width: 100%;
  max-width: 600px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}
.search-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.search-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
}
.search-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.search-results {
  max-height: 260px;
  overflow-y: auto;
  padding: 4px 0;
}
.search-result-item {
  padding: 4px 12px;
  transition: background 0.15s;
}
.search-result-item:hover {
  background: var(--el-fill-color-light);
}
.search-result-item .el-checkbox {
  width: 100%;
}
.stock-code {
  font-family: monospace;
  font-weight: 600;
  margin-right: 8px;
  color: var(--el-color-primary);
}
.stock-name {
  margin-right: 6px;
}
.stock-type-tag {
  margin-left: 6px;
}
.search-footer {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  justify-content: flex-end;
}
</style>
