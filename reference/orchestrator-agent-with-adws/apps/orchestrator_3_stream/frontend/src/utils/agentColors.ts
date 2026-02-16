/**
 * Agent Color Generation Utility
 *
 * Generates consistent colors for agents based on their name and session_id.
 * Uses a hash function to ensure the same agent always gets the same color.
 *
 * This is a pure utility function that can be used anywhere without Vue reactivity.
 */

/**
 * Generate consistent border color for an agent
 *
 * @param agentName - Agent name (preferred)
 * @param agentId - Agent ID (fallback if name not available)
 * @returns RGBA color string for border (100% opacity)
 */
export function getAgentBorderColor(
  agentName: string | undefined,
  agentId: string | undefined
): string {
  const identifier = agentName || agentId || 'unknown-agent'
  const color = stringToColor(identifier, 1)
  return color
}

/**
 * Generate consistent background color for an agent
 *
 * @param agentName - Agent name (preferred)
 * @param agentId - Agent ID (fallback if name not available)
 * @returns RGBA color string for background (8% opacity)
 */
export function getAgentBackgroundColor(
  agentName: string | undefined,
  agentId: string | undefined
): string {
  const identifier = agentName || agentId || 'unknown-agent'
  return stringToColor(identifier, 0.08)
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
