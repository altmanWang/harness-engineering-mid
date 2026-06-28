import { ref } from 'vue'
import type { BacktestSummary, BacktestBar, DiagnosisResult } from '@/types/stock'

export function useBacktest() {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const summary = ref<BacktestSummary | null>(null)
  const bars = ref<BacktestBar[]>([])

  async function fetchBacktest(result: DiagnosisResult, sessionId: string) {
    // Already cached — fetch directly
    if (result.backtestSummaryPath && result.backtestBarsPath) {
      loading.value = true
      error.value = null
      try {
        const [summaryRes, barsRes] = await Promise.all([
          fetch(`/api/stock/backtest/summary/${sessionId}/${result.code}`),
          fetch(`/api/stock/backtest/bars/${sessionId}/${result.code}`),
        ])

        if (!summaryRes.ok) throw new Error('Failed to load backtest summary')
        if (!barsRes.ok) throw new Error('Failed to load backtest bars')

        summary.value = await summaryRes.json()
        const barsData = await barsRes.json()
        bars.value = barsData.bars as BacktestBar[]
      } catch (e: any) {
        error.value = e.message || '加载回测数据失败'
      } finally {
        loading.value = false
      }
      return
    }

    // No cache — trigger backtest
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/stock/backtest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: result.code,
          sessionId,
          strategy: 'ema_pullback',
          strategyConfig: {},
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '回测计算失败')
      }

      summary.value = await res.json()

      // Fetch bars after successful backtest
      const barsRes = await fetch(`/api/stock/backtest/bars/${sessionId}/${result.code}`)
      if (barsRes.ok) {
        const barsData = await barsRes.json()
        bars.value = barsData.bars as BacktestBar[]
      }

      // Update result cache paths for subsequent opens
      result.backtestSummaryPath = `worktrees/${sessionId}/backtest/${result.code}_summary.json`
      result.backtestBarsPath = `worktrees/${sessionId}/backtest/${result.code}_bars.csv`
    } catch (e: any) {
      error.value = e.message || '回测计算失败'
    } finally {
      loading.value = false
    }
  }

  function reset() {
    loading.value = false
    error.value = null
    summary.value = null
    bars.value = []
  }

  return { loading, error, summary, bars, fetchBacktest, reset }
}
