/**
 * Header Bar Composable
 *
 * Manages state and computed properties for the application header bar.
 * Provides easy access to stats like active agents, running agents, logs, total cost, and CWD.
 */

import { computed, ref, onMounted } from 'vue'
import { useOrchestratorStore } from '../stores/orchestratorStore'
import type { AppStats } from '../types'

/**
 * Composable for header bar state management
 *
 * @returns {Object} Header bar state and computed properties
 */
export function useHeaderBar() {
  const store = useOrchestratorStore()
  const cwdValue = ref<string>('/test/hardcoded/path')

  /**
   * Fetch current working directory from backend
   */
  const fetchCwd = async () => {
    try {
      const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9403'
      const response = await fetch(`${backendUrl}/get_headers`)
      const data = await response.json()
      console.log('CWD API Response:', data, 'Type:', typeof data.cwd, 'Value:', data.cwd)
      if (data.status === 'success' && typeof data.cwd === 'string') {
        cwdValue.value = String(data.cwd)  // Explicitly cast to string
        console.log('CWD Set to:', cwdValue.value, 'Type:', typeof cwdValue.value)
      } else {
        console.warn('Invalid CWD response:', data)
        cwdValue.value = '/error/invalid/response'
      }
    } catch (error) {
      console.error('Failed to fetch CWD:', error)
      cwdValue.value = '/error/fetch/failed'
    }
  }

  /**
   * Load CWD on mount
   */
  onMounted(() => {
    fetchCwd()
  })

  /**
   * Current working directory - returns string directly
   */
  const cwd = computed<string>(() => {
    const val = cwdValue.value
    console.log('CWD computed called, returning:', val, 'Type:', typeof val)
    return String(val)  // Explicitly return as string
  })

  /**
   * Orchestrator agent cost (the main orchestrator's own cost)
   */
  const orchestratorCost = computed(() => {
    return store.orchestratorAgent?.total_cost ?? 0
  })

  /**
   * Total cost across all subagents only
   * Sums the total_cost field from all agents (excludes orchestrator)
   */
  const totalAgentCost = computed(() => {
    return store.agents.reduce((sum, agent) => sum + agent.total_cost, 0)
  })

  /**
   * Combined total cost (orchestrator + all agents)
   */
  const totalCombinedCost = computed(() => {
    return orchestratorCost.value + totalAgentCost.value
  })

  /**
   * Number of active agents (not archived and not complete)
   */
  const activeAgentCount = computed(() => {
    return store.activeAgents.length
  })

  /**
   * Number of currently running/executing agents
   */
  const runningAgentCount = computed(() => {
    return store.runningAgents.length
  })

  /**
   * Total number of log entries in the event stream
   */
  const logCount = computed(() => {
    return store.eventStreamEntries.length
  })

  /**
   * Total number of WebSocket events received in current session
   * Counts ALL WebSocket messages, not just event stream entries
   */
  const websocketEventCount = computed(() => {
    return store.websocketEventCount
  })

  /**
   * Complete stats object for the header
   * Aggregates all header statistics in one place
   */
  const headerStats = computed<AppStats>(() => ({
    active: activeAgentCount.value,
    running: runningAgentCount.value,
    logs: logCount.value,
    cost: totalCombinedCost.value
  }))

  /**
   * Formatted total combined cost string with 2 decimal places
   */
  const formattedCost = computed(() => {
    return totalCombinedCost.value.toFixed(2)
  })

  /**
   * Formatted orchestrator cost with 2 decimal places
   */
  const formattedOrchestratorCost = computed(() => {
    return orchestratorCost.value.toFixed(2)
  })

  /**
   * Formatted total agent cost with 2 decimal places
   */
  const formattedAgentsCost = computed(() => {
    return totalAgentCost.value.toFixed(2)
  })

  /**
   * Detailed cost breakdown including orchestrator and all agents
   * Returns object with orchestrator cost and array of agent costs
   */
  const costBreakdown = computed(() => ({
    orchestrator: {
      cost: orchestratorCost.value,
      formatted: formattedOrchestratorCost.value
    },
    agents: store.agents.map(agent => ({
      id: agent.id,
      name: agent.name,
      cost: agent.total_cost,
      formatted: agent.total_cost.toFixed(3)
    })),
    total: {
      agents: totalAgentCost.value,
      orchestrator: orchestratorCost.value,
      combined: totalCombinedCost.value,
      formattedAgents: formattedAgentsCost.value,
      formattedOrchestrator: formattedOrchestratorCost.value,
      formattedCombined: formattedCost.value
    }
  }))

  /**
   * Individual agent costs for detailed breakdown (kept for backward compatibility)
   * Returns array of {id, name, cost} objects
   */
  const agentCostBreakdown = computed(() => {
    return store.agents.map(agent => ({
      id: agent.id,
      name: agent.name,
      cost: agent.total_cost
    }))
  })

  /**
   * Clear all event stream entries
   */
  const clearEventStream = () => {
    store.clearEventStream()
  }

  /**
   * Export event stream to JSON file
   */
  const exportEventStream = () => {
    store.exportEventStream()
  }

  return {
    // Raw computed values
    orchestratorCost,
    totalAgentCost,
    totalCombinedCost,
    activeAgentCount,
    runningAgentCount,
    logCount,
    websocketEventCount,

    // Formatted values
    formattedCost,
    formattedOrchestratorCost,
    formattedAgentsCost,

    // Complete stats
    headerStats,

    // Detailed breakdown
    costBreakdown,
    agentCostBreakdown,

    // Header info
    cwd,

    // Actions
    clearEventStream,
    exportEventStream,

    // Direct store access if needed
    store
  }
}
