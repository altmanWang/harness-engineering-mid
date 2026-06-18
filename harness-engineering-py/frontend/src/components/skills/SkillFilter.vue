<template>
  <div class="skill-filter">
    <el-input
      v-model="searchModel"
      placeholder="搜索 Skills..."
      :prefix-icon="Search"
      clearable
      @input="onSearchChange"
    />
    <div class="filter-tags">
      <el-tag
        :type="selectedTags.length === 0 ? 'primary' : 'info'"
        class="filter-tag"
        @click="$emit('update:selectedTags', [])"
      >
        全部
      </el-tag>
      <el-tag
        v-for="tag in FIXED_TAGS"
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

const FIXED_TAGS = ['代码开发', 'DSL', '悍马平台', '数据']

const props = defineProps<{
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

function onSearchChange(val: string | number) {
  emit('update:searchQuery', String(val))
}
</script>

<style scoped>
.skill-filter {
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
