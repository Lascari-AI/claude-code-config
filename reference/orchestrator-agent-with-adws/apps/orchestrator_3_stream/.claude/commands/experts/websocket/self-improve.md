---
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Self-improve WebSocket expertise by validating against codebase implementation
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

You maintain the WebSocket expert system's expertise accuracy by comparing the existing expertise file against the actual codebase implementation. It follows the `Workflow` section to detect and remedy any differences, missing pieces, or outdated information, ensuring the expertise file remains a powerful **mental model** and accurate memory reference for WebSocket-related tasks.

## Variables

CHECK_GIT_DIFF: $1 default to false if not specified
FOCUS_AREA: $2 default to empty string
EXPERTISE_FILE: .claude/commands/experts/websocket/expertise.yaml
MAX_LINES: 1000

## Instructions

- This is a self-improvement workflow to keep WebSocket expertise synchronized with the actual codebase
- Think of the expertise file as your **mental model** and memory reference for all WebSocket-related functionality
- Always validate expertise against real implementation, not assumptions
- Focus exclusively on WebSocket-related functionality throughout the codebase
- If FOCUS_AREA is provided, prioritize validation and updates for that specific area
- Maintain the YAML structure of the expertise file
- Enforce strict line limit of 1000 lines maximum
- Prioritize actionable, high-value expertise over verbose documentation
- When trimming, remove least critical information that won't impact expert performance
- Git diff checking is optional and controlled by the CHECK_GIT_DIFF variable
- Be thorough in validation but concise in documentation
- Don't include 'summaries' of work done in your expertise when a git diff is checked. Focus on true, important information that pertains to the key websocket functionality and implementation.
- Write as a principle engineer that writes CLEARLY and CONCISELY for future engineers so they can easily understand how to read and update functionality surrounding the websocket implementation.
- Keep in mind, after your thorough search, there may be nothing to be done - this is perfectly acceptable. If there's nothing to be done, report that and stop.

## Workflow

1. **Check Git Diff (Conditional)**
   - If CHECK_GIT_DIFF is "true", run `git diff` to identify recent changes to WebSocket-related files
   - If changes detected, note them for targeted validation in step 3
   - If CHECK_GIT_DIFF is "false", skip this step

2. **Read Current Expertise**
   - Read the entire EXPERTISE_FILE to understand current documented expertise
   - Identify key sections: overview, core_implementation, event_types, streaming_architecture, etc.
   - Note any areas that seem outdated or incomplete

3. **Validate Against Codebase**
   - Read the EXPERTISE_FILE to identify which files are documented as key implementation files
   - Read those files to understand current implementation
   - Use Grep to search for WebSocket event types, broadcast methods, and connection handling
   - Compare documented expertise against actual code:
     - Event types and their fields
     - Broadcast methods and their signatures
     - File locations and line numbers
     - Architecture patterns and data flows
     - Hook integration points
     - Frontend integration patterns
   - If FOCUS_AREA is provided, prioritize validation of that specific area
   - If git diff was checked in step 1, pay special attention to changed areas

4. **Identify Discrepancies**
   - List all differences found:
     - Missing events or methods in expertise file
     - Outdated line numbers or file paths
     - Changed method signatures or parameters
     - New features not documented
     - Removed features still documented
     - Incorrect architecture descriptions

5. **Update Expertise File**
   - Remedy all identified discrepancies by updating EXPERTISE_FILE
   - Add missing information
   - Update outdated information
   - Remove obsolete information
   - Maintain YAML structure and formatting
   - Ensure all file paths and line numbers are accurate
   - Keep descriptions concise and actionable

6. **Enforce Line Limit**
   - Run: `wc -l .claude/commands/experts/websocket/expertise.yaml`
   - Check if line count exceeds MAX_LINES (1000)
   - If line count > MAX_LINES:
     - Identify least important expertise sections that won't impact expert performance:
       - Overly verbose descriptions
       - Redundant examples
       - Low-priority edge cases
       - Excessive detail in less critical areas
     - Trim identified sections
     - Run line count check again
     - REPEAT this sub-workflow until line count ≤ MAX_LINES
   - Document what was trimmed in the report

7. **Validation Check**
   - Read the updated EXPERTISE_FILE
   - Verify all critical WebSocket information is present
   - Ensure line count is within limit
   - Validate YAML syntax by compiling the file:
     - Run: `python3 -c "import yaml; yaml.safe_load(open('EXPERTISE_FILE'))"`
     - Replace EXPERTISE_FILE with the actual path from the variable
     - Confirm no syntax errors are raised
     - If errors occur, fix the YAML structure and re-validate

## Report

Provide a structured report with the following sections:

### Summary
- Brief overview of self-improvement execution
- Whether git diff was checked
- Focus area (if any)
- Total discrepancies found and remedied
- Final line count vs MAX_LINES

### Discrepancies Found
- List each discrepancy identified:
  - What was incorrect/missing/outdated
  - Where in the codebase the correct information was found
  - How it was remedied

### Updates Made
- Concise list of all updates to EXPERTISE_FILE:
  - Added sections/information
  - Updated sections/information
  - Removed sections/information

### Line Limit Enforcement
- Initial line count
- Final line count
- If trimming was needed:
  - Number of trimming iterations
  - What was trimmed and why
  - Confirmation that trimming didn't impact critical expertise

### Validation Results
- Confirm all critical WebSocket expertise is present
- Confirm line count is within limit
- Note any areas that may need future attention

### Codebase References
- List of files validated against with line numbers where relevant
- Key methods and functions verified

**Example Report Format:**

```
✅ Self-Improvement Complete

Summary:
- Git diff checked: Yes
- Focus area: agent logs
- Discrepancies found: 8
- Discrepancies remedied: 8
- Final line count: 847/1000 lines

Discrepancies Found:
1. Missing event: 'agent_summary_update' not documented
   - Found in: websocket_manager.py:159
   - Remedied: Added to event_types.agent_activity section

2. Outdated line numbers: websocket_manager.py lifecycle methods
   - Found: Methods shifted due to new code
   - Remedied: Updated all line number references

Updates Made:
- Added: agent_summary_update event type
- Updated: websocket_manager.py line numbers (8 references)
- Updated: thinking_block event structure (added persistence field)
- Removed: Obsolete heartbeat_scheduled reference

Line Limit Enforcement:
- Initial: 1048 lines
- Required trimming: Yes
- Trimming iterations: 2
- Trimmed: Verbose examples in testing section, redundant error handling descriptions
- Final: 847 lines ✓

Validation Results:
✓ All 17 event types documented with accurate fields
✓ Core WebSocketManager methods present
✓ Hook integration patterns documented
✓ Frontend patterns included
✓ Line count within limit (847/1000)
✓ YAML syntax valid (compiled successfully)

Codebase References:
- websocket_manager.py:1-261 (validated)
- orchestrator_service.py:435-930 (validated)
- command_agent_hooks.py (validated)
- main.py:590-624 (validated)
- chatService.ts:74-169 (validated)
```