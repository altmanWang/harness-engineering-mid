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

      <el-table-column label="结论" width="100">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result">
            <span
              :class="['conclusion-badge', row.result.conclusion === '买入' ? 'conclusion-buy' : 'conclusion-wait']"
            >
              <span class="conclusion-dot" />
              {{ row.result.conclusion || '—' }}
            </span>
          </template>
          <template v-else-if="row.status === 'analyzing'">
            <span class="status-badge status-analyzing">分析中</span>
          </template>
          <template v-else-if="row.status === 'pending'">
            <span class="status-badge status-pending">等待</span>
          </template>
          <template v-else>
            <span class="status-badge status-error">失败</span>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="收盘" width="85" align="right" sortable>
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.close !== null">
            {{ row.result.close.toFixed(2) }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="开盘" width="85" align="right">
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.open !== null">
            {{ row.result.open.toFixed(2) }}
          </template>
        </template>
      </el-table-column>

      <el-table-column label="涨跌" width="90" align="right" sortable>
        <template #default="{ row }">
          <template v-if="row.status === 'done' && row.result && row.result.pct_chg !== null">
            <span :class="(row.result.pct_chg ?? 0) >= 0 ? 'text-green' : 'text-red'">
              {{ (row.result.pct_chg ?? 0) >= 0 ? '+' : '' }}{{ (row.result.pct_chg ?? 0).toFixed(2) }}%
            </span>
          </template>
        </template>
      </el-table-column>

      <el-table-column label="EMA20" width="85" align="right" sortable>
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
        <span class="footer-dot dot-success" />
        成功 <strong>{{ successCount }}</strong>
      </span>
      <span class="footer-stat">
        <span class="footer-dot dot-error" />
        失败 <strong>{{ failedCount }}</strong>
      </span>
      <span class="footer-stat">
        <span class="footer-dot dot-pending" />
        等待 <strong>{{ pendingCount }}</strong>
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
import type { StockItem } from '@/composables/useStockAnalysis'
import KLineChart from '@/components/stock/KLineChart.vue'

const props = defineProps<{
  items: StockItem[]
  sessionId?: string
}>()

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
</script>

<style scoped>
.stock-table-wrap {
  background: var(--el-bg-color);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.code-font {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: #0F172A;
}

.text-muted { color: #94a3b8; }
.text-green { color: #059669; font-weight: 600; }
.text-red { color: #dc2626; font-weight: 600; }
.text-danger { color: #dc2626; }

/* 结论徽章 */
.conclusion-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.conclusion-buy {
  background: #ecfdf5;
  color: #059669;
}

.conclusion-wait {
  background: #fffbeb;
  color: #d97706;
}

.conclusion-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* 状态徽章 */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-analyzing {
  background: #eff6ff;
  color: #3b82f6;
}

.status-pending {
  background: #f1f5f9;
  color: #64748b;
}

.status-error {
  background: #fef2f2;
  color: #dc2626;
}

/* 表尾统计 */
.table-footer {
  display: flex;
  gap: 24px;
  padding: 12px 20px;
  border-top: 1px solid #f1f5f9;
  font-size: 13px;
  color: #64748b;
  background: #f8fafc;
}

.footer-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-stat strong {
  font-weight: 600;
  color: #334155;
}

.footer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-success { background: #059669; }
.dot-error { background: #dc2626; }
.dot-pending { background: #94a3b8; }
</style>
