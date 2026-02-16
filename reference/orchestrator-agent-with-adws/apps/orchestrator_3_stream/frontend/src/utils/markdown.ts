/**
 * Markdown Rendering Utility
 *
 * Provides secure markdown-to-HTML conversion with syntax highlighting.
 * Uses marked for markdown parsing, DOMPurify for XSS protection,
 * and highlight.js for code block syntax highlighting.
 */

import { marked } from 'marked'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'

// Configure marked for optimal rendering
marked.setOptions({
  // Enable syntax highlighting for code blocks
  highlight: function(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(code, { language: lang }).value
      } catch (err) {
        console.error('Syntax highlighting error:', err)
      }
    }
    // Auto-detect language if not specified
    return hljs.highlightAuto(code).value
  },

  // GitHub Flavored Markdown
  gfm: true,

  // Convert \n to <br> for better line breaks
  breaks: true,

  // Use pedantic mode for more strict markdown parsing
  pedantic: false,

  // Enable smartypants for better typography
  smartypants: true,
})

/**
 * Render markdown to sanitized HTML
 *
 * @param markdown - Raw markdown string
 * @returns Sanitized HTML string safe for v-html
 *
 * @example
 * ```typescript
 * const html = renderMarkdown('# Hello\n\nThis is **bold**')
 * // Returns: '<h1>Hello</h1><p>This is <strong>bold</strong></p>'
 * ```
 */
export function renderMarkdown(markdown: string): string {
  if (!markdown) return ''

  try {
    // Parse markdown to HTML
    const rawHtml = marked.parse(markdown, { async: false }) as string

    // Sanitize HTML to prevent XSS attacks
    const sanitizedHtml = DOMPurify.sanitize(rawHtml, {
      // Allow these additional tags
      ADD_TAGS: ['iframe'],

      // Allow these additional attributes
      ADD_ATTR: ['target', 'rel', 'class'],

      // Allow data attributes (for code blocks)
      ALLOW_DATA_ATTR: true,
    })

    return sanitizedHtml
  } catch (error) {
    console.error('Markdown rendering error:', error)
    // Fallback: return escaped text
    return DOMPurify.sanitize(markdown)
  }
}

/**
 * Render inline markdown (no block elements)
 * Useful for single-line markdown in constrained spaces
 *
 * @param markdown - Raw markdown string
 * @returns Sanitized HTML string with only inline elements
 */
export function renderInlineMarkdown(markdown: string): string {
  if (!markdown) return ''

  try {
    const rawHtml = marked.parseInline(markdown) as string
    return DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: ['strong', 'em', 'code', 'a', 'del', 'ins'],
      ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
    })
  } catch (error) {
    console.error('Inline markdown rendering error:', error)
    return DOMPurify.sanitize(markdown)
  }
}

/**
 * Check if a string contains markdown formatting
 * Useful for conditional rendering
 *
 * @param text - Text to check
 * @returns True if text appears to contain markdown
 */
export function hasMarkdown(text: string): boolean {
  if (!text) return false

  // Check for common markdown patterns
  const markdownPatterns = [
    /#{1,6}\s/,           // Headers
    /\*\*.*?\*\*/,        // Bold
    /\*.*?\*/,            // Italic
    /__.*?__/,            // Bold (alternative)
    /_.*?_/,              // Italic (alternative)
    /`.*?`/,              // Inline code
    /```[\s\S]*?```/,     // Code blocks
    /^\s*[-*+]\s/m,       // Unordered lists
    /^\s*\d+\.\s/m,       // Ordered lists
    /\[.*?\]\(.*?\)/,     // Links
    /!\[.*?\]\(.*?\)/,    // Images
  ]

  return markdownPatterns.some(pattern => pattern.test(text))
}
