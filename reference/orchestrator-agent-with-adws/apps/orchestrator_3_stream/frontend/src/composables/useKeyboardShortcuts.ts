import { onMounted, onUnmounted } from 'vue'
import { useOrchestratorStore } from '../stores/orchestratorStore'

export function useKeyboardShortcuts() {
  const store = useOrchestratorStore()

  const handleKeyDown = (event: KeyboardEvent) => {
    // Check for cmd+k (Mac) or ctrl+k (Windows/Linux)
    const isModifierPressed = event.metaKey || event.ctrlKey

    if (isModifierPressed && event.key === 'k') {
      // Prevent default browser behavior (usually focuses search bar)
      event.preventDefault()
      store.toggleCommandInput()
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    // Expose nothing for now, but could add manual trigger functions if needed
  }
}