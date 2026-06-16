<template>
  <div class="skills-page">
    <h2 class="page-title">Skills 市场</h2>
    <SkillFilter
      :tags="skillTags"
      v-model:selected-tags="selectedTags"
      v-model:search-query="searchQuery"
    />
    <div class="skills-grid">
      <SkillCard v-for="skill in filtered" :key="skill.id" :skill="skill" />
    </div>
    <el-empty v-if="filtered.length === 0" description="没有匹配的 Skills" />
  </div>
</template>

<script setup lang="ts">
import SkillCard from '@/components/skills/SkillCard.vue'
import SkillFilter from '@/components/skills/SkillFilter.vue'
import { useMarketFilter } from '@/composables/useMarketFilter'
import { skills, skillTags } from '@/mock/data'

const { selectedTags, searchQuery, filtered } = useMarketFilter(skills, skillTags)
</script>

<style scoped>
.skills-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px;
}
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
