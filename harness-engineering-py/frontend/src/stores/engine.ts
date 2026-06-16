import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { EngineAvailability } from '@/types/chat'

export const useEngineStore = defineStore('engine', () => {
  const engineInfo = ref<EngineAvailability | null>(null)
  const loading = ref(false)

  async function fetchAvailability() {
    loading.value = true
    try {
      const res = await fetch('/api/engines/availability')
      const data = await res.json()
      engineInfo.value = (data.engines || [])[0] || null
    } catch (err) {
      console.error('[EngineStore] Failed to fetch engine availability:', err)
    } finally {
      loading.value = false
    }
  }

  return { engineInfo, loading, fetchAvailability }
})
