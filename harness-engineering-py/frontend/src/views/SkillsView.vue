<template>
  <div class="skills-page">
    <div class="page-header">
      <h2 class="page-title">Skills 管理</h2>
      <el-button type="primary" :icon="Upload" @click="uploadDialog?.open()">
        上传 Skill
      </el-button>
    </div>
    <SkillFilter
      v-model:selected-tags="selectedTags"
      v-model:search-query="searchQuery"
    />
    <div v-if="filtered.length > 0" class="skills-grid">
      <SkillCard
        v-for="skill in filtered"
        :key="skill.id"
        :skill="skill"
        @deleted="onDeleted"
      />
    </div>
    <el-empty v-else description="暂无 Skill，点击上方按钮上传" />

    <SkillUploadDialog ref="uploadDialog" @uploaded="loadSkills" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import SkillCard from '@/components/skills/SkillCard.vue'
import SkillFilter from '@/components/skills/SkillFilter.vue'
import SkillUploadDialog from '@/components/skills/SkillUploadDialog.vue'
import type { Skill } from '@/types'

const skills = ref<Skill[]>([])
const selectedTags = ref<string[]>([])
const searchQuery = ref('')
const uploadDialog = ref<InstanceType<typeof SkillUploadDialog>>()

const filtered = computed(() => {
  let result = [...skills.value]
  if (selectedTags.value.length > 0) {
    result = result.filter(item =>
      item.tags.some(tag => selectedTags.value.includes(tag))
    )
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(item =>
      item.name.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q)
    )
  }
  return result
})

async function loadSkills() {
  try {
    const res = await fetch('/api/skills')
    if (!res.ok) throw new Error('加载失败')
    const data = await res.json()
    skills.value = data.skills || []
  } catch {
    skills.value = []
  }
}

function onDeleted(id: string) {
  skills.value = skills.value.filter(s => s.id !== id)
}

onMounted(loadSkills)
</script>

<style scoped>
.skills-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
</style>
