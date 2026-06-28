import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { DiagnosisResult } from '@/types/stock'

export interface StockItem {
  code: string
  status: 'pending' | 'analyzing' | 'done' | 'error'
  result: DiagnosisResult | null
  error: string | null
}

export function useStockAnalysis() {
  const items = ref<StockItem[]>([])
  const isAnalyzing = ref(false)
  const isSuppressed = ref(false)
  const suppressedSnapshot = ref<StockItem[] | null>(null)
  const analysisId = ref<string | null>(null)
  const sessionId = ref<string | null>(null)
  const totalCount = ref(0)
  const completedCount = ref(0)

  let eventSource: EventSource | null = null

  function initItems(codes: string[]) {
    items.value = codes.map(code => ({
      code,
      status: 'pending' as const,
      result: null,
      error: null,
    }))
  }

  function setItemStatus(code: string, status: StockItem['status']) {
    if (isSuppressed.value) return
    const item = items.value.find(i => i.code === code)
    if (item) item.status = status
  }

  /** 抑制 SSE 更新（切换到历史会话时），保存当前快照以便恢复 */
  function suppress() {
    suppressedSnapshot.value = items.value.map(i => ({ ...i }))
    isSuppressed.value = true
  }

  /** 恢复 SSE 更新（切回运行中会话时），从快照恢复 items */
  function resume() {
    isSuppressed.value = false
    if (suppressedSnapshot.value) {
      items.value = suppressedSnapshot.value
      suppressedSnapshot.value = null
    }
  }

  async function startAnalysis(codes: string[], days: number, strategy: string, strategyConfig: Record<string, any>, existingSessionId?: string) {
    if (isAnalyzing.value) return

    initItems(codes)
    isAnalyzing.value = true
    isSuppressed.value = false
    suppressedSnapshot.value = null
    totalCount.value = codes.length
    completedCount.value = 0

    try {
      const res = await fetch('/api/stock/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codes,
          days,
          strategy,
          strategyConfig,
          sessionId: existingSessionId || undefined,
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '请求失败')
      }

      const { analysisId: aid, sessionId: sid } = await res.json()
      analysisId.value = aid
      sessionId.value = sid

      const es = new EventSource(`/api/stock/stream?analysisId=${aid}`)
      eventSource = es

      es.addEventListener('start', (e) => {
        if (isSuppressed.value) return
        const data = JSON.parse(e.data)
        totalCount.value = data.total || codes.length
        if (data.codes && data.codes.length > 0) {
          setItemStatus(data.codes[0], 'analyzing')
        }
      })

      es.addEventListener('stock_result', (e) => {
        if (isSuppressed.value) return
        const data = JSON.parse(e.data) as DiagnosisResult
        const item = items.value.find(i => i.code === data.code)
        if (item) {
          item.status = 'done'
          item.result = data
        }
        completedCount.value++
        const nextPending = items.value.find(i => i.status === 'pending')
        if (nextPending) {
          nextPending.status = 'analyzing'
        }
      })

      es.addEventListener('stock_error', (e) => {
        if (isSuppressed.value) return
        const data = JSON.parse(e.data)
        const item = items.value.find(i => i.code === data.code)
        if (item) {
          item.status = 'error'
          item.error = data.error || '未知错误'
        }
        completedCount.value++
        const nextPending = items.value.find(i => i.status === 'pending')
        if (nextPending) {
          nextPending.status = 'analyzing'
        }
      })

      es.addEventListener('done', () => {
        isAnalyzing.value = false
        es.close()
        eventSource = null
      })

      es.onerror = () => {
        isAnalyzing.value = false
        es.close()
        eventSource = null
      }

    } catch (err) {
      isAnalyzing.value = false
      console.error('Stock analysis failed:', err)
      throw err
    }
  }

  function cancelAnalysis() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isAnalyzing.value = false
    isSuppressed.value = false
    suppressedSnapshot.value = null
  }

  return {
    items,
    isAnalyzing,
    isSuppressed,
    analysisId,
    sessionId,
    totalCount,
    completedCount,
    startAnalysis,
    cancelAnalysis,
    suppress,
    resume,
  }
}
