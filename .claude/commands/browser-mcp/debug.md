---
allowed-tools: Read, Edit, Write, Bash, browser_navigate, browser_go_back, browser_go_forward, browser_snapshot, browser_click, browser_hover, browser_type, browser_select_option, browser_press_key, browser_wait, browser_get_console_logs, browser_screenshot
description: Start collaborative front-end debugging workflow
arguments: "Description of the issue to debug"
---

issue = $ARGUMENTS

# Front-End Debugging

Read and execute the debugging workflow:

1. Read `.claude/skills/browser-mcp/SKILL.md` for context on Browser MCP tools and debug log convention
2. Read `.claude/skills/browser-mcp/workflows/debug.md` for the workflow phases
3. Execute the workflow, starting with Setup phase

**Issue provided by user**: {issue}

Follow the workflow phases in order. This is a collaborative workflow — confirm key decisions with the user.
