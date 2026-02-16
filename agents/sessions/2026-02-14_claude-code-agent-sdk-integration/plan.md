# Implementation Plan

> **Session**: `2026-02-14_claude-code-agent-sdk-integration`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-02-16
> **Updated**: 2026-02-16

---

## Overview

- **Checkpoints**: 7 (0 complete)
- **Total Tasks**: 36

## ⬜ Checkpoint 1: StateManager Core + One Phase Transition

**Goal**: Create the Python StateManager class with one working phase transition (spec→plan), proving the full vertical slice: state.json v2 schema → StateManager → validated transition → file write

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/session_db/models.py` | 📄 exists | SQLModel database models for Session, Agent, AgentLog |
| Before | `apps/core/backend/main.py` | 📄 exists | FastAPI app with health check only |
| After | `apps/core/state_manager/__init__.py` | ✨ new | StateManager package init |
| After | `apps/core/state_manager/models.py` | ✨ new | Pydantic models for state.json v2 schema |
| After | `apps/core/state_manager/state_manager.py` | ✨ new | StateManager class with load/save/transition methods |
| After | `apps/core/state_manager/exceptions.py` | ✨ new | Custom exceptions for validation errors |
| After | `apps/core/state_manager/tests/__init__.py` | ✨ new | Test package init |
| After | `apps/core/state_manager/tests/test_state_manager.py` | ✨ new | Unit tests for StateManager |

**Projected Structure**:
```
apps/core/
├── backend/
│   ├── main.py
│   └── routers/
├── session_db/
│   ├── models.py
│   ├── crud.py
│   └── database.py
└── state_manager/  ← NEW
    ├── __init__.py
    ├── models.py
    ├── state_manager.py
    ├── exceptions.py
    └── tests/
        └── test_state_manager.py
```

### Testing Strategy

**Approach**: Unit tests for StateManager + manual verification

**Verification Steps**:
- [ ] `pytest apps/core/state_manager/tests/ -v`
- [ ] `Manual: Create test session, call transition_to_phase('plan'), verify state.json updated`

### ⬜ Task Group 1.1: Define state.json v2 Pydantic Models

**Objective**: Create type-safe Pydantic models matching the state.json v2 schema from the spec. These models will be used by StateManager for serialization/deserialization.

#### ⬜ Task 1.1.1: Create enums and base types

**File**: `apps/core/state_manager/models.py`

**Description**: Define Phase, Status, SessionType enums. These constrain the valid values for state transitions.

**Context to Load**:
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 246-327) - state.json v2 schema definition with field types and enums

**Actions**:
- ⬜ **1.1.1.1**: CREATE FILE apps/core/state_manager/models.py (`apps/core/state_manager/models.py`)
- ⬜ **1.1.1.2**: CREATE TYPE Phase(str, Enum): spec, plan, build, docs, complete (`apps/core/state_manager/models.py`)
- ⬜ **1.1.1.3**: CREATE TYPE Status(str, Enum): active, paused, complete, failed (`apps/core/state_manager/models.py`)
- ⬜ **1.1.1.4**: CREATE TYPE SessionType(str, Enum): full, quick, research (`apps/core/state_manager/models.py`)

#### ⬜ Task 1.1.2: Create nested Pydantic models

**File**: `apps/core/state_manager/models.py`

**Description**: Define PhaseHistory, BuildProgress, GitContext, Commit, Artifacts models. These are nested objects within SessionState.

**Context to Load**:
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 266-307) - Nested object schemas: phase_history, build_progress, git, commits, artifacts

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.2.1**: CREATE TYPE PhaseHistory(BaseModel): spec_started_at, spec_completed_at, plan_started_at, plan_completed_at, build_started_at, build_completed_at, docs_started_at, docs_completed_at - all Optional[datetime] (`apps/core/state_manager/models.py`)
- ⬜ **1.1.2.2**: CREATE TYPE BuildProgress(BaseModel): checkpoints_total: int, checkpoints_completed: list[int], current_checkpoint: Optional[int] (`apps/core/state_manager/models.py`)
- ⬜ **1.1.2.3**: CREATE TYPE GitContext(BaseModel): branch: Optional[str], worktree: Optional[str], base_branch: Optional[str] (`apps/core/state_manager/models.py`)
- ⬜ **1.1.2.4**: CREATE TYPE Commit(BaseModel): sha: str, message: str, checkpoint: Optional[int], created_at: datetime (`apps/core/state_manager/models.py`)
- ⬜ **1.1.2.5**: CREATE TYPE Artifacts(BaseModel): spec: str DEFAULT 'spec.md', plan: str DEFAULT 'plan.json', plan_readable: str DEFAULT 'plan.md' (`apps/core/state_manager/models.py`)

#### ⬜ Task 1.1.3: Create SessionState root model

**File**: `apps/core/state_manager/models.py`

**Description**: Define the root SessionState model that encompasses all fields. Includes model_config for JSON serialization with datetime handling.

**Context to Load**:
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 246-327) - Complete state.json v2 schema showing all top-level fields

**Depends On**: Tasks 1.1.2

**Actions**:
- ⬜ **1.1.3.1**: CREATE TYPE SessionState(BaseModel): session_id, topic, description, session_type, created_at, updated_at, current_phase, status, phase_history, build_progress, git, commits, artifacts - using previously defined types (`apps/core/state_manager/models.py`)
- ⬜ **1.1.3.2**: ADD model_config with json_encoders for datetime serialization to ISO format (`apps/core/state_manager/models.py`)

### ⬜ Task Group 1.2: Implement StateManager Core

**Objective**: Create the SessionStateManager class with load(), save(), and transition_to_phase() methods. Validates transitions (spec→plan allowed, spec→build not allowed).

#### ⬜ Task 1.2.1: Create custom exceptions

**File**: `apps/core/state_manager/exceptions.py`

**Description**: Define exceptions for invalid state transitions and session not found errors.

**Actions**:
- ⬜ **1.2.1.1**: CREATE FILE apps/core/state_manager/exceptions.py (`apps/core/state_manager/exceptions.py`)
- ⬜ **1.2.1.2**: CREATE CLASS InvalidPhaseTransitionError(Exception): message includes from_phase, to_phase (`apps/core/state_manager/exceptions.py`)
- ⬜ **1.2.1.3**: CREATE CLASS SessionNotFoundError(Exception): message includes session_id and path (`apps/core/state_manager/exceptions.py`)
- ⬜ **1.2.1.4**: CREATE CLASS StateValidationError(Exception): for Pydantic validation failures (`apps/core/state_manager/exceptions.py`)

#### ⬜ Task 1.2.2: Create SessionStateManager class

**File**: `apps/core/state_manager/state_manager.py`

**Description**: Implement the core StateManager class with load(), save(), and transition_to_phase() methods. Uses Pydantic models for type safety.

**Context to Load**:
- `apps/core/state_manager/models.py` (lines all) - Pydantic models for serialization
- `apps/core/state_manager/exceptions.py` (lines all) - Exception types to raise
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 364-392) - StateManager API design from spec

**Depends On**: Tasks 1.1.3, 1.2.1

**Actions**:
- ⬜ **1.2.2.1**: CREATE FILE apps/core/state_manager/state_manager.py (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.2**: CREATE CLASS SessionStateManager: __init__(self, session_dir: Path) - stores session_dir, initializes _state to None (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.3**: CREATE FUNCTION load(self) -> SessionState: reads state.json, parses with Pydantic, caches in _state, raises SessionNotFoundError if missing (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.4**: CREATE FUNCTION save(self) -> None: serializes _state to JSON, writes to state.json atomically, updates updated_at timestamp (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.5**: CREATE FUNCTION _validate_transition(self, from_phase: Phase, to_phase: Phase) -> bool: returns True if transition allowed per VALID_TRANSITIONS map (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.6**: CREATE VAR VALID_TRANSITIONS: dict mapping each phase to list of valid next phases (spec→plan, plan→build, build→docs, docs→complete) (`apps/core/state_manager/state_manager.py`)
- ⬜ **1.2.2.7**: CREATE FUNCTION transition_to_phase(self, new_phase: Phase) -> None: validates transition, updates current_phase, sets phase_history timestamps, calls save() (`apps/core/state_manager/state_manager.py`)

#### ⬜ Task 1.2.3: Create package init

**File**: `apps/core/state_manager/__init__.py`

**Description**: Export public API: SessionStateManager, SessionState, Phase, Status, exceptions.

**Depends On**: Tasks 1.2.2

**Actions**:
- ⬜ **1.2.3.1**: CREATE FILE apps/core/state_manager/__init__.py (`apps/core/state_manager/__init__.py`)
- ⬜ **1.2.3.2**: ADD imports and __all__ exporting: SessionStateManager, SessionState, Phase, Status, SessionType, InvalidPhaseTransitionError, SessionNotFoundError, StateValidationError (`apps/core/state_manager/__init__.py`)

### ⬜ Task Group 1.3: Add Unit Tests

**Objective**: Write pytest tests verifying: load/save round-trip, valid transitions succeed, invalid transitions raise exceptions.

#### ⬜ Task 1.3.1: Create test fixtures

**File**: `apps/core/state_manager/tests/conftest.py`

**Description**: Create pytest fixtures for temporary session directories with valid state.json files.

**Context to Load**:
- `apps/core/state_manager/models.py` (lines all) - Model structure for creating valid test data
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/state.json` (lines all) - Example of real state.json structure

**Depends On**: Tasks 1.2.3

**Actions**:
- ⬜ **1.3.1.1**: CREATE FILE apps/core/state_manager/tests/__init__.py (`apps/core/state_manager/tests/__init__.py`)
- ⬜ **1.3.1.2**: CREATE FILE apps/core/state_manager/tests/conftest.py (`apps/core/state_manager/tests/conftest.py`)
- ⬜ **1.3.1.3**: CREATE FUNCTION fixture sample_state_json() -> dict: returns valid state.json v2 structure with all required fields (`apps/core/state_manager/tests/conftest.py`)
- ⬜ **1.3.1.4**: CREATE FUNCTION fixture temp_session_dir(tmp_path, sample_state_json) -> Path: creates temp dir with state.json, returns path (`apps/core/state_manager/tests/conftest.py`)

#### ⬜ Task 1.3.2: Write StateManager tests

**File**: `apps/core/state_manager/tests/test_state_manager.py`

**Description**: Test load/save round-trip, valid phase transitions, and invalid transition rejection.

**Context to Load**:
- `apps/core/state_manager/state_manager.py` (lines all) - StateManager implementation to test
- `apps/core/state_manager/tests/conftest.py` (lines all) - Available fixtures

**Depends On**: Tasks 1.3.1

**Actions**:
- ⬜ **1.3.2.1**: CREATE FILE apps/core/state_manager/tests/test_state_manager.py (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.2**: TEST test_load_returns_session_state: ASSERT manager.load() returns SessionState instance with correct session_id (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.3**: TEST test_load_missing_file_raises: ASSERT SessionNotFoundError raised when state.json doesn't exist (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.4**: TEST test_save_updates_file: modify state, call save(), re-read file, ASSERT changes persisted (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.5**: TEST test_transition_spec_to_plan_succeeds: start at spec phase, call transition_to_phase(plan), ASSERT current_phase is plan (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.6**: TEST test_transition_spec_to_build_fails: start at spec phase, call transition_to_phase(build), ASSERT InvalidPhaseTransitionError raised (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **1.3.2.7**: TEST test_transition_updates_phase_history: transition spec→plan, ASSERT phase_history.spec_completed_at is set, phase_history.plan_started_at is set (`apps/core/state_manager/tests/test_state_manager.py`)

---

## ⬜ Checkpoint 2: SDK MCP Server for State Transitions

**Goal**: Create an in-process SDK MCP server that exposes StateManager operations as tools. Backend agents using the Claude Agent SDK will connect to this server via the mcpServers option.

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/state_manager/state_manager.py` | 📄 exists | StateManager with phase transition (from CP1) |
| After | `apps/core/mcp_tools/__init__.py` | ✨ new | MCP tools package init |
| After | `apps/core/mcp_tools/session_tools.py` | ✨ new | Session state MCP tool implementations |
| After | `apps/core/mcp_tools/server.py` | ✨ new | SDK MCP server that registers session tools |
| After | `apps/core/agent/session_agent.py` | ✨ new | Example agent using session MCP tools via SDK |

**Projected Structure**:
```
apps/core/
├── state_manager/
├── mcp_tools/  ← NEW
│   ├── __init__.py
│   ├── session_tools.py
│   └── server.py
└── agent/  ← NEW
    └── session_agent.py
```

### Testing Strategy

**Approach**: SDK integration test + example agent verification

**Verification Steps**:
- [ ] `Run example agent, verify MCP tools connected via SDK`
- [ ] `Agent successfully calls session_transition_phase`
- [ ] `state.json updated after tool execution`

### ⬜ Task Group 2.1: Create SDK MCP Tool Implementations

**Objective**: Implement session state tools as Python functions that can be registered with the Claude Agent SDK. These run in-process, not as a separate server.

#### ⬜ Task 2.1.1: Install Claude Agent SDK

**File**: `apps/core/pyproject.toml`

**Description**: Add claude-agent-sdk package to dependencies.

**Context to Load**:
- `apps/core/pyproject.toml` (lines all) - Existing dependencies to extend

**Actions**:
- ⬜ **2.1.1.1**: UPDATE apps/core/pyproject.toml: ADD dependency 'claude-agent-sdk' to project.dependencies (`apps/core/pyproject.toml`)

#### ⬜ Task 2.1.2: Create session MCP tool functions

**File**: `apps/core/mcp_tools/session_tools.py`

**Description**: Implement tool functions that wrap StateManager operations. Each function takes session_dir and parameters, returns result dict.

**Context to Load**:
- `apps/core/state_manager/state_manager.py` (lines all) - StateManager API to wrap

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.1.2.1**: CREATE FILE apps/core/mcp_tools/__init__.py (`apps/core/mcp_tools/__init__.py`)
- ⬜ **2.1.2.2**: CREATE FILE apps/core/mcp_tools/session_tools.py (`apps/core/mcp_tools/session_tools.py`)
- ⬜ **2.1.2.3**: CREATE FUNCTION session_transition_phase(session_dir: str, new_phase: str) -> dict: instantiate StateManager, call load(), transition_to_phase(), return {success: True, current_phase: ...} (`apps/core/mcp_tools/session_tools.py`)

### ⬜ Task Group 2.2: Create SDK MCP Server

**Objective**: Create an MCP server module that registers session tools. This server runs in-process with the agent.

#### ⬜ Task 2.2.1: Create SDK MCP server module

**File**: `apps/core/mcp_tools/server.py`

**Description**: Create MCP server that can be passed to ClaudeAgentOptions.mcp_servers. Uses SDK MCP server pattern for in-process tools.

**Context to Load**:
- `apps/core/mcp_tools/session_tools.py` (lines all) - Tools to register

**Depends On**: Tasks 2.1.2

**Actions**:
- ⬜ **2.2.1.1**: CREATE FILE apps/core/mcp_tools/server.py: create MCP server class/factory that registers session tools (`apps/core/mcp_tools/server.py`)
- ⬜ **2.2.1.2**: CREATE FUNCTION get_session_mcp_server() -> dict: returns MCP server config dict for use in ClaudeAgentOptions.mcp_servers (`apps/core/mcp_tools/server.py`)

### ⬜ Task Group 2.3: Create Example Agent Integration

**Objective**: Create an example agent that uses the session MCP tools via the Claude Agent SDK query() function.

#### ⬜ Task 2.3.1: Create session agent example

**File**: `apps/core/agent/session_agent.py`

**Description**: Example script showing how to use session MCP tools with the Claude Agent SDK.

**Context to Load**:
- `apps/core/mcp_tools/server.py` (lines all) - MCP server to use

**Depends On**: Tasks 2.2.1

**Actions**:
- ⬜ **2.3.1.1**: CREATE FILE apps/core/agent/__init__.py (`apps/core/agent/__init__.py`)
- ⬜ **2.3.1.2**: CREATE FILE apps/core/agent/session_agent.py: example using query() with mcp_servers={session_state: get_session_mcp_server()}, allowed_tools=['mcp__session_state__*'] (`apps/core/agent/session_agent.py`)

#### ⬜ Task 2.3.2: Test SDK agent integration

**File**: `None`

**Description**: Run the example agent to verify MCP tools work end-to-end via SDK.

**Depends On**: Tasks 2.3.1

**Actions**:
- ⬜ **2.3.2.1**: VERIFY: Run session_agent.py, verify agent can call session_transition_phase tool
- ⬜ **2.3.2.2**: VERIFY: Check state.json updated after agent tool call

---

## ⬜ Checkpoint 3: Complete StateManager Operations

**Goal**: Add remaining StateManager methods: checkpoint tracking, commit tracking, status updates, git context. Full state.json v2 coverage

**Prerequisites**: Checkpoints 1

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/state_manager/state_manager.py` | 📄 exists | StateManager with load/save/transition (from CP1) |
| After | `apps/core/state_manager/state_manager.py` | 📝 modified | StateManager with full API coverage |

**Projected Structure**:
```
apps/core/state_manager/ (same structure, extended functionality)
```

### Testing Strategy

**Approach**: Unit tests for each StateManager method

**Verification Steps**:
- [ ] `pytest apps/core/state_manager/tests/ -v`
- [ ] `All new methods have corresponding test coverage`

### ⬜ Task Group 3.1: Add Checkpoint Tracking Methods

**Objective**: Implement start_checkpoint(), complete_checkpoint(), and init_build_progress() for tracking build phase progress.

#### ⬜ Task 3.1.1: Add checkpoint methods to StateManager

**File**: `apps/core/state_manager/state_manager.py`

**Description**: Add methods to track checkpoint start/completion. Updates build_progress in state.json.

**Context to Load**:
- `apps/core/state_manager/state_manager.py` (lines all) - Existing StateManager to extend
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 278-283) - build_progress schema

**Actions**:
- ⬜ **3.1.1.1**: CREATE FUNCTION init_build_progress(self, checkpoints_total: int) -> None: initialize build_progress with total count, empty completed list, current=1 (`apps/core/state_manager/state_manager.py`)
- ⬜ **3.1.1.2**: CREATE FUNCTION start_checkpoint(self, checkpoint_id: int) -> None: set current_checkpoint, validate checkpoint_id is valid (`apps/core/state_manager/state_manager.py`)
- ⬜ **3.1.1.3**: CREATE FUNCTION complete_checkpoint(self, checkpoint_id: int) -> None: add to checkpoints_completed, increment current_checkpoint, save() (`apps/core/state_manager/state_manager.py`)

#### ⬜ Task 3.1.2: Add checkpoint tests

**File**: `apps/core/state_manager/tests/test_state_manager.py`

**Description**: Test checkpoint tracking methods.

**Context to Load**:
- `apps/core/state_manager/tests/test_state_manager.py` (lines all) - Existing tests to extend

**Depends On**: Tasks 3.1.1

**Actions**:
- ⬜ **3.1.2.1**: TEST test_init_build_progress: ASSERT build_progress initialized with correct total and empty completed (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **3.1.2.2**: TEST test_complete_checkpoint: ASSERT checkpoint added to completed list (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **3.1.2.3**: TEST test_complete_invalid_checkpoint_fails: ASSERT error when completing checkpoint out of order (`apps/core/state_manager/tests/test_state_manager.py`)

### ⬜ Task Group 3.2: Add Commit Tracking Methods

**Objective**: Implement add_commit() for recording git commits during build phase.

#### ⬜ Task 3.2.1: Add commit tracking method

**File**: `apps/core/state_manager/state_manager.py`

**Description**: Add method to record commits with SHA, message, and checkpoint association.

**Context to Load**:
- `apps/core/state_manager/state_manager.py` (lines all) - Existing StateManager
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 292-300) - commits schema

**Actions**:
- ⬜ **3.2.1.1**: CREATE FUNCTION add_commit(self, sha: str, message: str, checkpoint: int | None = None) -> None: append Commit to commits list, save() (`apps/core/state_manager/state_manager.py`)

#### ⬜ Task 3.2.2: Add commit tests

**File**: `apps/core/state_manager/tests/test_state_manager.py`

**Description**: Test commit tracking.

**Context to Load**:
- `apps/core/state_manager/tests/test_state_manager.py` (lines all) - Existing tests

**Depends On**: Tasks 3.2.1

**Actions**:
- ⬜ **3.2.2.1**: TEST test_add_commit: ASSERT commit appended with sha, message, checkpoint, created_at (`apps/core/state_manager/tests/test_state_manager.py`)

### ⬜ Task Group 3.3: Add Status and Git Context Methods

**Objective**: Implement set_status() and git context methods.

#### ⬜ Task 3.3.1: Add status and git methods

**File**: `apps/core/state_manager/state_manager.py`

**Description**: Add methods for setting session status (active/paused/complete/failed) and git context (branch/worktree).

**Context to Load**:
- `apps/core/state_manager/state_manager.py` (lines all) - Existing StateManager
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 285-290) - git schema

**Actions**:
- ⬜ **3.3.1.1**: CREATE FUNCTION set_status(self, status: Status) -> None: update status field, save() (`apps/core/state_manager/state_manager.py`)
- ⬜ **3.3.1.2**: CREATE FUNCTION set_git_branch(self, branch: str) -> None: update git.branch, save() (`apps/core/state_manager/state_manager.py`)
- ⬜ **3.3.1.3**: CREATE FUNCTION set_git_worktree(self, worktree: str | None) -> None: update git.worktree, save() (`apps/core/state_manager/state_manager.py`)

#### ⬜ Task 3.3.2: Add status and git tests

**File**: `apps/core/state_manager/tests/test_state_manager.py`

**Description**: Test status and git context methods.

**Context to Load**:
- `apps/core/state_manager/tests/test_state_manager.py` (lines all) - Existing tests

**Depends On**: Tasks 3.3.1

**Actions**:
- ⬜ **3.3.2.1**: TEST test_set_status: ASSERT status updated correctly (`apps/core/state_manager/tests/test_state_manager.py`)
- ⬜ **3.3.2.2**: TEST test_set_git_branch: ASSERT git.branch updated (`apps/core/state_manager/tests/test_state_manager.py`)

---

## ⬜ Checkpoint 4: Complete SDK MCP Tool Suite

**Goal**: Expose all StateManager operations as SDK MCP tools. Full toolset: phase transitions, checkpoint progress, commits, status, git context - all usable via Claude Agent SDK.

**Prerequisites**: Checkpoints 2, 3

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/mcp_tools/session_tools.py` | 📄 exists | Session tools with transition (from CP2) |
| Before | `apps/core/state_manager/state_manager.py` | 📄 exists | Full StateManager API (from CP3) |
| After | `apps/core/mcp_tools/session_tools.py` | 📝 modified | Full suite of session MCP tools |

**Projected Structure**:
```
apps/core/mcp_tools/ (same structure, more tools)
```

### Testing Strategy

**Approach**: SDK integration test + example agent verification

**Verification Steps**:
- [ ] `Run example agent with full tool suite`
- [ ] `All 7 session tools callable via SDK`
- [ ] `state.json correctly updated by each tool`

### ⬜ Task Group 4.1: Add Remaining SDK MCP Tools

**Objective**: Add checkpoint, commit, status, and git tools to session_tools.py for use via Claude Agent SDK.

#### ⬜ Task 4.1.1: Add checkpoint SDK tools

**File**: `apps/core/mcp_tools/session_tools.py`

**Description**: Add tool functions for checkpoint operations that wrap StateManager methods.

**Context to Load**:
- `apps/core/mcp_tools/session_tools.py` (lines all) - Existing tools
- `apps/core/state_manager/state_manager.py` (lines all) - Checkpoint methods to wrap

**Actions**:
- ⬜ **4.1.1.1**: CREATE FUNCTION session_init_build(session_dir: str, checkpoints_total: int) -> dict: wrap StateManager.init_build_progress() (`apps/core/mcp_tools/session_tools.py`)
- ⬜ **4.1.1.2**: CREATE FUNCTION session_start_checkpoint(session_dir: str, checkpoint_id: int) -> dict: wrap StateManager.start_checkpoint() (`apps/core/mcp_tools/session_tools.py`)
- ⬜ **4.1.1.3**: CREATE FUNCTION session_complete_checkpoint(session_dir: str, checkpoint_id: int) -> dict: wrap StateManager.complete_checkpoint() (`apps/core/mcp_tools/session_tools.py`)

#### ⬜ Task 4.1.2: Add commit SDK tool

**File**: `apps/core/mcp_tools/session_tools.py`

**Description**: Add tool function for recording commits.

**Context to Load**:
- `apps/core/mcp_tools/session_tools.py` (lines all) - Existing tools

**Actions**:
- ⬜ **4.1.2.1**: CREATE FUNCTION session_add_commit(session_dir: str, sha: str, message: str, checkpoint: int | None = None) -> dict: wrap StateManager.add_commit() (`apps/core/mcp_tools/session_tools.py`)

#### ⬜ Task 4.1.3: Add status and git SDK tools

**File**: `apps/core/mcp_tools/session_tools.py`

**Description**: Add tool functions for status and git context updates.

**Context to Load**:
- `apps/core/mcp_tools/session_tools.py` (lines all) - Existing tools

**Actions**:
- ⬜ **4.1.3.1**: CREATE FUNCTION session_set_status(session_dir: str, status: str) -> dict: wrap StateManager.set_status() (`apps/core/mcp_tools/session_tools.py`)
- ⬜ **4.1.3.2**: CREATE FUNCTION session_set_git(session_dir: str, branch: str | None = None, worktree: str | None = None) -> dict: wrap StateManager.set_git_branch/worktree() (`apps/core/mcp_tools/session_tools.py`)

#### ⬜ Task 4.1.4: Update MCP server registration

**File**: `apps/core/mcp_tools/server.py`

**Description**: Register all new tools in the MCP server.

**Context to Load**:
- `apps/core/mcp_tools/server.py` (lines all) - Existing server
- `apps/core/mcp_tools/session_tools.py` (lines all) - New tools to register

**Depends On**: Tasks 4.1.1, 4.1.2, 4.1.3

**Actions**:
- ⬜ **4.1.4.1**: UPDATE server registration to include all session tools: transition, init_build, start_checkpoint, complete_checkpoint, add_commit, set_status, set_git (`apps/core/mcp_tools/server.py`)

### ⬜ Task Group 4.2: Verify Full SDK Tool Suite

**Objective**: Test all MCP tools work end-to-end via Claude Agent SDK.

#### ⬜ Task 4.2.1: Update example agent for full verification

**File**: `apps/core/agent/session_agent.py`

**Description**: Extend example agent to test all session tools.

**Context to Load**:
- `apps/core/agent/session_agent.py` (lines all) - Existing example agent

**Depends On**: Tasks 4.1.4

**Actions**:
- ⬜ **4.2.1.1**: UPDATE example to test all 7 session tools: transition, init_build, start_checkpoint, complete_checkpoint, add_commit, set_status, set_git (`apps/core/agent/session_agent.py`)

#### ⬜ Task 4.2.2: Run full verification tests

**File**: `None`

**Description**: Test full tool suite via SDK agent.

**Depends On**: Tasks 4.2.1

**Actions**:
- ⬜ **4.2.2.1**: VERIFY: Run full agent example, all 7 tools callable
- ⬜ **4.2.2.2**: VERIFY: state.json reflects all tool operations

---

## ⬜ Checkpoint 5: Update Skill Prompts

**Goal**: Replace direct state.json editing instructions with MCP tool calls in all session skill prompts. Migrate goals/questions/decisions to spec.md

**Prerequisites**: Checkpoints 4

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/spec/OVERVIEW.md` | 📄 exists | Spec skill - currently writes to state.json directly |
| Before | `.claude/skills/session/plan/OVERVIEW.md` | 📄 exists | Plan skill - updates plan_state in state.json |
| Before | `.claude/skills/session/build/OVERVIEW.md` | 📄 exists | Build skill - updates checkpoints and commits |
| Before | `.claude/skills/session/SKILL.md` | 📄 exists | Main session skill overview |
| After | `.claude/skills/session/spec/OVERVIEW.md` | 📝 modified | Uses MCP tools for phase transitions |
| After | `.claude/skills/session/plan/OVERVIEW.md` | 📝 modified | Uses MCP tools for plan_state updates |
| After | `.claude/skills/session/build/OVERVIEW.md` | 📝 modified | Uses MCP tools for checkpoint/commit tracking |
| After | `.claude/skills/session/SKILL.md` | 📝 modified | Documents MCP tool usage |

**Projected Structure**:
```
.claude/skills/session/ (same structure, updated content)
```

### Testing Strategy

**Approach**: Prompt review + end-to-end session test

**Verification Steps**:
- [ ] `Grep for 'state.json' in skill prompts - should only reference reading, not direct editing`
- [ ] `Run /session:spec on test session, verify MCP tools called for transitions`

### ⬜ Task Group 5.1: Update Spec Skill

**Objective**: Replace state.json editing with MCP tool calls in spec skill. Move goals/questions/decisions sections to spec.md guidance.

#### ⬜ Task 5.1.1: Update spec OVERVIEW.md

**File**: `.claude/skills/session/spec/OVERVIEW.md`

**Description**: Remove instructions to update state.json goals/questions/decisions. Add instruction to use session_transition_phase MCP tool when finalizing spec.

**Context to Load**:
- `.claude/skills/session/spec/OVERVIEW.md` (lines all) - Current spec skill instructions
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 329-358) - New spec.md sections for goals/questions/decisions

**Actions**:
- ⬜ **5.1.1.1**: REMOVE instructions to update state.json goals, open_questions, key_decisions fields (`.claude/skills/session/spec/OVERVIEW.md`)
- ⬜ **5.1.1.2**: ADD instruction to write goals/questions/decisions to spec.md sections instead (`.claude/skills/session/spec/OVERVIEW.md`)
- ⬜ **5.1.1.3**: ADD instruction: when finalizing spec, use mcp__session_state__session_transition_phase tool with new_phase='plan' (available via SDK MCP server) (`.claude/skills/session/spec/OVERVIEW.md`)

### ⬜ Task Group 5.2: Update Plan Skill

**Objective**: Replace plan_state updates with MCP tool calls.

#### ⬜ Task 5.2.1: Update plan OVERVIEW.md

**File**: `.claude/skills/session/plan/OVERVIEW.md`

**Description**: Replace direct state.json updates with MCP tool calls for plan phase transitions.

**Context to Load**:
- `.claude/skills/session/plan/OVERVIEW.md` (lines all) - Current plan skill instructions

**Actions**:
- ⬜ **5.2.1.1**: REMOVE instructions to directly update plan_state in state.json (`.claude/skills/session/plan/OVERVIEW.md`)
- ⬜ **5.2.1.2**: ADD instruction: when finalizing plan, use mcp__session_state__session_transition_phase with new_phase='build' (`.claude/skills/session/plan/OVERVIEW.md`)
- ⬜ **5.2.1.3**: ADD instruction: use mcp__session_state__session_init_build to set checkpoints_total (`.claude/skills/session/plan/OVERVIEW.md`)

### ⬜ Task Group 5.3: Update Build Skill

**Objective**: Replace checkpoint and commit tracking with MCP tool calls.

#### ⬜ Task 5.3.1: Update build OVERVIEW.md

**File**: `.claude/skills/session/build/OVERVIEW.md`

**Description**: Replace direct state.json updates with MCP tool calls for checkpoint completion and commit tracking.

**Context to Load**:
- `.claude/skills/session/build/OVERVIEW.md` (lines all) - Current build skill instructions

**Actions**:
- ⬜ **5.3.1.1**: REMOVE instructions to directly update checkpoints_completed in state.json (`.claude/skills/session/build/OVERVIEW.md`)
- ⬜ **5.3.1.2**: ADD instruction: after checkpoint commit, use mcp__session_state__session_complete_checkpoint tool (`.claude/skills/session/build/OVERVIEW.md`)
- ⬜ **5.3.1.3**: ADD instruction: after git commit, use mcp__session_state__session_add_commit tool with sha and message (`.claude/skills/session/build/OVERVIEW.md`)
- ⬜ **5.3.1.4**: ADD instruction: when build complete, use mcp__session_state__session_transition_phase with new_phase='docs' or 'complete' (`.claude/skills/session/build/OVERVIEW.md`)

### ⬜ Task Group 5.4: Update Main Session Skill

**Objective**: Document MCP tools in main SKILL.md overview.

#### ⬜ Task 5.4.1: Update SKILL.md

**File**: `.claude/skills/session/SKILL.md`

**Description**: Add section documenting available MCP tools and when to use them.

**Context to Load**:
- `.claude/skills/session/SKILL.md` (lines all) - Current session skill overview

**Depends On**: Tasks 5.1.1, 5.2.1, 5.3.1

**Actions**:
- ⬜ **5.4.1.1**: ADD section 'SDK MCP Tools for State Updates' listing all mcp__session_state__* tools and their purposes (`.claude/skills/session/SKILL.md`)
- ⬜ **5.4.1.2**: UPDATE overview to reference state.json v2 schema and SDK MCP tool usage (`.claude/skills/session/SKILL.md`)
- ⬜ **5.4.1.3**: ADD note: these tools are available when agent runs via Claude Agent SDK with session_state MCP server configured (`.claude/skills/session/SKILL.md`)

---

## ⬜ Checkpoint 6: Templates & Init Script Update

**Goal**: Update state.json template to v2 schema, update spec.md template with Goals/Questions/Decisions sections, update init-session.py

**Prerequisites**: Checkpoints 5

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `.claude/skills/session/spec/templates/state.json` | 📄 exists | Current v1 state.json template |
| Before | `.claude/skills/session/spec/templates/spec.md` | 📄 exists | Current spec.md template (if exists) |
| Before | `.claude/skills/session/scripts/init-session.py` | 📄 exists | Session initialization script |
| After | `.claude/skills/session/spec/templates/state.json` | 📝 modified | v2 state.json template |
| After | `.claude/skills/session/spec/templates/spec.md` | 📝 modified | Updated with Goals/Questions/Decisions sections |
| After | `.claude/skills/session/scripts/init-session.py` | 📝 modified | Creates v2 state.json |

**Projected Structure**:
```
.claude/skills/session/ (same structure, updated templates)
```

### Testing Strategy

**Approach**: Create new session and verify structure

**Verification Steps**:
- [ ] `Run init-session.py, verify state.json matches v2 schema`
- [ ] `Verify spec.md has Goals/Questions/Decisions sections`
- [ ] `StateManager.load() succeeds on newly created session`

### ⬜ Task Group 6.1: Update state.json Template

**Objective**: Replace v1 template with v2 schema matching the spec.

#### ⬜ Task 6.1.1: Update state.json template

**File**: `.claude/skills/session/spec/templates/state.json`

**Description**: Replace template with v2 schema: remove goals/questions/decisions, add phase_history, build_progress, git, commits, artifacts.

**Context to Load**:
- `.claude/skills/session/spec/templates/state.json` (lines all) - Current template to replace
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 246-327) - v2 schema definition

**Actions**:
- ⬜ **6.1.1.1**: REPLACE entire state.json template with v2 schema (`.claude/skills/session/spec/templates/state.json`)
- ⬜ **6.1.1.2**: REMOVE goals, open_questions, key_decisions fields (`.claude/skills/session/spec/templates/state.json`)
- ⬜ **6.1.1.3**: ADD phase_history object with null timestamps (`.claude/skills/session/spec/templates/state.json`)
- ⬜ **6.1.1.4**: ADD build_progress object with null values (`.claude/skills/session/spec/templates/state.json`)
- ⬜ **6.1.1.5**: ADD git object with null branch/worktree/base_branch (`.claude/skills/session/spec/templates/state.json`)
- ⬜ **6.1.1.6**: ADD artifacts object with default paths (`.claude/skills/session/spec/templates/state.json`)

### ⬜ Task Group 6.2: Update spec.md Template

**Objective**: Add Goals, Open Questions, Key Decisions sections to spec.md template.

#### ⬜ Task 6.2.1: Update spec.md template

**File**: `.claude/skills/session/spec/templates/spec.md`

**Description**: Add structured sections for Goals (High/Mid/Low), Open Questions (checkbox list), Key Decisions (with rationale).

**Context to Load**:
- `.claude/skills/session/spec/templates/spec.md` (lines all) - Current template (if exists)
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 337-358) - Example sections structure

**Actions**:
- ⬜ **6.2.1.1**: ADD section '## Goals' with subsections High-Level, Mid-Level, Implementation Goals (`.claude/skills/session/spec/templates/spec.md`)
- ⬜ **6.2.1.2**: ADD section '## Open Questions' with checkbox list format (`.claude/skills/session/spec/templates/spec.md`)
- ⬜ **6.2.1.3**: ADD section '## Key Decisions' with decision/rationale/date format (`.claude/skills/session/spec/templates/spec.md`)

### ⬜ Task Group 6.3: Update Init Script

**Objective**: Update init-session.py to create v2 state.json structure.

#### ⬜ Task 6.3.1: Update init-session.py

**File**: `.claude/skills/session/scripts/init-session.py`

**Description**: Update script to generate v2 state.json with new schema fields.

**Context to Load**:
- `.claude/skills/session/scripts/init-session.py` (lines all) - Current init script
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 246-327) - v2 schema to generate

**Depends On**: Tasks 6.1.1

**Actions**:
- ⬜ **6.3.1.1**: UPDATE state.json generation to match v2 schema (`.claude/skills/session/scripts/init-session.py`)
- ⬜ **6.3.1.2**: ADD phase_history initialization with spec_started_at set to creation time (`.claude/skills/session/scripts/init-session.py`)
- ⬜ **6.3.1.3**: ADD build_progress initialization with null values (`.claude/skills/session/scripts/init-session.py`)
- ⬜ **6.3.1.4**: ADD git initialization (detect current branch if in git repo) (`.claude/skills/session/scripts/init-session.py`)
- ⬜ **6.3.1.5**: ADD artifacts initialization with default paths (`.claude/skills/session/scripts/init-session.py`)

#### ⬜ Task 6.3.2: Test init script

**File**: `None`

**Description**: Verify init-session.py creates correct v2 structure.

**Depends On**: Tasks 6.3.1

**Actions**:
- ⬜ **6.3.2.1**: VERIFY: Run init-session.py, check state.json matches v2 schema
- ⬜ **6.3.2.2**: VERIFY: Created state.json can be loaded by StateManager

---

## ⬜ Checkpoint 7: Database Onboarding & Sync

**Goal**: Implement filesystem→database sync: onboard existing sessions from state.json v2, query sessions by project. Database becomes reconstructable index from filesystem.

**Prerequisites**: Checkpoints 6

### File Context

| State | File | Status | Description |
|-------|------|--------|-------------|
| Before | `apps/core/session_db/crud.py` | 📄 exists | Existing CRUD operations |
| Before | `apps/core/session_db/models.py` | 📄 exists | SQLModel database models |
| After | `apps/core/session_db/sync.py` | ✨ new | Sync functions for filesystem→database |
| After | `apps/core/session_db/models.py` | 📝 modified | Updated to match state.json v2 fields |
| After | `apps/core/session_db/tests/test_sync.py` | ✨ new | Tests for sync functions |

**Projected Structure**:
```
apps/core/session_db/
├── models.py
├── crud.py
├── sync.py  ← NEW
└── tests/
    └── test_sync.py  ← NEW
```

### Testing Strategy

**Approach**: Integration tests for sync functions

**Verification Steps**:
- [ ] `pytest apps/core/session_db/tests/test_sync.py -v`
- [ ] `Manual: Onboard real project, verify sessions appear in database`
- [ ] `Query sessions by project_id, verify matches filesystem`

### ⬜ Task Group 7.1: Update Database Models for state.json v2

**Objective**: Ensure database Session model has fields matching state.json v2 schema for proper sync.

#### ⬜ Task 7.1.1: Update Session model fields

**File**: `apps/core/session_db/models.py`

**Description**: Add/update fields to match state.json v2: phase_history, build_progress, git context, artifacts.

**Context to Load**:
- `apps/core/session_db/models.py` (lines all) - Current Session model
- `agents/sessions/2026-02-14_claude-code-agent-sdk-integration/spec.md` (lines 246-327) - state.json v2 schema

**Actions**:
- ⬜ **7.1.1.1**: UPDATE Session model: ensure fields match v2 schema - phase_history, build_progress as JSON columns (`apps/core/session_db/models.py`)
- ⬜ **7.1.1.2**: ADD git_branch, git_worktree, git_base_branch fields if not present (`apps/core/session_db/models.py`)
- ⬜ **7.1.1.3**: REMOVE any fields that don't exist in v2 (goals, open_questions, key_decisions - now in spec.md) (`apps/core/session_db/models.py`)

### ⬜ Task Group 7.2: Create Sync Functions

**Objective**: Implement sync_session_from_filesystem() and onboard_project_sessions() functions.

#### ⬜ Task 7.2.1: Create sync module

**File**: `apps/core/session_db/sync.py`

**Description**: Implement functions to read state.json v2 and upsert to database.

**Context to Load**:
- `apps/core/state_manager/models.py` (lines all) - SessionState Pydantic model to load
- `apps/core/session_db/models.py` (lines all) - Session SQLModel to upsert
- `docs/.drafts/agent-architecture/85-session-data-architecture.md` (lines 255-305) - Sync function design

**Depends On**: Tasks 7.1.1

**Actions**:
- ⬜ **7.2.1.1**: CREATE FILE apps/core/session_db/sync.py (`apps/core/session_db/sync.py`)
- ⬜ **7.2.1.2**: CREATE FUNCTION sync_session_from_filesystem(working_dir: str, session_slug: str, project_id: UUID | None) -> Session: read state.json, map to Session, upsert (`apps/core/session_db/sync.py`)
- ⬜ **7.2.1.3**: CREATE FUNCTION onboard_project_sessions(working_dir: str, project_id: UUID) -> list[Session]: scan agents/sessions/*, sync each (`apps/core/session_db/sync.py`)
- ⬜ **7.2.1.4**: CREATE FUNCTION map_state_to_session(state: SessionState, project_id: UUID | None) -> SessionCreate: map v2 fields to database DTO (`apps/core/session_db/sync.py`)

### ⬜ Task Group 7.3: Add Sync Tests

**Objective**: Test sync functions with real session directories.

#### ⬜ Task 7.3.1: Create sync tests

**File**: `apps/core/session_db/tests/test_sync.py`

**Description**: Test sync_session_from_filesystem and onboard_project_sessions.

**Context to Load**:
- `apps/core/session_db/sync.py` (lines all) - Functions to test

**Depends On**: Tasks 7.2.1

**Actions**:
- ⬜ **7.3.1.1**: CREATE FILE apps/core/session_db/tests/test_sync.py (`apps/core/session_db/tests/test_sync.py`)
- ⬜ **7.3.1.2**: TEST test_sync_creates_session: sync from temp dir with state.json, ASSERT session created in DB (`apps/core/session_db/tests/test_sync.py`)
- ⬜ **7.3.1.3**: TEST test_sync_updates_existing: sync twice, ASSERT session updated not duplicated (`apps/core/session_db/tests/test_sync.py`)
- ⬜ **7.3.1.4**: TEST test_onboard_scans_sessions: create temp dir with 3 sessions, ASSERT all 3 synced (`apps/core/session_db/tests/test_sync.py`)

---

---
*Auto-generated from plan.json on 2026-02-16 10:24*