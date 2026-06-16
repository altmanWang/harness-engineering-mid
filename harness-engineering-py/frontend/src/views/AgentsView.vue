<template>
  <div class="agents-page">
    <h2 class="page-title">Agents 市场</h2>
    <AgentFilter
      :tags="agentTags"
      v-model:selected-tags="selectedTags"
      v-model:search-query="searchQuery"
    />
    <div class="agents-grid">
      <AgentCard v-for="agent in filtered" :key="agent.id" :agent="agent" />
    </div>
    <el-empty v-if="filtered.length === 0" description="没有匹配的 Agents" />
  </div>
</template>

<script setup lang="ts">
import AgentCard from '@/components/agents/AgentCard.vue'
import AgentFilter from '@/components/agents/AgentFilter.vue'
import { useMarketFilter } from '@/composables/useMarketFilter'
import { agents, agentTags } from '@/mock/data'

const { selectedTags, searchQuery, filtered } = useMarketFilter(agents, agentTags)
</script>

<style scoped>
.agents-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
}
.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
