<template>
  <div class="stock-table-wrap">
    <el-table :data="items" stripe style="width: 100%" max-height="520" aria-label="诊股分析结果">
      <el-table-column prop="code" label="代码" width="110" sortable>
        <template #default="{ row }">
          <span class="code-font">{{ row.code }}</span>
        </template>
      </el-table-column>

      <el-table-column label="名称" width="110">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result">
            {{ row.result.name }}
          </template>
          <template v-else-if="row.status === 'analyzing'">
            <span class="text-muted">分析中...</span>
          </template>
          <template v-else-if="row.status === 'pending'">
            <span class="text-muted">等待中</span>
          </template>
          <template v-else>
            <span class="text-danger">—</span>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="结论" width="90">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result">
            <el-tag
              :type="conclusionTagType(row.result.conclusion)"
              size="small"
            >
              <el-icon style="margin-right: 2px; vertical-align: middle;">
                <CircleCheck v-if="row.result.conclusion === '买入'" />
                <Clock v-else />
              </el-icon>
              {{ row.result.conclusion || '—' }}
            </el-tag>
          </template>
          <template v-else-if="row.status === 'analyzing'">
            <el-tag type="info" size="small">分析中</el-tag>
          </template>
          <template v-else-if="row.status === 'pending'">
            <el-tag type="info" size="small">等待</el-tag>
          </template>
          <template v-else>
            <el-tag type="danger" size="small">失败</el-tag>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="收盘" width="80" align="right" sortable>
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.close !== null">
            {{ row.result.close.toFixed(2) }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="开盘" width="80" align="right">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.open !== null">
            {{ row.result.open.toFixed(2) }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="涨跌" width="80" align="right" sortable>
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.pct_chg !== null">
            <span :class="(row.result.pct_chg ?? 0) >= 0 ? 'text-green' : 'text-red'">
              {{ (row.result.pct_chg ?? 0) >= 0 ? '+' : '' }}{{ (row.result.pct_chg ?? 0).toFixed(2) }}%
            </span>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="EMA20" width="80" align="right" sortable>
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.ema20 !== null">
            {{ row.result.ema20.toFixed(2) }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="K线日期" width="110" align="center">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.klineDate">
            {{ row.result.klineDate }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="90" align="center" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'done' && row.result"
            type="primary"
            link
            size="small"
            @click="openKLine(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="table-footer">
      <span class="footer-stat">
        成功 <strong class="text-green">{{ successCount }}</strong>
      </span>
      <span class="footer-stat">
        失败 <strong class="text-red">{{ failedCount }}</strong>
      </span>
      <span class="footer-stat">
        等待 <strong class="text-muted">{{ pendingCount }}</strong>
      </span>
    </div>

    <KLineChart
      v-model="klineVisible"
      :code="klineCode"
      :stock-name="klineName"
      :session-id="sessionId || ''"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { CircleCheck, Clock } from '@element-plus/icons-vue'
import type { StockItem } from '@/composables/useStockAnalysis'
import KLineChart from '@/components/stock/KLineChart.vue'

const props = defineProps<{
  items: StockItem[]
  sessionId?: string
}>()

// K线图弹窗状态
const klineVisible = ref(false)
const klineCode = ref('')
const klineName = ref('')

function openKLine(row: StockItem) {
  if (!row.result) return
  klineCode.value = row.result.code
  klineName.value = row.result.name || row.result.code
  klineVisible.value = true
}

const successCount = computed(() => props.items.filter(i => i.status === 'done').length)
const failedCount = computed(() => props.items.filter(i => i.status === 'error').length)
const pendingCount = computed(() => props.items.filter(i => i.status !== 'done' && i.status !== 'error').length)

function conclusionTagType(conclusion: string | null): 'success' | 'danger' | 'warning' | 'info' {
  if (conclusion === '买入') return 'success'
  if (conclusion === '观望') return 'warning'
  return 'info'
}
</script>

<style scoped>
.stock-table-wrap {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;
}
.code-font {
  font-family: monospace;
  font-weight: 600;
}
.text-muted { color: var(--el-text-color-secondary); }
.text-green { color: var(--el-color-success); font-weight: 600; }
.text-red { color: var(--el-color-danger); font-weight: 600; }
.text-danger { color: var(--el-color-danger); }
.table-footer {
  display: flex;
  gap: 20px;
  padding: 10px 16px;
  border-top: 1px solid var(--el-border-color-extra-light);
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.footer-stat strong {
  margin-left: 4px;
}
</style>
