# Intelligent Autocomplete System - Master Implementation Plan

**Version:** 2.2 - Type-Safe with Pydantic Models
**Target:** Orchestrator 3 Stream Multi-Agent System
**Estimated Time:** 8-10 hours (1-2 days)

**CRITICAL UPDATES:**
- ✅ Uses Claude Agent SDK (not raw Anthropic client)
- ✅ Uses latest Haiku model: `claude-haiku-4-5-20251001`
- ✅ Session persistence via expertise.yaml
- ✅ Both orchestrator_agent_id AND completion_agent_id tracking
- ✅ **FULL TYPE SAFETY**: Pydantic models for all expertise.yaml data
- ✅ **UNION TYPE SUPPORT**: Properly handles 'none' and 'autocomplete' completion types

---

## 📋 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [File Changes](#3-file-changes)
4. [Data Flow](#4-data-flow)
5. [Implementation Guide](#5-implementation-guide)
6. [Testing](#6-testing)
7. [Quick Reference](#7-quick-reference)
8. [Deployment](#8-deployment)

---

# 1. Executive Summary

## What We're Building

An **intelligent autocomplete system** that displays **3 context-aware completion suggestions as pills** with keyboard shortcuts (Ctrl+1/2/3) in the Orchestrator chat interface. The system learns from user behavior via `expertise.yaml` and uses **Claude Haiku** for fast, relevant suggestions.

## Key Features

✅ **Pills UI** - Visual suggestions below chat input with hotkey badges
✅ **Context-Aware** - Uses active agents, slash commands, templates, codebase structure
✅ **Smart Debouncing** - 1-second delay prevents excessive API calls
✅ **Session Management** - Per-orchestrator state with auto-reset
✅ **Keyboard Shortcuts** - Ctrl+1/2/3 for rapid acceptance
✅ **Learning System** - Tracks accepted/rejected completions in expertise.yaml
✅ **Fast Response** - Claude Haiku targets <2s response time

## System Overview

```
┌──────────────────────────────────────────┐
│         FRONTEND (Vue 3)                 │
│  Input → useAutocomplete (1s debounce)  │
│           ↓                               │
│  Pills: [Ctrl+1] [Ctrl+2] [Ctrl+3]     │
└──────────────────────────────────────────┘
                  ↓ HTTP
┌──────────────────────────────────────────┐
│        BACKEND (FastAPI)                 │
│  /autocomplete-generate                  │
│  /autocomplete-update                    │
│           ↓                               │
│  Service → Agent → Claude Haiku          │
│                ↓                          │
│           expertise.yaml                 │
└──────────────────────────────────────────┘
```

---

# 2. Architecture Overview

## Complete System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                            │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  OrchestratorChat.vue                                │    │
│  │                                                        │    │
│  │  Input: "create a new "                              │    │
│  │         ↓ @input (debounced 1s)                      │    │
│  │  ┌───────────────────────────────────────────┐      │    │
│  │  │ Pills (v-if="hasAutocompleteItems")      │      │    │
│  │  │ [Ctrl+1 testing] [Ctrl+2 database] ...   │      │    │
│  │  └───────────────────────────────────────────┘      │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                 FRONTEND STATE (Pinia Store)                  │
│                                                                │
│  orchestratorStore:                                           │
│    • autocompleteItems: AutocompleteItem[]                   │
│    • autocompleteLoading: boolean                            │
│    • autocompleteError: string | null                        │
│    • generateAutocomplete(input)                             │
│    • updateAutocompleteHistory(...)                          │
└───────────────────────────────────────────────────────────────┘
                            ↓ HTTP POST
┌───────────────────────────────────────────────────────────────┐
│                     API ENDPOINTS                              │
│                                                                │
│  POST /autocomplete-generate                                  │
│    → Request: { user_input, orchestrator_agent_id }          │
│    → Response: { autocompletes: [], total_items, ... }       │
│                                                                │
│  POST /autocomplete-update                                    │
│    → Request: { completion_type, user_input_on_enter, ... }  │
│    → Response: { status: "success" }                         │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                  BACKEND SERVICES                              │
│                                                                │
│  AutocompleteService                                          │
│    • generate_autocomplete(user_input, orch_id)              │
│    • update_completion_history(...)                          │
│         ↓                                                      │
│  AutocompleteAgent (Claude Agent SDK)                        │
│    • Load expertise.yaml                                      │
│    • Check orchestrator_agent_id match                       │
│    • Reuse OR reset session based on ID match               │
│    • Replace variables (7 total)                             │
│    • Call Claude Agent SDK (Haiku 4.5)                       │
│    • Parse JSON response                                      │
│    • Save session_id + data to expertise.yaml               │
└───────────────────────────────────────────────────────────────┘
                ↓                           ↓
┌──────────────────────┐      ┌─────────────────────────────────┐
│  Claude Agent SDK    │      │  expertise.yaml                 │
│  (Haiku 4.5)         │      │  • orchestrator_agent_id        │
│                      │      │  • completion_agent_id (NEW)    │
│  System Prompt       │      │  • previous_completions[]       │
│  User Prompt         │      │    (union type: none | auto)    │
│  Response: JSON      │      │                                 │
│  Session: Persisted  │      │  Session Management:            │
└──────────────────────┘      │  • Per-orchestrator session     │
                              │  • Session reuse via SDK        │
                              │  • Reset on orchestrator change │
                              └─────────────────────────────────┘
```

## Component Relationships

```
OrchestratorChat.vue
    └─► uses: useAutocomplete.ts
            └─► uses: orchestratorStore.ts
                    └─► uses: autocompleteService.ts (API client)
                            └─► calls: Backend API

main.py (FastAPI)
    ├─► POST /autocomplete-generate
    └─► POST /autocomplete-update
            └─► AutocompleteService
                    └─► AutocompleteAgent (Claude Agent SDK)
                            ├─► Claude Agent SDK (Haiku 4.5)
                            └─► expertise.yaml (session + completions)
```

---

# 3. File Changes

## Files to Modify (4 files)

### Backend

1. **`backend/main.py`**
   - Add autocomplete imports
   - Add 2 new endpoints: `/autocomplete-generate`, `/autocomplete-update`
   - Initialize `AutocompleteService` in lifespan
   - Store service in `app.state`

### Frontend

2. **`frontend/src/types.d.ts`**
   - Add `AutocompleteItem`, `AutocompleteResponse`, request interfaces
   - Add `CompletionType` type
   - Add `PreviousCompletion` union type

3. **`frontend/src/stores/orchestratorStore.ts`**
   - Add autocomplete state (items, loading, error)
   - Add actions: `generateAutocomplete`, `updateAutocompleteHistory`, `clearAutocomplete`
   - Add computed: `hasAutocompleteItems`

4. **`frontend/src/components/OrchestratorChat.vue`**
   - Import `useAutocomplete` composable
   - Add pills UI template
   - Add keyboard event handlers (Ctrl+1/2/3)
   - Modify send handler to track completion events
   - Add CSS for pills

## New Files to Create (7 files)

### Backend

1. **`backend/modules/autocomplete_models.py`**
   - Pydantic models for requests/responses
   - Model validators

2. **`backend/modules/autocomplete_agent.py`**
   - `AutocompleteAgent` class
   - YAML I/O for expertise.yaml
   - Variable replacement (7 variables)
   - Claude Haiku integration
   - Session management

3. **`backend/modules/autocomplete_service.py`**
   - `AutocompleteService` class
   - Service layer orchestration
   - Error handling

4. **`backend/tests/test_autocomplete_agent.py`**
   - Unit tests for agent

5. **`backend/tests/test_autocomplete_endpoints.py`**
   - Integration tests for API

### Frontend

6. **`frontend/src/composables/useAutocomplete.ts`**
   - Composable with debouncing (1s)
   - Keyboard shortcut handlers
   - Pill selection state

7. **`frontend/src/services/autocompleteService.ts`**
   - API client functions
   - HTTP request/response handling

---

# 4. Data Flow

## Flow 1: Generate Autocomplete (User Typing)

```
USER types "create a new "
        ↓
OrchestratorChat @input event (debounced 1s)
        ↓
useAutocomplete.generateAutocomplete()
        ↓
orchestratorStore.generateAutocomplete()
        ↓ HTTP POST
/autocomplete-generate endpoint
        ↓
AutocompleteService.generate_autocomplete()
        ↓
AutocompleteAgent.generate_autocomplete()
        ├─► Load expertise.yaml
        ├─► Get variables (agents, commands, templates, codebase)
        ├─► Replace {{VARIABLES}} in prompts
        ├─► Call Claude Haiku
        ↓
Claude returns: { autocompletes: [{ completion, reasoning }, ...] }
        ↓
Agent parses JSON → List[AutocompleteItem]
        ↓
Service formats → AutocompleteResponse
        ↓ HTTP 200
Frontend updates store.autocompleteItems
        ↓
Pills UI renders: [Ctrl+1 testing] [Ctrl+2 database] [Ctrl+3 API]
```

## Flow 2: Accept Autocomplete (Ctrl+1)

```
USER presses Ctrl+1
        ↓
OrchestratorChat @keydown event
        ↓
useAutocomplete.handleAutocompleteKeydown()
        ↓ Detects Ctrl+1
acceptAutocomplete(0) → Get item at index 0
        ↓
Update input: "create a new " + "testing"
        ↓
Clear pills UI
        ↓
store.updateAutocompleteHistory(
    'autocomplete',
    undefined,
    'create a new ',  // user_input_before_completion
    'testing',         // autocomplete_item
    'Common pattern...' // reasoning
)
        ↓ HTTP POST
/autocomplete-update endpoint
        ↓
Agent.add_completion_event()
        ├─► Load expertise.yaml
        ├─► Append: { completion_type: "autocomplete", ..., order: N }
        ├─► Save expertise.yaml
        ↓
History updated
```

## Flow 3: Manual Send (Ignore Autocomplete)

```
USER types full message, presses Enter
        ↓
OrchestratorChat send handler
        ├─► Send message to orchestrator
        ├─► Track completion_type = "none"
        ↓
store.updateAutocompleteHistory('none', full_message)
        ↓ HTTP POST
/autocomplete-update
        ↓
Agent appends: { completion_type: "none", user_input_on_enter: "...", order: N }
        ↓
expertise.yaml updated
```

## Flow 4: Session Reset (Orchestrator Changes)

```
Backend starts with new orchestrator_id: "uuid-456"
        ↓
AutocompleteService.__init__()
        ↓
AutocompleteAgent.__init__()
        ↓
STEP 1: Load expertise.yaml FIRST
        ├─► Read orchestrator_agent_id from file: "uuid-123"
        ├─► Read completion_agent_id (session_id) from file
        ├─► Read previous_completions
        ↓
STEP 2: Check orchestrator_agent_id match
        ├─► Current: "uuid-456"
        ├─► File:    "uuid-123"
        ├─► Match? NO → Orchestrator changed!
        ↓
STEP 3: Reset session (orchestrator changed)
        ├─► Clear previous_completions: []
        ├─► Update orchestrator_agent_id: "uuid-456"
        ├─► Create NEW Claude Agent SDK client (no resume)
        ├─► Get new session_id from first SDK interaction
        ├─► Store new completion_agent_id (session_id) in expertise.yaml
        ├─► Save updated expertise.yaml
        ↓
Fresh autocomplete session with new Claude Agent SDK instance

--- OR if IDs match ---

STEP 2: Check orchestrator_agent_id match
        ├─► Current: "uuid-456"
        ├─► File:    "uuid-456"
        ├─► Match? YES → Same orchestrator!
        ↓
STEP 3: Reuse existing session
        ├─► Keep previous_completions (context preserved)
        ├─► Resume Claude Agent SDK with saved completion_agent_id
        ├─► Continue learning from previous interactions
        ↓
Existing autocomplete session resumed with full history
```

---

# 5. Implementation Guide

## 🔴 CRITICAL ARCHITECTURE NOTES

Before implementing, understand these key architectural decisions:

### 1. **Claude Agent SDK (Not Raw Anthropic Client)**
- ✅ Use `ClaudeSDKClient` from `claude_agent_sdk`
- ❌ Do NOT use `Anthropic()` client directly
- **Why:** SDK manages session persistence automatically

### 2. **Latest Haiku Model**
- ✅ Use `claude-haiku-4-5-20251001`
- ❌ Do NOT use older versions like `claude-3-haiku-20240307`
- **Why:** Latest model has better performance and features

### 3. **Dual ID Tracking**
- `orchestrator_agent_id` - Orchestrator UUID (backend provides)
- `completion_agent_id` - Claude Agent SDK session_id (captured after first interaction)
- **Both stored in expertise.yaml**

### 4. **Session Initialization Flow**
```python
# ALWAYS do this order:
1. Load expertise.yaml FIRST
2. Check orchestrator_agent_id match
3. If different → Reset (clear completions, new SDK client)
4. If same → Resume (reuse SDK session with completion_agent_id)
5. Instantiate Claude Agent SDK client
6. After first interaction → Capture and store session_id as completion_agent_id
```

### 5. **Session Resume Logic**
```python
# If completion_agent_id exists in expertise.yaml:
ClaudeAgentOptions(
    resume=completion_agent_id,  # ← Resume existing session
    ...
)

# If no completion_agent_id:
ClaudeAgentOptions(
    # No resume parameter = fresh session
    ...
)
# Then capture session_id after first response
```

### 6. **Type Safety with Pydantic Models** 🔴 NEW

**CRITICAL: All expertise.yaml data uses Pydantic models for type safety**

```python
# ✅ CORRECT: Use Pydantic model (type-safe)
expertise_data: AutocompleteExpertiseData = load_expertise()
session_id = expertise_data.completion_agent_id  # Type-checked access
completions = expertise_data.previous_completions  # List[PreviousCompletion]

# ❌ WRONG: Don't use raw dict (not type-safe)
expertise_data: dict = load_expertise()  # Bad!
session_id = expertise_data.get('completion_agent_id')  # No type checking
```

**Key Pydantic Models:**
- `AutocompleteExpertiseData` - Root model for entire expertise.yaml
- `PreviousCompletionNone` - Event when user typed manually
- `PreviousCompletionAutocomplete` - Event when user accepted autocomplete
- `PreviousCompletion` - Union type for both event types

**Benefits:**
- ✅ Compile-time type checking (with type hints)
- ✅ Runtime validation (Pydantic catches malformed YAML)
- ✅ Auto-complete in IDEs
- ✅ Self-documenting code
- ✅ Prevents typos in field names
- ✅ Handles union types correctly

---

## Phase 1: Backend (3-4 hours)

### Step 1: Create Pydantic Models

**File:** `backend/modules/autocomplete_models.py`

```python
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List, Union
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# API REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════

class AutocompleteItem(BaseModel):
    """Single autocomplete suggestion"""
    completion: str
    reasoning: str

class AutocompleteGenerateRequest(BaseModel):
    """Request to generate autocomplete suggestions"""
    user_input: str
    orchestrator_agent_id: str

class AutocompleteResponse(BaseModel):
    """Response containing autocomplete suggestions"""
    status: str = "success"
    autocompletes: List[AutocompleteItem]
    total_items: int
    orchestrator_agent_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AutocompleteUpdateRequest(BaseModel):
    """Request to update completion history"""
    orchestrator_agent_id: str
    completion_type: Literal['none', 'autocomplete']
    user_input_on_enter: Optional[str] = None
    user_input_before_completion: Optional[str] = None
    autocomplete_item: Optional[str] = None
    reasoning: Optional[str] = None

    @model_validator(mode='after')
    def validate_fields(self):
        if self.completion_type == 'none' and not self.user_input_on_enter:
            raise ValueError("user_input_on_enter required for type 'none'")
        if self.completion_type == 'autocomplete':
            if not all([self.user_input_before_completion, self.autocomplete_item, self.reasoning]):
                raise ValueError("All autocomplete fields required")
        return self

# ═══════════════════════════════════════════════════════════
# EXPERTISE.YAML STRUCTURE MODELS (Type Safety)
# ═══════════════════════════════════════════════════════════

class PreviousCompletionNone(BaseModel):
    """
    Completion event where user typed manually (didn't accept autocomplete).

    Maps to expertise.yaml structure when completion_type='none'
    """
    completion_type: Literal['none']
    user_input_on_enter: str = Field(..., description="Full user input when Enter was pressed")
    order: int = Field(..., description="Sequential order of this completion event")

    class Config:
        frozen = False  # Allow updates if needed

class PreviousCompletionAutocomplete(BaseModel):
    """
    Completion event where user accepted an autocomplete suggestion.

    Maps to expertise.yaml structure when completion_type='autocomplete'
    """
    completion_type: Literal['autocomplete']
    user_input_before_completion: str = Field(..., description="User input before autocomplete was applied")
    autocomplete_item: str = Field(..., description="The autocomplete text that was accepted")
    reasoning: str = Field(..., description="Why this autocomplete was suggested")
    order: int = Field(..., description="Sequential order of this completion event")

    class Config:
        frozen = False  # Allow updates if needed

# Union type for previous_completions list items
PreviousCompletion = Union[PreviousCompletionNone, PreviousCompletionAutocomplete]

class AutocompleteExpertiseData(BaseModel):
    """
    CRITICAL: Type-safe model for entire expertise.yaml structure.

    This model ensures type safety when loading/saving expertise.yaml.
    All access to expertise_data should go through this model.

    Fields:
        orchestrator_agent_id: Current orchestrator UUID (triggers reset if changed)
        completion_agent_id: Claude Agent SDK session_id (None until first interaction)
        previous_completions: List of completion events (union type)
    """
    orchestrator_agent_id: str = Field(..., description="Current orchestrator UUID")
    completion_agent_id: Optional[str] = Field(
        None,
        description="Claude Agent SDK session_id (captured after first interaction)"
    )
    previous_completions: List[PreviousCompletion] = Field(
        default_factory=list,
        description="History of completion events (union of 'none' and 'autocomplete' types)"
    )

    class Config:
        frozen = False  # Allow mutations during runtime

    def to_dict(self) -> dict:
        """Convert to dict for YAML serialization"""
        return self.model_dump(mode='python', exclude_none=False)

    @classmethod
    def from_dict(cls, data: dict) -> 'AutocompleteExpertiseData':
        """Load from dict (YAML data) with validation"""
        return cls(**data)
```

### Step 2: Create Autocomplete Agent

**File:** `backend/modules/autocomplete_agent.py`

```python
from pathlib import Path
from typing import List, Optional
import yaml
import json
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from .autocomplete_models import (
    AutocompleteItem,
    AutocompleteExpertiseData,
    PreviousCompletionNone,
    PreviousCompletionAutocomplete
)

class AutocompleteAgent:
    """
    Autocomplete agent using Claude Agent SDK for session persistence.

    CRITICAL:
    - Uses Claude Agent SDK (not raw Anthropic client) for session management
    - Uses Pydantic models for type-safe expertise.yaml handling
    - All expertise_data access is type-checked via AutocompleteExpertiseData
    """

    def __init__(self, orchestrator_agent_id, logger, working_dir):
        self.orchestrator_agent_id = str(orchestrator_agent_id)
        self.logger = logger
        self.working_dir = working_dir

        # Paths
        self.expertise_dir = Path(__file__).parent.parent / "prompts/experts/orch_autocomplete"
        self.expertise_yaml_path = self.expertise_dir / "expertise.yaml"
        self.system_prompt_path = self.expertise_dir / "autocomplete_expert_system_prompt.md"
        self.user_prompt_path = self.expertise_dir / "autocomplete_expert_user_prompt.md"

        # Load prompts
        self.system_prompt_template = self.system_prompt_path.read_text()
        self.user_prompt_template = self.user_prompt_path.read_text()

        # Claude Agent SDK client (initialized after expertise check)
        self.client: Optional[ClaudeSDKClient] = None

        # CRITICAL: Type-safe expertise data (Pydantic model)
        self.expertise_data: AutocompleteExpertiseData

        # Load expertise FIRST, then check if we need to reset
        self.expertise_data = self._load_or_init_expertise()

        # Initialize Claude Agent SDK with session resume if available
        self._init_claude_agent()

    def _load_or_init_expertise(self) -> AutocompleteExpertiseData:
        """
        STEP 1: Load expertise.yaml FIRST with type-safe Pydantic validation

        Returns:
            AutocompleteExpertiseData: Validated expertise data

        CRITICAL: Returns Pydantic model (not dict) for type safety
        """
        if not self.expertise_yaml_path.exists():
            self.logger.info("No expertise.yaml found, creating new")
            # Create new typed data
            return AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,  # Will be set after first interaction
                previous_completions=[]
            )

        # Load YAML file
        with open(self.expertise_yaml_path, 'r') as f:
            raw_data = yaml.safe_load(f)

        # CRITICAL: Validate with Pydantic (raises if invalid)
        try:
            expertise = AutocompleteExpertiseData.from_dict(raw_data)
        except Exception as e:
            self.logger.error(f"Invalid expertise.yaml format: {e}")
            self.logger.info("Creating fresh expertise.yaml")
            # Fallback to new data if YAML is corrupt
            return AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,
                previous_completions=[]
            )

        # STEP 2: Check orchestrator_agent_id match
        if expertise.orchestrator_agent_id != self.orchestrator_agent_id:
            self.logger.info(
                f"Orchestrator changed: {expertise.orchestrator_agent_id} → {self.orchestrator_agent_id}"
            )
            self.logger.info("Resetting expertise.yaml (clearing history)")

            # STEP 3: Reset on orchestrator change
            return AutocompleteExpertiseData(
                orchestrator_agent_id=self.orchestrator_agent_id,
                completion_agent_id=None,  # Clear old session
                previous_completions=[]  # Clear history
            )

        # Same orchestrator - keep everything
        self.logger.info(f"Resuming autocomplete session for orchestrator: {self.orchestrator_agent_id}")
        return expertise

    def _init_claude_agent(self):
        """
        Initialize Claude Agent SDK client with session resume if available.

        If completion_agent_id exists in expertise.yaml, resume that session.
        Otherwise, start fresh and capture session_id after first interaction.
        """
        # CRITICAL: Type-safe access via Pydantic model
        completion_agent_id = self.expertise_data.completion_agent_id

        # Build ClaudeAgentOptions
        options_dict = {
            'system_prompt': self._load_system_prompt_with_variables(""),  # Placeholder
            'model': 'claude-haiku-4-5-20251001',  # LATEST HAIKU MODEL
            'cwd': self.working_dir,
        }

        # Resume session if we have a completion_agent_id
        if completion_agent_id:
            options_dict['resume'] = completion_agent_id
            self.logger.info(f"Resuming Claude Agent SDK session: {completion_agent_id[:20]}...")
        else:
            self.logger.info("Starting fresh Claude Agent SDK session")

        # Create client
        self.client = ClaudeSDKClient(ClaudeAgentOptions(**options_dict))
        self.logger.success("Claude Agent SDK client initialized")

    def _save_expertise(self):
        """
        Save expertise data to YAML file with type safety.

        CRITICAL: Converts Pydantic model to dict for YAML serialization
        """
        with open(self.expertise_yaml_path, 'w') as f:
            yaml.dump(
                self.expertise_data.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False
            )

    def _get_variable_values(self, user_input: str) -> dict[str, str]:
        """Get all 7 variables for prompt replacement"""
        from .slash_command_parser import discover_slash_commands
        from .subagent_loader import SubagentRegistry

        # CRITICAL: Type-safe access to previous_completions via Pydantic model
        # Convert to dict for YAML serialization
        previous_completions_data = [
            comp.model_dump(mode='python')
            for comp in self.expertise_data.previous_completions
        ]

        return {
            'TOTAL_AUTOCOMPLETE_ITEMS': '3',
            'USER_PROMPT': user_input,
            'PREVIOUS_AUTOCOMPLETE_ITEMS': yaml.dump(previous_completions_data),
            'AVAILABLE_ACTIVE_AGENTS': json.dumps([], indent=2),  # TODO: Get from DB
            'AVAILABLE_SLASH_COMMANDS': json.dumps(discover_slash_commands(self.working_dir), indent=2),
            'AVAILABLE_AGENT_TEMPLATES': json.dumps(SubagentRegistry(self.working_dir, self.logger).list_templates(), indent=2),
            'CODEBASE_STRUCTURE': json.dumps({}, indent=2)  # TODO: Implement
        }

    def _load_system_prompt_with_variables(self, user_input: str) -> str:
        """Load system prompt and replace all variables"""
        variables = self._get_variable_values(user_input)
        result = self.system_prompt_template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", value)
        return result

    async def generate_autocomplete(self, user_input: str) -> List[AutocompleteItem]:
        """
        Generate autocomplete suggestions using Claude Agent SDK.

        CRITICAL: Uses Claude Agent SDK's prompt() method which maintains session.
        After first interaction, captures and stores session_id in expertise.yaml.
        """
        # Update system prompt with current user input context
        system_prompt = self._load_system_prompt_with_variables(user_input)

        # Update client system prompt if needed
        if self.client.options.system_prompt != system_prompt:
            # Recreate client with updated system prompt
            self._init_claude_agent()
            self.client.options.system_prompt = system_prompt

        # Build user prompt
        user_prompt = self.user_prompt_template.replace('$1', user_input)

        self.logger.info(f"Generating autocomplete for: {user_input[:50]}...")

        # Call Claude Agent SDK
        response = await self.client.prompt(user_prompt)

        # CRITICAL: Capture session_id after first interaction (type-safe)
        if not self.expertise_data.completion_agent_id and hasattr(response, 'session_id'):
            self.expertise_data.completion_agent_id = response.session_id
            self._save_expertise()
            self.logger.info(f"Captured autocomplete session_id: {response.session_id[:20]}...")

        # Extract text from response
        content = ""
        for block in response.content:
            if hasattr(block, 'text'):
                content += block.text

        # Extract JSON from markdown
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()

        data = json.loads(content)
        items = [AutocompleteItem(**item) for item in data.get('autocompletes', [])]

        self.logger.success(f"Generated {len(items)} autocomplete suggestions")
        return items

    def add_completion_event(
        self,
        completion_type: str,
        user_input_on_enter: Optional[str] = None,
        user_input_before_completion: Optional[str] = None,
        autocomplete_item: Optional[str] = None,
        reasoning: Optional[str] = None
    ):
        """
        Add a completion event to expertise.yaml with type safety.

        CRITICAL: Uses Pydantic models to ensure type safety when appending events.

        Args:
            completion_type: 'none' or 'autocomplete'
            user_input_on_enter: Required if completion_type='none'
            user_input_before_completion: Required if completion_type='autocomplete'
            autocomplete_item: Required if completion_type='autocomplete'
            reasoning: Required if completion_type='autocomplete'
        """
        # Calculate next order number (type-safe access)
        order = len(self.expertise_data.previous_completions) + 1

        # Create typed event based on completion_type
        if completion_type == 'none':
            event = PreviousCompletionNone(
                completion_type='none',
                user_input_on_enter=user_input_on_enter,
                order=order
            )
        else:  # autocomplete
            event = PreviousCompletionAutocomplete(
                completion_type='autocomplete',
                user_input_before_completion=user_input_before_completion,
                autocomplete_item=autocomplete_item,
                reasoning=reasoning,
                order=order
            )

        # Append typed event to list (type-safe)
        self.expertise_data.previous_completions.append(event)

        # Save with type safety
        self._save_expertise()
```

### Step 3: Create Service Layer

**File:** `backend/modules/autocomplete_service.py`

```python
from typing import List
from .autocomplete_agent import AutocompleteAgent
from .autocomplete_models import AutocompleteResponse

class AutocompleteService:
    def __init__(self, orchestrator_agent_id, logger, working_dir):
        self.orchestrator_agent_id = orchestrator_agent_id
        self.logger = logger
        self.agent = AutocompleteAgent(orchestrator_agent_id, logger, working_dir)

    async def generate_autocomplete(self, user_input: str, orchestrator_agent_id: str) -> AutocompleteResponse:
        try:
            if str(self.orchestrator_agent_id) != orchestrator_agent_id:
                raise ValueError("Orchestrator ID mismatch")

            items = await self.agent.generate_autocomplete(user_input)

            return AutocompleteResponse(
                status="success",
                autocompletes=items,
                total_items=len(items),
                orchestrator_agent_id=orchestrator_agent_id
            )
        except Exception as e:
            self.logger.error(f"Autocomplete generation failed: {e}")
            return AutocompleteResponse(
                status="error",
                autocompletes=[],
                total_items=0,
                orchestrator_agent_id=orchestrator_agent_id
            )

    async def update_completion_history(
        self,
        orchestrator_agent_id: str,
        completion_type: str,
        user_input_on_enter: str = None,
        user_input_before_completion: str = None,
        autocomplete_item: str = None,
        reasoning: str = None
    ):
        """
        Update completion history with type-safe event.

        CRITICAL: Type annotations match Pydantic models for validation
        """
        try:
            self.agent.add_completion_event(
                completion_type=completion_type,
                user_input_on_enter=user_input_on_enter,
                user_input_before_completion=user_input_before_completion,
                autocomplete_item=autocomplete_item,
                reasoning=reasoning
            )
            self.logger.info(f"Updated completion history: {completion_type}")
        except Exception as e:
            self.logger.error(f"Failed to update completion history: {e}")
            raise
```

### Step 4: Add API Endpoints

**File:** `backend/main.py` (modifications)

```python
# Add to imports
from modules.autocomplete_service import AutocompleteService
from modules.autocomplete_models import (
    AutocompleteGenerateRequest,
    AutocompleteUpdateRequest,
    AutocompleteResponse
)

# Add to lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup

    # Initialize autocomplete service
    logger.info("Initializing autocomplete service...")
    autocomplete_service = AutocompleteService(
        orchestrator_agent_id=orchestrator.id,
        logger=logger,
        working_dir=config.get_working_dir()
    )
    app.state.autocomplete_service = autocomplete_service
    logger.success("Autocomplete service initialized")

    yield
    # ... existing shutdown

# Add endpoints
@app.post("/autocomplete-generate")
async def autocomplete_generate(request: AutocompleteGenerateRequest) -> AutocompleteResponse:
    try:
        logger.http_request("POST", "/autocomplete-generate")
        service: AutocompleteService = app.state.autocomplete_service
        response = await service.generate_autocomplete(
            user_input=request.user_input,
            orchestrator_agent_id=request.orchestrator_agent_id
        )
        logger.http_request("POST", "/autocomplete-generate", 200)
        return response
    except Exception as e:
        logger.error(f"Autocomplete generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autocomplete-update")
async def autocomplete_update(request: AutocompleteUpdateRequest):
    try:
        logger.http_request("POST", "/autocomplete-update")
        service: AutocompleteService = app.state.autocomplete_service
        await service.update_completion_history(
            orchestrator_agent_id=request.orchestrator_agent_id,
            completion_type=request.completion_type,
            user_input_on_enter=request.user_input_on_enter,
            user_input_before_completion=request.user_input_before_completion,
            autocomplete_item=request.autocomplete_item,
            reasoning=request.reasoning
        )
        logger.http_request("POST", "/autocomplete-update", 200)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Autocomplete update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Phase 2: Frontend (2-3 hours)

### Step 5: Add TypeScript Types

**File:** `frontend/src/types.d.ts` (additions)

```typescript
export type CompletionType = 'none' | 'autocomplete'

export interface AutocompleteItem {
  completion: string
  reasoning: string
}

export interface AutocompleteResponse {
  status: string
  autocompletes: AutocompleteItem[]
  total_items: number
  orchestrator_agent_id: string
  timestamp: string
}

export interface AutocompleteGenerateRequest {
  user_input: string
  orchestrator_agent_id: string
}

export interface AutocompleteUpdateRequest {
  orchestrator_agent_id: string
  completion_type: CompletionType
  user_input_on_enter?: string
  user_input_before_completion?: string
  autocomplete_item?: string
  reasoning?: string
}
```

### Step 6: Create API Service

**File:** `frontend/src/services/autocompleteService.ts`

```typescript
import api from './api'
import type {
  AutocompleteGenerateRequest,
  AutocompleteUpdateRequest,
  AutocompleteResponse
} from '../types'

export async function generateAutocomplete(
  userInput: string,
  orchestratorAgentId: string
): Promise<AutocompleteResponse> {
  const response = await api.post<AutocompleteResponse>('/autocomplete-generate', {
    user_input: userInput,
    orchestrator_agent_id: orchestratorAgentId
  })
  return response.data
}

export async function updateAutocompleteHistory(
  request: AutocompleteUpdateRequest
): Promise<{ status: string }> {
  const response = await api.post('/autocomplete-update', request)
  return response.data
}
```

### Step 7: Update Store

**File:** `frontend/src/stores/orchestratorStore.ts` (additions)

```typescript
import * as autocompleteService from '../services/autocompleteService'

// Add to state
const autocompleteItems = ref<AutocompleteItem[]>([])
const autocompleteLoading = ref<boolean>(false)
const autocompleteError = ref<string | null>(null)

// Add computed
const hasAutocompleteItems = computed(() => autocompleteItems.value.length > 0)

// Add actions
async function generateAutocomplete(userInput: string) {
  try {
    autocompleteLoading.value = true
    autocompleteError.value = null

    const response = await autocompleteService.generateAutocomplete(
      userInput,
      orchestratorAgentId.value
    )

    autocompleteItems.value = response.autocompletes
  } catch (error) {
    console.error('Failed to generate autocomplete:', error)
    autocompleteError.value = error instanceof Error ? error.message : 'Unknown error'
    autocompleteItems.value = []
  } finally {
    autocompleteLoading.value = false
  }
}

async function updateAutocompleteHistory(
  completion_type: CompletionType,
  user_input_on_enter?: string,
  user_input_before_completion?: string,
  autocomplete_item?: string,
  reasoning?: string
) {
  try {
    await autocompleteService.updateAutocompleteHistory({
      orchestrator_agent_id: orchestratorAgentId.value,
      completion_type,
      user_input_on_enter,
      user_input_before_completion,
      autocomplete_item,
      reasoning
    })
  } catch (error) {
    console.error('Failed to update autocomplete history:', error)
  }
}

function clearAutocomplete() {
  autocompleteItems.value = []
  autocompleteError.value = null
}

// Add to return
return {
  // ... existing
  autocompleteItems,
  autocompleteLoading,
  autocompleteError,
  hasAutocompleteItems,
  generateAutocomplete,
  updateAutocompleteHistory,
  clearAutocomplete
}
```

### Step 8: Create Composable

**File:** `frontend/src/composables/useAutocomplete.ts`

```typescript
import { ref, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { useOrchestratorStore } from '../stores/orchestratorStore'

export function useAutocomplete() {
  const store = useOrchestratorStore()
  const selectedPillIndex = ref<number | null>(null)

  const debouncedGenerate = useDebounceFn(async (input: string) => {
    if (!input.trim()) {
      store.clearAutocomplete()
      return
    }
    await store.generateAutocomplete(input)
  }, 1000)

  function generateAutocomplete(input: string) {
    debouncedGenerate(input)
  }

  function acceptAutocomplete(index: number) {
    const item = store.autocompleteItems[index]
    if (!item) return
    return { completion: item.completion, reasoning: item.reasoning }
  }

  function handleAutocompleteKeydown(event: KeyboardEvent) {
    if (!store.hasAutocompleteItems) return

    // Ctrl+1, Ctrl+2, Ctrl+3
    if (event.ctrlKey && event.key >= '1' && event.key <= '3') {
      event.preventDefault()
      const index = parseInt(event.key) - 1
      if (index < store.autocompleteItems.length) {
        const result = acceptAutocomplete(index)
        if (result) {
          const customEvent = new CustomEvent('autocomplete-accept', {
            detail: { index, ...result }
          })
          event.target?.dispatchEvent(customEvent)
        }
      }
    }

    // Escape to clear
    if (event.key === 'Escape') {
      event.preventDefault()
      store.clearAutocomplete()
    }
  }

  return {
    autocompleteItems: computed(() => store.autocompleteItems),
    autocompleteLoading: computed(() => store.autocompleteLoading),
    autocompleteError: computed(() => store.autocompleteError),
    hasAutocompleteItems: computed(() => store.autocompleteItems.length > 0),
    selectedPillIndex,
    generateAutocomplete,
    acceptAutocomplete,
    clearAutocomplete: () => store.clearAutocomplete(),
    handleAutocompleteKeydown
  }
}
```

## Phase 3: UI Integration (2-3 hours)

### Step 9: Modify Chat Component

**File:** `frontend/src/components/OrchestratorChat.vue`

**Template:**

```vue
<template>
  <div class="orchestrator-chat">
    <!-- ... existing header and messages ... -->

    <div class="chat-input-container">
      <input
        v-model="inputMessage"
        @input="handleInput"
        @keydown="handleKeydown"
        @autocomplete-accept="handleAutocompleteAccept"
        placeholder="Message the orchestrator..."
        ref="inputRef"
      />

      <!-- Autocomplete Pills -->
      <div v-if="hasAutocompleteItems" class="autocomplete-pills">
        <div
          v-for="(item, index) in autocompleteItems"
          :key="index"
          class="autocomplete-pill"
          @click="handlePillClick(index)"
        >
          <span class="pill-hotkey">Ctrl+{{ index + 1 }}</span>
          <span class="pill-text">{{ item.completion }}</span>
        </div>
      </div>

      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>
```

**Script:**

```typescript
import { useAutocomplete } from '../composables/useAutocomplete'

const {
  autocompleteItems,
  hasAutocompleteItems,
  selectedPillIndex,
  generateAutocomplete,
  clearAutocomplete,
  handleAutocompleteKeydown
} = useAutocomplete()

const inputMessage = ref('')
const inputBeforeCompletion = ref('')
const inputRef = ref<HTMLInputElement>()

function handleInput(event: Event) {
  const value = (event.target as HTMLInputElement).value
  inputMessage.value = value
  generateAutocomplete(value)
}

function handleKeydown(event: KeyboardEvent) {
  handleAutocompleteKeydown(event)

  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

function handleAutocompleteAccept(event: CustomEvent) {
  const { completion, reasoning } = event.detail
  inputBeforeCompletion.value = inputMessage.value
  inputMessage.value += completion

  store.updateAutocompleteHistory(
    'autocomplete',
    undefined,
    inputBeforeCompletion.value,
    completion,
    reasoning
  )

  clearAutocomplete()
  nextTick(() => inputRef.value?.focus())
}

function handlePillClick(index: number) {
  const event = new KeyboardEvent('keydown', {
    ctrlKey: true,
    key: String(index + 1)
  })
  inputRef.value?.dispatchEvent(event)
}

async function sendMessage() {
  if (!inputMessage.value.trim()) return

  const message = inputMessage.value

  if (hasAutocompleteItems.value) {
    await store.updateAutocompleteHistory('none', message)
  }

  clearAutocomplete()
  await store.sendUserMessage(message)

  inputMessage.value = ''
  inputBeforeCompletion.value = ''
}
```

**CSS:**

```css
.autocomplete-pills {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}

.autocomplete-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--gray-800);
  border: 1px solid var(--gray-700);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.autocomplete-pill:hover {
  background: var(--gray-700);
  border-color: var(--cyan-500);
}

.pill-hotkey {
  font-size: 11px;
  font-weight: 600;
  color: var(--cyan-400);
  padding: 2px 6px;
  background: var(--gray-900);
  border-radius: 4px;
  font-family: monospace;
}

.pill-text {
  font-size: 13px;
  color: var(--gray-200);
}
```

---

# 6. Testing

## Backend Tests

**`backend/tests/test_autocomplete_agent.py`:**

```python
import pytest
from modules.autocomplete_agent import AutocompleteAgent

@pytest.fixture
def agent(tmp_path):
    return AutocompleteAgent(
        uuid.uuid4(),
        get_logger(),
        tmp_path
    )

def test_create_expertise(agent):
    assert agent.expertise_data['orchestrator_agent_id']
    assert agent.expertise_data['previous_completions'] == []

def test_add_event_none(agent):
    agent.add_completion_event('none', user_input_on_enter='test')
    assert len(agent.expertise_data['previous_completions']) == 1

@pytest.mark.asyncio
async def test_generate(agent):
    items = await agent.generate_autocomplete("create a new ")
    assert isinstance(items, list)
    assert len(items) <= 3
```

**`backend/tests/test_autocomplete_endpoints.py`:**

```python
@pytest.mark.asyncio
async def test_generate_endpoint(client):
    response = await client.post(
        "/autocomplete-generate",
        json={"user_input": "create", "orchestrator_agent_id": "test-id"}
    )
    assert response.status_code == 200
    assert 'autocompletes' in response.json()
```

## Frontend Tests

**`frontend/tests/useAutocomplete.spec.ts`:**

```typescript
describe('useAutocomplete', () => {
  it('should debounce', async () => {
    const { generateAutocomplete } = useAutocomplete()
    // Test debounce logic
  })
})
```

## Manual Testing

```bash
# Start services
./start_be.sh
./start_fe.sh

# Test endpoint
curl -X POST http://localhost:8002/autocomplete-generate \
  -H "Content-Type: application/json" \
  -d '{"user_input": "create a new ", "orchestrator_agent_id": "uuid"}'

# Playwright
npx playwright test
```

---

# 7. Quick Reference

## API Contracts

### POST `/autocomplete-generate`

```json
// Request
{"user_input": "create a new ", "orchestrator_agent_id": "uuid"}

// Response
{
  "status": "success",
  "autocompletes": [
    {"completion": "testing", "reasoning": "..."},
    {"completion": "database", "reasoning": "..."}
  ],
  "total_items": 2
}
```

### POST `/autocomplete-update`

```json
// Manual input
{"orchestrator_agent_id": "uuid", "completion_type": "none", "user_input_on_enter": "..."}

// Autocomplete
{
  "orchestrator_agent_id": "uuid",
  "completion_type": "autocomplete",
  "user_input_before_completion": "create ",
  "autocomplete_item": "a new agent",
  "reasoning": "..."
}
```

## expertise.yaml Structure

```yaml
# CRITICAL: Both orchestrator_agent_id AND completion_agent_id are tracked
orchestrator_agent_id: "uuid-123"  # Current orchestrator session
completion_agent_id: "sdk_session_abc123..."  # Claude Agent SDK session_id

previous_completions:
  - completion_type: "none"
    user_input_on_enter: "create agent"
    order: 1
  - completion_type: "autocomplete"
    user_input_before_completion: "add "
    autocomplete_item: "database"
    reasoning: "context"
    order: 2
```

**Session Management Rules:**
- `orchestrator_agent_id` - Current orchestrator UUID (from backend)
- `completion_agent_id` - Claude Agent SDK session_id (captured after first interaction)
- If `orchestrator_agent_id` changes → Reset both IDs + clear `previous_completions`
- If `orchestrator_agent_id` matches → Resume Claude Agent SDK session with `completion_agent_id`

## Keyboard Shortcuts

- **Ctrl+1** - Accept first pill
- **Ctrl+2** - Accept second pill
- **Ctrl+3** - Accept third pill
- **Escape** - Clear pills

## Variable Replacement (7 total)

1. `{{TOTAL_AUTOCOMPLETE_ITEMS}}` → "3"
2. `{{USER_PROMPT}}` → current input
3. `{{PREVIOUS_AUTOCOMPLETE_ITEMS}}` → YAML dump
4. `{{AVAILABLE_ACTIVE_AGENTS}}` → JSON
5. `{{AVAILABLE_SLASH_COMMANDS}}` → JSON
6. `{{AVAILABLE_AGENT_TEMPLATES}}` → JSON
7. `{{CODEBASE_STRUCTURE}}` → JSON

---

# 8. Deployment

## Timeline

**Day 1:** Backend (3-4h) + Frontend Foundation (2-3h)
**Day 2:** UI Integration (2-3h) + Testing (2-3h)
**Day 3:** Polish + Deploy

## Checklist

### Backend
- [ ] Create `autocomplete_models.py`
- [ ] Create `autocomplete_agent.py`
- [ ] Create `autocomplete_service.py`
- [ ] Modify `main.py` (2 endpoints + lifespan)
- [ ] Write tests
- [ ] Test with curl

### Frontend
- [ ] Modify `types.d.ts`
- [ ] Create `autocompleteService.ts`
- [ ] Modify `orchestratorStore.ts`
- [ ] Create `useAutocomplete.ts`
- [ ] Modify `OrchestratorChat.vue`
- [ ] Write tests

### Testing
- [ ] Backend unit tests pass
- [ ] Backend integration tests pass
- [ ] Frontend unit tests pass
- [ ] Manual testing with Playwright
- [ ] Performance targets met (<2s API response)

### Deploy
- [ ] Commit changes
- [ ] Push to repository
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Monitor logs
- [ ] Gather feedback

## Success Criteria

✅ Generates 3 suggestions in <2 seconds
✅ Keyboard shortcuts work (Ctrl+1/2/3)
✅ Pills display correctly
✅ History tracks in expertise.yaml
✅ Session resets on orchestrator change
✅ Empty input clears autocomplete
✅ No memory leaks
✅ Smooth 60fps animations

---

**END OF MASTER PLAN**

This is your single source of truth for implementing the autocomplete system. Everything you need is in this document:

- Architecture diagrams
- Complete file changes
- Implementation code
- Testing strategy
- Deployment checklist
- Quick reference

Good luck building! 🚀
