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
        :session-id="sessionId || loadedSessionId || ''"
      />

      <!-- 分析进度条 -->
      <div v-if="isAnalyzing && !isSuppressed" class="analysis-progress">
        <el-progress
          :percentage="totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0"
          :stroke-width="6"
          :show-text="false"
        />
        <span class="progress-text">正在分析第 {{ completedCount + 1 > totalCount ? totalCount : completedCount + 1 }}/{{ totalCount }} 只</span>
      </div>

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
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
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

const { items, isAnalyzing, isSuppressed, totalCount, completedCount, startAnalysis, cancelAnalysis, suppress, resume, sessionId } = useStockAnalysis()

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
    // 切换到已完成的历史会话：抑制 SSE 但不关闭连接
    if (isAnalyzing.value && sessionId.value !== sid) {
      suppress()
    }

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
  } else if (session && session.type === 'stock_diagnosis' && isAnalyzing.value && sessionId.value === sid) {
    // 切回正在运行的 session：恢复 SSE 更新，从快照恢复
    resume()
    viewingRecord.value = null
    loadedSessionId.value = sid
  }
}

async function handleStart() {
  viewingRecord.value = null
  loadedSessionId.value = null
  try {
    await startAnalysis(codes.value, days.value, selectedSkills.value, undefined, chatStore.model || undefined)
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
.analysis-progress {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}
.analysis-progress .el-progress {
  flex: 1;
}
.progress-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}
</style>
