# Session Sync Issue

## Problem

Sessions created by the Claude Code session skill are not visible in the frontend UI.

**Root cause**: The session skill writes to the filesystem only, while the frontend reads from PostgreSQL. There's no bridge between them.

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   SESSION SKILL                           FRONTEND UI                   │
│   ──────────────                          ───────────                   │
│                                                                         │
│   /session:spec                           React + Drizzle ORM           │
│        │                                         │                      │
│        ▼                                         ▼                      │
│   ┌─────────────┐                         ┌─────────────┐               │
│   │ Filesystem  │          GAP            │ PostgreSQL  │               │
│   │             │  ◄─────────────────►    │             │               │
│   │ agents/     │     (no sync)           │ sessions    │               │
│   │ sessions/   │                         │ table       │               │
│   └─────────────┘                         └─────────────┘               │
│                                                                         │
│   Writes:                                 Reads:                        │
│   - spec.md                               - session metadata            │
│   - plan.json                             - status, type, project_id    │
│   - state.json                            - checkpoints progress        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Impact

- Projects like `bubba-phone` have many sessions on filesystem but 0 visible in UI
- New sessions created via `/session:spec` don't appear in the UI
- Session artifact routes (`/api/sessions/[slug]/spec`) work, but only if session exists in DB first

## Proposed Solution

### Phase 1: Import Script (Migration)

Create a script/API endpoint to scan a project's `agents/sessions/` directory and import existing sessions into PostgreSQL.

```
POST /api/projects/{id}/import-sessions

Scans: {project.path}/agents/sessions/*/state.json
Creates: Session records in database
```

### Phase 2: Session Skill Integration (Real-time)

Update the session skill to call the frontend API when creating new sessions:

```markdown
# In session skill, after creating state.json:

Call POST /api/sessions with:
- session_slug (from directory name)
- title (from state.json)
- project_id (from context)
- working_dir, session_dir
- status: "spec_in_progress"
```

### Phase 3: Bidirectional Sync (Future)

Consider filesystem watcher or periodic sync to keep DB in sync with filesystem changes made by agents.

## Files Involved

| Component | Path | Role |
|-----------|------|------|
| Session skill | `.claude/skills/session/` | Creates filesystem sessions |
| Sessions API | `frontend/src/app/api/sessions/` | CRUD for DB sessions |
| Sessions store | `frontend/src/store/sessions.ts` | UI state management |
| Session artifacts | `frontend/src/app/api/sessions/[slug]/spec,plan,state/` | Reads from filesystem |

## Workaround (Manual)

Until sync is implemented, sessions can be manually inserted into the database:

```sql
INSERT INTO sessions (id, session_slug, title, project_id, status, session_type, working_dir, session_dir)
VALUES (
  gen_random_uuid(),
  'my-session-slug',
  'My Session Title',
  '<project-uuid>',
  'planning',
  'full',
  '/path/to/project',
  '/path/to/project/agents/sessions/my-session-slug'
);
```

## Related Decisions

From `agents/sessions/refactor-frontend-db-access/state.json`:

> **"state.json stays filesystem-only"**: Agent can easily write via Write tool, keeps things simple for this refactor

> **"Filesystem artifacts stay in filesystem"**: Agents need to walk codebase and read spec.md, plan.json

The decision to keep artifacts on filesystem is correct (agents need direct file access). The missing piece is syncing **session metadata** to the database.
