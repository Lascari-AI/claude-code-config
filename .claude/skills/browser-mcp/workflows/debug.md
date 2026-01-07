---
covers: Collaborative front-end debugging using Browser MCP
type: workflow
concepts: [debugging, browser-mcp, console-logs, instrumentation, multi-turn]
---

# Front-End Debugging Workflow

A collaborative debugging workflow where the agent handles mechanical tedium while the user stays in loop for judgment calls.

## Overview

This workflow enables systematic front-end debugging by:
1. **Observing** - Capturing console logs and screenshots without manual copy/paste
2. **Instrumenting** - Strategically adding `[DEBUG-AGENT]` markers for deeper visibility
3. **Iterating** - Refreshing and re-capturing until root cause is identified
4. **Fixing** - Implementing the fix with user approval
5. **Cleaning** - Removing all temporary instrumentation

**Key principle**: Agent handles the mechanical back-and-forth (screenshots, log capture, instrumentation, refreshes). User confirms key decisions (is this the right page? should I apply this fix?).

## Workflow

```xml
<workflow id="frontend-debugging">
    <global_constraints>
        - This is a collaborative workflow — user stays in loop for judgment calls
        - Agent handles mechanical tedium: screenshots, log capture, instrumentation, refreshes
        - Use AskUserQuestion for confirmations, not implicit assumptions
        - Track all instrumentation added for cleanup phase
    </global_constraints>

    <phase id="0" name="Setup">
        <action>
            - Call `browser_snapshot` to see current URL and page state
        </action>
        <action>
            - Present to user: "I see you're on [URL]. Is this where the issue is?"
        </action>
        <action>
            - Wait for user confirmation. If user provides different URL, use `browser_navigate`
        </action>
    </phase>

    <phase id="1" name="Observe">
        <action>
            - Call `browser_screenshot` to capture current visual state
        </action>
        <action>
            - Call `browser_get_console_logs` to get existing console output
        </action>
        <action>
            - Present findings to user: what you see visually, any errors/warnings in logs
        </action>
    </phase>

    <phase id="2" name="Analyze">
        <action>
            - Examine captured state: visual anomalies, console errors, missing elements
        </action>
        <action>
            - Determine: Is there enough information to identify root cause?
            - If yes → proceed to Propose phase
            - If no → proceed to Instrument phase
        </action>
    </phase>

    <phase id="3" name="Instrument">
        <action>
            - Identify strategic points in source code needing visibility
        </action>
        <action>
            - Add console.log statements using [DEBUG-AGENT] convention:
              `console.log('[DEBUG-AGENT]', '[Context.location]', { data })`
        </action>
        <action>
            - Track all files and line numbers modified for cleanup
        </action>
    </phase>

    <phase id="4" name="Refresh">
        <action>
            - Call `browser_navigate` to the same URL (full page refresh)
            - This clears console logs and ensures fresh page state
        </action>
    </phase>

    <phase id="5" name="Iterate">
        <action>
            - Return to Observe phase (capture new screenshot + logs)
        </action>
        <action>
            - Return to Analyze phase (examine new data)
        </action>
        <action>
            - Repeat until root cause is identified
        </action>
    </phase>

    <phase id="6" name="Propose">
        <action>
            - Explain the identified root cause to user
        </action>
        <action>
            - Propose specific fix
        </action>
        <action>
            - Wait for user approval: "Should I apply this fix?"
        </action>
    </phase>

    <phase id="7" name="Fix_and_Cleanup">
        <action>
            - Implement the approved fix
        </action>
        <action>
            - Call `browser_navigate` to refresh and verify fix works
        </action>
        <action>
            - Ask user: "Does this look like it's working properly?"
        </action>
        <action>
            - Remove all [DEBUG-AGENT] markers from source code
            - Use grep to find: `grep -r "\[DEBUG-AGENT\]" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx"`
        </action>
        <action>
            - Verify codebase is clean (fix remains, instrumentation removed)
        </action>
    </phase>
</workflow>
```
