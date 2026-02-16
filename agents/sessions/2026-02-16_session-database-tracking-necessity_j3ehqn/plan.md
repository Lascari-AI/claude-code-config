# Implementation Plan

> **Session**: `2026-02-16_session-database-tracking-necessity_j3ehqn`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-02-16
> **Updated**: 2026-02-16

---

## Overview

- **Checkpoints**: 4 (0 complete)
- **Total Tasks**: 27

## ⬜ Checkpoint 1: Add Save Callback to StateManager + Minimal Async Sync

**Goal**: Implement the on_save_callback mechanism in StateManager and create the minimal async sync infrastructure. This is the tracer bullet: StateManager.save() triggers callback → callback queues async task → task syncs to DB. End-to-end working with one session save.

### Testing Strategy

**Approach**: Unit tests for callback mechanism, integration test for async sync

**Verification Steps**:
- [ ] `pytest apps/core/backend/state_manager/tests/`
- [ ] `pytest apps/core/session_db/tests/test_async_sync.py`

### ⬜ Task Group 1.1: Add on_save_callback to SessionStateManager

**Objective**: Modify SessionStateManager to accept an optional callback that fires after save() completes. The callback receives the session_dir path. Callback is fire-and-forget: exceptions are logged but don't break save().

#### ⬜ Task 1.1.1: Define SaveCallback type alias

**File**: `apps/core/backend/state_manager/state_manager.py`

**Description**: Add a type alias for the callback signature at module level. The callback receives session_dir (Path) and returns None. This type alias will be used by __init__ and save() methods for type safety.

**Context to Load**:
- `apps/core/backend/state_manager/state_manager.py` (lines 1-55) - Understand existing imports and class structure

**Actions**:
- ⬜ **1.1.1.1**: UPDATE imports: ADD Callable from typing (`apps/core/backend/state_manager/state_manager.py`)
- ⬜ **1.1.1.2**: CREATE TYPE SaveCallback = Callable[[Path], None] | None AFTER imports BEFORE class (`apps/core/backend/state_manager/state_manager.py`)

#### ⬜ Task 1.1.2: Add on_save_callback parameter to __init__

**File**: `apps/core/backend/state_manager/state_manager.py`

**Description**: Modify SessionStateManager.__init__ to accept optional on_save_callback parameter. Store as instance attribute self._on_save_callback. Default to None.

**Context to Load**:
- `apps/core/backend/state_manager/state_manager.py` (lines 47-55) - Understand current __init__ signature and attributes

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.2.1**: UPDATE FUNCTION __init__: ADD param on_save_callback: SaveCallback DEFAULT None (`apps/core/backend/state_manager/state_manager.py`)
- ⬜ **1.1.2.2**: UPDATE FUNCTION __init__: ADD self._on_save_callback = on_save_callback (`apps/core/backend/state_manager/state_manager.py`)
- ⬜ **1.1.2.3**: UPDATE docstring __init__: ADD on_save_callback parameter description (`apps/core/backend/state_manager/state_manager.py`)

#### ⬜ Task 1.1.3: Invoke callback in save() method

**File**: `apps/core/backend/state_manager/state_manager.py`

**Description**: Modify save() method to invoke callback in finally block after successful file write. Wrap callback invocation in try/except to log errors without re-raising. Callback should be fire-and-forget to not block save().

**Context to Load**:
- `apps/core/backend/state_manager/state_manager.py` (lines 97-123) - Understand current save() implementation

**Depends On**: Tasks 1.1.2

**Actions**:
- ⬜ **1.1.3.1**: UPDATE imports: ADD logging (`apps/core/backend/state_manager/state_manager.py`)
- ⬜ **1.1.3.2**: CREATE VAR logger = logging.getLogger(__name__) AFTER imports (`apps/core/backend/state_manager/state_manager.py`)
- ⬜ **1.1.3.3**: UPDATE FUNCTION save: WRAP file write in try/finally, ADD callback invocation in finally with try/except logging errors (`apps/core/backend/state_manager/state_manager.py`)

#### ⬜ Task 1.1.4: Update __init__.py exports

**File**: `apps/core/backend/state_manager/__init__.py`

**Description**: Export SaveCallback type alias from __init__.py for external callers who need to type-hint callbacks they pass to SessionStateManager.

**Context to Load**:
- `apps/core/backend/state_manager/__init__.py` (lines 1-58) - Understand current exports and structure

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.4.1**: UPDATE import from .state_manager: ADD SaveCallback (`apps/core/backend/state_manager/__init__.py`)
- ⬜ **1.1.4.2**: UPDATE __all__: ADD "SaveCallback" to exports list (`apps/core/backend/state_manager/__init__.py`)

### ⬜ Task Group 1.2: Create async sync task module

**Objective**: Create the async_sync.py module in session_db/ that provides a queue_sync_task() function. This wraps the existing sync_session_from_filesystem for background execution. Uses asyncio.create_task or similar pattern.

#### ⬜ Task 1.2.1: Create async_sync.py module skeleton

**File**: `apps/core/session_db/async_sync.py`

**Description**: Create new async_sync.py module with imports, module docstring, and logger setup. This will contain the queue_sync_task function and related async infrastructure.

**Context to Load**:
- `apps/core/session_db/sync.py` (lines 1-50) - Understand existing sync module structure and imports
- `apps/core/session_db/database.py` (lines 1-50) - Understand how to get database sessions

**Actions**:
- ⬜ **1.2.1.1**: CREATE FILE apps/core/session_db/async_sync.py with module docstring, imports (asyncio, logging, Path, sync functions) (`apps/core/session_db/async_sync.py`)
- ⬜ **1.2.1.2**: CREATE VAR logger = logging.getLogger(__name__) (`apps/core/session_db/async_sync.py`)

#### ⬜ Task 1.2.2: Implement queue_sync_task function

**File**: `apps/core/session_db/async_sync.py`

**Description**: Create queue_sync_task(session_dir: Path) function that creates an asyncio task to sync the session. Uses sync_session_from_filesystem wrapped in async context with database session.

**Context to Load**:
- `apps/core/session_db/sync.py` (lines 321-391) - Understand sync_session_from_filesystem signature and usage
- `apps/core/session_db/database.py` (lines 1-100) - Understand get_async_session context manager

**Depends On**: Tasks 1.2.1

**Actions**:
- ⬜ **1.2.2.1**: CREATE FUNCTION _sync_session_async(session_dir: Path, working_dir: str): async wrapper that gets db session and calls sync_session_from_filesystem (`apps/core/session_db/async_sync.py`)
- ⬜ **1.2.2.2**: CREATE FUNCTION queue_sync_task(session_dir: Path, working_dir: str | None = None): creates asyncio.create_task for _sync_session_async, logs errors, returns None (fire-and-forget) (`apps/core/session_db/async_sync.py`)

#### ⬜ Task 1.2.3: Create callback factory function

**File**: `apps/core/session_db/async_sync.py`

**Description**: Create make_sync_callback(working_dir: str) function that returns a SaveCallback-compatible function. This is the callback to inject into StateManager.

**Context to Load**:
- `apps/core/backend/state_manager/state_manager.py` (lines 1-20) - Understand SaveCallback type signature

**Depends On**: Tasks 1.2.2

**Actions**:
- ⬜ **1.2.3.1**: CREATE FUNCTION make_sync_callback(working_dir: str) -> Callable[[Path], None]: returns closure that calls queue_sync_task with working_dir (`apps/core/session_db/async_sync.py`)

#### ⬜ Task 1.2.4: Update session_db __init__.py exports

**File**: `apps/core/session_db/__init__.py`

**Description**: Export queue_sync_task and make_sync_callback from the session_db package for external use.

**Context to Load**:
- `apps/core/session_db/__init__.py` (lines 1-50) - Understand current exports

**Depends On**: Tasks 1.2.3

**Actions**:
- ⬜ **1.2.4.1**: UPDATE apps/core/session_db/__init__.py: ADD imports from .async_sync (queue_sync_task, make_sync_callback) (`apps/core/session_db/__init__.py`)
- ⬜ **1.2.4.2**: UPDATE __all__: ADD queue_sync_task, make_sync_callback (`apps/core/session_db/__init__.py`)

### ⬜ Task Group 1.3: Add tests for callback and async sync

**Objective**: Test that the callback is invoked correctly after save(), callback exceptions don't break save(), and the async sync task correctly calls sync_session_from_filesystem.

#### ⬜ Task 1.3.1: Test StateManager callback invocation

**File**: `apps/core/backend/state_manager/tests/test_callback.py`

**Description**: Create test file for callback functionality. Test that callback is called after save(), callback receives correct session_dir, and that callback errors are logged but don't break save().

**Context to Load**:
- `apps/core/backend/state_manager/state_manager.py` (lines 97-130) - Understand save() method with callback

**Actions**:
- ⬜ **1.3.1.1**: CREATE FILE apps/core/backend/state_manager/tests/test_callback.py with imports (pytest, Mock, SessionStateManager) (`apps/core/backend/state_manager/tests/test_callback.py`)
- ⬜ **1.3.1.2**: TEST test_callback_invoked_after_save: MOCK callback, call save(), VERIFY callback was called once with session_dir (`apps/core/backend/state_manager/tests/test_callback.py`)
- ⬜ **1.3.1.3**: TEST test_callback_exception_does_not_break_save: MOCK callback to raise, call save(), VERIFY save completes and state file exists (`apps/core/backend/state_manager/tests/test_callback.py`)
- ⬜ **1.3.1.4**: TEST test_no_callback_works: create StateManager without callback, call save(), VERIFY no error (`apps/core/backend/state_manager/tests/test_callback.py`)

#### ⬜ Task 1.3.2: Test async sync queue function

**File**: `apps/core/session_db/tests/test_async_sync.py`

**Description**: Create test file for async_sync module. Test queue_sync_task creates task, make_sync_callback returns callable, and integration with sync_session_from_filesystem.

**Context to Load**:
- `apps/core/session_db/async_sync.py` (lines 1-100) - Understand async_sync module implementation

**Actions**:
- ⬜ **1.3.2.1**: CREATE FILE apps/core/session_db/tests/test_async_sync.py with imports (pytest, asyncio, patch) (`apps/core/session_db/tests/test_async_sync.py`)
- ⬜ **1.3.2.2**: TEST test_queue_sync_task_creates_task: MOCK sync_session_from_filesystem, call queue_sync_task, VERIFY task is created (`apps/core/session_db/tests/test_async_sync.py`)
- ⬜ **1.3.2.3**: TEST test_make_sync_callback_returns_callable: call make_sync_callback, ASSERT returns callable that accepts Path (`apps/core/session_db/tests/test_async_sync.py`)
- ⬜ **1.3.2.4**: TEST test_callback_calls_queue_sync_task: create callback via make_sync_callback, call with session_dir, VERIFY queue_sync_task invoked (`apps/core/session_db/tests/test_async_sync.py`)

---

## ⬜ Checkpoint 2: Project Open Triggers Batch Sync

**Goal**: When a project is opened in the UI, trigger batch sync for all sessions in that project. Uses existing sync_all_sessions_in_project function but runs it asynchronously without blocking the UI response.

**Prerequisites**: Checkpoints 1

### Testing Strategy

**Approach**: API endpoint test with mocked background task

**Verification Steps**:
- [ ] `npm test -- --grep 'project sync'`
- [ ] `Manual: open project detail, verify sessions appear/update`

### ⬜ Task Group 2.1: Add batch sync API endpoint

**Objective**: Create a POST /api/projects/[id]/sync endpoint that triggers background batch sync for all sessions in the project. Uses async_sync infrastructure from CP1.

#### ⬜ Task 2.1.1: Create sync API route file

**File**: `apps/core/frontend/src/app/api/projects/[id]/sync/route.ts`

**Description**: Create new API route for POST /api/projects/[id]/sync. Returns 202 Accepted immediately while triggering background sync. Calls Python backend's async sync function via server action or API.

**Context to Load**:
- `apps/core/frontend/src/app/api/projects/[id]/route.ts` (lines 1-75) - Understand existing project API route pattern

**Actions**:
- ⬜ **2.1.1.1**: CREATE FILE apps/core/frontend/src/app/api/projects/[id]/sync/route.ts with NextJS route handler structure (`apps/core/frontend/src/app/api/projects/[id]/sync/route.ts`)
- ⬜ **2.1.1.2**: CREATE FUNCTION POST: get project by id, trigger sync_all_sessions, return 202 Accepted with sync status (`apps/core/frontend/src/app/api/projects/[id]/sync/route.ts`)

#### ⬜ Task 2.1.2: Add batch sync function wrapper

**File**: `apps/core/session_db/async_sync.py`

**Description**: Add queue_batch_sync_task function that wraps sync_all_sessions_in_project for async background execution. Similar pattern to queue_sync_task but for batch operations.

**Context to Load**:
- `apps/core/session_db/async_sync.py` (lines 1-100) - Understand existing async sync pattern
- `apps/core/session_db/sync.py` (lines 442-522) - Understand sync_all_sessions_in_project function

**Actions**:
- ⬜ **2.1.2.1**: CREATE FUNCTION _batch_sync_async(working_dir: str, project_id: UUID | None): async wrapper for sync_all_sessions_in_project (`apps/core/session_db/async_sync.py`)
- ⬜ **2.1.2.2**: CREATE FUNCTION queue_batch_sync_task(working_dir: str, project_id: UUID | None): creates asyncio task for batch sync, returns immediately (`apps/core/session_db/async_sync.py`)

### ⬜ Task Group 2.2: Trigger sync on project detail view load

**Objective**: When the project detail page loads, call the sync endpoint to ensure session data is fresh. Fire-and-forget call that doesn't block UI rendering.

#### ⬜ Task 2.2.1: Add useEffect sync trigger in project detail

**File**: `apps/core/frontend/src/app/(dashboard)/projects/[id]/page.tsx`

**Description**: Add useEffect hook that calls POST /api/projects/[id]/sync when the project detail page mounts. Fire-and-forget - don't await the response. Just ensure sessions are synced in background.

**Context to Load**:
- `apps/core/frontend/src/app/(dashboard)/projects/[id]/page.tsx` (lines 1-100) - Understand project detail page structure

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.2.1.1**: UPDATE project detail page: ADD useEffect hook that calls fetch('/api/projects/${id}/sync', { method: 'POST' }) on mount (`apps/core/frontend/src/app/(dashboard)/projects/[id]/page.tsx`)

### ⬜ Task Group 2.3: Add tests for project sync

**Objective**: Test the sync endpoint behavior and verify it correctly triggers background sync without blocking.

#### ⬜ Task 2.3.1: Test batch sync API endpoint

**File**: `apps/core/frontend/src/app/api/projects/[id]/sync/__tests__/route.test.ts`

**Description**: Test POST /api/projects/[id]/sync endpoint returns 202, triggers background sync, and handles errors gracefully.

**Context to Load**:
- `apps/core/frontend/src/app/api/projects/[id]/sync/route.ts` (lines 1-50) - Understand the sync endpoint implementation

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.3.1.1**: CREATE FILE with test setup, imports, MOCK background sync function (`apps/core/frontend/src/app/api/projects/[id]/sync/__tests__/route.test.ts`)
- ⬜ **2.3.1.2**: TEST test_sync_returns_202: POST to sync endpoint, ASSERT response status 202 (`apps/core/frontend/src/app/api/projects/[id]/sync/__tests__/route.test.ts`)
- ⬜ **2.3.1.3**: TEST test_sync_triggers_background_task: POST to sync, VERIFY background sync was queued (`apps/core/frontend/src/app/api/projects/[id]/sync/__tests__/route.test.ts`)
- ⬜ **2.3.1.4**: TEST test_sync_returns_404_for_missing_project: POST to sync with invalid id, ASSERT 404 (`apps/core/frontend/src/app/api/projects/[id]/sync/__tests__/route.test.ts`)

---

## ⬜ Checkpoint 3: Split models.py into Domain Modules

**Goal**: Refactor session_db/models.py (855 lines) into domain-organized modules while maintaining backward compatibility via re-exports. This is a pure refactoring checkpoint with no behavior change.

### Testing Strategy

**Approach**: Type checking and import verification

**Verification Steps**:
- [ ] `python -c "from session_db.models import Session, Agent, AgentLog, Project"`
- [ ] `pytest apps/core/session_db/tests/`

### ⬜ Task Group 3.1: Create models/ directory structure

**Objective**: Create the models/ subdirectory with base.py containing shared type aliases. This establishes the foundation for the split.

#### ⬜ Task 3.1.1: Create base.py with type aliases

**File**: `apps/core/session_db/models/base.py`

**Description**: Create models/base.py with the Literal type aliases (SessionStatus, SessionType, AgentType, AgentStatus, EventCategory, ProjectStatus) extracted from models.py.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 1-80) - Identify type aliases to extract

**Actions**:
- ⬜ **3.1.1.1**: CREATE FILE apps/core/session_db/models/base.py with module docstring and imports (`apps/core/session_db/models/base.py`)
- ⬜ **3.1.1.2**: MOVE type aliases (SessionStatus, SessionType, AgentType, AgentStatus, EventCategory, ProjectStatus) from models.py to base.py (`apps/core/session_db/models/base.py`)

### ⬜ Task Group 3.2: Extract Project models

**Objective**: Move Project, ProjectCreate, ProjectUpdate, ProjectSummary to models/project.py with proper imports from base.py.

#### ⬜ Task 3.2.1: Create project.py with Project models

**File**: `apps/core/session_db/models/project.py`

**Description**: Create models/project.py containing Project (SQLModel table), ProjectCreate, ProjectUpdate, and ProjectSummary. Import shared types from base.py.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 82-160) - Identify Project model and related DTOs

**Depends On**: Tasks 3.1.1

**Actions**:
- ⬜ **3.2.1.1**: CREATE FILE apps/core/session_db/models/project.py with imports (SQLModel, Field, Relationship, JSON, base types) (`apps/core/session_db/models/project.py`)
- ⬜ **3.2.1.2**: MOVE CLASS Project from models.py to project.py (`apps/core/session_db/models/project.py`)
- ⬜ **3.2.1.3**: MOVE CLASS ProjectCreate, ProjectUpdate, ProjectSummary from models.py to project.py (`apps/core/session_db/models/project.py`)

### ⬜ Task Group 3.3: Extract Session models

**Objective**: Move Session, SessionCreate, SessionUpdate, SessionSummary to models/session.py.

#### ⬜ Task 3.3.1: Create session.py with Session models

**File**: `apps/core/session_db/models/session.py`

**Description**: Create models/session.py containing Session (SQLModel table), SessionCreate, SessionUpdate, SessionSummary. Handle forward references for relationships.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 160-365) - Identify Session model and relationships

**Depends On**: Tasks 3.2.1

**Actions**:
- ⬜ **3.3.1.1**: CREATE FILE apps/core/session_db/models/session.py with imports and TYPE_CHECKING for forward refs (`apps/core/session_db/models/session.py`)
- ⬜ **3.3.1.2**: MOVE CLASS Session from models.py to session.py, USE string annotations for Agent/AgentLog relationships (`apps/core/session_db/models/session.py`)
- ⬜ **3.3.1.3**: MOVE CLASS SessionCreate, SessionUpdate, SessionSummary from models.py to session.py (`apps/core/session_db/models/session.py`)

### ⬜ Task Group 3.4: Extract Agent and AgentLog models

**Objective**: Move Agent, AgentLog and their DTOs to models/agent.py and models/agent_log.py.

#### ⬜ Task 3.4.1: Create agent.py with Agent models

**File**: `apps/core/session_db/models/agent.py`

**Description**: Create models/agent.py containing Agent (SQLModel table), AgentCreate, AgentUpdate, AgentSummary.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 365-515) - Identify Agent model

**Depends On**: Tasks 3.3.1

**Actions**:
- ⬜ **3.4.1.1**: CREATE FILE apps/core/session_db/models/agent.py with imports (`apps/core/session_db/models/agent.py`)
- ⬜ **3.4.1.2**: MOVE CLASS Agent, AgentCreate, AgentUpdate, AgentSummary from models.py to agent.py (`apps/core/session_db/models/agent.py`)

#### ⬜ Task 3.4.2: Create agent_log.py with AgentLog models

**File**: `apps/core/session_db/models/agent_log.py`

**Description**: Create models/agent_log.py containing AgentLog (SQLModel table), AgentLogCreate, AgentLogSummary.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 515-645) - Identify AgentLog model

**Depends On**: Tasks 3.4.1

**Actions**:
- ⬜ **3.4.2.1**: CREATE FILE apps/core/session_db/models/agent_log.py with imports (`apps/core/session_db/models/agent_log.py`)
- ⬜ **3.4.2.2**: MOVE CLASS AgentLog, AgentLogCreate, AgentLogSummary from models.py to agent_log.py (`apps/core/session_db/models/agent_log.py`)

### ⬜ Task Group 3.5: Create __init__.py with re-exports

**Objective**: Create models/__init__.py that re-exports all models for backward compatibility. Existing imports from session_db.models should continue to work.

#### ⬜ Task 3.5.1: Create models/__init__.py with all exports

**File**: `apps/core/session_db/models/__init__.py`

**Description**: Create __init__.py that imports and re-exports all models from the submodules. Use __all__ to define public API. Ensure backward compatibility.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 1-50) - Identify all exported names

**Depends On**: Tasks 3.4.2

**Actions**:
- ⬜ **3.5.1.1**: CREATE FILE apps/core/session_db/models/__init__.py with imports from all submodules (`apps/core/session_db/models/__init__.py`)
- ⬜ **3.5.1.2**: CREATE __all__ list with all model names for backward compat (`apps/core/session_db/models/__init__.py`)

#### ⬜ Task 3.5.2: Delete old models.py

**File**: `apps/core/session_db/models.py`

**Description**: Remove the old monolithic models.py file now that all content has been moved to models/ directory.

**Depends On**: Tasks 3.5.1

**Actions**:
- ⬜ **3.5.2.1**: DELETE FILE apps/core/session_db/models.py (`apps/core/session_db/models.py`)

---

## ⬜ Checkpoint 4: Backend Integration + Task Pool Setup

**Goal**: Create the background task pool infrastructure and integrate callback injection where StateManager instances are created in the backend. Ensure sync tasks run in a pool that doesn't block the main event loop.

**Prerequisites**: Checkpoints 1, 2

### Testing Strategy

**Approach**: Integration tests with concurrent sync operations

**Verification Steps**:
- [ ] `pytest apps/core/backend/task_pool/tests/`
- [ ] `Manual: verify UI remains responsive during sync`

### ⬜ Task Group 4.1: Create background task pool module

**Objective**: Create a task_pool.py module that manages a pool of background sync tasks. Uses asyncio task management with configurable concurrency limits.

#### ⬜ Task 4.1.1: Create task_pool.py with pool management

**File**: `apps/core/backend/task_pool/task_pool.py`

**Description**: Create task_pool.py with SyncTaskPool class. Manages background asyncio tasks, limits concurrency, handles task lifecycle. Provides singleton instance for the application.

**Context to Load**:
- `apps/core/session_db/async_sync.py` (lines 1-100) - Understand async sync functions that will be pooled

**Actions**:
- ⬜ **4.1.1.1**: CREATE FILE apps/core/backend/task_pool/__init__.py with exports (`apps/core/backend/task_pool/__init__.py`)
- ⬜ **4.1.1.2**: CREATE FILE apps/core/backend/task_pool/task_pool.py with SyncTaskPool class (`apps/core/backend/task_pool/task_pool.py`)
- ⬜ **4.1.1.3**: CREATE CLASS SyncTaskPool with: __init__(max_concurrent), submit(coro), shutdown(), active_count property (`apps/core/backend/task_pool/task_pool.py`)
- ⬜ **4.1.1.4**: CREATE VAR default_pool: SyncTaskPool singleton instance (`apps/core/backend/task_pool/task_pool.py`)

### ⬜ Task Group 4.2: Create callback factory using task pool

**Objective**: Create a factory function that returns a StateManager callback. The callback submits sync tasks to the pool instead of running directly.

#### ⬜ Task 4.2.1: Create pooled callback factory

**File**: `apps/core/backend/task_pool/callbacks.py`

**Description**: Create callbacks.py with make_pooled_sync_callback function. Returns a callback that submits sync tasks to the default pool. Fire-and-forget semantics.

**Context to Load**:
- `apps/core/session_db/async_sync.py` (lines 1-100) - Understand make_sync_callback pattern
- `apps/core/backend/task_pool/task_pool.py` (lines 1-100) - Understand pool submit API

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.2.1.1**: CREATE FILE apps/core/backend/task_pool/callbacks.py with imports (`apps/core/backend/task_pool/callbacks.py`)
- ⬜ **4.2.1.2**: CREATE FUNCTION make_pooled_sync_callback(working_dir: str) -> SaveCallback: returns callback that submits to pool (`apps/core/backend/task_pool/callbacks.py`)

### ⬜ Task Group 4.3: Integrate callback injection at StateManager creation points

**Objective**: Find where StateManager is instantiated in the backend and inject the pooled callback. This connects the save→sync pipeline.

#### ⬜ Task 4.3.1: Identify StateManager instantiation points

**File**: `apps/core/backend/`

**Description**: Search the backend codebase to find all places where SessionStateManager is created. Document each location for callback injection.

**Actions**:
- ⬜ **4.3.1.1**: SEARCH codebase for SessionStateManager( instantiation patterns, document findings (`apps/core/backend/`)

#### ⬜ Task 4.3.2: Inject callback at MCP tool creation

**File**: `apps/core/backend/mcp_server/tools.py`

**Description**: Update MCP tools that create StateManager instances to inject the pooled sync callback. This ensures MCP state changes trigger DB sync.

**Context to Load**:
- `apps/core/backend/mcp_server/tools.py` (lines 1-100) - Understand MCP tool structure and StateManager usage

**Depends On**: Tasks 4.2.1, 4.3.1

**Actions**:
- ⬜ **4.3.2.1**: UPDATE MCP tools: import make_pooled_sync_callback (`apps/core/backend/mcp_server/tools.py`)
- ⬜ **4.3.2.2**: UPDATE SessionStateManager instantiation: ADD on_save_callback=make_pooled_sync_callback(working_dir) (`apps/core/backend/mcp_server/tools.py`)

### ⬜ Task Group 4.4: Add integration tests

**Objective**: Test the complete pipeline: StateManager.save() -> callback -> pool -> sync. Verify non-blocking behavior.

#### ⬜ Task 4.4.1: Test task pool functionality

**File**: `apps/core/backend/task_pool/tests/test_task_pool.py`

**Description**: Test SyncTaskPool: submit tasks, verify concurrency limits, test graceful shutdown.

**Context to Load**:
- `apps/core/backend/task_pool/task_pool.py` (lines 1-100) - Understand pool API to test

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.4.1.1**: CREATE FILE with pytest fixtures and imports (`apps/core/backend/task_pool/tests/test_task_pool.py`)
- ⬜ **4.4.1.2**: TEST test_pool_submits_task: submit coroutine, VERIFY task runs (`apps/core/backend/task_pool/tests/test_task_pool.py`)
- ⬜ **4.4.1.3**: TEST test_pool_limits_concurrency: submit many tasks, VERIFY only max_concurrent run (`apps/core/backend/task_pool/tests/test_task_pool.py`)
- ⬜ **4.4.1.4**: TEST test_pool_shutdown: submit tasks, shutdown, VERIFY clean exit (`apps/core/backend/task_pool/tests/test_task_pool.py`)

#### ⬜ Task 4.4.2: Test end-to-end sync pipeline

**File**: `apps/core/backend/task_pool/tests/test_integration.py`

**Description**: Integration test: StateManager save triggers callback, callback submits to pool, pool runs sync. Verify DB updated.

**Depends On**: Tasks 4.3.2

**Actions**:
- ⬜ **4.4.2.1**: CREATE FILE with integration test setup (`apps/core/backend/task_pool/tests/test_integration.py`)
- ⬜ **4.4.2.2**: TEST test_save_triggers_db_sync: create StateManager with callback, save, VERIFY DB session updated (`apps/core/backend/task_pool/tests/test_integration.py`)

---

---
*Auto-generated from plan.json on 2026-02-16 15:44*