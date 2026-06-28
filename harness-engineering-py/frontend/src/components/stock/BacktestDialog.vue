<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="1100px"
    top="3vh"
    destroy-on-close
    @opened="onOpened"
    @closed="onClosed"
  >
    <div v-if="loading" class="bt-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>回测计算中...</span>
    </div>

    <div v-else-if="error" class="bt-error">
      <el-icon><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>

    <template v-else-if="summary">
      <!-- 汇总卡片 -->
      <div class="bt-summary-cards">
        <div class="bt-card">
          <div class="bt-card-label">总收益率</div>
          <div class="bt-card-value" :class="summary.total_return >= 0 ? 'text-green' : 'text-red'">
            {{ summary.total_return >= 0 ? '+' : '' }}{{ summary.total_return.toFixed(2) }}%
          </div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">最大回撤</div>
          <div class="bt-card-value text-red">-{{ summary.max_drawdown.toFixed(2) }}%</div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">胜率</div>
          <div class="bt-card-value" :class="summary.win_rate >= 50 ? 'text-green' : 'text-orange'">
            {{ summary.win_rate.toFixed(1) }}%
          </div>
        </div>
        <div class="bt-card">
          <div class="bt-card-label">交易次数</div>
          <div class="bt-card-value text-default">{{ summary.trade_count }}</div>
        </div>
      </div>

      <!-- K线图 -->
      <div class="bt-chart-section">
        <div class="bt-chart-title">K线图 · 买卖信号</div>
        <div ref="klineChartRef" class="bt-chart kline-chart"></div>
      </div>

      <!-- 底部双图 -->
      <div class="bt-charts-row">
        <div class="bt-chart-section bt-chart-half">
          <div class="bt-chart-title">收益率曲线</div>
          <div ref="returnChartRef" class="bt-chart"></div>
        </div>
        <div class="bt-chart-section bt-chart-half">
          <div class="bt-chart-title">资金变化</div>
          <div ref="capitalChartRef" class="bt-chart"></div>
        </div>
      </div>
    </template>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useBacktest } from '@/composables/useBacktest'
import type { DiagnosisResult } from '@/types/stock'

const props = defineProps<{
  modelValue: boolean
  result: DiagnosisResult | null
  sessionId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => { visible.value = v })
watch(visible, v => { emit('update:modelValue', v) })

const { loading, error, summary, bars, fetchBacktest, reset } = useBacktest()

interface KLineRow {
  date: string; open: number; close: number; high: number; low: number; volume: number; ema20: number
}
const klineData = ref<KLineRow[]>([])

const title = computed(() => {
  if (!props.result) return '回测详情'
  return `回测详情 — ${props.result.name || props.result.code} (${props.result.code})`
})

const klineChartRef = ref<HTMLDivElement | null>(null)
const returnChartRef = ref<HTMLDivElement | null>(null)
const capitalChartRef = ref<HTMLDivElement | null>(null)

let klineInstance: echarts.ECharts | null = null
let returnInstance: echarts.ECharts | null = null
let capitalInstance: echarts.ECharts | null = null

function onOpened() {
  if (!props.result) return
  fetchBacktest(props.result, props.sessionId).then(() => {
    // Also fetch real K-line data for the candlestick chart
    fetch(`/api/stock/kline/${props.sessionId}/${props.result!.code}`)
      .then(res => res.ok ? res.json() : null)
      .then(json => {
        if (json?.data) klineData.value = json.data as KLineRow[]
      })
      .finally(() => {
        if (!error.value && bars.value.length > 0) {
          nextTick(() => {
            renderKLineChart()
            renderReturnChart()
            renderCapitalChart()
          })
        }
      })
  })
}

function onClosed() {
  reset()
  klineData.value = []
  disposeCharts()
}

function disposeCharts() {
  klineInstance?.dispose(); klineInstance = null
  returnInstance?.dispose(); returnInstance = null
  capitalInstance?.dispose(); capitalInstance = null
}

function renderKLineChart() {
  if (!klineChartRef.value || bars.value.length === 0) return
  if (klineInstance) klineInstance.dispose()
  klineInstance = echarts.init(klineChartRef.value)

  const dates = bars.value.map(b => b.date)

  // Use real K-line data if available, otherwise approximate from bars
  const ohlcData = klineData.value.length > 0
    ? klineData.value.map(d => [d.open, d.close, d.low, d.high])
    : bars.value.map(b => {
        const o = b.open; const c = b.close
        return [o, c, Math.max(o, c), Math.min(o, c)]
      })

  const volumeData = klineData.value.length > 0
    ? klineData.value.map(d => d.volume)
    : bars.value.map(b => {
        const cost = b.cost || 0
        return cost > 0 ? Math.round(cost / (b.close || 1)) : 0
      })

  // Buy/Sell markers from backtest bars
  const buyMarks = bars.value
    .map((b, i) => b.signal === '买入' ? { coord: [dates[i], ohlcData[i][2]], value: '买入' } : null)
    .filter(Boolean) as { coord: [string, number]; value: string }[]
  const sellMarks = bars.value
    .map((b, i) => b.signal === '卖出' ? { coord: [dates[i], ohlcData[i][3]], value: '卖出' } : null)
    .filter(Boolean) as { coord: [string, number]; value: string }[]

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    grid: [
      { left: '8%', right: '4%', top: 20, height: '55%' },
      { left: '8%', right: '4%', top: '76%', height: '16%' },
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: true, axisLine: { onZero: false }, gridIndex: 0 },
      { type: 'category', data: dates, boundaryGap: true, axisLabel: { show: false }, axisTick: { show: false }, gridIndex: 1 },
    ],
    yAxis: [
      { type: 'value', scale: true, position: 'left', gridIndex: 0 },
      { type: 'value', scale: true, position: 'left', gridIndex: 1, splitNumber: 3 },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100, bottom: 4 },
    ],
    series: [
      {
        name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0, data: ohlcData,
        itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' },
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumeData.map((vol, i) => {
          const item = ohlcData[i]
          return { value: vol, itemStyle: { color: item[1] >= item[0] ? '#ef5350' : '#26a69a' } }
        }),
      },
      {
        name: '买入', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0,
        data: buyMarks.map(m => m.coord),
        symbol: 'triangle', symbolSize: 16, symbolRotate: 0,
        itemStyle: { color: '#16a34a' },
        label: { show: true, formatter: '买', position: 'bottom', color: '#16a34a', fontSize: 10, fontWeight: 'bold' },
      },
      {
        name: '卖出', type: 'scatter', xAxisIndex: 0, yAxisIndex: 0,
        data: sellMarks.map(m => m.coord),
        symbol: 'triangle', symbolSize: 16, symbolRotate: 180,
        itemStyle: { color: '#dc2626' },
        label: { show: true, formatter: '卖', position: 'top', color: '#dc2626', fontSize: 10, fontWeight: 'bold' },
      },
    ],
  }

  klineInstance.setOption(option)
  klineInstance.group = 'backtest-group'
}

function renderReturnChart() {
  if (!returnChartRef.value || bars.value.length === 0 || !summary.value) return
  if (returnInstance) returnInstance.dispose()
  returnInstance = echarts.init(returnChartRef.value)

  const dates = bars.value.map(b => b.date)
  const initialCapital = summary.value.initial_capital
  const returns = bars.value.map(b => {
    const cap = b.capital || initialCapital
    return ((cap / initialCapital) - 1) * 100
  })

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `${p.axisValue}<br/>收益率: ${p.data >= 0 ? '+' : ''}${p.data.toFixed(2)}%`
      },
    },
    grid: { left: '12%', right: '6%', top: 16, bottom: 32 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `${v.toFixed(1)}%` },
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, bottom: 4, height: 20 },
    ],
    series: [
      {
        type: 'line', data: returns, smooth: true, symbol: 'none',
        lineStyle: { color: '#059669', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(5, 150, 105, 0.15)' },
            { offset: 1, color: 'rgba(5, 150, 105, 0.02)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: '#94a3b8', type: 'dashed' },
          data: [{ yAxis: 0, label: { formatter: '0%', color: '#94a3b8' } }],
        },
      },
    ],
  }
  returnInstance.setOption(option)
  returnInstance.group = 'backtest-group'
}

function renderCapitalChart() {
  if (!capitalChartRef.value || bars.value.length === 0 || !summary.value) return
  if (capitalInstance) capitalInstance.dispose()
  capitalInstance = echarts.init(capitalChartRef.value)

  const dates = bars.value.map(b => b.date)
  const capitals = bars.value.map(b => b.capital || summary.value!.initial_capital)
  const initialCapital = summary.value.initial_capital

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params
        return `${p.axisValue}<br/>资金: ¥${p.data.toLocaleString()}`
      },
    },
    grid: { left: '12%', right: '6%', top: 16, bottom: 32 },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (v: number) => `¥${(v / 10000).toFixed(1)}万` },
      splitLine: { lineStyle: { type: 'dashed', color: '#e2e8f0' } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, bottom: 4, height: 20 },
    ],
    series: [
      {
        type: 'line', data: capitals, smooth: true, symbol: 'none',
        lineStyle: { color: '#3b82f6', width: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.12)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.02)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: '#94a3b8', type: 'dashed' },
          data: [{ yAxis: initialCapital, label: { formatter: `初始 ¥${(initialCapital / 10000).toFixed(1)}万`, color: '#94a3b8' } }],
        },
        markPoint: {
          data: [
            { type: 'max', name: '最高', symbol: 'pin', symbolSize: 24, itemStyle: { color: '#16a34a' } },
            { type: 'min', name: '最低', symbol: 'pin', symbolSize: 24, itemStyle: { color: '#dc2626' } },
          ],
        },
      },
    ],
  }
  capitalInstance.setOption(option)
  capitalInstance.group = 'backtest-group'

  // Connect dataZoom across all three charts
  echarts.connect('backtest-group')
}

function onResize() {
  klineInstance?.resize()
  returnInstance?.resize()
  capitalInstance?.resize()
}

import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})

watch(visible, v => {
  if (v) {
    window.addEventListener('resize', onResize)
  } else {
    window.removeEventListener('resize', onResize)
  }
})
</script>

<style scoped>
.bt-loading,
.bt-error {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 60px 20px;
  color: #64748b;
  font-size: 15px;
}

.bt-error {
  color: #dc2626;
}

.bt-summary-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.bt-card {
  flex: 1;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 20px;
  text-align: center;
}

.bt-card-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 6px;
}

.bt-card-value {
  font-size: 22px;
  font-weight: 700;
}

.text-green { color: #059669; }
.text-red { color: #dc2626; }
.text-orange { color: #d97706; }
.text-default { color: #0F172A; }

.bt-chart-section {
  margin-bottom: 16px;
}

.bt-chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 8px;
}

.bt-charts-row {
  display: flex;
  gap: 16px;
}

.bt-chart-half {
  flex: 1;
  min-width: 0;
}

.bt-chart {
  width: 100%;
  height: 280px;
}

.kline-chart {
  height: 380px;
}
</style>
