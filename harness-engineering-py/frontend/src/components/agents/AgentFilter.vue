<template>
  <div class="agent-filter">
    <el-input
      v-model="searchModel"
      placeholder="搜索 Agents..."
      :prefix-icon="Search"
      clearable
      @input="onSearchChange"
    />
    <div class="filter-tags">
      <el-tag
        :type="selectedTags.length === 0 ? 'primary' : 'info'"
        class="filter-tag"
        @click="onTagChange([])"
      >
        全部
      </el-tag>
      <el-tag
        v-for="tag in tags"
        :key="tag"
        :type="selectedTags.includes(tag) ? 'primary' : 'info'"
        class="filter-tag"
        @click="toggleTag(tag)"
      >
        {{ tag }}
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps<{
  tags: string[]
  selectedTags: string[]
  searchQuery: string
}>()

const emit = defineEmits<{
  'update:selectedTags': [tags: string[]]
  'update:searchQuery': [query: string]
}>()

const searchModel = ref(props.searchQuery)

watch(() => props.searchQuery, (val) => {
  searchModel.value = val
})

function toggleTag(tag: string) {
  const current = [...props.selectedTags]
  if (current.includes(tag)) {
    emit('update:selectedTags', current.filter(t => t !== tag))
  } else {
    emit('update:selectedTags', [...current, tag])
  }
}

function onTagChange(tags: string[]) {
  emit('update:selectedTags', tags)
}

function onSearchChange(val: string | number) {
  emit('update:searchQuery', String(val))
}
</script>

<style scoped>
.agent-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}
.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.filter-tag {
  cursor: pointer;
}
</style>
