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
    const item = items.value.find(i => i.code === code)
    if (item) item.status = status
  }

  async function startAnalysis(codes: string[], days: number, skills: string[], existingSessionId?: string, model?: string) {
    if (isAnalyzing.value) return

    initItems(codes)
    isAnalyzing.value = true
    totalCount.value = codes.length
    completedCount.value = 0

    try {
      const res = await fetch('/api/stock/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codes,
          days,
          skills,
          sessionId: existingSessionId || undefined,
          model: model || undefined,
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
        const data = JSON.parse(e.data)
        totalCount.value = data.total || codes.length
        if (data.codes && data.codes.length > 0) {
          setItemStatus(data.codes[0], 'analyzing')
        }
      })

      es.addEventListener('stock_result', (e) => {
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
  }

  return {
    items,
    isAnalyzing,
    analysisId,
    sessionId,
    totalCount,
    completedCount,
    startAnalysis,
    cancelAnalysis,
  }
}
