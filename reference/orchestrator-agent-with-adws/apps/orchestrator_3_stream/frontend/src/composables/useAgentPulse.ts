/**
 * Agent Pulse Composable (Optimized for High Frequency Events)
 *
 * Manages pulsing animations with aggressive debouncing for production use.
 * Optimized for handling hundreds/thousands of simultaneous pulses with
 * minimal CPU/memory overhead and GPU-accelerated animations.
 *
 * Performance optimizations:
 * - Uses Set for O(1) lookups instead of Map
 * - Uses plain object for timer storage (faster than Map)
 * - Aggressive debouncing prevents animation thrashing
 * - Single ref update batches reactivity
 * - No computed properties that recalculate on every change
 */

import { ref } from 'vue'

// High-performance storage: plain object for timers (faster than Map)
const pulseTimers: Record<string, NodeJS.Timeout> = {}

// Track pulsing agents using Set for O(1) lookups
const isPulsing = ref<Set<string>>(new Set())

// Configuration - optimized for production
const PULSE_DURATION_MS = 335    // Snappy animation (33% faster - 500ms → 335ms)
const DEBOUNCE_MS = 400           // Aggressive debounce for high-frequency events
const TOTAL_DURATION_MS = PULSE_DURATION_MS + DEBOUNCE_MS

/**
 * Track which agents are currently pulsing
 * PERFORMANCE: Optimized for high-frequency events
 */
export function useAgentPulse() {
  /**
   * Trigger a pulse for an agent with aggressive debouncing
   *
   * CRITICAL: This function is called potentially thousands of times per second.
   * Optimized for minimal overhead:
   * - Early return if already pulsing (prevents Map operations)
   * - Reuses existing timer when possible
   * - Batch updates to reduce Vue reactivity overhead
   *
   * @param agentId - The agent to pulse
   */
  function triggerPulse(agentId: string): void {
    // Fast path: check if already pulsing (Set lookup is O(1))
    if (isPulsing.value.has(agentId)) {
      return  // Already animating, skip to prevent CPU waste
    }

    // Clear any existing timer for this agent (cleanup)
    if (agentId in pulseTimers) {
      clearTimeout(pulseTimers[agentId])
    }

    // Add to pulsing set - trigger reactivity once
    const newSet = new Set(isPulsing.value)
    newSet.add(agentId)
    isPulsing.value = newSet

    // Schedule cleanup after animation + debounce
    pulseTimers[agentId] = setTimeout(() => {
      const newSet = new Set(isPulsing.value)
      newSet.delete(agentId)
      isPulsing.value = newSet
      delete pulseTimers[agentId]
    }, TOTAL_DURATION_MS)
  }

  /**
   * Check if an agent is currently pulsing
   * PERFORMANCE: O(1) lookup using Set
   */
  function isAgentPulsing(agentId: string): boolean {
    return isPulsing.value.has(agentId)
  }

  /**
   * Get CSS class for an agent
   * PERFORMANCE: Minimal string allocation
   */
  function getAgentPulseClass(agentId: string): string {
    return isPulsing.value.has(agentId) ? 'agent-pulsing' : ''
  }

  /**
   * Clear all pulse states and cleanup timers
   * CRITICAL: Call on disconnect to prevent memory leaks
   */
  function clearAllPulses(): void {
    // Clear all pending timers
    Object.values(pulseTimers).forEach(timer => clearTimeout(timer))

    // Clear timer storage
    for (const key in pulseTimers) {
      delete pulseTimers[key]
    }

    // Reset pulse states
    isPulsing.value = new Set()
  }

  /**
   * Get list of currently pulsing agents
   * PERFORMANCE: Returns the Set directly for fast iteration
   */
  function getPulsingAgents(): Set<string> {
    return isPulsing.value
  }

  return {
    triggerPulse,
    isAgentPulsing,
    getAgentPulseClass,
    clearAllPulses,
    getPulsingAgents,
    isPulsing
  }
}
