/**
 * Autocomplete Composable
 *
 * Provides debounced autocomplete generation and keyboard shortcut handling
 */

import { ref, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { useOrchestratorStore } from '../stores/orchestratorStore'

export function useAutocomplete() {
  const store = useOrchestratorStore()
  const selectedPillIndex = ref<number | null>(null)

  /**
   * Debounced autocomplete generation (1 second delay)
   */
  const debouncedGenerate = useDebounceFn(async (input: string) => {
    if (!input.trim()) {
      store.clearAutocomplete()
      return
    }
    await store.generateAutocomplete(input)
  }, 1000)

  /**
   * Generate autocomplete suggestions with debouncing
   */
  function generateAutocomplete(input: string) {
    debouncedGenerate(input)
  }

  /**
   * Accept an autocomplete suggestion by index
   */
  function acceptAutocomplete(index: number) {
    const item = store.autocompleteItems[index]
    if (!item) return null
    return { completion: item.completion, reasoning: item.reasoning }
  }

  /**
   * Handle keyboard shortcuts for autocomplete
   * - Ctrl+1/2/3: Accept autocomplete at index 0/1/2
   * - Escape: Clear autocomplete
   */
  function handleAutocompleteKeydown(event: KeyboardEvent) {
    if (!store.hasAutocompleteItems) return

    // Ctrl+1, Ctrl+2, Ctrl+3
    if (event.ctrlKey && event.key >= '1' && event.key <= '3') {
      event.preventDefault()
      const index = parseInt(event.key) - 1
      if (index < store.autocompleteItems.length) {
        const result = acceptAutocomplete(index)
        if (result) {
          // Dispatch custom event for OrchestratorChat to handle
          const customEvent = new CustomEvent('autocomplete-accept', {
            detail: { index, ...result }
          })
          event.target?.dispatchEvent(customEvent)
        }
      }
    }

    // Escape to clear
    if (event.key === 'Escape') {
      event.preventDefault()
      store.clearAutocomplete()
    }
  }

  return {
    autocompleteItems: computed(() => store.autocompleteItems),
    autocompleteLoading: computed(() => store.autocompleteLoading),
    autocompleteError: computed(() => store.autocompleteError),
    hasAutocompleteItems: computed(() => store.hasAutocompleteItems),
    selectedPillIndex,
    generateAutocomplete,
    acceptAutocomplete,
    clearAutocomplete: () => store.clearAutocomplete(),
    handleAutocompleteKeydown
  }
}
