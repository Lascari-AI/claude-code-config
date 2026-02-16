/**
 * Event Stream Filter Composable
 *
 * Manages all filter functionality for the event stream including:
 * - Main filter tabs (Combined Stream)
 * - Agent filters (by agent name)
 * - Category filters (Tool, Response, Thinking)
 * - Quick filters by log level (DEBUG, INFO, WARN, ERROR, SUCCESS)
 * - Search query with regex support (searches: content, event type, agent name, summary,
 *   task ID, session ID, ADW fields, file paths, and orchestrator chat messages)
 * - Auto-scroll/auto-follow functionality
 */

import { ref, computed } from 'vue'
import type { EventStreamEntry } from '../types'

export interface FilterTab {
  label: string
  value: string
}

export interface QuickFilter {
  label: string
  value: string
  class: string
}

export interface AgentFilter {
  label: string
  value: string
}

/**
 * Composable for event stream filtering and control
 *
 * @param events - Function that returns the events to filter
 * @returns {Object} Filter state, computed filtered events, and handler functions
 */
export function useEventStreamFilter(getEvents: () => EventStreamEntry[]) {
  // Filter state
  const currentFilter = ref<string>('all')
  const activeAgentFilters = ref<Set<string>>(new Set())
  const activeCategoryFilters = ref<Set<string>>(new Set())
  const activeToolFilters = ref<Set<string>>(new Set())
  const activeQuickFilters = ref<Set<string>>(new Set())
  const searchQuery = ref<string>('')
  const autoScroll = ref<boolean>(true)

  // Filter configuration
  const filterTabs: FilterTab[] = [
    { label: 'Combined Stream', value: 'all' }
  ]

  // Category filters (RESPONSE, TOOL, THINKING, HOOK)
  const categoryFilters: QuickFilter[] = [
    { label: 'RESPONSE', value: 'RESPONSE', class: 'qf-response' },
    { label: 'TOOL', value: 'TOOL', class: 'qf-tool' },
    { label: 'THINKING', value: 'THINKING', class: 'qf-thinking' },
    { label: 'HOOK', value: 'HOOK', class: 'qf-hook' }
  ]

  const quickFilters: QuickFilter[] = [
    { label: 'DBG', value: 'DEBUG', class: 'qf-debug' },
    { label: 'INF', value: 'INFO', class: 'qf-info' },
    { label: 'WARN', value: 'WARNING', class: 'qf-warn' },
    { label: 'ERR', value: 'ERROR', class: 'qf-error' },
    { label: 'OK', value: 'SUCCESS', class: 'qf-success' }
  ]

  // Get unique agent names from events
  const agentFilters = computed<AgentFilter[]>(() => {
    const events = getEvents()
    const uniqueAgents = new Set<string>()

    events.forEach(event => {
      if (event.agentName) {
        uniqueAgents.add(event.agentName)
      }
    })

    return Array.from(uniqueAgents)
      .sort()
      .map(name => ({ label: name, value: name }))
  })

  // Get unique tool names from tool_use events
  const toolFilters = computed<AgentFilter[]>(() => {
    const events = getEvents()
    const uniqueTools = new Set<string>()

    events.forEach(event => {
      const eventType = event.eventType?.toLowerCase()
      if (eventType === 'tool_use' || eventType === 'tooluseblock') {
        // Extract tool name from metadata or eventType
        const toolName = event.metadata?.tool_name
        if (toolName) {
          uniqueTools.add(toolName)
        }
      }
    })

    return Array.from(uniqueTools)
      .sort()
      .map(name => ({ label: name, value: name }))
  })

  /**
   * Filtered events based on all active filters and search query
   */
  const filteredEvents = computed(() => {
    let filtered = getEvents()

    // Apply agent filters
    if (activeAgentFilters.value.size > 0) {
      filtered = filtered.filter(event =>
        event.agentName && activeAgentFilters.value.has(event.agentName)
      )
    }

    // Apply category filters (TOOL, RESPONSE, THINKING, HOOK)
    if (activeCategoryFilters.value.size > 0) {
      filtered = filtered.filter(event => {
        const eventType = event.eventType?.toLowerCase()

        if (activeCategoryFilters.value.has('TOOL')) {
          if (eventType === 'tool_use' || eventType === 'tooluseblock') return true
        }
        if (activeCategoryFilters.value.has('RESPONSE')) {
          if (eventType === 'text' || eventType === 'textblock') return true
        }
        if (activeCategoryFilters.value.has('THINKING')) {
          if (eventType === 'thinking' || eventType === 'thinkingblock') return true
        }
        if (activeCategoryFilters.value.has('HOOK')) {
          if (event.eventCategory === 'hook') return true
        }

        return false
      })
    }

    // Apply tool filters (specific tools)
    if (activeToolFilters.value.size > 0) {
      filtered = filtered.filter(event => {
        const toolName = event.metadata?.tool_name
        return toolName && activeToolFilters.value.has(toolName)
      })
    }

    // Apply quick filters (by log level)
    if (activeQuickFilters.value.size > 0) {
      filtered = filtered.filter(event =>
        activeQuickFilters.value.has(event.level)
      )
    }

    // Apply search query (regex or simple string search) across all relevant fields
    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      try {
        // Try as regex first
        const regex = new RegExp(query, 'i')
        filtered = filtered.filter(event => {
          // Core fields - always searched
          if (regex.test(event.content)) return true
          if (regex.test(event.eventType || '')) return true

          // Agent identification
          if (event.agentName && regex.test(event.agentName)) return true

          // Summary field
          if (event.metadata?.summary && regex.test(event.metadata.summary)) return true

          // Task and session identifiers
          if (event.metadata?.task_slug && regex.test(event.metadata.task_slug)) return true
          if (event.metadata?.session_id && regex.test(event.metadata.session_id)) return true

          // ADW fields (workflow tracking)
          if (event.metadata?.adw_id && regex.test(event.metadata.adw_id)) return true
          if (event.metadata?.adw_step && regex.test(event.metadata.adw_step)) return true

          // File paths from metadata
          const filePaths = [
            ...(event.metadata?.file_changes?.map((f: any) => f.path) || []),
            ...(event.metadata?.read_files?.map((f: any) => f.path) || [])
          ].join(' ')
          if (filePaths && regex.test(filePaths)) return true

          return false
        })
      } catch {
        // Fall back to simple string search if regex fails
        filtered = filtered.filter(event => {
          const searchFields = [
            event.content.toLowerCase(),
            (event.eventType || '').toLowerCase(),
            (event.agentName || '').toLowerCase(),
            (event.metadata?.summary || '').toLowerCase(),
            (event.metadata?.task_slug || '').toLowerCase(),
            (event.metadata?.session_id || '').toLowerCase(),
            (event.metadata?.adw_id || '').toLowerCase(),
            (event.metadata?.adw_step || '').toLowerCase(),
            [
              ...(event.metadata?.file_changes?.map((f: any) => f.path) || []),
              ...(event.metadata?.read_files?.map((f: any) => f.path) || [])
            ].join(' ').toLowerCase()
          ].join(' ')

          return searchFields.includes(query)
        })
      }
    }

    return filtered
  })

  /**
   * Set the main filter tab
   */
  const setFilter = (filter: string) => {
    currentFilter.value = filter
  }

  /**
   * Check if a quick filter is active
   */
  const quickFilterActive = (value: string): boolean => {
    return activeQuickFilters.value.has(value)
  }

  /**
   * Check if an agent filter is active
   */
  const agentFilterActive = (value: string): boolean => {
    return activeAgentFilters.value.has(value)
  }

  /**
   * Check if a category filter is active
   */
  const categoryFilterActive = (value: string): boolean => {
    return activeCategoryFilters.value.has(value)
  }

  /**
   * Check if a tool filter is active
   */
  const toolFilterActive = (value: string): boolean => {
    return activeToolFilters.value.has(value)
  }

  /**
   * Toggle a quick filter on/off
   */
  const toggleQuickFilter = (value: string) => {
    if (activeQuickFilters.value.has(value)) {
      activeQuickFilters.value.delete(value)
    } else {
      activeQuickFilters.value.add(value)
    }
    // Force reactivity
    activeQuickFilters.value = new Set(activeQuickFilters.value)
  }

  /**
   * Toggle an agent filter on/off
   */
  const toggleAgentFilter = (value: string) => {
    if (activeAgentFilters.value.has(value)) {
      activeAgentFilters.value.delete(value)
    } else {
      activeAgentFilters.value.add(value)
    }
    // Force reactivity
    activeAgentFilters.value = new Set(activeAgentFilters.value)
  }

  /**
   * Toggle a category filter on/off
   */
  const toggleCategoryFilter = (value: string) => {
    if (activeCategoryFilters.value.has(value)) {
      activeCategoryFilters.value.delete(value)
    } else {
      activeCategoryFilters.value.add(value)
    }
    // Force reactivity
    activeCategoryFilters.value = new Set(activeCategoryFilters.value)
  }

  /**
   * Toggle a tool filter on/off
   */
  const toggleToolFilter = (value: string) => {
    if (activeToolFilters.value.has(value)) {
      activeToolFilters.value.delete(value)
    } else {
      activeToolFilters.value.add(value)
    }
    // Force reactivity
    activeToolFilters.value = new Set(activeToolFilters.value)
  }

  /**
   * Toggle auto-scroll on/off
   */
  const toggleAutoScroll = () => {
    autoScroll.value = !autoScroll.value
  }

  /**
   * Clear all active filters and search
   */
  const clearAllFilters = () => {
    currentFilter.value = 'all'
    activeAgentFilters.value.clear()
    activeCategoryFilters.value.clear()
    activeToolFilters.value.clear()
    activeQuickFilters.value.clear()
    searchQuery.value = ''
    // Force reactivity
    activeAgentFilters.value = new Set()
    activeCategoryFilters.value = new Set()
    activeToolFilters.value = new Set()
    activeQuickFilters.value = new Set()
  }

  return {
    // State
    currentFilter,
    activeAgentFilters,
    activeCategoryFilters,
    activeToolFilters,
    activeQuickFilters,
    searchQuery,
    autoScroll,

    // Configuration
    filterTabs,
    categoryFilters,
    quickFilters,
    agentFilters,
    toolFilters,

    // Computed
    filteredEvents,

    // Handlers
    setFilter,
    quickFilterActive,
    agentFilterActive,
    categoryFilterActive,
    toolFilterActive,
    toggleQuickFilter,
    toggleAgentFilter,
    toggleCategoryFilter,
    toggleToolFilter,
    toggleAutoScroll,
    clearAllFilters
  }
}
