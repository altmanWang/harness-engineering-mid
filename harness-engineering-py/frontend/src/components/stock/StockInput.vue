<template>
  <div class="stock-input">
    <div class="input-row">
      <div class="option-item search-option-item">
        <label class="option-label">股票搜索</label>
        <div class="search-row">
          <el-input
            v-model="searchKeyword"
            placeholder="输入关键字搜索股票..."
            :loading="searchLoading"
            class="search-input"
            @keydown="onSearchKeydown"
            @focus="onSearchFocus"
            @input="onSearchInput"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #suffix>
              <el-icon
                v-if="searchKeyword && !searchLoading"
                class="search-clear-icon"
                @click.stop="clearSearch"
              >
                <CircleClose />
              </el-icon>
            </template>
          </el-input>
          <el-button
            :loading="searchLoading"
            :disabled="!searchKeyword.trim()"
            type="primary"
            @click="handleSearchEnter"
          >
            搜索
          </el-button>
        </div>
        <div
          v-if="showDropdown && (searchResults.length > 0 || searchLoading)"
          class="search-dropdown"
          @mouseleave="onDropdownLeave"
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
                  :class="{ 'is-added': isCodeAdded(stock.code) }"
                  @click="handleResultClick(stock)"
                >
                  <el-checkbox
                    :value="stock.code"
                    :disabled="isCodeAdded(stock.code)"
                    @click.stop
                  >
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
      <span class="input-helper">搜索股票后勾选添加，或直接输入代码按回车添加</span>
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
        <label class="option-label">策略</label>
        <el-select
          :model-value="selectedStrategy"
          placeholder="选择策略"
          style="width: 220px"
          @update:model-value="onStrategyChange"
        >
          <el-option
            v-for="s in strategyList"
            :key="s.id"
            :label="s.name"
            :value="s.id"
          />
        </el-select>
      </div>

      <el-button
        type="primary"
        :loading="isAnalyzing"
        :disabled="modelValue.length === 0 || !selectedStrategy"
        class="btn-start"
        @click="$emit('start')"
      >
        {{ isAnalyzing ? '分析中...' : '开始诊股' }}
      </el-button>

      <el-button
        v-if="modelValue.length > 0 && !isAnalyzing"
        class="btn-clear"
        @click="$emit('clear')"
      >
        清空
      </el-button>
    </div>

    <div v-if="selectedStrategy && getCurrentStrategy()" class="strategy-config-panel">
      <div class="config-header" @click="configExpanded = !configExpanded">
        <div class="config-summary">
          <span class="config-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20V10"/><path d="M18 20V4"/><path d="M6 20v-4"/>
            </svg>
          </span>
          <span class="config-strategy-name">{{ getCurrentStrategy()?.name }}</span>
          <span class="config-summary-text">{{ getSummary(currentConfigValues) }}</span>
        </div>
        <div class="config-actions">
          <el-button size="small" text @click.stop="resetConfig">重置默认</el-button>
          <el-icon :class="{ 'is-expanded': configExpanded }" class="config-arrow">
            <ArrowDown />
          </el-icon>
        </div>
      </div>
      <div v-show="configExpanded" class="config-body">
        <div
          v-for="item in getCurrentStrategy()?.configSchema || []"
          :key="item.key"
          class="config-item"
        >
          <label class="config-label">{{ item.label }}</label>
          <el-input-number
            v-if="item.type === 'int'"
            :model-value="currentConfigValues[item.key] ?? item.default"
            :min="item.min"
            :max="item.max"
            :step="item.step || 1"
            size="small"
            controls-position="right"
            class="config-input"
            @update:model-value="onConfigChange(item.key, $event)"
          />
          <el-input-number
            v-else-if="item.type === 'float'"
            :model-value="currentConfigValues[item.key] ?? item.default"
            :min="item.min"
            :max="item.max"
            :step="item.step || 0.01"
            :precision="3"
            size="small"
            controls-position="right"
            class="config-input"
            @update:model-value="onConfigChange(item.key, $event)"
          />
          <span class="config-desc">{{ item.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { Search, Loading, ArrowDown, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { StrategyInfo } from '@/types/stock'
import type { StockSearchResult } from '@/types/stock'

const props = defineProps<{
  modelValue: string[]
  days: number
  strategyList: StrategyInfo[]
  selectedStrategy: string
  strategyConfig: Record<string, any>
  isAnalyzing: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [codes: string[]]
  'update:days': [days: number]
  'update:selectedStrategy': [strategy: string]
  'update:strategyConfig': [config: Record<string, any>]
  start: []
  clear: []
}>()

const configExpanded = ref(false)
const currentConfigValues = ref<Record<string, any>>({})

function getCurrentStrategy(): StrategyInfo | undefined {
  return props.strategyList.find(s => s.id === props.selectedStrategy)
}

function onStrategyChange(strategyId: string) {
  emit('update:selectedStrategy', strategyId)
  const strategy = props.strategyList.find(s => s.id === strategyId)
  if (strategy) {
    const defaults: Record<string, any> = {}
    strategy.configSchema.forEach(item => {
      defaults[item.key] = item.default
    })
    currentConfigValues.value = defaults
    emit('update:strategyConfig', { ...defaults })
  }
}

function resetConfig() {
  const strategy = getCurrentStrategy()
  if (strategy) {
    const defaults: Record<string, any> = {}
    strategy.configSchema.forEach(item => {
      defaults[item.key] = item.default
    })
    currentConfigValues.value = { ...defaults }
    emit('update:strategyConfig', { ...defaults })
  }
}

function onConfigChange(key: string, value: any) {
  currentConfigValues.value[key] = value
  emit('update:strategyConfig', { ...currentConfigValues.value })
}

function getSummary(config: Record<string, any>): string {
  const strategy = getCurrentStrategy()
  if (!strategy || !strategy.configSchema || strategy.configSchema.length === 0) return ''
  return strategy.configSchema.slice(0, 3)
    .map(item => {
      const val = config[item.key] ?? item.default
      return `${item.label.split(/[（(]/)[0]}${val}`
    })
    .join(' · ')
}

const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

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

// 聚焦时自动重新搜索（如果有关键词）
function onSearchFocus() {
  if (searchKeyword.value.trim() && searchResults.value.length === 0) {
    handleSearchEnter()
  } else if (searchResults.value.length > 0) {
    showDropdown.value = true
  }
}

// 输入时自动搜索（防抖 300ms）
let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    // 清空输入框后关闭下拉
    searchResults.value = []
    checkedStocks.value = []
    showDropdown.value = false
    return
  }
  // 如果之前有结果，直接显示下拉；否则自动搜索
  if (searchResults.value.length > 0) {
    showDropdown.value = true
  }
  searchTimer = setTimeout(() => {
    doSearch(keyword)
  }, 300)
}

// 点击结果行直接添加（已添加的不可再添加）
function handleResultClick(stock: StockSearchResult) {
  if (isCodeAdded(stock.code)) return
  emit('update:modelValue', [...props.modelValue, stock.code])
  ElMessage.success(`已添加 ${stock.code} ${stock.name}`)
  // 不关闭下拉，允许继续添加
}

// 鼠标移出下拉区域自动关闭
function onDropdownLeave() {
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
  margin-bottom: 24px;
}

.input-row {
  margin-bottom: 14px;
}

.options-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.option-label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  letter-spacing: 0.01em;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.tag-input-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  min-height: 42px;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: var(--el-bg-color);
  transition: border-color 0.2s;
}

.tag-input-wrapper:focus-within {
  border-color: #059669;
  box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
}

.stock-tag {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  font-weight: 500;
}

.tag-input {
  width: 160px;
}

.add-tag-btn {
  border-style: dashed;
  color: #64748b;
}

.input-helper {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.btn-start {
  font-weight: 600;
  padding: 0 24px;
  background: #059669;
  border-color: #059669;
}

.btn-start:hover {
  background: #047857;
  border-color: #047857;
}

.btn-clear {
  color: #64748b;
  border-color: #e2e8f0;
}

.strategy-config-panel {
  margin-top: 6px;
  margin-bottom: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: var(--el-bg-color);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.strategy-config-panel:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}

.config-header:hover {
  background: #f8fafc;
}

.config-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.config-icon {
  color: #059669;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.config-strategy-name {
  font-size: 14px;
  font-weight: 600;
  color: #0F172A;
  white-space: nowrap;
}

.config-summary-text {
  font-size: 12px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.config-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.config-arrow {
  transition: transform 0.2s;
  font-size: 14px;
  color: #64748b;
}

.config-arrow.is-expanded {
  transform: rotate(180deg);
}

.config-body {
  padding: 12px 16px 16px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  flex-wrap: wrap;
  gap: 12px 24px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  font-size: 13px;
  color: #334155;
  white-space: nowrap;
  min-width: 110px;
  font-weight: 500;
}

.config-input {
  width: 160px;
}

.config-desc {
  font-size: 11px;
  color: #94a3b8;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 搜索容器设置相对定位，让下拉框定位在此下方 */
.search-option-item {
  position: relative;
}

/* 自定义清除图标，比 el-input 自带的 clearable 更大更好点 */
.search-clear-icon {
  cursor: pointer;
  color: #94a3b8;
  font-size: 16px;
  transition: color 0.15s;
}
.search-clear-icon:hover {
  color: #475569;
}

/* 搜索结果下拉 */
.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  margin-top: 6px;
  width: 100%;
  max-width: 600px;
  background: var(--el-bg-color);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.search-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #64748b;
  font-size: 13px;
}

.search-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  background: #f8fafc;
}

.search-count {
  font-size: 12px;
  color: #64748b;
}

.search-results {
  max-height: 280px;
  overflow-y: auto;
  padding: 6px 0;
}

.search-result-item {
  padding: 4px 12px;
  transition: background 0.15s;
  cursor: pointer;
}

.search-result-item:hover {
  background: #f8fafc;
}
.search-result-item.is-added {
  cursor: default;
  opacity: 0.65;
}
.search-result-item.is-added:hover {
  background: transparent;
}
.search-result-item .el-checkbox {
  width: 100%;
}

.stock-code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-weight: 600;
  margin-right: 8px;
  color: #059669;
}

.stock-name {
  margin-right: 6px;
  color: #334155;
}

.stock-type-tag {
  margin-left: 6px;
}

.search-footer {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  border-top: 1px solid #f1f5f9;
  justify-content: flex-end;
}
</style>
