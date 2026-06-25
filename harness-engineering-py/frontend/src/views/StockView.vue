<template>
  <div class="stock-page">
    <div class="page-header">
      <h2 class="page-title">
        {{ viewingRecord ? `智能诊股 — ${viewingRecord.title}` : '智能诊股' }}
      </h2>
    </div>

    <StockCompare
      v-if="compareRecords.length >= 2"
      :compare-records="compareRecords"
    />

    <template v-else>
      <StockInput
        v-model="codes"
        v-model:days="days"
        :skills="skillList"
        v-model:selected-skills="selectedSkills"
        :is-analyzing="isAnalyzing"
        @start="handleStart"
        @clear="handleClear"
      />

      <StockResultTable
        v-if="items.length > 0"
        :items="items"
      />

      <el-empty
        v-else-if="!isAnalyzing"
        description="输入股票代码，点击「开始诊股」开始分析"
      />
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import StockInput from '@/components/stock/StockInput.vue'
import StockResultTable from '@/components/stock/StockResultTable.vue'
import StockCompare from '@/components/stock/StockCompare.vue'
import { useStockAnalysis } from '@/composables/useStockAnalysis'
import type { Skill } from '@/types'
import type { StockItem } from '@/composables/useStockAnalysis'
import type { ChatSession } from '@/types/chat'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const { items, isAnalyzing, startAnalysis } = useStockAnalysis()

const codes = ref<string[]>([])
const days = ref(90)
const skillList = ref<Skill[]>([])
const selectedSkills = ref<string[]>([])

const viewingRecord = ref<ChatSession | null>(null)
const loadedSessionId = ref<string | null>(null)

// Compare mode
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
    const res = await fetch('/api/skills')
    if (res.ok) {
      const data = await res.json()
      skillList.value = data.skills || []
    }
  } catch {}

  await chatStore.loadSessions()
  loadViewingRecord()
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
    viewingRecord.value = session
    loadedSessionId.value = sid

    codes.value = session.diagnosis.codes || []
    days.value = session.diagnosis.days || 90
    selectedSkills.value = session.diagnosis.skills || []

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
  }
}

async function handleStart() {
  viewingRecord.value = null
  loadedSessionId.value = null
  try {
    await startAnalysis(codes.value, days.value, selectedSkills.value)
    await chatStore.loadSessions()
  } catch (err: any) {
    console.error('Analysis failed:', err)
  }
}

function handleClear() {
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
    .map(r => `${r.code} ${r.name}: ${r.conclusion} - ${r.reason}`)
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
</script>

<style scoped>
.stock-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.page-header {
  margin-bottom: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
.record-actions {
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.record-time {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
}
</style>
