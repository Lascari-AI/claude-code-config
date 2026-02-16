# Backend Architecture Diagrams

## Module Relationship Map

```mermaid
graph TB
    subgraph "API Layer"
        A["main.py<br/>(FastAPI)"]
    end

    subgraph "Configuration & Logging"
        B["config.py<br/>(Environment & Settings)"]
        C["logger.py<br/>(Rich + File Logs)"]
    end

    subgraph "Data Layer"
        D["database.py<br/>(asyncpg Pool)"]
        E["orch_database_models.py<br/>(Pydantic Models)"]
    end

    subgraph "Real-time Communication"
        F["websocket_manager.py<br/>(Connection & Broadcasting)"]
    end

    subgraph "Business Logic"
        G["orchestrator_service.py<br/>(Claude SDK Integration)"]
        H["agent_manager.py<br/>(Agent Lifecycle)"]
    end

    subgraph "Event Capture"
        I["hooks.py<br/>(Generic Hooks)"]
        J["orchestrator_hooks.py<br/>(Orch-specific)"]
        K["command_agent_hooks.py<br/>(Agent-specific)"]
    end

    subgraph "Template & Discovery"
        L["slash_command_parser.py<br/>(Slash Command Discovery)"]
        M["subagent_loader.py<br/>(Template Registry)"]
        N["subagent_models.py<br/>(Template Types)"]
    end

    subgraph "Utilities"
        O["single_agent_prompt.py<br/>(Event Summarization)"]
        P["file_tracker.py<br/>(Change Detection)"]
        Q["event_summarizer.py<br/>(Summary Generation)"]
    end

    subgraph "External Services"
        R["PostgreSQL<br/>(NeonDB)"]
        S["Claude SDK<br/>(Claude Agent)"]
    end

    A -->|uses| B
    A -->|uses| C
    A -->|uses| D
    A -->|uses| F
    A -->|uses| G

    D -->|uses| E
    D -->|connects to| R

    G -->|uses| B
    G -->|uses| C
    G -->|uses| D
    G -->|uses| F
    G -->|uses| H
    G -->|uses| J
    G -->|uses| M
    G -->|uses| S

    H -->|uses| B
    H -->|uses| C
    H -->|uses| D
    H -->|uses| F
    H -->|uses| K
    H -->|uses| P
    H -->|uses| M
    H -->|uses| S

    I -->|calls| D
    I -->|calls| F
    I -->|calls| C
    I -->|spawns| O

    J -->|extends| I
    K -->|extends| I

    M -->|uses| N
    M -->|uses| C
    L -->|uses| C

    O -->|uses| C
    O -->|uses| S
    Q -->|uses| C

    style A fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#2196F3,stroke:#333,stroke-width:1px,color:#fff
    style C fill:#2196F3,stroke:#333,stroke-width:1px,color:#fff
    style D fill:#FF9800,stroke:#333,stroke-width:1px,color:#fff
    style E fill:#FF9800,stroke:#333,stroke-width:1px,color:#fff
    style F fill:#9C27B0,stroke:#333,stroke-width:1px,color:#fff
    style G fill:#E91E63,stroke:#333,stroke-width:2px,color:#fff
    style H fill:#E91E63,stroke:#333,stroke-width:2px,color:#fff
    style I fill:#00BCD4,stroke:#333,stroke-width:1px,color:#fff
    style J fill:#00BCD4,stroke:#333,stroke-width:1px,color:#fff
    style K fill:#00BCD4,stroke:#333,stroke-width:1px,color:#fff
    style R fill:#795548,stroke:#333,stroke-width:2px,color:#fff
    style S fill:#3F51B5,stroke:#333,stroke-width:2px,color:#fff
```

---

## Data Flow: User Message Processing

```mermaid
sequenceDiagram
    participant Frontend as Frontend<br/>(Vue 3)
    participant API as main.py<br/>(FastAPI)
    participant Service as orchestrator_service
    participant SDK as Claude SDK<br/>(Agent)
    participant DB as PostgreSQL
    participant WS as WebSocket<br/>Manager
    participant Hooks as Event Hooks

    Frontend->>API: POST /send_chat { message }
    API->>Service: create_task(process_user_message)
    API-->>Frontend: 200 OK { "processing" }

    par Service Execution
        Service->>DB: insert_chat_message(user msg)
        DB-->>Service: msg_id

        Service->>SDK: ClaudeSDKClient.interact()

        loop During Execution
            SDK->>Hooks: PreToolUse hook
            Hooks->>DB: insert_hook_event(PreToolUse)
            Hooks->>WS: broadcast_agent_log
            WS-->>Frontend: Agent log event

            SDK->>SDK: Execute tool

            Hooks->>Hooks: PostToolUse hook
            Hooks->>DB: insert_hook_event(PostToolUse)
            Hooks->>WS: broadcast_agent_log
            WS-->>Frontend: Agent log event
        end

        SDK->>Hooks: Stop hook
        Hooks->>DB: update costs

        Service->>DB: insert_chat_message(orchestrator response)
        Service->>DB: update_orchestrator_costs()
        Service->>WS: broadcast_orchestrator_updated()
        WS-->>Frontend: Cost update event
    end

    Frontend->>Frontend: Render event stream + updated UI
```

---

## Component Interaction: Agent Creation

```mermaid
graph LR
    A["User Command:<br/>create_agent"]
    B["OrchestratorService<br/>(tool handler)"]
    C["AgentManager<br/>(create_agent)"]
    D["Database<br/>(create_agent)"]
    E["ClaudeSDK<br/>(Agent instance)"]
    F["WebSocket<br/>(broadcast)"]
    G["Frontend<br/>(update UI)"]

    A -->|management tool| B
    B -->|delegate| C
    C -->|create DB record| D
    D -->|return agent_id| C
    C -->|new ClaudeSDK| E
    E -->|store client| C
    C -->|broadcast event| F
    F -->|send to all| G

    style A fill:#FFC107,stroke:#333,stroke-width:2px
    style B fill:#E91E63,stroke:#333,stroke-width:1px
    style C fill:#E91E63,stroke:#333,stroke-width:1px
    style D fill:#FF9800,stroke:#333,stroke-width:1px
    style E fill:#3F51B5,stroke:#333,stroke-width:1px
    style F fill:#9C27B0,stroke:#333,stroke-width:1px
    style G fill:#4CAF50,stroke:#333,stroke-width:1px
```

---

## Database Schema Relationships

```mermaid
erDiagram
    ORCHESTRATOR_AGENTS ||--o{ AGENTS : manages
    ORCHESTRATOR_AGENTS ||--o{ ORCHESTRATOR_CHAT : initiates
    AGENTS ||--o{ AGENT_LOGS : generates
    AGENTS ||--o{ PROMPTS : receives
    ORCHESTRATOR_AGENTS ||--o{ PROMPTS : sends
    AGENTS ||--o{ ORCHESTRATOR_CHAT : participates
    SYSTEM_LOGS ||--|{ "*" : "global events"

    ORCHESTRATOR_AGENTS {
        uuid id PK
        string session_id UK
        string system_prompt
        string status
        string working_dir
        int input_tokens
        int output_tokens
        decimal total_cost
        jsonb metadata
        boolean archived
        timestamp created_at
        timestamp updated_at
    }

    AGENTS {
        uuid id PK
        uuid orchestrator_agent_id FK
        string name
        string model
        string system_prompt
        string working_dir
        string git_worktree
        string status
        string session_id
        int input_tokens
        int output_tokens
        decimal total_cost
        jsonb metadata
        boolean archived
        timestamp created_at
        timestamp updated_at
    }

    AGENT_LOGS {
        uuid id PK
        uuid agent_id FK
        string task_slug
        int entry_index
        string event_category
        string event_type
        string content
        jsonb payload
        string summary
        timestamp timestamp
    }

    ORCHESTRATOR_CHAT {
        uuid id PK
        uuid orchestrator_agent_id FK
        uuid agent_id FK "nullable"
        string sender_type
        string receiver_type
        string message
        string summary
        jsonb metadata
        timestamp created_at
        timestamp updated_at
    }

    PROMPTS {
        uuid id PK
        uuid agent_id FK "nullable"
        string task_slug
        string author
        string prompt_text
        string summary
        timestamp timestamp
    }

    SYSTEM_LOGS {
        uuid id PK
        string level
        string message
        string summary
        jsonb metadata
        timestamp timestamp
    }
```

---

## Request/Response Processing Pipeline

```mermaid
graph TD
    A["HTTP Request<br/>POST /send_chat"] -->|request validation| B{"Request Valid?"}
    B -->|No| C["400 Bad Request"]
    B -->|Yes| D["Parse to Pydantic<br/>SendChatRequest"]
    D --> E["Create async task"]
    E --> F["Return 200 OK<br/>immediately"]
    F -->|async| G["OrchestratorService<br/>.process_user_message"]

    G --> H["1. Log user msg<br/>to orchestrator_chat"]
    H --> I["2. Create Claude SDK<br/>client + hooks"]
    I --> J["3. Call client.interact<br/>with user message"]

    J -->|streaming response| K["Hook captures<br/>all events"]
    K --> L["Log to database<br/>agent_logs table"]
    L --> M["Broadcast to<br/>WebSocket clients"]
    M -->|real-time| N["Frontend receives<br/>event stream"]

    J --> O["4. Process response<br/>blocks"]
    O --> P["TextBlock<br/>ThinkingBlock<br/>ToolUseBlock"]
    P --> Q["5. Update orchestrator<br/>costs & status"]
    Q --> R["6. Send final event<br/>via WebSocket"]
    R -->|final| N

    N --> S["Frontend updates:<br/>Event log<br/>Agent status<br/>Cost display"]

    style A fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style G fill:#E91E63,stroke:#333,stroke-width:2px,color:#fff
    style N fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    style S fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
```

---

## Module Dependency Tree

```mermaid
graph TD
    A["main.py"] -->|imports| B["config"]
    A -->|imports| C["logger"]
    A -->|imports| D["database"]
    A -->|imports| E["websocket_manager"]
    A -->|imports| F["orchestrator_service"]

    F -->|imports| G["agent_manager"]
    F -->|imports| H["orchestrator_hooks"]
    F -->|imports| I["subagent_loader"]
    F -->|imports| D
    F -->|imports| C

    G -->|imports| D
    G -->|imports| J["command_agent_hooks"]
    G -->|imports| K["file_tracker"]
    G -->|imports| I
    G -->|imports| C

    D -->|imports| L["orch_database_models"]

    I -->|imports| M["subagent_models"]
    I -->|imports| C

    H -->|imports| C
    J -->|imports| C

    N["slash_command_parser"] -->|imports| C
    O["hooks.py"] -->|imports| D
    O -->|imports| E
    O -->|imports| C
    O -->|imports| P["single_agent_prompt"]

    P -->|imports| C
    Q["event_summarizer"] -->|imports| C
    R["file_tracker"] -->|imports| C

    style A fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#2196F3,stroke:#333
    style C fill:#2196F3,stroke:#333
    style D fill:#FF9800,stroke:#333
    style E fill:#9C27B0,stroke:#333
    style F fill:#E91E63,stroke:#333,stroke-width:2px
    style G fill:#E91E63,stroke:#333,stroke-width:2px
```

---

## API Endpoints Overview

```mermaid
graph LR
    subgraph "Health & Info"
        A["GET /health"]
        B["GET /get_orchestrator"]
        C["GET /get_headers"]
    end

    subgraph "Chat Management"
        D["POST /send_chat"]
        E["POST /load_chat"]
    end

    subgraph "Data Retrieval"
        F["GET /get_events"]
        G["GET /list_agents"]
    end

    subgraph "IDE Integration"
        H["POST /api/open-file"]
    end

    subgraph "Real-time Streaming"
        I["WebSocket /ws"]
    end

    J["Frontend"] -->|query| A
    J -->|query| B
    J -->|query| C
    J -->|command| D
    J -->|fetch| E
    J -->|fetch| F
    J -->|fetch| G
    J -->|action| H
    J -->|stream| I

    style A fill:#4CAF50,stroke:#333
    style B fill:#4CAF50,stroke:#333
    style C fill:#4CAF50,stroke:#333
    style D fill:#FF9800,stroke:#333,stroke-width:2px
    style E fill:#2196F3,stroke:#333
    style F fill:#2196F3,stroke:#333
    style G fill:#2196F3,stroke:#333
    style H fill:#9C27B0,stroke:#333
    style I fill:#E91E63,stroke:#333,stroke-width:2px
    style J fill:#FFC107,stroke:#333,stroke-width:2px
```

---

## Event Broadcasting Architecture

```mermaid
graph TD
    A["Claude SDK<br/>Hooks"] -->|hook events| B["Hook Handler<br/>Functions"]
    B -->|1. Log| C["Database<br/>agent_logs"]
    B -->|2. Broadcast| D["WebSocket<br/>Manager"]
    B -->|3. Summarize| E["Background<br/>Task"]

    C -->|persist| F["PostgreSQL"]
    D -->|send to all| G["WebSocket<br/>Clients"]
    E -->|AI Summary| H["Update DB<br/>Summary Field"]
    H -->|persist| F

    G -->|real-time event| I["Frontend<br/>Components"]
    I -->|render| J["Event Stream<br/>Display"]

    K["Tools"] -->|results| B
    L["Thinking"] -->|blocks| B
    M["Stop"] -->|events| B

    style B fill:#00BCD4,stroke:#333,stroke-width:2px
    style D fill:#9C27B0,stroke:#333,stroke-width:2px
    style G fill:#4CAF50,stroke:#333,stroke-width:2px
    style J fill:#2196F3,stroke:#333,stroke-width:2px
```

---

## State Management & Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Startup

    Startup --> Loading: Parse CLI args
    Loading --> DBInit: Load config
    DBInit --> PoolInit: Initialize pool
    PoolInit --> OrchestratorLoad: Connect to DB
    OrchestratorLoad --> ServiceInit: Get/Create orchestrator
    ServiceInit --> Ready: Initialize services

    Ready --> Idle: Ready for requests

    Idle --> Processing: Receive user message
    Processing --> Streaming: Start Claude SDK
    Streaming --> ToolExec: Tool call
    ToolExec --> Streaming: Continue execution
    Streaming --> Complete: Finalize response
    Complete --> Idle: Return to idle

    Idle --> Shutdown: Interrupt signal
    Processing --> Shutdown: Interrupt signal
    Streaming --> Shutdown: Interrupt signal

    Shutdown --> Closing: Begin shutdown
    Closing --> PoolClose: Close DB pool
    PoolClose --> [*]

    style Idle fill:#4CAF50,stroke:#333
    style Processing fill:#FF9800,stroke:#333
    style Streaming fill:#FF9800,stroke:#333
    style Ready fill:#4CAF50,stroke:#333,stroke-width:2px
```

---

## Configuration Layers

```mermaid
graph TD
    A["Environment Variables<br/>(.env file)"]
    B["Default Values<br/>(config.py fallbacks)"]
    C["CLI Overrides<br/>(--cwd flag)"]
    D["Runtime State<br/>(config.get_working_dir)"]

    A -->|primary| D
    B -->|if not set| D
    C -->|override| D

    D -->|provides| E["OrchestratorService"]
    D -->|provides| F["AgentManager"]
    D -->|provides| G["Database"]

    subgraph "Environment Variables"
        H["BACKEND_HOST/PORT"]
        I["FRONTEND_HOST/PORT"]
        J["DATABASE_URL"]
        K["ORCHESTRATOR_MODEL"]
        L["LOG_LEVEL/DIR"]
        M["IDE_COMMAND"]
    end

    A -.->|includes| H
    A -.->|includes| I
    A -.->|includes| J
    A -.->|includes| K
    A -.->|includes| L
    A -.->|includes| M

    style D fill:#E91E63,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#2196F3,stroke:#333
    style F fill:#2196F3,stroke:#333
    style G fill:#FF9800,stroke:#333
```

---

## Error Handling Flow

```mermaid
graph TD
    A["Operation<br/>Attempted"]
    B{"Exception<br/>Raised?"}
    C{"Is Expected?"}
    D["Log Error<br/>logger.error()"]
    E["Raise to Caller"]
    F["HTTP 500<br/>Internal Error"]
    G["HTTP with<br/>Status Code"]

    A --> B
    B -->|No| H["Operation<br/>Succeeds"]
    B -->|Yes| C
    C -->|No| D
    D --> E
    C -->|Yes| E
    E -->|REST endpoint| F
    E -->|REST endpoint| G

    F -->|broadcast| I["WebSocket<br/>Error Event"]
    G -->|broadcast| I
    I -->|display| J["Frontend<br/>Error UI"]

    H -->|Success| J

    style D fill:#E91E63,stroke:#333,stroke-width:2px
    style F fill:#F44336,stroke:#333,stroke-width:2px
    style I fill:#9C27B0,stroke:#333
```
