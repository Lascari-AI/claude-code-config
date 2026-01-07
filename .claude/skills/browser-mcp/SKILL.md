---
name: browser-mcp
description: Browser automation via MCP for debugging and design critique. Use when debugging front-end issues, performing design reviews, or any task requiring visual reference to user's browser.
---

# Purpose

Enable direct browser automation through MCP tools. Connect to the user's ACTUAL Chrome browser for debugging, design critique, and visual inspection tasks.

## Variables

SKILL_ROOT: .claude/skills/browser-mcp/

## Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to a URL |
| `browser_go_back` | Navigate back in history |
| `browser_go_forward` | Navigate forward in history |
| `browser_snapshot` | Get DOM/page state (text representation) |
| `browser_click` | Click on an element |
| `browser_hover` | Hover over an element |
| `browser_type` | Type text into an input |
| `browser_select_option` | Select dropdown option |
| `browser_press_key` | Send keyboard input |
| `browser_wait` | Wait for conditions |
| `browser_get_console_logs` | Get console output (key for debugging) |
| `browser_screenshot` | Capture visual state (key for debugging)

## Key Differentiator

Browser MCP connects to the user's ACTUAL Chrome browser:

- No separate browser instance (not Selenium/Puppeteer-style)
- No infrastructure setup needed
- Auth already handled — see exactly what the user sees
- Direct visual access to their current session

**When to use**:

- Front-end debugging (console logs, visual state)
- Design critique and visual inspection
- Any task requiring visual reference to user's browser

## Debug Log Convention

Agent-added instrumentation uses a structured format in a single `console.log()` call:

```javascript
console.log('[DEBUG-AGENT]', '[ComponentName.functionName]', { relevantData });
```

**Format breakdown:**
- `[DEBUG-AGENT]` — Marker for cleanup (grep-able, distinctive)
- `[Context]` — Where in the code/flow this log lives
- `{data}` — Values to inspect (expandable in browser devtools)

**Why single-call:** Browser console groups arguments from one `console.log()` as a single expandable entry.

**Cleanup strategy:**
1. Primary: Find all lines with `[DEBUG-AGENT]` marker and remove
2. Fallback: Git diff to see what was added

**Common log placement patterns** (agent decides contextually):
- Component boundaries (props in, render out)
- Before/after async operations (fetches, timers)
- Data transformation points
- Event handlers and callbacks
- State updates

## Cookbook

### Front-End Debugging

- IF: Debugging front-end issues, investigating UI bugs, or tracing JavaScript errors
- THEN: Read and execute: `workflows/debug.md`
- EXAMPLES:
  - "Help me debug this React component"
  - "Why isn't this button click working?"
  - "There's a console error I need to investigate"
  - "The page state isn't updating correctly"

### Design Critique

- IF: Reviewing UI/UX design, providing visual feedback, or analyzing design quality
- THEN: Read and execute: `workflows/critique.md`
- EXAMPLES:
  - "Critique this landing page design"
  - "What could be improved about this UI?"
  - "Review the visual design of my app"
  - "Give me feedback on this interface"

## Commands

| Command | Description |
|---------|-------------|
| `/browser-mcp:debug` | Start collaborative debugging workflow |
| `/browser-mcp:critique` | Start design critique workflow |
