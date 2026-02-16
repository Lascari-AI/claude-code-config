---
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Self-improve ADW expertise by validating against codebase implementation
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

You maintain the ADW expert system's expertise accuracy by comparing the existing expertise file against the actual codebase implementation. It follows the `Workflow` section to detect and remedy any differences, missing pieces, or outdated information, ensuring the expertise file remains a powerful **mental model** and accurate memory reference for ADW-related tasks.

## Variables

CHECK_GIT_DIFF: $1 default to false if not specified
FOCUS_AREA: $2 default to empty string
EXPERTISE_FILE: .claude/commands/experts/adw/expertise.yaml
MAX_LINES: 1000

## Instructions

- This is a self-improvement workflow to keep ADW expertise synchronized with the actual codebase
- Think of the expertise file as your **mental model** and memory reference for all ADW-related functionality
- Always validate expertise against real implementation, not assumptions
- Focus exclusively on ADW-related functionality: workflows, triggers, swimlane UI, WebSocket events, orchestrator tools
- If FOCUS_AREA is provided, prioritize validation and updates for that specific area
- Maintain the YAML structure of the expertise file
- Enforce strict line limit of 1000 lines maximum
- Prioritize actionable, high-value expertise over verbose documentation
- When trimming, remove least critical information that won't impact expert performance
- Git diff checking is optional and controlled by the CHECK_GIT_DIFF variable
- Be thorough in validation but concise in documentation
- Don't include 'summaries' of work done in your expertise when a git diff is checked. Focus on true, important information that pertains to the key ADW functionality and implementation.
- Write as a principal engineer that writes CLEARLY and CONCISELY for future engineers so they can easily understand how to read and update functionality surrounding the ADW implementation.
- Keep in mind, after your thorough search, there may be nothing to be done - this is perfectly acceptable. If there's nothing to be done, report that and stop.

## Workflow

1. **Check Git Diff (Conditional)**
   - If CHECK_GIT_DIFF is "true", run `git diff` to identify recent changes to ADW-related files
   - If changes detected, note them for targeted validation in step 3
   - If CHECK_GIT_DIFF is "false", skip this step

2. **Read Current Expertise**
   - Read the entire EXPERTISE_FILE to understand current documented expertise
   - Identify key sections: overview, workflow_types, core_implementation, orchestrator_integration, frontend_integration, etc.
   - Note any areas that seem outdated or incomplete

3. **Validate Against Codebase**
   - Read the EXPERTISE_FILE to identify which files are documented as key implementation files
   - Read those files to understand current implementation
   - Use Grep to search for ADW-related patterns:
     - Workflow step functions (run_plan_step, run_build_step, etc.)
     - WebSocket broadcast methods (broadcast_adw_*)
     - Database functions (create_adw, get_adw, update_adw_status)
     - Tool implementations (start_adw_tool, check_adw_tool)
   - Compare documented expertise against actual code:
     - Workflow types and their step counts
     - File locations and line numbers
     - Function signatures and parameters
     - WebSocket event types and fields
     - Frontend component structure
     - Database schema and functions
   - If FOCUS_AREA is provided, prioritize validation of that specific area
   - If git diff was checked in step 1, pay special attention to changed areas

4. **Identify Discrepancies**
   - List all differences found:
     - Missing workflows or steps in expertise file
     - Outdated line numbers or file paths
     - Changed function signatures or parameters
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
   - Run: `wc -l .claude/commands/experts/adw/expertise.yaml`
   - Check if line count exceeds MAX_LINES (1000)
   - If line count > MAX_LINES:
     - Identify least important expertise sections that won't impact expert performance:
       - Overly verbose descriptions
       - Redundant examples
       - Low-priority edge cases
       - Excessive detail in less critical areas
     - Trim identified sections
     - Run line count check again
     - REPEAT this sub-workflow until line count <= MAX_LINES
   - Document what was trimmed in the report

7. **Validation Check**
   - Read the updated EXPERTISE_FILE
   - Verify all critical ADW information is present
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
- Confirm all critical ADW expertise is present
- Confirm line count is within limit
- Note any areas that may need future attention

### Codebase References
- List of files validated against with line numbers where relevant
- Key methods and functions verified

**Example Report Format:**

```
Self-Improvement Complete

Summary:
- Git diff checked: Yes
- Focus area: workflows
- Discrepancies found: 5
- Discrepancies remedied: 5
- Final line count: 423/1000 lines

Discrepancies Found:
1. Missing workflow: 'plan_build_test' not documented
   - Found in: adws/adw_workflows/adw_plan_build_test.py
   - Remedied: Added to workflow_types section

2. Outdated line numbers: agent_manager.py start_adw function
   - Found: Function shifted due to new code
   - Remedied: Updated all line number references

Updates Made:
- Added: plan_build_test workflow type
- Updated: agent_manager.py line numbers (4 references)
- Updated: frontend types line numbers
- Removed: Obsolete workflow reference

Line Limit Enforcement:
- Initial: 423 lines
- Required trimming: No
- Final: 423 lines

Validation Results:
- All 4 workflow types documented with accurate files
- Core ADW functions present
- WebSocket event types documented
- Frontend integration patterns included
- Line count within limit (423/1000)
- YAML syntax valid (compiled successfully)

Codebase References:
- adws/adw_workflows/adw_plan_build.py (validated)
- adws/adw_modules/adw_logging.py (validated)
- apps/orchestrator_3_stream/backend/modules/agent_manager.py:638-742 (validated)
- apps/orchestrator_3_stream/frontend/src/components/AdwSwimlanes.vue (validated)
```
