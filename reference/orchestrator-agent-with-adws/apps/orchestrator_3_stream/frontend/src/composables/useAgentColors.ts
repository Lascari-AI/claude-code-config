/**
 * Agent Color Generation Composable
 *
 * Generates consistent colors for agents based on their name and session_id.
 * Uses a hash function to ensure the same agent always gets the same color.
 */

import { computed, type ComputedRef, toValue, type MaybeRefOrGetter } from 'vue'

export interface AgentColorOptions {
  agentName?: MaybeRefOrGetter<string | undefined>
  agentId: MaybeRefOrGetter<string>
  sessionId?: MaybeRefOrGetter<string | null | undefined>
}

export interface AgentColors {
  borderColor: ComputedRef<string>
  backgroundColor: ComputedRef<string>
}

/**
 * Generate consistent colors for an agent
 *
 * @param options - Agent identification options (can be reactive)
 * @returns Object with reactive border and background colors
 */
export function useAgentColors(options: AgentColorOptions): AgentColors {
  // Generate identifier from agent name/id + session_id
  const identifier = computed(() => {
    const base = toValue(options.agentName) || toValue(options.agentId)
    const session = toValue(options.sessionId) || ''
    return `${base}_${session}`
  })

  // Generate solid color for border (100% opacity)
  const borderColor = computed(() => {
    return stringToColor(identifier.value, 1)
  })

  // Generate transparent color for background (8% opacity)
  const backgroundColor = computed(() => {
    return stringToColor(identifier.value, 0.08)
  })

  return {
    borderColor,
    backgroundColor,
  }
}

/**
 * Convert string to consistent HSL-based RGB color
 *
 * @param str - Input string to hash
 * @param alpha - Opacity (0-1)
 * @returns RGBA color string
 */
function stringToColor(str: string, alpha: number = 1): string {
  // Generate consistent hash from string
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
    hash = hash & hash // Convert to 32-bit integer
  }

  // Generate RGB values with good saturation and lightness for dark theme
  const h = Math.abs(hash % 360) // Hue: 0-360
  const s = 65 + (Math.abs(hash >> 8) % 20) // Saturation: 65-85%
  const l = 55 + (Math.abs(hash >> 16) % 15) // Lightness: 55-70%

  // Convert HSL to RGB
  const [r, g, b] = hslToRgb(h, s, l)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

/**
 * Convert HSL color to RGB
 *
 * @param h - Hue (0-360)
 * @param s - Saturation (0-100)
 * @param l - Lightness (0-100)
 * @returns RGB tuple [r, g, b] (0-255)
 */
function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  s /= 100
  l /= 100
  const k = (n: number) => (n + h / 30) % 12
  const a = s * Math.min(l, 1 - l)
  const f = (n: number) =>
    l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)))
  return [
    Math.round(255 * f(0)),
    Math.round(255 * f(8)),
    Math.round(255 * f(4)),
  ]
}
