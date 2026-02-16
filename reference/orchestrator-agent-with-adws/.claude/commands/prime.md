# Prime

Execute the `Run`, `Read` and `Report` sections to understand the codebase then summarize your understanding.

## Focus
- Primary focus: `apps/orchestrator_3_stream/*`

## Run
git ls-files

## Read

### Core (always read these):
- @README.md
- @apps/orchestrator_db/README.md
- @apps/orchestrator_db/models.py
- @apps/orchestrator_3_stream/README.md
- apps/orchestrator_3_stream/frontend/src/types.d.ts
- apps/orchestrator_3_stream/backend/modules/orch_database_models.py

### Backend (if working on backend):
- apps/orchestrator_3_stream/backend/main.py
- apps/orchestrator_3_stream/backend/modules/orchestrator_service.py
- apps/orchestrator_3_stream/backend/modules/websocket_manager.py

### Frontend (if working on frontend):
- apps/orchestrator_3_stream/frontend/src/stores/orchestratorStore.ts
- apps/orchestrator_3_stream/frontend/src/services/chatService.ts
- apps/orchestrator_3_stream/frontend/src/components/OrchestratorChat.vue
- apps/orchestrator_3_stream/frontend/src/components/EventStream.vue
- apps/orchestrator_3_stream/frontend/src/components/AgentList.vue

## Report
Summarize your understanding of the codebase.