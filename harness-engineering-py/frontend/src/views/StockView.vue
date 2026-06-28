<template>
  <div class="stock-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          {{ viewingRecord ? `智能诊股 — ${viewingRecord.title}` : '智能诊股' }}
        </h2>
        <p class="page-subtitle">基于策略信号模型，智能判断买入/观望时机</p>
      </div>
    </div>

    <StockCompare
      v-if="compareRecords.length >= 2"
      :compare-records="compareRecords"
    />

    <template v-else>
      <StockInput
        v-model="codes"
        v-model:days="days"
        :strategy-list="strategyList"
        v-model:selected-strategy="selectedStrategy"
        v-model:strategy-config="strategyConfig"
        :is-analyzing="isAnalyzing"
        @start="handleStart"
        @clear="handleClear"
      />

      <StockResultTable
        v-if="items.length > 0"
        :items="items"
        :session-id="sessionId || loadedSessionId || ''"
        @backtest="handleBacktest"
      />

      <BacktestDialog
        v-model="backtestVisible"
        :result="backtestResult"
        :session-id="sessionId || loadedSessionId || ''"
      />

      <div v-if="isAnalyzing && !isSuppressed" class="analysis-progress">
        <div class="progress-info">
          <span class="progress-label">分析进度</span>
          <span class="progress-count">{{ completedCount }} / {{ totalCount }}</span>
        </div>
        <el-progress
          :percentage="totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0"
          :stroke-width="8"
          :show-text="false"
          color="#059669"
        />
      </div>

      <div v-else-if="!isAnalyzing && items.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h3 class="empty-title">开始智能诊股</h3>
        <p class="empty-desc">搜索并添加股票代码，选择策略后点击「开始诊股」</p>
      </div>
    </template>

    <div v-if="viewingRecord && compareRecords.length < 2" class="record-actions">
      <el-button type="primary" @click="handleAskAI">
        追问 AI
      </el-button>
      <span class="record-time">{{ viewingRecord.updatedAt }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import StockInput from '@/components/stock/StockInput.vue'
import StockResultTable from '@/components/stock/StockResultTable.vue'
import StockCompare from '@/components/stock/StockCompare.vue'
import BacktestDialog from '@/components/stock/BacktestDialog.vue'
import { useStockAnalysis } from '@/composables/useStockAnalysis'
import type { StrategyInfo } from '@/types/stock'
import type { DiagnosisResult } from '@/types/stock'
import type { StockItem } from '@/composables/useStockAnalysis'
import type { ChatSession } from '@/types/chat'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const { items, isAnalyzing, isSuppressed, totalCount, completedCount, startAnalysis, cancelAnalysis, suppress, resume, sessionId } = useStockAnalysis()

const codes = ref<string[]>([])
const days = ref(90)
const strategyList = ref<StrategyInfo[]>([])
const selectedStrategy = ref('ema_pullback')
const strategyConfig = ref<Record<string, any>>({})

const backtestVisible = ref(false)
const backtestResult = ref<DiagnosisResult | null>(null)

const viewingRecord = ref<ChatSession | null>(null)
const loadedSessionId = ref<string | null>(null)

const compareIds = computed(() => {
  const raw = route.query.compare as string
  if (!raw) return []
  return raw.split(',').filter(Boolean)
})
const compareRecords = computed(() => {
  if (compareIds.value.length === 0) return []
  return compareIds.value
    .map(id => chatStore.sessions.find(s => s.id === id))
    .filter(Boolean) as ChatSession[]
})

onMounted(async () => {
  try {
    const res = await fetch('/api/stock/strategies')
    if (res.ok) {
      const data = await res.json()
      strategyList.value = data.strategies || []
      if (strategyList.value.length > 0) {
        const defaults: Record<string, any> = {}
        strategyList.value[0].configSchema.forEach(item => {
          defaults[item.key] = item.default
        })
        strategyConfig.value = defaults
      }
    }
  } catch {}

  await chatStore.loadSessions()
  loadViewingRecord()
})

onBeforeUnmount(() => {
  if (isAnalyzing.value) {
    cancelAnalysis()
  }
})

watch(() => chatStore.currentSessionId, () => {
  loadViewingRecord()
})

function loadViewingRecord() {
  const sid = chatStore.currentSessionId
  if (!sid) return
  if (sid === loadedSessionId.value) return

  const session = chatStore.sessions.find(s => s.id === sid)
  if (session && session.type === 'stock_diagnosis' && session.diagnosis) {
    if (isAnalyzing.value && sessionId.value !== sid) {
      suppress()
    }

    viewingRecord.value = session
    loadedSessionId.value = sid

    codes.value = session.diagnosis.codes || []
    days.value = session.diagnosis.days || 90
    selectedStrategy.value = session.diagnosis.strategy || 'ema_pullback'
    strategyConfig.value = session.diagnosis.strategyConfig || {}

    const diag = session.diagnosis
    items.value = (diag.codes || []).map(code => {
      const result = diag.results.find(r => r.code === code)
      if (result) {
        return {
          code,
          status: (result.conclusion ? 'done' : 'error') as StockItem['status'],
          result: result.conclusion ? result : null,
          error: result.error || null,
        }
      }
      return { code, status: 'pending' as const, result: null, error: null }
    })
  } else if (session && session.type === 'stock_diagnosis' && isAnalyzing.value && sessionId.value === sid) {
    resume()
    viewingRecord.value = null
    loadedSessionId.value = sid
  }
}

async function handleStart() {
  viewingRecord.value = null
  loadedSessionId.value = null
  try {
    await startAnalysis(codes.value, days.value, selectedStrategy.value, strategyConfig.value)
    await chatStore.loadSessions()
  } catch (err: any) {
    ElMessage.error(err?.message || '分析启动失败，请重试')
  }
}

function handleClear() {
  if (isAnalyzing.value) {
    cancelAnalysis()
  }
  codes.value = []
  items.value = []
  viewingRecord.value = null
  loadedSessionId.value = null
  chatStore.clearSession()
}

async function handleAskAI() {
  if (!viewingRecord.value?.diagnosis) return

  const diag = viewingRecord.value.diagnosis
  const summary = diag.results
    .filter(r => r.conclusion)
    .map(r => `${r.code} ${r.name}: ${r.conclusion}`)
    .join('\n')

  const prompt = `以下是之前对以下股票的诊股结果:\n${summary}\n\n我想进一步了解: `

  await chatStore.createSession()
  chatStore.messages = [{
    id: `msg-${Date.now()}`,
    role: 'user',
    content: prompt,
    timestamp: new Date().toISOString(),
  }]
  router.push('/')
}

function handleBacktest(row: StockItem) {
  if (!row.result) return
  backtestResult.value = row.result
  backtestVisible.value = true
}
</script>

<style scoped>
.stock-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  color: #0F172A;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.record-actions {
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.record-time {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}

.analysis-progress {
  margin-top: 16px;
  padding: 16px 20px;
  background: var(--el-bg-color);
  border-radius: 10px;
  border: 1px solid var(--el-border-color-light);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.progress-label {
  font-size: 13px;
  font-weight: 500;
  color: #334155;
}

.progress-count {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
}

.empty-state {
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 24px;
}

.empty-icon {
  margin-bottom: 8px;
  opacity: 0.6;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.empty-desc {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}
</style>
