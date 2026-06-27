<template>
  <el-dialog
    v-model="visible"
    :title="`${stockName} (${code}) K线图 — 近${data.length}天`"
    width="960px"
    top="5vh"
    destroy-on-close
    @opened="onOpened"
  >
    <div ref="chartRef" class="kline-chart"></div>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

export interface KLineRow {
  date: string
  open: number
  close: number
  high: number
  low: number
  volume: number
  ema20: number
}

const props = defineProps<{
  modelValue: boolean
  code: string
  stockName: string
  sessionId: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(props.modelValue)
watch(() => props.modelValue, v => { visible.value = v })
watch(visible, v => { emit('update:modelValue', v) })

const chartRef = ref<HTMLDivElement | null>(null)
const data = ref<KLineRow[]>([])
const loading = ref(false)
let chartInstance: echarts.ECharts | null = null

async function fetchKLine() {
  if (!props.sessionId || !props.code) return
  loading.value = true
  try {
    const res = await fetch(`/api/stock/kline/${props.sessionId}/${props.code}`)
    if (!res.ok) throw new Error('K线数据加载失败')
    const json = await res.json()
    data.value = json.data as KLineRow[]
    await nextTick()
    renderChart()
  } catch (err) {
    console.error('Failed to load K-line data:', err)
  } finally {
    loading.value = false
  }
}

function onOpened() {
  if (data.value.length === 0) {
    fetchKLine()
  } else {
    nextTick(() => renderChart())
  }
}

function renderChart() {
  if (!chartRef.value || data.value.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  const dates = data.value.map(d => d.date)
  const ohlc = data.value.map(d => [d.open, d.close, d.low, d.high])
  const volumes = data.value.map(d => d.volume)
  const ema20 = data.value.map(d => d.ema20)

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter(params: any) {
        const k = params.find((p: any) => p.seriesName === 'K线')
        const e = params.find((p: any) => p.seriesName === 'EMA20')
        const v = params.find((p: any) => p.seriesName === '成交量')
        if (!k) return ''
        const data = k.data
        return [
          `<strong>${k.axisValue}</strong>`,
          `开: ${data[1]}&nbsp;&nbsp;收: ${data[2]}`,
          `低: ${data[3]}&nbsp;&nbsp;高: ${data[4]}`,
          e ? `EMA20: ${e.data}` : '',
          v ? `成交量: ${(v.data / 10000).toFixed(0)}万手` : '',
        ].filter(Boolean).join('<br/>')
      },
    },
    axisPointer: {
      link: [{ xAxisIndex: 'all' }],
    },
    grid: [
      { left: '8%', right: '4%', top: 20, height: '60%' },
      { left: '8%', right: '4%', top: '78%', height: '14%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLine: { onZero: false },
        axisLabel: { show: true, rotate: 0 },
        gridIndex: 0,
      },
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLabel: { show: false },
        axisLine: { onZero: false },
        axisTick: { show: false },
        gridIndex: 1,
      },
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        position: 'left',
        gridIndex: 0,
        axisLabel: {
          formatter: (val: number) => val.toFixed(2),
        },
      },
      {
        type: 'value',
        scale: true,
        position: 'left',
        gridIndex: 1,
        axisLabel: {
          formatter: (val: number) => `${(val / 10000).toFixed(0)}万`,
        },
        splitNumber: 3,
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 0, end: 100, bottom: 4 },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a',
        },
      },
      {
        name: 'EMA20',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ema20,
        smooth: true,
        lineStyle: { color: '#7c4dff', width: 1.5 },
        symbol: 'none',
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((vol, i) => {
          const item = ohlc[i]
          const isUp = item[1] >= item[0]
          return {
            value: vol,
            itemStyle: { color: isUp ? '#ef5350' : '#26a69a' },
          }
        }),
      },
    ],
  }

  chartInstance.setOption(option)
  window.addEventListener('resize', () => chartInstance?.resize())
}
</script>

<style scoped>
.kline-chart {
  width: 100%;
  height: 520px;
}
</style>
