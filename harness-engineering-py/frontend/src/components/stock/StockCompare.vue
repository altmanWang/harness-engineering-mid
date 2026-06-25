<template>
  <div class="compare-container">
    <div
      v-for="(record, idx) in compareRecords"
      :key="record.id"
      class="compare-panel"
    >
      <div class="compare-title">{{ record.title }}</div>
      <el-table :data="buildCompareRows(record)" size="small" stripe>
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" width="100" />
        <el-table-column label="结论" width="80">
          <template #default="{ row }">
            <el-tag
              :type="conclusionTagType(row.conclusion)"
              size="small"
              :class="{ 'highlight-change': row.changed }"
            >
              {{ row.conclusion || '—' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="理由" min-width="150" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatSession } from '@/types/chat'

const props = defineProps<{
  compareRecords: ChatSession[]
}>()

interface CompareRow {
  code: string
  name: string
  conclusion: string | null
  reason: string
  changed: boolean
}

function buildCompareRows(record: ChatSession): CompareRow[] {
  const diag = record.diagnosis
  if (!diag) return []

  // Detect changed conclusions by comparing with the first record
  const baseDiag = props.compareRecords[0]?.diagnosis
  return diag.results.map(r => {
    let changed = false
    if (baseDiag && record.id !== props.compareRecords[0].id) {
      const baseResult = baseDiag.results.find(br => br.code === r.code)
      if (baseResult && baseResult.conclusion !== r.conclusion) {
        changed = true
      }
    }
    return {
      code: r.code,
      name: r.name,
      conclusion: r.conclusion,
      reason: r.reason,
      changed,
    }
  })
}

function conclusionTagType(c: string | null): 'success' | 'danger' | 'warning' | 'info' {
  if (c === '看多') return 'success'
  if (c === '看空') return 'danger'
  if (c === '观望') return 'warning'
  return 'info'
}
</script>

<style scoped>
.compare-container {
  display: flex;
  gap: 16px;
}
.compare-panel {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  overflow: hidden;
}
.compare-title {
  padding: 10px 16px;
  font-weight: 600;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-extra-light);
}
.highlight-change {
  box-shadow: 0 0 0 2px #e6a23c;
}
</style>
