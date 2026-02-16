# Plan: Agent File Tracking and Visualization System

## Visual Reference
**REQUIRED PREREADING**: Review `apps/orchestrator_3_stream/frontend/specs/images/heatmap-ui-mock.png` to understand the target UI layout and visual design for the file tracking heatmap.

## Task Description
Implement a comprehensive file tracking system that captures files modified by each agent during execution and displays this information visually in the agent's final response block. The system will track file changes through pre_tool_use hooks, store metadata in agent_logs payload, and render a visual heatmap showing modified files with diff summaries in the frontend UI.

## Objective
Enable users to see exactly what files each agent created, modified, or deleted during their execution, along with files that were read for context, displayed in a visual heatmap similar to the provided mockup. Each file change includes an AI-generated summary describing what was changed. This provides concrete visibility into agent work and helps track asset generation and context usage across multiple concurrent agents.

## Problem Statement
Currently, when agents execute tasks and modify or read files, there is no visual record of which files were changed, what the changes were, which files were read for context, or which agent performed these operations. This makes it difficult to:
- Audit agent work and verify changes
- Track file modifications when multiple agents run concurrently
- Understand which files the agent read to gather context
- Understand the scope of an agent's work at a glance
- Debug issues caused by file conflicts between agents
- Generate comprehensive reports of agent activity with natural language summaries

## UI Presentation: "Consumed" vs "Produced"

The file tracking UI will present two distinct sections to clearly separate files that were **read for context** vs files that were **created, modified, or deleted**:

### "Produced" Section (Green/Yellow/Red)
**What it shows**: Files the agent created, modified, or deleted (CUD operations)
- **Header**: "📝 Produced" with count badge (e.g., "5 files")
- **Visual theme**: Green (created), Yellow (modified), Red (deleted) status badges
- **Content per file**:
  - File path (relative, e.g., `src/components/Header.vue`)
  - Status badge with icon (✓ Created, ✎ Modified, ✗ Deleted)
  - Line change stats: `+234 -8`
  - **AI-generated summary** (prominent): "Added user authentication middleware with JWT validation"
  - Expandable diff viewer (syntax highlighted)
- **Layout**: Grid cards with full file information

### "Consumed" Section (Blue)
**What it shows**: Files the agent read to gather context (Read operations)
- **Header**: "📖 Consumed" with count badge (e.g., "12 files")
- **Visual theme**: Blue throughout (distinct from produced files)
- **Content per file**:
  - File path (relative, e.g., `config/database.js`)
  - Line count only: "1,234 lines"
  - No diffs (read-only, no changes to show)
- **Layout**: Compact grid cards (smaller than produced)

### Key UI Principles
1. **Visual Separation**: Clear distinction between the two sections with headers, colors, and spacing
2. **Information Density**: Produced files show more detail (summaries, diffs), consumed files are compact (just paths and line counts)
3. **Clickable**: Both sections allow clicking file cards to open in IDE
4. **Collapsible**: Produced files can expand to show full diffs, consumed files have no expansion (nothing to expand)

## Type Definitions

### Backend (Pydantic)
```python
from pydantic import BaseModel
from typing import Optional, List

class FileChange(BaseModel):
    path: str
    absolute_path: str
    status: str  # 'created' | 'modified' | 'deleted'
    lines_added: int
    lines_removed: int
    diff: Optional[str] = None
    summary: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

class FileRead(BaseModel):
    path: str
    absolute_path: str
    line_count: int
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None

class AgentLogMetadata(BaseModel):
    """Metadata structure stored in agent_log.payload"""
    file_changes: Optional[List[FileChange]] = None
    read_files: Optional[List[FileRead]] = None
    total_files_modified: Optional[int] = None
    total_files_read: Optional[int] = None
    generated_at: Optional[str] = None
```

### Frontend (TypeScript)
```typescript
export interface FileChange {
  path: string
  absolute_path: string
  status: 'created' | 'modified' | 'deleted'
  lines_added: number
  lines_removed: number
  diff?: string
  summary?: string
  agent_id?: string
  agent_name?: string
}

export interface FileRead {
  path: string
  absolute_path: string
  line_count: number
  agent_id?: string
  agent_name?: string
}

export interface AgentLogMetadata {
  // Metadata structure stored in agent_log.payload
  file_changes?: FileChange[]
  read_files?: FileRead[]
  total_files_modified?: number
  total_files_read?: number
  generated_at?: string
}
```

## Solution Approach
Implement a five-layer solution:

1. **Backend File Tracking Layer**: Create a dedicated `create_post_tool_file_tracking_hook()` to detect file-modifying tools (Write, Edit, MultiEdit) and file-reading tools (Read), extract file paths from tool_input, generate git diffs for modified files, generate AI summaries for each change, and track line counts for read files. **Store both relative and absolute file paths** to enable IDE integration.

2. **Per-Agent File Registry**: Create an in-memory file tracking registry that maintains separate lists of modified and read files per agent_id, ensuring file operations don't mix between concurrent agents. This registry will be populated during pre/post_tool_use hooks and persisted in the final response metadata.

3. **AI Summarization Layer**: For each file modification, generate a concise AI summary describing what was changed using an LLM API call. This provides natural language context without requiring users to read full diffs.

4. **Frontend Visualization Layer**: Create a new `FileChangesDisplay.vue` component that renders two distinct sections:
   - **Modified Files** (green/yellow/red heatmap) with status badges, line stats, AI summaries, and expandable diffs
   - **Read Files** (blue section) with file paths, line counts, and context indicators

5. **IDE Integration Layer**: Add click handlers to file cards that send requests to a backend endpoint to open files in the user's configured IDE (VS Code, Cursor, etc.). Store absolute file paths in metadata to enable direct file opening at specific line numbers.

## Relevant Files
Use these files to complete the task:

**Backend - File Tracking:**
- `apps/orchestrator_3_stream/backend/modules/command_agent_hooks.py` - Create new `create_post_tool_file_tracking_hook()` for file tracking (both modified and read files)
- `apps/orchestrator_3_stream/backend/modules/agent_manager.py` - Track file changes per agent during execution
- `apps/orchestrator_db/models.py` - Verify AgentLog payload structure (no changes needed)
- `apps/orchestrator_3_stream/backend/main.py` - Add `/api/open-file` endpoint for IDE integration
- `apps/orchestrator_3_stream/backend/modules/config.py` - Add IDE configuration and LLM API key for summarization
- `apps/orchestrator_3_stream/backend/modules/single_agent_prompt.py` - Use existing LLM utilities for generating file change summaries

**Backend - Git Utilities (New):**
- `apps/orchestrator_db/git_utils.py` - NEW: Create git diff generation utilities
- `apps/orchestrator_3_stream/backend/modules/file_tracker.py` - NEW: Create file tracking utilities

**Frontend - Type Definitions:**
- `apps/orchestrator_3_stream/frontend/src/types.d.ts` - Add FileChange interface and extend AgentLog payload types

**Frontend - Components:**
- `apps/orchestrator_3_stream/frontend/src/components/event-rows/AgentLogRow.vue` - Integrate file changes display
- `apps/orchestrator_3_stream/frontend/src/components/event-rows/FileChangesDisplay.vue` - NEW: Visual heatmap component
- `apps/orchestrator_3_stream/frontend/src/components/EventStream.vue` - Verify event routing (likely no changes)

**Frontend - Store:**
- `apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts` - Verify event handling (likely no changes)

**Frontend - Services:**
- `apps/orchestrator_3_stream/frontend/src/services/chatService.ts` - Verify WebSocket handling (likely no changes)
- `apps/orchestrator_3_stream/frontend/src/services/fileService.ts` - NEW: Service for opening files in IDE

**Documentation:**
- `ai_docs/claude-code-sdk-python.md` - Reference for hook implementation patterns

### New Files
- `apps/orchestrator_db/git_utils.py` - Git operations and diff generation
- `apps/orchestrator_3_stream/backend/modules/file_tracker.py` - File tracking logic
- `apps/orchestrator_3_stream/frontend/src/components/event-rows/FileChangesDisplay.vue` - File heatmap component
- `apps/orchestrator_3_stream/frontend/src/services/fileService.ts` - Service for IDE integration

## Implementation Phases

### Phase 1: Foundation (Backend File Tracking Infrastructure)
Set up the core file tracking infrastructure, including git utilities for diff generation, line counting for read files, AI summarization, file tracking registry, and new dedicated hook for capturing file operations (both modifications and reads).

### Phase 2: Core Implementation (Hook Integration & Data Flow)
Integrate file tracking into the existing hook system, ensure per-agent isolation, and test the data flow from tool execution through WebSocket to frontend.

### Phase 3: Integration & Polish (Frontend Visualization)
Create the visual file heatmap component, integrate with existing event rows, and add smooth animations and expand/collapse functionality for diffs.

### Phase 4: IDE Integration (Click to Open)
Add backend endpoint for opening files in configured IDE, implement click handlers in file cards, and add configuration UI for IDE selection.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Git Utilities Module
- Create new file `apps/orchestrator_db/git_utils.py`
- Implement `GitUtils` class with methods:
  - `get_file_diff(file_path: str, working_dir: str) -> Optional[str]` - Generate unified diff for a file
  - `parse_diff_stats(diff: str) -> Tuple[int, int]` - Extract lines added/removed from diff
  - `get_file_status(file_path: str, working_dir: str) -> str` - Determine if file is "created", "modified", or "deleted"
  - `resolve_absolute_path(file_path: str, working_dir: str) -> str` - Convert relative path to absolute path
  - `count_file_lines(file_path: str, working_dir: str) -> int` - Count total lines in a file
- Use subprocess.run with git commands (diff, ls-files, status)
- Use `wc -l` or Python file reading for line counting
- Follow existing subprocess patterns with timeout and error handling
- Use the Pydantic models defined in the **Type Definitions** section: `FileChange` and `FileRead`

### 2. Create File Tracker Module
- Create new file `apps/orchestrator_3_stream/backend/modules/file_tracker.py`
- Define constants:
  - `FILE_MODIFYING_TOOLS = ["Write", "Edit", "MultiEdit", "Bash"]`
  - `FILE_READING_TOOLS = ["Read"]`
- Implement `FileTracker` class with:
  - `__init__(agent_id: UUID, working_dir: str)` - Initialize with agent context
  - `track_modified_file(tool_name: str, tool_input: Dict[str, Any]) -> None` - Record file modification
  - `track_read_file(file_path: str) -> None` - Record file read operation
  - `get_modified_files() -> List[str]` - Return list of modified file paths
  - `get_read_files() -> List[str]` - Return list of read file paths
  - `generate_file_changes_summary() -> Dict[str, Any]` - Generate final summary with diffs and AI summaries
  - `generate_read_files_summary() -> List[Dict[str, Any]]` - Generate summary with line counts
- Store tracked files in separate sets (modified_files, read_files) to avoid duplicates
- Use GitUtils to generate diffs and count lines when creating summaries
- **IMPORTANT**: Use `resolve_absolute_path()` to store both relative and absolute paths in metadata

### 3. Add In-Memory File Registry to AgentManager
- In `apps/orchestrator_3_stream/backend/modules/agent_manager.py`, add new field:
  - `self.file_trackers: Dict[str, FileTracker] = {}` (keyed by agent_id)
- In `create_agent()` method, initialize FileTracker:
  - `self.file_trackers[str(agent_id)] = FileTracker(agent_id, self.working_dir)`
- In cleanup/agent deletion, remove tracker from registry
- Pass tracker instance to hooks via closure

### 4. Create Dedicated File Tracking Hook
- In `apps/orchestrator_3_stream/backend/modules/command_agent_hooks.py`, create new function `create_post_tool_file_tracking_hook()`
- Accept parameters: `file_tracker: FileTracker`, `agent_id: UUID`, `agent_name: str`, `logger: OrchestratorLogger`
- In the hook implementation:
  - **For Modified Files**: Check if `tool_name in FILE_MODIFYING_TOOLS`
    - Extract `file_path` from `input_data.get("tool_input", {})`
    - Call `file_tracker.track_modified_file(tool_name, tool_input)`
    - **Generate AI summary**: Use existing LLM utility to summarize the change
      ```python
      # Get the diff
      diff = GitUtils.get_file_diff(file_path, working_dir)
      # Generate summary using LLM
      summary = await generate_file_change_summary(file_path, diff, tool_name)
      ```
    - Store in payload with AI summary
  - **For Read Files**: Check if `tool_name in FILE_READING_TOOLS`
    - Extract `file_path` from `input_data.get("tool_input", {})`
    - Call `file_tracker.track_read_file(file_path)`
    - Count lines in file using `GitUtils.count_file_lines()`
    - Store in payload with line count
  - For Bash commands, parse stdout for file operations (optional, focus on Write/Edit/Read first)
- Do NOT broadcast individual file operations (only include in final response)
- Return empty dict (no blocking or modification needed)

### 5. Add AI Summary Generation Utility
- Create new function `generate_file_change_summary()` in `file_tracker.py`
- Use existing LLM utilities from `apps/orchestrator_3_stream/backend/modules/single_agent_prompt.py`
- Prompt template:
  ```
  Analyze this file change and provide a concise 1-2 sentence summary of what was changed and why:

  File: {file_path}
  Operation: {tool_name}
  Diff:
  {diff}

  Summary (1-2 sentences):
  ```
- Use fast model (haiku or equivalent) for quick summaries
- Handle API errors gracefully (return "Summary generation failed" on error)
- Cache summaries to avoid duplicate API calls
- Limit diff size sent to LLM (max 2000 chars, truncate if larger)

### 6. Capture File Changes in Final Response Block
- In `apps/orchestrator_3_stream/backend/modules/agent_manager.py`, in `_process_agent_messages()`
- When processing `ResponseMessage` (final message), check if file_tracker exists for agent
- Generate comprehensive file summary:
  ```python
  file_tracker = self.file_trackers.get(str(agent_id))
  if file_tracker:
      modified_files_summary = file_tracker.generate_file_changes_summary()
      read_files_summary = file_tracker.generate_read_files_summary()
  ```
- Add to response message payload or agent_log metadata using `AgentLogMetadata`:
  ```python
  from datetime import datetime

  metadata = AgentLogMetadata(
      file_changes=modified_files_summary,  # List[FileChange] with AI summaries
      read_files=read_files_summary,        # List[FileRead] with line counts
      total_files_modified=len(modified_files_summary),
      total_files_read=len(read_files_summary),
      generated_at=datetime.utcnow().isoformat()
  )
  ```
- Ensure this data is included in the agent_log event broadcasted via WebSocket

### 7. Update Frontend TypeScript Types
- In `apps/orchestrator_3_stream/frontend/src/types.d.ts`, add the interfaces defined in the **Type Definitions** section above
- Update `AgentLog` interface to reference `AgentLogMetadata` for the payload field:
  ```typescript
  export interface AgentLog {
    // ... existing fields
    payload?: AgentLogMetadata  // File tracking metadata
  }
  ```

### 8. Create FileChangesDisplay Component
- Create new file `apps/orchestrator_3_stream/frontend/src/components/event-rows/FileChangesDisplay.vue`
- Props: `fileChanges: FileChange[]`, `readFiles: FileRead[]`
- Implement two distinct sections with visual separation:

**Section 1: Modified Files (Green/Yellow/Red Heatmap)**
  - Display modified files as cards with file path, status badge, line stats, and **AI summary**
  - Color-code status: created (green), modified (yellow), deleted (red)
  - Show line changes: `+234 -8` format
  - **Show AI summary in subtitle**: e.g., "Added user authentication middleware with JWT validation"
  - Add expand/collapse for individual files to show full diff
  - **Add click handler to each file card to open in IDE**

**Section 2: Read Files (Blue Section)**
  - Display read files in a distinct blue-themed section below modified files
  - Header: "📖 Context Files Read" with count badge
  - Show file cards with:
    - File path (relative, truncated if long)
    - Line count badge: "1,234 lines"
    - Blue status indicator (distinct from green/yellow/red)
  - **Smaller, more compact cards than modified files**
  - **Clickable to open in IDE**
  - No diffs (read-only context, no changes to show)
  - Tooltip: "Read for context"

**Shared Styling:**
- Use JetBrains Mono font for file paths
- Apply theme colors from global.css
- Implement smooth expand/collapse animation
- Add hover state and cursor pointer to indicate files are clickable
- Show tooltip on hover: "Click to open in IDE"

### 9. Integrate FileChangesDisplay into AgentLogRow
- In `apps/orchestrator_3_stream/frontend/src/components/event-rows/AgentLogRow.vue`
- Add computed properties:
  ```typescript
  const fileChanges = computed(() => {
    return props.event.payload?.file_changes || []
  })

  const readFiles = computed(() => {
    return props.event.payload?.read_files || []
  })

  const hasFileActivity = computed(() => {
    return fileChanges.value.length > 0 || readFiles.value.length > 0
  })
  ```
- Add conditional section in template after main content:
  ```vue
  <FileChangesDisplay
    v-if="hasFileActivity && event.eventCategory === 'response'"
    :file-changes="fileChanges"
    :read-files="readFiles"
    class="file-changes-section"
  />
  ```
- Import FileChangesDisplay component
- Add styling for `.file-changes-section` with proper spacing and borders

### 10. Add File Count Badge to Event Row Header
- In `AgentLogRow.vue`, add file activity indicator next to category badge
- Display: "📝 5 modified • 📖 12 read" when files exist
- Use accent color (cyan) for modified count, blue for read count
- Only show for response events with file activity
- Make badge clickable to scroll to FileChangesDisplay section

### 10. Test File Tracking with Write Tool
- Create test agent that executes multiple Write operations
- Verify file_tracker captures all file paths
- Check that final response payload contains file_changes array
- Verify WebSocket broadcasts include file metadata
- Confirm frontend displays file heatmap correctly

### 11. Test File Tracking with Edit Tool
- Create test agent that edits existing files
- Verify diff generation works correctly
- Check line count statistics (lines_added, lines_removed)
- Ensure "modified" status is correctly assigned
- Test expandable diff display in UI

### 12. Test Concurrent Agent Isolation
- Run two agents simultaneously that modify different files
- Verify each agent's file_tracker only contains its own files
- Check that final responses show correct files per agent
- Ensure no file mixing between agents
- Validate agent_id scoping in file metadata

### 13. Add Diff Syntax Highlighting
- In `FileChangesDisplay.vue`, use highlight.js for diff syntax highlighting
- Apply diff language: `<pre><code class="language-diff">{{diff}}</code></pre>`
- Use existing markdown rendering utilities from `utils/markdown.ts`
- Style diff additions (green) and deletions (red) using global CSS patterns

### 14. Add Styling for Read Files Section
- In `FileChangesDisplay.vue`, create distinct blue theme for read files section:
  ```css
  .read-files-section {
    margin-top: var(--spacing-lg);
    padding: var(--spacing-md);
    background: rgba(59, 130, 246, 0.05); /* Blue tint */
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 8px;
  }

  .read-file-card {
    background: rgba(59, 130, 246, 0.1);
    border-left: 3px solid var(--status-info); /* Blue */
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .read-file-card:hover {
    background: rgba(59, 130, 246, 0.15);
    transform: translateX(2px);
  }

  .line-count-badge {
    color: var(--status-info);
    font-size: 0.75rem;
    font-weight: 600;
  }
  ```
- Use compact grid layout for read files: `grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))`
- Make read file cards smaller than modified file cards

### 15. Optimize Performance for Large Diffs and Many Files
- Add diff truncation for files with >500 lines changed
- Show summary stats and "Load Full Diff" button for large files
- Implement lazy loading: only generate full diff when user expands file
- Add loading state while generating diffs and AI summaries
- For read files: if >50 files read, show "Show More" pagination
- Consider virtual scrolling if agent reads >100 files

### 16. Add Export Functionality
- Add "Export File Activity" button in FileChangesDisplay
- Generate JSON export with all file changes, read files, and summaries
- Format: `agent-{name}-files-{timestamp}.json`
- Include metadata:
  ```json
  {
    "agent_id": "...",
    "agent_name": "...",
    "timestamp": "...",
    "file_changes": [
      {
        "path": "...",
        "absolute_path": "...",
        "status": "modified",
        "lines_added": 234,
        "lines_removed": 8,
        "summary": "Added user authentication middleware...",
        "diff": "..."
      }
    ],
    "read_files": [
      {
        "path": "...",
        "absolute_path": "...",
        "line_count": 1234
      }
    ]
  }
  ```

### 16. Add IDE Configuration to Backend
- In `apps/orchestrator_3_stream/backend/modules/config.py`, add new environment variables:
  - `EDITOR_COMMAND` - Command to open files (default: "code" for VS Code)
  - `EDITOR_ARGS` - Additional arguments (default: "" for VS Code, "-g" for line numbers)
- Support common editors:
  - VS Code: `code {file}:{line}` or `code -g {file}:{line}`
  - Cursor: `cursor {file}:{line}`
  - Sublime Text: `subl {file}:{line}`
  - IntelliJ IDEA: `idea {file}:{line}`
  - Vim: `vim +{line} {file}`
  - Emacs: `emacs +{line} {file}`
- Update `.env.sample` with IDE configuration examples

### 17. Create Backend Open File Endpoint
- In `apps/orchestrator_3_stream/backend/main.py`, add new POST endpoint `/api/open-file`
- Request body: `{ "absolute_path": string, "line": number (optional) }`
- Use subprocess.run to execute editor command with file path
- Build command string: `f"{EDITOR_COMMAND} {format_file_path(absolute_path, line)}"`
- Handle errors gracefully (editor not found, file doesn't exist, permission errors)
- Return success/error response: `{ "status": "success" | "error", "message": string }`
- Add CORS support for frontend requests
- Log all file open attempts for debugging

### 18. Create Frontend File Service
- Create new file `apps/orchestrator_3_stream/frontend/src/services/fileService.ts`
- Implement `openFileInIDE(absolutePath: string, line?: number)` function
- Make POST request to `/api/open-file` with axios
- Handle response and show toast notification on success/error
- Export function for use in components

### 19. Add Click Handler to FileChangesDisplay
- In `FileChangesDisplay.vue`, add `@click` handler to each file card
- Implement `handleFileClick(fileChange: FileChange)` method:
  ```typescript
  const handleFileClick = async (fileChange: FileChange) => {
    try {
      await openFileInIDE(fileChange.absolute_path)
      // Optional: Show success toast
    } catch (error) {
      console.error('Failed to open file:', error)
      // Show error toast
    }
  }
  ```
- Add CSS cursor pointer and hover effects
- Add title/tooltip: "Click to open in IDE"
- Prevent click event from bubbling to expand/collapse handlers

### 20. Add File Opening Icon to File Cards
- Add small "open in editor" icon (📂 or external link icon) to each file card
- Position in top-right corner of card
- Make icon prominent on hover
- Add subtle animation on hover (scale up slightly)
- Ensure icon is visible even when card is not hovered

### 21. Validate Implementation End-to-End
- Run complete test scenario: orchestrator → agent → file modifications → UI display → IDE opening
- Verify all data flows correctly: hooks → database → WebSocket → store → component → IDE
- Check console for errors during file tracking
- Verify no performance degradation with multiple concurrent agents
- Test edge cases: deleted files, binary files, permission errors
- Ensure graceful fallbacks when git operations fail
- **Test IDE integration: click file card and verify it opens in configured editor**
- **Test with different IDEs (VS Code, Cursor) if available**
- **Test error handling when editor is not installed or file doesn't exist**

## Testing Strategy

### Unit Testing
- Test `GitUtils.get_file_diff()` with sample files and git repos
- Test `GitUtils.parse_diff_stats()` with various diff formats
- Test `GitUtils.count_file_lines()` with files of varying sizes
- Test `FileTracker.track_modified_file()` with different tool inputs
- Test `FileTracker.track_read_file()` with file paths
- Test `FileTracker.generate_file_changes_summary()` output format with AI summaries
- Test `FileTracker.generate_read_files_summary()` output format with line counts
- Test `generate_file_change_summary()` LLM integration with mocked API
- Mock git subprocess calls to test error handling
- Test AI summary generation with various diff types (additions, deletions, modifications)

### Component Testing
- Test `FileChangesDisplay.vue` renders correctly with mock data for both sections
- Verify modified files section shows AI summaries correctly
- Verify read files section has distinct blue styling
- Verify expand/collapse behavior works smoothly
- Test status badge color coding (created/modified/deleted for modified, blue for read)
- Verify line stat formatting (+234 -8 for modified, "1,234 lines" for read)
- Test "Load Full Diff" lazy loading for modified files
- Test compact layout for read file cards
- Verify read files section doesn't show expand/diff options

### Integration Testing
- Test hook captures both file modifications and reads during real agent execution
- Verify AI summaries are generated and included in metadata
- Verify file_tracker registry maintains per-agent isolation for both modified and read files
- Test WebSocket broadcasts include file_changes and read_files in payload
- Verify frontend receives and displays both sections correctly
- Test AI summary display in modified file cards
- Test line count display in read file cards
- Test concurrent agents don't interfere with each other's file tracking

### E2E Testing with Playwright MCP
- Launch orchestrator and create agent
- Send command that modifies multiple files and reads context files
- Wait for agent completion
- Verify file heatmap appears with both modified and read sections
- **Verify AI summaries appear in modified file cards**
- **Verify line counts appear in read file cards**
- **Verify blue styling for read files section**
- Click expand on a modified file and verify diff displays
- Click on a read file card and verify no diff (read-only)
- Test export functionality downloads correct JSON with both sections
- **Test clicking file cards opens them in IDE**

### Edge Case Testing
- Agent modifies 0 files and reads 0 files (no heatmap should appear)
- Agent only reads files without modifications (only blue section should appear)
- Agent only modifies files without reads (only modified section should appear)
- Agent modifies >50 files (pagination should activate)
- Agent reads >100 files (virtual scrolling or pagination)
- Binary file modifications (should show file path, no diff, AI summary says "Binary file")
- Git operations fail (should gracefully fallback, show file paths only)
- **LLM API fails for summary generation (show "Summary unavailable" fallback)**
- **LLM API slow (show loading state, don't block file display)**
- Multiple agents modify same file (each agent's tracker should record independently)
- Multiple agents read same file (each agent's tracker should record independently)
- Agent deleted mid-execution (cleanup should remove tracker)
- File read but then modified (should appear in both sections with different metadata)

## Acceptance Criteria

**File Modification Tracking:**
- [ ] Dedicated `create_post_tool_file_tracking_hook()` captures file paths from Write/Edit tools
- [ ] GitUtils module generates unified diffs for modified files
- [ ] **AI summaries generated for each file change using LLM API**
- [ ] **AI summaries are concise (1-2 sentences) and describe what changed**
- [ ] GitUtils resolves and stores both relative and absolute file paths
- [ ] FileTracker maintains per-agent file registry with no cross-agent contamination
- [ ] Final response agent_log includes `file_changes` array with summaries and absolute_path fields

**File Read Tracking:**
- [ ] **Hook captures file paths from Read tool operations**
- [ ] **Line counts generated for each read file**
- [ ] **Read files stored separately from modified files in metadata**
- [ ] **Final response includes `read_files` array with line counts**

**Frontend Visualization:**
- [ ] WebSocket broadcasts file_changes and read_files metadata to frontend
- [ ] FileChangesDisplay component renders two distinct sections (modified and read)
- [ ] **Modified files section shows AI summaries as subtitles**
- [ ] File cards show status badges (created/modified/deleted) with correct colors
- [ ] Line change statistics display correctly (+234 -8 format)
- [ ] **Read files section has distinct blue theme and styling**
- [ ] **Read file cards show line count badges (e.g., "1,234 lines")**
- [ ] **Read file cards are more compact than modified file cards**
- [ ] Clicking file card expands to show syntax-highlighted diff (modified files only)
- [ ] File cards are clickable with cursor pointer and hover effects
- [ ] Clicking any file card (modified or read) opens file in configured IDE

**IDE Integration:**
- [ ] Backend `/api/open-file` endpoint successfully launches editor
- [ ] IDE configuration is loaded from .env (EDITOR_COMMAND, EDITOR_ARGS)
- [ ] Error handling works when editor is not installed or file doesn't exist

**General Requirements:**
- [ ] File activity indicators only appear for response events
- [ ] Badge shows "📝 5 modified • 📖 12 read" counts
- [ ] Concurrent agents maintain isolated file tracking (no mixing)
- [ ] No console errors or WebSocket errors during file tracking
- [ ] Performance remains acceptable with 20+ files modified and 50+ files read
- [ ] Export functionality generates valid JSON with both modified and read files
- [ ] System gracefully handles git command failures and LLM API errors

## Validation Commands
Execute these commands to validate the task is complete:

- `cd apps/orchestrator_3_stream/backend && uv run python -m pytest tests/test_file_tracker.py -v` - Test file tracking logic
- `cd apps/orchestrator_3_stream/backend && uv run python -m pytest tests/test_git_utils.py -v` - Test git utilities
- `cd apps/orchestrator_3_stream/frontend && npm run type-check` - Verify TypeScript types are correct
- `cd apps/orchestrator_3_stream/frontend && npm run lint` - Verify code follows linting standards
- Manual testing checklist (using playwright mcp):
  - Configure IDE: Add `EDITOR_COMMAND=code` and LLM API key to `.env`
  - Start backend: `cd apps/orchestrator_3_stream/backend && uv run python main.py`
  - Start frontend: `cd apps/orchestrator_3_stream/frontend && npm run dev`
  - Open http://127.0.0.1:5175 in browser
  - Send orchestrator command: "Read the config file, then create a new Python module with 3 functions"
  - Wait for agent to complete
  - **Verify two sections appear: Modified Files (green/yellow/red) and Read Files (blue)**
  - **Verify modified files show AI summaries (e.g., "Added user authentication middleware...")**
  - **Verify read files show line counts (e.g., "1,234 lines")**
  - **Verify read files section has blue theme and compact cards**
  - Hover over a file card and verify cursor changes to pointer
  - Click on a modified file card and verify it opens in your IDE
  - Click on a read file card and verify it opens in your IDE
  - Verify file opens at correct location (check absolute path)
  - Click expand button on modified file to show diff
  - Verify diff syntax highlighting works
  - **Verify read files don't have expand/diff buttons**
  - Test export button downloads JSON (should include file_changes, read_files, AI summaries)
  - Send concurrent commands and verify file isolation
  - Test with different IDEs if available (VS Code, Cursor, Sublime)
  - Test error handling: click file that doesn't exist, test with unconfigured editor
  - **Test with LLM API disabled (should show "Summary unavailable" fallback)**

## Notes

**Important Implementation Details:**

1. **AI Summary Generation**: Use the existing LLM utilities from `apps/orchestrator_3_stream/backend/modules/single_agent_prompt.py`to generate summaries. Keep summaries concise (1-2 sentences). Handle API errors gracefully with fallback text. Use a fast model (Haiku) to avoid delays. Truncate diffs before sending to LLM (max 2000 chars) to reduce costs and latency. (Reuse the existing prompt here you shouldn't need to change much here. EVENT_SUMMARIZER_SYSTEM_PROMPT and EVENT_SUMMARIZER_USER_PROMPT)

2. **Read vs Modified Files**: Maintain completely separate tracking for read files vs modified files. Read files should:
   - Have blue theme (not green/yellow/red)
   - Show line count (not diffs)
   - Be more compact (smaller cards)
   - Not have expand/collapse for diffs
   - Still be clickable to open in IDE
   - Display "Read for context" tooltip

3. **Absolute Path Resolution**: Always resolve relative file paths to absolute paths using `os.path.abspath()` or `Path.resolve()`. Store both relative (for display) and absolute (for IDE opening) in metadata. The absolute path is critical for IDE integration to work correctly.

2. **IDE Command Format**: Different IDEs have different command formats:
   - VS Code: `code /absolute/path/to/file.py:123` or `code -g /absolute/path/to/file.py:123`
   - Cursor: `cursor /absolute/path/to/file.py:123`
   - Sublime Text: `subl /absolute/path/to/file.py:123`
   - IntelliJ: `idea /absolute/path/to/file.py:123`
   - Vim: `vim +123 /absolute/path/to/file.py`
   Use environment variables to configure editor command and argument format.

3. **Security**: Validate file paths before opening to prevent command injection. Use subprocess with list arguments (not shell=True) and validate that file paths don't contain shell metacharacters.

4. **Git Operations**: Use subprocess.run with `cwd` parameter to ensure git commands execute in agent's working directory. Handle cases where working_dir is not a git repository gracefully.

5. **Bash Tool Handling**: The Bash tool is complex to parse for file operations. Initial implementation should focus on Write/Edit tools. Bash tool file tracking can be added in a future enhancement by parsing stdout for file paths.

6. **Binary Files**: When `git diff` returns empty for binary files, detect this and show a special indicator in the UI (e.g., "Binary file modified").

7. **Performance**: Generating diffs for large files can be slow. Implement diff generation asynchronously and show loading states. Consider setting a max diff size (e.g., 10KB) and truncating larger diffs.

8. **File Path Display**: Truncate long file paths in the heatmap cards using ellipsis (...) in the middle of the path to preserve directory structure and filename. Always use relative path for display, absolute path for opening.

9. **Agent Colors**: Use the existing `getAgentBorderColor()` utility from `agentColors.ts` to color-code file cards by agent, matching the agent log row border colors.

10. **Dependencies**: No new NPM or Python packages required. Use existing libraries:
    - Backend: subprocess (stdlib), typing (stdlib), os/pathlib (stdlib)
    - Frontend: highlight.js (already imported), existing Vue 3 composition API

11. **Database Migration**: No database schema changes needed. The agent_logs.payload JSONB column already supports arbitrary data.

12. **Cleanup Strategy**: Remove file_tracker from agent_manager registry when agent completes or is deleted to prevent memory leaks.

13. **Visual Reference**: The provided screenshot shows a grid layout with colored borders matching agent colors. Replicate this using CSS Grid with `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))` for responsive file cards. While separating the two sections: 'Consumed' and 'Produced', make sure to keep the same visual style and layout as the provided screenshot.

14. **Click Behavior**: Prevent click event propagation when clicking the expand/collapse button vs clicking the file card itself. Use `@click.stop` on the expand button to prevent it from triggering the file open action.

15. **LLM API Configuration**: Use the same LLM configuration as existing hooks. Check `.env` for `ANTHROPIC_API_KEY` or `OLLAMA_HOST`. Default to Haiku model for fast, cheap summaries. Cache summaries per agent session to avoid duplicate API calls for the same file.

16. **Line Counting Performance**: For large files (>10,000 lines), use `wc -l` command via subprocess instead of reading entire file into memory. This is much faster for line counting only.

**Future Enhancements (Not in Scope):**
- Real-time file change updates (currently only in final response)
- Git worktree integration for true agent isolation
- Conflict detection when multiple agents modify same file
- Merge preview UI (shown in mockup but complex, defer to v2)
- File change history timeline
- Undo/rollback functionality for agent changes
