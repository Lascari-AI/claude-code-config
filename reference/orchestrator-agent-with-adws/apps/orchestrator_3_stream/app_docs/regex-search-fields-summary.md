# Regex Search Fields Summary

## Overview

The Event Stream regex search functionality is implemented in the `useEventStreamFilter` composable and searches across multiple fields in event stream entries to provide comprehensive filtering capabilities.

**File Location:** `apps/orchestrator_3_stream/frontend/src/composables/useEventStreamFilter.ts`

**Lines:** 157-211 (search implementation logic)

---

## Search Mechanism

### Implementation Details

- **Type:** Regex-based search with fallback to simple string matching
- **Case Sensitivity:** Case-insensitive (flag: `'i'`)
- **Scope:** Applied to all filtered events in real-time
- **Error Handling:** Falls back to simple substring matching if regex compilation fails

### Search Process Flow

1. User enters search query in the search input field
2. Query is converted to lowercase for case-insensitive matching
3. Regex is compiled with case-insensitive flag: `new RegExp(query, 'i')`
4. For each event, regex is tested against all configured fields
5. Event matches if ANY field matches the pattern
6. If regex fails, fallback to simple string search across all fields

---

## Searchable Fields

### 1. **Core Content Fields** (Always Searched)
- **`event.content`** - Main event message/summary text
  - Description: Primary content of the event
  - Example: "Agent executed tool successfully"

- **`event.eventType`** - Event type identifier
  - Description: Type classification of the event
  - Example: "RESPONSE", "TOOL_USE", "THINKING", "HOOK"

### 2. **Agent Identification**
- **`event.agentName`** - Agent name/identifier
  - Description: Human-readable name of the agent
  - Example: "CodeAnalyzer", "DocumentWriter", "ProjectPlanner"

### 3. **Summary Field**
- **`event.metadata?.summary`** - Event summary
  - Description: Detailed summary of the event from metadata
  - Example: "Analyzed 45 files, found 3 issues"

### 4. **Task and Session Identifiers**
- **`event.metadata?.task_slug`** - Task slug identifier
  - Description: Unique identifier for the task
  - Example: "fix-auth-bug-2024", "add-feature-xyz"

- **`event.metadata?.session_id`** - Session identifier
  - Description: Session tracking ID
  - Example: "sess_abc123def456"

### 5. **ADW (Agentic Directed Workflow) Fields**
- **`event.metadata?.adw_id`** - ADW workflow identifier
  - Description: Workflow/orchestration ID
  - Example: "adw_workflow_123"

- **`event.metadata?.adw_step`** - ADW step identifier
  - Description: Current step within the workflow
  - Example: "analysis", "implementation", "review"

### 6. **File Paths** (Composite Field)
- **`event.metadata?.file_changes[].path`** - Changed file paths
  - Description: Paths to files modified/created/deleted
  - Example: "src/components/Button.tsx", "tests/auth.test.ts"

- **`event.metadata?.read_files[].path`** - Read file paths
  - Description: Paths to files read during execution
  - Example: "config/settings.json", "README.md"

**Note:** All file paths are combined and joined with spaces before regex matching

---

## Search Query Examples

### Basic Searches
- `auth` - Matches "authentication", "authorize", "auth_token", etc.
- `error` - Matches all events containing "error" (case-insensitive)
- `tool` - Matches tool-related events

### Regex Pattern Examples
- `^TOOL$` - Exact match for "TOOL" event type
- `file.*\.ts$` - File changes ending with `.ts` extension
- `agent.*execute` - Agent names followed by "execute"
- `session.*123` - Session IDs containing "123"
- `(error|warn|fail)` - Multiple condition match
- `\d+\s*tokens?` - Token count references
- `src/.*\.(js|ts)` - TypeScript/JavaScript file paths

### Complex Workflow Searches
- `adw_.*step.*analysis` - ADW workflow steps containing "analysis"
- `task_slug.*feature.*db` - Task slugs related to database features
- `agent.*CodeAnalyzer.*error` - Errors from specific agent

---

## Search Behavior Details

### What Gets Searched

| Category | Fields | Searchable |
|----------|--------|-----------|
| **Content** | `content`, `eventType` | ✅ Always |
| **Agent Info** | `agentName` | ✅ Always |
| **Metadata** | `summary`, `task_slug`, `session_id`, `adw_id`, `adw_step` | ✅ Always |
| **File Paths** | `file_changes[].path`, `read_files[].path` | ✅ Combined field |
| **Other Metadata** | Additional custom fields | ❌ Not searched |

### What Does NOT Get Searched

- `event.level` - Log level (DEBUG, INFO, WARNING, ERROR) - use quick filters instead
- `event.agentId` - Agent UUID - not human-searchable
- `event.id` - Event ID - not searchable
- `event.lineNumber` - Line number - not searchable
- `event.tokens` - Token count - searchable as part of content if included there
- Deeply nested metadata objects - only top-level paths

### Combined Field Processing

File paths from multiple sources are combined into a single searchable string:

```
[...file_changes.map(f => f.path), ...read_files.map(f => f.path)].join(' ')
```

This allows matching across multiple files with a single regex pattern.

---

## Search Input Field

**Component:** `FilterControls.vue`
**HTML Element:** `<input class="search-input" />`
**Placeholder Text:** `"Search agents, events, tasks, files (regex)"`
**Tooltip:** `"Search across: agent name, content, event type, summary, task ID, session ID, file paths"`

---

## Implementation Code Reference

### Search Implementation (useEventStreamFilter.ts, lines 157-211)

```typescript
// Regex search with fallback
if (searchQuery.value.trim()) {
  const query = searchQuery.value.toLowerCase()
  try {
    // Try as regex first
    const regex = new RegExp(query, 'i')
    filtered = filtered.filter(event => {
      // Core fields
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
```

---

## Related Filter Types

While not part of regex search, the following filter types work alongside search:

- **Quick Filters:** Log level filters (DEBUG, INFO, WARNING, ERROR, SUCCESS)
- **Category Filters:** Event category filters (RESPONSE, TOOL, THINKING, HOOK)
- **Agent Filters:** Filter by specific agent names
- **Tool Filters:** Filter by specific tool names (from `metadata.tool_name`)

---

## Performance Considerations

### Regex Compilation
- Regex is compiled once per search query update
- Case-insensitive flag reduces need for query normalization
- Fallback mechanism prevents page freezing on invalid regex

### Field Access Pattern
- Tests fields in order: content → eventType → agentName → summary → identifiers → paths
- Short-circuit logic: stops testing after first match
- File path arrays are joined into single string for efficiency

### Optimization Tips for Users
- Use anchors (`^`, `$`) for more specific matches
- Use character classes `[abc]` instead of alternatives `(a|b|c)` when possible
- Avoid complex lookaheads/lookbehinds if performance matters

---

## Type Definitions

**EventStreamEntry Interface** (`types.d.ts`):
```typescript
export interface EventStreamEntry {
  id: string
  lineNumber: number
  sourceType: EventSourceType
  level: LogLevel | 'SUCCESS'
  agentId?: string
  agentName?: string                    // Searchable
  content: string                       // Searchable
  tokens?: number
  timestamp: Date | string
  eventType?: string                    // Searchable
  eventCategory?: EventCategory
  metadata?: Record<string, any>        // Contains searchable fields
}
```

**Metadata Fields** (commonly included):
- `summary?: string` - Searchable
- `task_slug?: string` - Searchable
- `session_id?: string` - Searchable
- `adw_id?: string` - Searchable
- `adw_step?: string` - Searchable
- `file_changes?: FileChange[]` - Paths searchable
- `read_files?: FileRead[]` - Paths searchable
- Additional custom fields as needed

---

## Complete Field List (in search order)

| # | Field Path | Type | Searchable |
|---|-----------|------|-----------|
| 1 | `event.content` | string | ✅ |
| 2 | `event.eventType` | string | ✅ |
| 3 | `event.agentName` | string | ✅ |
| 4 | `event.metadata.summary` | string | ✅ |
| 5 | `event.metadata.task_slug` | string | ✅ |
| 6 | `event.metadata.session_id` | string | ✅ |
| 7 | `event.metadata.adw_id` | string | ✅ |
| 8 | `event.metadata.adw_step` | string | ✅ |
| 9 | `event.metadata.file_changes[].path` | string[] | ✅ (combined) |
| 10 | `event.metadata.read_files[].path` | string[] | ✅ (combined) |

---

## Notes & Future Enhancements

- **Current State:** 10 primary fields + composite file path field
- **Search Scope:** Event stream entries only (orchestrator_chat messages are included in metadata but not displayed in stream)
- **Regex Support:** Full JavaScript RegExp syntax supported
- **Fallback Mechanism:** Simple substring matching ensures robustness
- **Future Consideration:** Could extend to search nested metadata, tool parameters, or response content
