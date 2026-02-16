# Prime

Execute the `Run`, `Read` and `Report` sections to understand the codebase then summarize your understanding.

## Instructions

- We're focused on apps/orchestrator_3_stream/*.

## Workflow

Run `git ls-files`
READ @README.md
READ @apps/orchestrator_db/README.md
READ @apps/orchestrator_db/models.py
READ @apps/orchestrator_3_stream/README.md
READ apps/orchestrator_3_stream/frontend/src/types.d.ts
READ @apps/orchestrator_3_stream/backend/modules/orch_database_models.py (should mirror models.py)

### If you're requested to work on the backend, read the following files:

READ apps/orchestrator_3_stream/backend/modules/orchestrator_service.py
READ apps/orchestrator_3_stream/backend/main.py
READ apps/orchestrator_3_stream/backend/modules/websocket_manager.py

### If you're requested to work on the frontend, read the following files:

READ apps/orchestrator_3_stream/frontend/src/components/AgentList.vue
READ apps/orchestrator_3_stream/frontend/src/components/EventStream.vue
READ apps/orchestrator_3_stream/frontend/src/components/OrchestratorChat.vue
READ apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts
READ apps/orchestrator_3_stream/frontend/src/services/chatService.ts

## Report
Summarize your understanding of the codebase.