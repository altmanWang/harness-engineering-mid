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

    <!-- 策略配置折叠面板 -->
    <div v-if="selectedStrategy && getCurrentStrategy()" class="strategy-config-panel">
      <div class="config-header" @click="configExpanded = !configExpanded">
        <div class="config-summary">
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
            style="width: 160px"
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
            style="width: 160px"
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
import { Search, Loading, ArrowDown } from '@element-plus/icons-vue'
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

// 策略配置面板
const configExpanded = ref(false)
const currentConfigValues = ref<Record<string, any>>({})

function getCurrentStrategy(): StrategyInfo | undefined {
  return props.strategyList.find(s => s.id === props.selectedStrategy)
}

function onStrategyChange(strategyId: string) {
  emit('update:selectedStrategy', strategyId)
  // 切换策略时重置配置为默认值
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
  // 取前3个参数作为摘要
  return strategy.configSchema.slice(0, 3)
    .map(item => {
      const val = config[item.key] ?? item.default
      return `${item.label.split(/[（(]/)[0]}${val}`
    })
    .join(' · ')
}

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

/* 策略配置折叠面板 */
.strategy-config-panel {
  margin-top: 4px;
  margin-bottom: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
  overflow: hidden;
}
.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.config-header:hover {
  background: var(--el-fill-color-light);
}
.config-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.config-strategy-name {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}
.config-summary-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.config-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.config-arrow {
  transition: transform 0.2s;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}
.config-arrow.is-expanded {
  transform: rotate(180deg);
}
.config-body {
  padding: 8px 14px 14px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-wrap: wrap;
  gap: 10px 20px;
}
.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.config-label {
  font-size: 13px;
  color: var(--el-text-color-regular);
  white-space: nowrap;
  min-width: 110px;
}
.config-desc {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
