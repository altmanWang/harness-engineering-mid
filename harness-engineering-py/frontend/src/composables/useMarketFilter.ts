import { ref, computed } from 'vue'
import type { MarketItem } from '@/types'

export function useMarketFilter(items: MarketItem[], tags: string[]) {
  const selectedTags = ref<string[]>([])
  const searchQuery = ref('')

  const filtered = computed(() => {
    let result = [...items]
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

  return { selectedTags, searchQuery, filtered }
}
