# Implementation Plan

> **Session**: `2026-02-11_build-initial-management-ui_mn3z2n`
> **Status**: Complete
> **Spec**: [./spec.md](./spec.md)
> **Created**: 2026-02-11
> **Updated**: 2026-02-11

---

## Overview

- **Checkpoints**: 5 (0 complete)
- **Total Tasks**: 53

## ⬜ Checkpoint 1: Project Entity - Model to UI End-to-End

**Goal**: Create the Project model, add FastAPI backend with CRUD endpoints, scaffold Next.js frontend, and display a basic projects list. This establishes the complete vertical slice from database to UI.

### File Context

### Testing Strategy

**Approach**: Backend API tests + manual frontend verification

### ⬜ Task Group 1.1: Database Layer - Project Model

**Objective**: Create Project SQLModel with all required fields (id, name, slug, path, status, onboarding_status, timestamps) and CRUD operations mirroring existing Session patterns

#### ⬜ Task 1.1.1: Create Project SQLModel

**File**: `apps/core/session_db/models.py`

**Description**: Add Project SQLModel class with fields: id (UUID PK), name (str), slug (str unique indexed), path (str - absolute codebase path), repo_url (optional str), status (Literal enum), onboarding_status (JSON dict), metadata_ (JSON), created_at, updated_at. Mirror Session model patterns for field definitions and relationships. Add ProjectStatus Literal type.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 1-120) - Understand existing Session model patterns, type aliases, and SQLModel conventions
- `agents/sessions/2026-02-11_build-initial-management-ui_mn3z2n/spec.md` (lines 79-128) - Reference Project model requirements from spec

**Actions**:
- ⬜ **1.1.1.1**: CREATE TYPE ProjectStatus Literal['pending', 'onboarding', 'active', 'paused', 'archived'] (`apps/core/session_db/models.py`)
- ⬜ **1.1.1.2**: CREATE CLASS Project(SQLModel, table=True) with __tablename__='projects', fields: id (UUID PK default_factory=uuid4), name (str), slug (str unique index), path (str), repo_url (Optional[str]), status (str default='pending' index), onboarding_status (dict[str,Any] JSON), metadata_ (dict[str,Any] JSON column='metadata'), created_at (datetime default_factory), updated_at (datetime default_factory) (`apps/core/session_db/models.py`)
- ⬜ **1.1.1.3**: ADD Relationship sessions: list['Session'] = Relationship(back_populates='project') to Project class (`apps/core/session_db/models.py`)

#### ⬜ Task 1.1.2: Create Project DTOs

**File**: `apps/core/session_db/models.py`

**Description**: Add ProjectCreate, ProjectUpdate, and ProjectSummary DTO classes following existing Session DTO patterns. ProjectCreate: name, slug, path, repo_url optional, status optional, onboarding_status optional, metadata_ optional. ProjectUpdate: all fields optional for partial updates. ProjectSummary: lightweight view for list endpoints.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 500-620) - Reference existing DTO patterns (SessionCreate, SessionUpdate, SessionSummary)

**Depends On**: Tasks 1.1.1

**Actions**:
- ⬜ **1.1.2.1**: CREATE CLASS ProjectSummary(SQLModel) with fields: id (UUID), name (str), slug (str), status (str), path (str), created_at (datetime), updated_at (datetime) (`apps/core/session_db/models.py`)
- ⬜ **1.1.2.2**: CREATE CLASS ProjectCreate(SQLModel) with fields: name (str), slug (str), path (str), repo_url (Optional[str]=None), status (str='pending'), onboarding_status (dict[str,Any]=Field(default_factory=dict)), metadata_ (dict[str,Any]=Field(default_factory=dict)) (`apps/core/session_db/models.py`)
- ⬜ **1.1.2.3**: CREATE CLASS ProjectUpdate(SQLModel) with all optional fields: name, slug, path, repo_url, status, onboarding_status, metadata_ (`apps/core/session_db/models.py`)

#### ⬜ Task 1.1.3: Add Project CRUD operations

**File**: `apps/core/session_db/crud.py`

**Description**: Implement CRUD functions for Project: create_project, get_project, get_project_by_slug, list_projects, list_project_summaries, update_project, delete_project. Follow existing Session CRUD patterns with async/await, optional filtering, pagination support.

**Context to Load**:
- `apps/core/session_db/crud.py` (lines 1-220) - Reference Session CRUD patterns for consistency
- `apps/core/session_db/models.py` (lines project model section) - Access Project model definition created in 1.1.1

**Depends On**: Tasks 1.1.2

**Actions**:
- ⬜ **1.1.3.1**: ADD import Project, ProjectCreate, ProjectUpdate, ProjectSummary from models (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.2**: CREATE FUNCTION create_project(db: AsyncSession, data: ProjectCreate) -> Project: MIRROR create_session pattern (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.3**: CREATE FUNCTION get_project(db: AsyncSession, project_id: UUID) -> Project | None: USE db.get pattern (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.4**: CREATE FUNCTION get_project_by_slug(db: AsyncSession, slug: str) -> Project | None: MIRROR get_session_by_slug (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.5**: CREATE FUNCTION list_projects(db: AsyncSession, status: str|None, limit: int=100, offset: int=0) -> Sequence[Project]: with optional status filter (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.6**: CREATE FUNCTION list_project_summaries(db: AsyncSession, limit: int=100, offset: int=0) -> list[ProjectSummary]: convert to summaries (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.7**: CREATE FUNCTION update_project(db: AsyncSession, project_id: UUID, data: ProjectUpdate) -> Project | None: MIRROR update_session (`apps/core/session_db/crud.py`)
- ⬜ **1.1.3.8**: CREATE FUNCTION delete_project(db: AsyncSession, project_id: UUID) -> bool: MIRROR delete_session (`apps/core/session_db/crud.py`)

#### ⬜ Task 1.1.4: Export Project from package

**File**: `apps/core/session_db/__init__.py`

**Description**: Add Project, ProjectStatus, ProjectCreate, ProjectUpdate, ProjectSummary to package imports and __all__ exports. Add Project CRUD functions to exports. Maintain existing import organization.

**Context to Load**:
- `apps/core/session_db/__init__.py` (lines 1-120) - Understand existing export structure and organization

**Depends On**: Tasks 1.1.3

**Actions**:
- ⬜ **1.1.4.1**: ADD import ProjectStatus, Project, ProjectSummary, ProjectCreate, ProjectUpdate from .models (`apps/core/session_db/__init__.py`)
- ⬜ **1.1.4.2**: ADD import create_project, get_project, get_project_by_slug, list_projects, list_project_summaries, update_project, delete_project from .crud (`apps/core/session_db/__init__.py`)
- ⬜ **1.1.4.3**: UPDATE __all__ list: ADD 'ProjectStatus', 'Project', 'ProjectSummary', 'ProjectCreate', 'ProjectUpdate' to type aliases section (`apps/core/session_db/__init__.py`)
- ⬜ **1.1.4.4**: UPDATE __all__ list: ADD 'create_project', 'get_project', 'get_project_by_slug', 'list_projects', 'list_project_summaries', 'update_project', 'delete_project' to Project CRUD section (`apps/core/session_db/__init__.py`)

### ⬜ Task Group 1.2: FastAPI Backend Setup

**Objective**: Scaffold FastAPI application structure with project CRUD endpoints, database connection, and CORS configuration

#### ⬜ Task 1.2.1: Create FastAPI app structure

**File**: `apps/core/api/`

**Description**: Create the FastAPI application directory structure with main.py entry point, routers directory, and dependencies module. Set up CORS middleware for frontend communication. Configure database lifecycle events (startup/shutdown).

**Context to Load**:
- `apps/core/session_db/database.py` (lines 1-80) - Understand database connection patterns for FastAPI integration

**Actions**:
- ⬜ **1.2.1.1**: CREATE FILE apps/core/api/__init__.py with docstring (`apps/core/api/__init__.py`)
- ⬜ **1.2.1.2**: CREATE FILE apps/core/api/main.py with FastAPI app, CORS middleware, lifespan context manager for db init/close (`apps/core/api/main.py`)
- ⬜ **1.2.1.3**: CREATE FILE apps/core/api/dependencies.py with get_db dependency using get_async_session (`apps/core/api/dependencies.py`)
- ⬜ **1.2.1.4**: CREATE FILE apps/core/api/routers/__init__.py (`apps/core/api/routers/__init__.py`)

#### ⬜ Task 1.2.2: Create projects router

**File**: `apps/core/api/routers/projects.py`

**Description**: Create FastAPI router with CRUD endpoints for projects: GET /projects (list), GET /projects/{id} (get by id), GET /projects/slug/{slug} (get by slug), POST /projects (create), PATCH /projects/{id} (update), DELETE /projects/{id} (delete). Use Pydantic response models.

**Context to Load**:
- `apps/core/session_db/crud.py` (lines project crud section) - Access CRUD functions to call from endpoints
- `apps/core/session_db/models.py` (lines Project DTOs) - Use DTOs as request/response models

**Depends On**: Tasks 1.2.1

**Actions**:
- ⬜ **1.2.2.1**: CREATE FILE apps/core/api/routers/projects.py with APIRouter prefix='/projects' tag='projects' (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.2**: CREATE FUNCTION list_projects endpoint: GET / returning list[ProjectSummary] with optional status filter, limit, offset params (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.3**: CREATE FUNCTION get_project endpoint: GET /{project_id} returning Project with 404 handling (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.4**: CREATE FUNCTION get_project_by_slug endpoint: GET /slug/{slug} returning Project with 404 handling (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.5**: CREATE FUNCTION create_project endpoint: POST / accepting ProjectCreate returning Project status 201 (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.6**: CREATE FUNCTION update_project endpoint: PATCH /{project_id} accepting ProjectUpdate returning Project with 404 handling (`apps/core/api/routers/projects.py`)
- ⬜ **1.2.2.7**: CREATE FUNCTION delete_project endpoint: DELETE /{project_id} returning 204 No Content with 404 handling (`apps/core/api/routers/projects.py`)

#### ⬜ Task 1.2.3: Register router and add health endpoint

**File**: `apps/core/api/main.py`

**Description**: Include projects router in main app. Add health check endpoint at GET /health for deployment verification.

**Context to Load**:
- `apps/core/api/main.py` (lines all) - Update existing main.py with router registration

**Depends On**: Tasks 1.2.2

**Actions**:
- ⬜ **1.2.3.1**: ADD import projects router from .routers.projects (`apps/core/api/main.py`)
- ⬜ **1.2.3.2**: ADD app.include_router(projects.router) to main.py (`apps/core/api/main.py`)
- ⬜ **1.2.3.3**: CREATE FUNCTION health_check: GET /health returning {'status': 'healthy'} (`apps/core/api/main.py`)

### ⬜ Task Group 1.3: Next.js Frontend Scaffold

**Objective**: Initialize Next.js 14+ app with App Router, Tailwind CSS, shadcn/ui components, and Zustand store

#### ⬜ Task 1.3.1: Initialize Next.js project

**File**: `apps/web/`

**Description**: Create Next.js 14+ app with App Router using create-next-app. Configure for TypeScript, Tailwind CSS, ESLint. Set up in apps/web/ directory.

**Context to Load**:
- `apps/README.md` (lines all) - Understand apps directory structure

**Actions**:
- ⬜ **1.3.1.1**: RUN npx create-next-app@latest apps/web --typescript --tailwind --eslint --app --src-dir --import-alias '@/*' --no-git (`apps/web/`)
- ⬜ **1.3.1.2**: UPDATE apps/web/package.json: ADD name='@lai/web' (`apps/web/package.json`)

#### ⬜ Task 1.3.2: Install and configure shadcn/ui

**File**: `apps/web/`

**Description**: Initialize shadcn/ui component library. Install base components: button, card, badge, input for MVP UI.

**Depends On**: Tasks 1.3.1

**Actions**:
- ⬜ **1.3.2.1**: RUN npx shadcn-ui@latest init in apps/web/ (`apps/web/`)
- ⬜ **1.3.2.2**: RUN npx shadcn-ui@latest add button card badge input in apps/web/ (`apps/web/components/ui/`)

#### ⬜ Task 1.3.3: Set up Zustand store

**File**: `apps/web/src/store/`

**Description**: Install Zustand and create projects store with state: projects list, loading state, error state. Actions: fetchProjects, createProject, updateProject, deleteProject.

**Depends On**: Tasks 1.3.1

**Actions**:
- ⬜ **1.3.3.1**: RUN npm install zustand in apps/web/ (`apps/web/package.json`)
- ⬜ **1.3.3.2**: CREATE FILE apps/web/src/store/index.ts exporting all stores (`apps/web/src/store/index.ts`)
- ⬜ **1.3.3.3**: CREATE FILE apps/web/src/store/projects.ts with useProjectsStore: state (projects, isLoading, error), actions (fetchProjects, createProject, updateProject, deleteProject) (`apps/web/src/store/projects.ts`)

#### ⬜ Task 1.3.4: Configure API client

**File**: `apps/web/src/lib/api.ts`

**Description**: Create API client module with base URL configuration, fetch wrapper with error handling, typed API functions for projects endpoints.

**Context to Load**:
- `apps/core/api/routers/projects.py` (lines all) - Match API endpoint signatures

**Depends On**: Tasks 1.3.1

**Actions**:
- ⬜ **1.3.4.1**: CREATE FILE apps/web/src/lib/api.ts with API_BASE_URL from env, fetchApi wrapper function (`apps/web/src/lib/api.ts`)
- ⬜ **1.3.4.2**: CREATE FILE apps/web/src/types/project.ts with Project, ProjectCreate, ProjectUpdate, ProjectSummary TypeScript interfaces (`apps/web/src/types/project.ts`)
- ⬜ **1.3.4.3**: CREATE FILE apps/web/src/lib/projects-api.ts with getProjects, getProject, createProject, updateProject, deleteProject functions (`apps/web/src/lib/projects-api.ts`)
- ⬜ **1.3.4.4**: CREATE FILE apps/web/.env.local with NEXT_PUBLIC_API_URL=http://localhost:8000 (`apps/web/.env.local`)

### ⬜ Task Group 1.4: Projects List UI

**Objective**: Build projects list page that fetches from API and displays project cards with status indicators

#### ⬜ Task 1.4.1: Create ProjectCard component

**File**: `apps/web/src/components/projects/ProjectCard.tsx`

**Description**: Create reusable ProjectCard component displaying: project name, status badge, path, created date. Use shadcn Card and Badge components. Include click handler for navigation.

**Context to Load**:
- `apps/web/src/types/project.ts` (lines all) - Use Project type for props

**Actions**:
- ⬜ **1.4.1.1**: CREATE FILE apps/web/src/components/projects/ProjectCard.tsx with interface ProjectCardProps {project: ProjectSummary}, Card layout, Badge for status, formatted date (`apps/web/src/components/projects/ProjectCard.tsx`)

#### ⬜ Task 1.4.2: Create ProjectsList component

**File**: `apps/web/src/components/projects/ProjectsList.tsx`

**Description**: Create ProjectsList component that uses Zustand store to fetch and display projects. Handle loading state, error state, empty state. Render grid of ProjectCards.

**Context to Load**:
- `apps/web/src/store/projects.ts` (lines all) - Use projects store for state management

**Depends On**: Tasks 1.4.1

**Actions**:
- ⬜ **1.4.2.1**: CREATE FILE apps/web/src/components/projects/ProjectsList.tsx with useEffect to fetch projects, loading spinner, error message, empty state, responsive grid of ProjectCards (`apps/web/src/components/projects/ProjectsList.tsx`)
- ⬜ **1.4.2.2**: CREATE FILE apps/web/src/components/projects/index.ts exporting ProjectCard, ProjectsList (`apps/web/src/components/projects/index.ts`)

#### ⬜ Task 1.4.3: Create projects page

**File**: `apps/web/src/app/projects/page.tsx`

**Description**: Create projects page at /projects route using App Router. Include page header with title, ProjectsList component. This is the main entry point for the projects UI.

**Depends On**: Tasks 1.4.2

**Actions**:
- ⬜ **1.4.3.1**: CREATE FILE apps/web/src/app/projects/page.tsx with 'use client', page title 'Projects', ProjectsList component (`apps/web/src/app/projects/page.tsx`)
- ⬜ **1.4.3.2**: UPDATE apps/web/src/app/page.tsx: redirect to /projects or add link to projects (`apps/web/src/app/page.tsx`)

#### ⬜ Task 1.4.4: Create basic layout

**File**: `apps/web/src/app/layout.tsx`

**Description**: Update root layout with app title, basic navigation header, consistent styling. Set up metadata for SEO.

**Context to Load**:
- `apps/web/src/app/layout.tsx` (lines all) - Modify existing layout

**Actions**:
- ⬜ **1.4.4.1**: UPDATE apps/web/src/app/layout.tsx: ADD metadata title='LAI Session Manager', ADD basic header with app name, ADD container wrapper for main content (`apps/web/src/app/layout.tsx`)

---

## ⬜ Checkpoint 2: Session-Project Link + Swimlane View

**Goal**: Add project_id FK to Session model, create migration, build session API endpoints, and implement the swimlane view showing sessions as horizontal lanes progressing through SPEC→PLAN→BUILD→DOCS phases.

**Prerequisites**: Checkpoints 1

### File Context

### Testing Strategy

**Approach**: Migration verification + API tests + visual swimlane inspection

### ⬜ Task Group 2.1: Session-Project Database Link

**Objective**: Add project_id foreign key to Session model, update Session DTOs, create Alembic migration

#### ⬜ Task 2.1.1: Add project_id FK to Session model

**File**: `apps/core/session_db/models.py`

**Description**: Add project_id UUID foreign key field to Session model with optional relationship. Add Relationship back to Project. Update Session to support project association.

**Context to Load**:
- `apps/core/session_db/models.py` (lines 78-215) - Understand existing Session model structure

**Actions**:
- ⬜ **2.1.1.1**: ADD field project_id: Optional[UUID] = Field(default=None, foreign_key='projects.id', index=True) to Session model (`apps/core/session_db/models.py`)
- ⬜ **2.1.1.2**: ADD relationship project: Optional['Project'] = Relationship(back_populates='sessions') to Session model (`apps/core/session_db/models.py`)

#### ⬜ Task 2.1.2: Update Session DTOs

**File**: `apps/core/session_db/models.py`

**Description**: Add project_id to SessionCreate and SessionUpdate DTOs. Add project_id to SessionSummary for list views.

**Context to Load**:
- `apps/core/session_db/models.py` (lines SessionCreate and SessionUpdate sections) - Update existing DTOs

**Depends On**: Tasks 2.1.1

**Actions**:
- ⬜ **2.1.2.1**: ADD field project_id: Optional[UUID] = None to SessionCreate (`apps/core/session_db/models.py`)
- ⬜ **2.1.2.2**: ADD field project_id: Optional[UUID] = None to SessionUpdate (`apps/core/session_db/models.py`)
- ⬜ **2.1.2.3**: ADD field project_id: Optional[UUID] to SessionSummary (`apps/core/session_db/models.py`)

#### ⬜ Task 2.1.3: Update Session CRUD for project filtering

**File**: `apps/core/session_db/crud.py`

**Description**: Update list_sessions and list_session_summaries to accept optional project_id filter. Update create_session to handle project_id.

**Context to Load**:
- `apps/core/session_db/crud.py` (lines 99-165) - Update list_sessions function

**Depends On**: Tasks 2.1.2

**Actions**:
- ⬜ **2.1.3.1**: UPDATE FUNCTION list_sessions: ADD parameter project_id: UUID | None = None, ADD where clause for project_id filter (`apps/core/session_db/crud.py`)
- ⬜ **2.1.3.2**: UPDATE FUNCTION create_session: ADD project_id assignment from data (`apps/core/session_db/crud.py`)
- ⬜ **2.1.3.3**: UPDATE FUNCTION list_session_summaries: ADD project_id to summary conversion (`apps/core/session_db/crud.py`)

#### ⬜ Task 2.1.4: Import Project in database.py for table creation

**File**: `apps/core/session_db/database.py`

**Description**: Import Project model in database.py to ensure it's registered for SQLModel table creation.

**Context to Load**:
- `apps/core/session_db/database.py` (lines 1-35) - See existing model imports

**Actions**:
- ⬜ **2.1.4.1**: ADD import Project to model imports in database.py (`apps/core/session_db/database.py`)

### ⬜ Task Group 2.2: Sessions API Endpoints

**Objective**: Create FastAPI router for sessions with CRUD endpoints and project-scoped queries

#### ⬜ Task 2.2.1: Create sessions router

**File**: `apps/core/api/routers/sessions.py`

**Description**: Create FastAPI router with session endpoints: GET /sessions (list with project filter), GET /sessions/{id}, GET /projects/{project_id}/sessions (project-scoped). Support filtering by status.

**Context to Load**:
- `apps/core/api/routers/projects.py` (lines all) - Follow established router patterns
- `apps/core/session_db/crud.py` (lines session crud section) - Use session CRUD functions

**Actions**:
- ⬜ **2.2.1.1**: CREATE FILE apps/core/api/routers/sessions.py with APIRouter prefix='/sessions' tag='sessions' (`apps/core/api/routers/sessions.py`)
- ⬜ **2.2.1.2**: CREATE FUNCTION list_sessions endpoint: GET / returning list[SessionSummary] with optional status, project_id, limit, offset params (`apps/core/api/routers/sessions.py`)
- ⬜ **2.2.1.3**: CREATE FUNCTION get_session endpoint: GET /{session_id} returning Session with 404 handling (`apps/core/api/routers/sessions.py`)
- ⬜ **2.2.1.4**: CREATE FUNCTION get_session_by_slug endpoint: GET /slug/{slug} returning Session with 404 handling (`apps/core/api/routers/sessions.py`)

#### ⬜ Task 2.2.2: Add project-sessions nested endpoint

**File**: `apps/core/api/routers/projects.py`

**Description**: Add endpoint to projects router: GET /projects/{project_id}/sessions to list sessions for a specific project.

**Context to Load**:
- `apps/core/api/routers/projects.py` (lines all) - Add to existing projects router

**Depends On**: Tasks 2.2.1

**Actions**:
- ⬜ **2.2.2.1**: CREATE FUNCTION list_project_sessions endpoint: GET /{project_id}/sessions returning list[SessionSummary] filtered by project_id (`apps/core/api/routers/projects.py`)

#### ⬜ Task 2.2.3: Register sessions router

**File**: `apps/core/api/main.py`

**Description**: Include sessions router in main FastAPI app.

**Context to Load**:
- `apps/core/api/main.py` (lines all) - Add router registration

**Depends On**: Tasks 2.2.1

**Actions**:
- ⬜ **2.2.3.1**: ADD import sessions router from .routers.sessions (`apps/core/api/main.py`)
- ⬜ **2.2.3.2**: ADD app.include_router(sessions.router) (`apps/core/api/main.py`)

### ⬜ Task Group 2.3: Frontend Sessions Store and API

**Objective**: Add sessions state management and API client functions in frontend

#### ⬜ Task 2.3.1: Add Session types

**File**: `apps/web/src/types/session.ts`

**Description**: Create TypeScript interfaces for Session, SessionSummary matching backend models. Include phase status type.

**Context to Load**:
- `apps/core/session_db/models.py` (lines Session model section) - Match backend types

**Actions**:
- ⬜ **2.3.1.1**: CREATE FILE apps/web/src/types/session.ts with Session, SessionSummary, SessionStatus types (`apps/web/src/types/session.ts`)

#### ⬜ Task 2.3.2: Add sessions API client

**File**: `apps/web/src/lib/sessions-api.ts`

**Description**: Create API functions: getSessions, getSession, getProjectSessions for fetching session data.

**Context to Load**:
- `apps/web/src/lib/api.ts` (lines all) - Use existing API helpers

**Depends On**: Tasks 2.3.1

**Actions**:
- ⬜ **2.3.2.1**: CREATE FILE apps/web/src/lib/sessions-api.ts with getSessions, getSession, getSessionBySlug, getProjectSessions functions (`apps/web/src/lib/sessions-api.ts`)

#### ⬜ Task 2.3.3: Add sessions Zustand store

**File**: `apps/web/src/store/sessions.ts`

**Description**: Create Zustand store for sessions: state (sessions by project, current session, loading), actions (fetchProjectSessions, setCurrentSession).

**Context to Load**:
- `apps/web/src/store/projects.ts` (lines all) - Follow existing store patterns

**Depends On**: Tasks 2.3.2

**Actions**:
- ⬜ **2.3.3.1**: CREATE FILE apps/web/src/store/sessions.ts with useSessionsStore: state (sessionsByProject Map, currentSession, isLoading), actions (fetchProjectSessions, setCurrentSession) (`apps/web/src/store/sessions.ts`)
- ⬜ **2.3.3.2**: UPDATE apps/web/src/store/index.ts: ADD export for sessions store (`apps/web/src/store/index.ts`)

### ⬜ Task Group 2.4: Swimlane View Component

**Objective**: Build the visual swimlane component showing sessions as horizontal lanes with phase progression

#### ⬜ Task 2.4.1: Create PhaseIndicator component

**File**: `apps/web/src/components/sessions/PhaseIndicator.tsx`

**Description**: Create component showing a single phase (SPEC/PLAN/BUILD/DOCS) with status indicator: checkmark for complete, dot for in-progress, empty for not started. Clickable for drill-down.

**Actions**:
- ⬜ **2.4.1.1**: CREATE FILE apps/web/src/components/sessions/PhaseIndicator.tsx with props: phase, status, onClick. Visual states: complete (green check), in_progress (blue dot), pending (gray empty) (`apps/web/src/components/sessions/PhaseIndicator.tsx`)

#### ⬜ Task 2.4.2: Create SessionLane component

**File**: `apps/web/src/components/sessions/SessionLane.tsx`

**Description**: Create horizontal lane component showing session name and 4 phase indicators (SPEC→PLAN→BUILD→DOCS). Each phase clickable to navigate to drill-down view.

**Context to Load**:
- `apps/web/src/components/sessions/PhaseIndicator.tsx` (lines all) - Use PhaseIndicator component

**Depends On**: Tasks 2.4.1

**Actions**:
- ⬜ **2.4.2.1**: CREATE FILE apps/web/src/components/sessions/SessionLane.tsx with session prop, horizontal layout, session name/title, 4 PhaseIndicators connected by arrows/lines (`apps/web/src/components/sessions/SessionLane.tsx`)

#### ⬜ Task 2.4.3: Create Swimlane component

**File**: `apps/web/src/components/sessions/Swimlane.tsx`

**Description**: Create container component that renders multiple SessionLane components vertically. Handle loading state, empty state (no sessions).

**Depends On**: Tasks 2.4.2

**Actions**:
- ⬜ **2.4.3.1**: CREATE FILE apps/web/src/components/sessions/Swimlane.tsx with sessions array prop, vertical stack of SessionLanes, loading spinner, empty state message (`apps/web/src/components/sessions/Swimlane.tsx`)
- ⬜ **2.4.3.2**: CREATE FILE apps/web/src/components/sessions/index.ts exporting PhaseIndicator, SessionLane, Swimlane (`apps/web/src/components/sessions/index.ts`)

#### ⬜ Task 2.4.4: Create Project detail page with swimlane

**File**: `apps/web/src/app/projects/[slug]/page.tsx`

**Description**: Create project detail page at /projects/[slug]. Fetch project by slug, fetch sessions for project, render Swimlane component with sessions.

**Context to Load**:
- `apps/web/src/app/projects/page.tsx` (lines all) - Follow existing page patterns

**Depends On**: Tasks 2.4.3

**Actions**:
- ⬜ **2.4.4.1**: CREATE FILE apps/web/src/app/projects/[slug]/page.tsx with 'use client', useParams for slug, fetch project and sessions, render project header + Swimlane (`apps/web/src/app/projects/[slug]/page.tsx`)
- ⬜ **2.4.4.2**: UPDATE apps/web/src/components/projects/ProjectCard.tsx: ADD Link wrapper to navigate to /projects/{slug} on click (`apps/web/src/components/projects/ProjectCard.tsx`)

---

## ⬜ Checkpoint 3: Phase Drill-Down Views

**Goal**: Implement phase-specific views: SPEC (render spec.md markdown), PLAN (render plan.json as visual hierarchy), BUILD (list agents with status), DOCS (show doc updates summary). Click-through navigation from swimlane to phase details.

**Prerequisites**: Checkpoints 2

### File Context

### Testing Strategy

**Approach**: Manual navigation testing + content rendering verification

### ⬜ Task Group 3.1: Session Artifacts API

**Objective**: Create API endpoints to serve session artifacts (spec.md content, plan.json, state.json) from filesystem

#### ⬜ Task 3.1.1: Add session artifacts endpoints

**File**: `apps/core/api/routers/sessions.py`

**Description**: Add endpoints to serve session artifacts: GET /sessions/{slug}/spec (returns spec.md content), GET /sessions/{slug}/plan (returns plan.json), GET /sessions/{slug}/state (returns state.json). Read from filesystem using session_dir.

**Context to Load**:
- `apps/core/api/routers/sessions.py` (lines all) - Add to existing sessions router

**Actions**:
- ⬜ **3.1.1.1**: CREATE FUNCTION get_session_spec endpoint: GET /{slug}/spec returning {content: string} by reading spec.md from session folder (`apps/core/api/routers/sessions.py`)
- ⬜ **3.1.1.2**: CREATE FUNCTION get_session_plan endpoint: GET /{slug}/plan returning plan.json as dict with 404 if not exists (`apps/core/api/routers/sessions.py`)
- ⬜ **3.1.1.3**: CREATE FUNCTION get_session_state endpoint: GET /{slug}/state returning state.json as dict (`apps/core/api/routers/sessions.py`)

#### ⬜ Task 3.1.2: Add agents list endpoint

**File**: `apps/core/api/routers/agents.py`

**Description**: Create agents router with endpoint to list agents for a session. Returns agent summaries with status, type, cost info.

**Context to Load**:
- `apps/core/session_db/crud.py` (lines agent crud section) - Use agent CRUD functions

**Actions**:
- ⬜ **3.1.2.1**: CREATE FILE apps/core/api/routers/agents.py with APIRouter prefix='/agents' tag='agents' (`apps/core/api/routers/agents.py`)
- ⬜ **3.1.2.2**: CREATE FUNCTION list_session_agents endpoint: GET /session/{session_id} returning list[AgentSummary] (`apps/core/api/routers/agents.py`)
- ⬜ **3.1.2.3**: ADD import and app.include_router(agents.router) to main.py (`apps/core/api/main.py`)

### ⬜ Task Group 3.2: Frontend Phase API and Types

**Objective**: Add frontend API functions and types for fetching phase content

#### ⬜ Task 3.2.1: Add phase content API functions

**File**: `apps/web/src/lib/sessions-api.ts`

**Description**: Add functions to fetch phase content: getSessionSpec, getSessionPlan, getSessionState, getSessionAgents.

**Context to Load**:
- `apps/web/src/lib/sessions-api.ts` (lines all) - Add to existing sessions API

**Actions**:
- ⬜ **3.2.1.1**: ADD FUNCTION getSessionSpec(slug: string) -> Promise<{content: string}> (`apps/web/src/lib/sessions-api.ts`)
- ⬜ **3.2.1.2**: ADD FUNCTION getSessionPlan(slug: string) -> Promise<Plan> (`apps/web/src/lib/sessions-api.ts`)
- ⬜ **3.2.1.3**: ADD FUNCTION getSessionState(slug: string) -> Promise<SessionState> (`apps/web/src/lib/sessions-api.ts`)
- ⬜ **3.2.1.4**: ADD FUNCTION getSessionAgents(sessionId: string) -> Promise<AgentSummary[]> (`apps/web/src/lib/sessions-api.ts`)

#### ⬜ Task 3.2.2: Add plan and agent types

**File**: `apps/web/src/types/`

**Description**: Create TypeScript types for plan.json structure (Checkpoint, TaskGroup, Task, Action) and Agent types.

**Context to Load**:
- `.claude/skills/session/plan/templates/plan.json` (lines all) - Match plan.json structure
- `apps/core/session_db/models.py` (lines Agent and AgentSummary sections) - Match agent types

**Actions**:
- ⬜ **3.2.2.1**: CREATE FILE apps/web/src/types/plan.ts with Plan, Checkpoint, TaskGroup, Task, Action interfaces (`apps/web/src/types/plan.ts`)
- ⬜ **3.2.2.2**: CREATE FILE apps/web/src/types/agent.ts with Agent, AgentSummary, AgentStatus, AgentType interfaces (`apps/web/src/types/agent.ts`)
- ⬜ **3.2.2.3**: CREATE FILE apps/web/src/types/index.ts exporting all types (`apps/web/src/types/index.ts`)

### ⬜ Task Group 3.3: Phase View Components

**Objective**: Create drill-down view components for each phase (SPEC, PLAN, BUILD, DOCS)

#### ⬜ Task 3.3.1: Create SpecView component

**File**: `apps/web/src/components/phases/SpecView.tsx`

**Description**: Create component to render spec.md content as formatted markdown. Use react-markdown for rendering. Handle loading state.

**Actions**:
- ⬜ **3.3.1.1**: RUN npm install react-markdown in apps/web/ (`apps/web/package.json`)
- ⬜ **3.3.1.2**: CREATE FILE apps/web/src/components/phases/SpecView.tsx with sessionSlug prop, fetch spec content, render with ReactMarkdown, loading state (`apps/web/src/components/phases/SpecView.tsx`)

#### ⬜ Task 3.3.2: Create PlanView component

**File**: `apps/web/src/components/phases/PlanView.tsx`

**Description**: Create component to render plan.json as visual hierarchy: checkpoints as cards, task groups as collapsible sections, tasks as list items with status indicators.

**Context to Load**:
- `apps/web/src/types/plan.ts` (lines all) - Use plan types

**Depends On**: Tasks 3.3.1

**Actions**:
- ⬜ **3.3.2.1**: CREATE FILE apps/web/src/components/phases/CheckpointCard.tsx with checkpoint prop, shows title, goal, progress bar, expandable task groups (`apps/web/src/components/phases/CheckpointCard.tsx`)
- ⬜ **3.3.2.2**: CREATE FILE apps/web/src/components/phases/PlanView.tsx with sessionSlug prop, fetch plan, render list of CheckpointCards, loading state (`apps/web/src/components/phases/PlanView.tsx`)

#### ⬜ Task 3.3.3: Create BuildView component

**File**: `apps/web/src/components/phases/BuildView.tsx`

**Description**: Create component to show build agents. List agents with type, status badge, checkpoint info, cost. Click agent to navigate to agent detail (future).

**Context to Load**:
- `apps/web/src/types/agent.ts` (lines all) - Use agent types

**Depends On**: Tasks 3.3.2

**Actions**:
- ⬜ **3.3.3.1**: CREATE FILE apps/web/src/components/phases/AgentCard.tsx with agent prop, shows type, status badge, checkpoint, tokens, cost (`apps/web/src/components/phases/AgentCard.tsx`)
- ⬜ **3.3.3.2**: CREATE FILE apps/web/src/components/phases/BuildView.tsx with sessionId prop, fetch agents, render AgentCards grid, loading/empty states (`apps/web/src/components/phases/BuildView.tsx`)

#### ⬜ Task 3.3.4: Create DocsView component

**File**: `apps/web/src/components/phases/DocsView.tsx`

**Description**: Create simple component showing doc updates from state.json. Display list of updated files or 'No documentation updates' message.

**Depends On**: Tasks 3.3.3

**Actions**:
- ⬜ **3.3.4.1**: CREATE FILE apps/web/src/components/phases/DocsView.tsx with sessionSlug prop, fetch state, show doc_updates list or empty message (`apps/web/src/components/phases/DocsView.tsx`)
- ⬜ **3.3.4.2**: CREATE FILE apps/web/src/components/phases/index.ts exporting SpecView, PlanView, BuildView, DocsView (`apps/web/src/components/phases/index.ts`)

### ⬜ Task Group 3.4: Phase Drill-Down Page

**Objective**: Create dynamic route for phase drill-down with tab-based navigation

#### ⬜ Task 3.4.1: Create session phase page

**File**: `apps/web/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`

**Description**: Create session detail page with tabs for each phase (SPEC, PLAN, BUILD, DOCS). Default to current phase based on session status. Render appropriate phase view component.

**Actions**:
- ⬜ **3.4.1.1**: RUN npx shadcn-ui@latest add tabs in apps/web/ (`apps/web/components/ui/tabs.tsx`)
- ⬜ **3.4.1.2**: CREATE FILE apps/web/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx with 'use client', useParams, tabs for SPEC/PLAN/BUILD/DOCS, render phase views (`apps/web/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)

#### ⬜ Task 3.4.2: Update PhaseIndicator to navigate

**File**: `apps/web/src/components/sessions/PhaseIndicator.tsx`

**Description**: Update PhaseIndicator to use Next.js Link for navigation. Clicking a phase navigates to /projects/[slug]/sessions/[sessionSlug]?phase=[phase].

**Context to Load**:
- `apps/web/src/components/sessions/PhaseIndicator.tsx` (lines all) - Add navigation behavior

**Depends On**: Tasks 3.4.1

**Actions**:
- ⬜ **3.4.2.1**: UPDATE apps/web/src/components/sessions/PhaseIndicator.tsx: ADD Link wrapper with href to session phase page, ADD projectSlug and sessionSlug to props (`apps/web/src/components/sessions/PhaseIndicator.tsx`)
- ⬜ **3.4.2.2**: UPDATE apps/web/src/components/sessions/SessionLane.tsx: pass projectSlug and sessionSlug to PhaseIndicators (`apps/web/src/components/sessions/SessionLane.tsx`)

---

## ⬜ Checkpoint 4: Hook Logger DB Integration + Events View

**Goal**: Modify universal_hook_logger.py for dual-write (JSONL + database). Add agent events API endpoint. Build agent detail view with event timeline showing tool calls, responses, and thinking blocks.

**Prerequisites**: Checkpoints 3

### File Context

### Testing Strategy

**Approach**: Hook execution test + event ingestion verification + timeline rendering

### ⬜ Task Group 4.1: Hook Logger Dual-Write

**Objective**: Modify universal_hook_logger.py to write events to both JSONL files and PostgreSQL database

#### ⬜ Task 4.1.1: Add database writer module

**File**: `.claude/hooks/logging/db_writer.py`

**Description**: Create async database writer module that creates AgentLog entries. Import from session_db, handle connection pooling for hook context. Include error handling to not block hook execution.

**Context to Load**:
- `.claude/hooks/logging/universal_hook_logger.py` (lines all) - Understand current hook structure
- `apps/core/session_db/crud.py` (lines create_agent_log section) - Use AgentLog creation pattern

**Actions**:
- ⬜ **4.1.1.1**: CREATE FILE .claude/hooks/logging/db_writer.py with async write_event_to_db function, imports session_db, handles connection setup/teardown, error handling (`.claude/hooks/logging/db_writer.py`)

#### ⬜ Task 4.1.2: Update hook logger for dual-write

**File**: `.claude/hooks/logging/universal_hook_logger.py`

**Description**: Modify main() to call both JSONL writer and database writer. Add SESSION_DB_URL env check to enable/disable DB write. Make DB write non-blocking.

**Context to Load**:
- `.claude/hooks/logging/universal_hook_logger.py` (lines all) - Modify existing logger
- `.claude/hooks/logging/db_writer.py` (lines all) - Import db writer

**Depends On**: Tasks 4.1.1

**Actions**:
- ⬜ **4.1.2.1**: UPDATE universal_hook_logger.py: ADD import db_writer, ADD env check for SESSION_DB_URL, ADD call to db_writer.write_event_to_db in main() (`.claude/hooks/logging/universal_hook_logger.py`)
- ⬜ **4.1.2.2**: ADD error handling around db write to ensure JSONL write always succeeds even if DB fails (`.claude/hooks/logging/universal_hook_logger.py`)

#### ⬜ Task 4.1.3: Add pyproject.toml for hook dependencies

**File**: `.claude/hooks/logging/pyproject.toml`

**Description**: Create pyproject.toml with dependencies needed for database writing (asyncpg, sqlmodel, session_db as local path).

**Actions**:
- ⬜ **4.1.3.1**: CREATE FILE .claude/hooks/logging/pyproject.toml with [project] section, dependencies for asyncpg, sqlmodel, python-dotenv (`.claude/hooks/logging/pyproject.toml`)

### ⬜ Task Group 4.2: Agent Events API

**Objective**: Create API endpoints for querying agent logs/events

#### ⬜ Task 4.2.1: Add agent logs endpoints

**File**: `apps/core/api/routers/agents.py`

**Description**: Add endpoints: GET /agents/{agent_id} (agent detail), GET /agents/{agent_id}/logs (event timeline with pagination and filtering).

**Context to Load**:
- `apps/core/api/routers/agents.py` (lines all) - Add to existing agents router
- `apps/core/session_db/crud.py` (lines agent log crud section) - Use log query functions

**Actions**:
- ⬜ **4.2.1.1**: CREATE FUNCTION get_agent endpoint: GET /{agent_id} returning Agent with full details (`apps/core/api/routers/agents.py`)
- ⬜ **4.2.1.2**: CREATE FUNCTION list_agent_logs endpoint: GET /{agent_id}/logs returning list[AgentLog] with event_category filter, limit, offset params (`apps/core/api/routers/agents.py`)

### ⬜ Task Group 4.3: Agent Events UI

**Objective**: Build agent detail view with event timeline

#### ⬜ Task 4.3.1: Add agent events API and types

**File**: `apps/web/src/lib/agents-api.ts`

**Description**: Create API functions for agent detail and logs. Add AgentLog TypeScript type.

**Context to Load**:
- `apps/core/session_db/models.py` (lines AgentLog section) - Match AgentLog type

**Actions**:
- ⬜ **4.3.1.1**: CREATE FILE apps/web/src/lib/agents-api.ts with getAgent, getAgentLogs functions (`apps/web/src/lib/agents-api.ts`)
- ⬜ **4.3.1.2**: UPDATE apps/web/src/types/agent.ts: ADD AgentLog interface with all fields (`apps/web/src/types/agent.ts`)

#### ⬜ Task 4.3.2: Create EventTimeline component

**File**: `apps/web/src/components/agents/EventTimeline.tsx`

**Description**: Create timeline component showing events chronologically. Different rendering for hook events (tool use), response blocks, phase transitions. Expandable details.

**Depends On**: Tasks 4.3.1

**Actions**:
- ⬜ **4.3.2.1**: CREATE FILE apps/web/src/components/agents/EventItem.tsx with event prop, different renders for hook/response/phase events, expandable content (`apps/web/src/components/agents/EventItem.tsx`)
- ⬜ **4.3.2.2**: CREATE FILE apps/web/src/components/agents/EventTimeline.tsx with agentId prop, fetch logs, render EventItems in chronological order, load more pagination (`apps/web/src/components/agents/EventTimeline.tsx`)

#### ⬜ Task 4.3.3: Create agent detail page

**File**: `apps/web/src/app/agents/[agentId]/page.tsx`

**Description**: Create agent detail page showing agent info header and EventTimeline. Link from AgentCard in BuildView.

**Depends On**: Tasks 4.3.2

**Actions**:
- ⬜ **4.3.3.1**: CREATE FILE apps/web/src/app/agents/[agentId]/page.tsx with 'use client', fetch agent, show header with type/status/model/cost, render EventTimeline (`apps/web/src/app/agents/[agentId]/page.tsx`)
- ⬜ **4.3.3.2**: UPDATE apps/web/src/components/phases/AgentCard.tsx: ADD Link to /agents/{agentId} (`apps/web/src/components/phases/AgentCard.tsx`)
- ⬜ **4.3.3.3**: CREATE FILE apps/web/src/components/agents/index.ts exporting EventItem, EventTimeline (`apps/web/src/components/agents/index.ts`)

---

## ⬜ Checkpoint 5: Polish, Refinement, and Edge Cases

**Goal**: Add loading states, error handling, empty states, status indicators. Implement project onboarding flow (path validation, .claude directory check). Final UI polish with consistent styling.

**Prerequisites**: Checkpoints 4

### File Context

### Testing Strategy

**Approach**: End-to-end user flow testing + edge case verification

### ⬜ Task Group 5.1: Project Onboarding Flow

**Objective**: Implement project creation with path validation and .claude directory checks

#### ⬜ Task 5.1.1: Add project onboarding API endpoint

**File**: `apps/core/api/routers/projects.py`

**Description**: Add POST /projects/onboard endpoint that validates path exists, checks for .claude directory, creates project with onboarding_status tracking.

**Context to Load**:
- `apps/core/api/routers/projects.py` (lines all) - Add to existing router
- `agents/sessions/2026-02-11_build-initial-management-ui_mn3z2n/spec.md` (lines 102-128) - Reference onboarding requirements

**Actions**:
- ⬜ **5.1.1.1**: CREATE FUNCTION onboard_project endpoint: POST /onboard accepting {name, path}, validates path exists, checks .claude dir, returns Project with onboarding_status (`apps/core/api/routers/projects.py`)

#### ⬜ Task 5.1.2: Create onboarding dialog in frontend

**File**: `apps/web/src/components/projects/OnboardingDialog.tsx`

**Description**: Create dialog/modal for onboarding a new project. Form with name and path inputs. Display validation results. Show onboarding status after creation.

**Depends On**: Tasks 5.1.1

**Actions**:
- ⬜ **5.1.2.1**: RUN npx shadcn-ui@latest add dialog in apps/web/ (`apps/web/components/ui/dialog.tsx`)
- ⬜ **5.1.2.2**: CREATE FILE apps/web/src/components/projects/OnboardingDialog.tsx with form inputs, submit handler calling onboard API, validation feedback, success state (`apps/web/src/components/projects/OnboardingDialog.tsx`)
- ⬜ **5.1.2.3**: UPDATE apps/web/src/app/projects/page.tsx: ADD 'Add Project' button that opens OnboardingDialog (`apps/web/src/app/projects/page.tsx`)

### ⬜ Task Group 5.2: Loading and Error States

**Objective**: Add consistent loading spinners, error messages, and empty states across all views

#### ⬜ Task 5.2.1: Create shared UI components

**File**: `apps/web/src/components/shared/`

**Description**: Create reusable LoadingSpinner, ErrorMessage, and EmptyState components with consistent styling.

**Actions**:
- ⬜ **5.2.1.1**: CREATE FILE apps/web/src/components/shared/LoadingSpinner.tsx with size variants (sm, md, lg), centered option (`apps/web/src/components/shared/LoadingSpinner.tsx`)
- ⬜ **5.2.1.2**: CREATE FILE apps/web/src/components/shared/ErrorMessage.tsx with message prop, retry button option, styled alert (`apps/web/src/components/shared/ErrorMessage.tsx`)
- ⬜ **5.2.1.3**: CREATE FILE apps/web/src/components/shared/EmptyState.tsx with title, description, icon, action button props (`apps/web/src/components/shared/EmptyState.tsx`)
- ⬜ **5.2.1.4**: CREATE FILE apps/web/src/components/shared/index.ts exporting all shared components (`apps/web/src/components/shared/index.ts`)

#### ⬜ Task 5.2.2: Update list components with states

**File**: `apps/web/src/components/`

**Description**: Update ProjectsList, Swimlane, BuildView, EventTimeline to use shared LoadingSpinner, ErrorMessage, EmptyState components.

**Context to Load**:
- `apps/web/src/components/shared/index.ts` (lines all) - Import shared components

**Depends On**: Tasks 5.2.1

**Actions**:
- ⬜ **5.2.2.1**: UPDATE apps/web/src/components/projects/ProjectsList.tsx: USE LoadingSpinner, ErrorMessage, EmptyState (`apps/web/src/components/projects/ProjectsList.tsx`)
- ⬜ **5.2.2.2**: UPDATE apps/web/src/components/sessions/Swimlane.tsx: USE LoadingSpinner, ErrorMessage, EmptyState for no sessions (`apps/web/src/components/sessions/Swimlane.tsx`)
- ⬜ **5.2.2.3**: UPDATE apps/web/src/components/phases/BuildView.tsx: USE LoadingSpinner, ErrorMessage, EmptyState for no agents (`apps/web/src/components/phases/BuildView.tsx`)
- ⬜ **5.2.2.4**: UPDATE apps/web/src/components/agents/EventTimeline.tsx: USE LoadingSpinner, ErrorMessage, EmptyState for no events (`apps/web/src/components/agents/EventTimeline.tsx`)

### ⬜ Task Group 5.3: Visual Polish

**Objective**: Final styling improvements, consistent spacing, hover states, transitions

#### ⬜ Task 5.3.1: Add status color utilities

**File**: `apps/web/src/lib/utils.ts`

**Description**: Create utility functions for consistent status colors: project status, session phase status, agent status. Map to Tailwind color classes.

**Actions**:
- ⬜ **5.3.1.1**: CREATE FUNCTION getProjectStatusColor(status) returning Tailwind color classes for badge variants (`apps/web/src/lib/utils.ts`)
- ⬜ **5.3.1.2**: CREATE FUNCTION getPhaseStatusColor(status) returning colors for complete/in_progress/pending phases (`apps/web/src/lib/utils.ts`)
- ⬜ **5.3.1.3**: CREATE FUNCTION getAgentStatusColor(status) returning colors for agent statuses (`apps/web/src/lib/utils.ts`)

#### ⬜ Task 5.3.2: Add hover and transition effects

**File**: `apps/web/src/components/`

**Description**: Add hover effects to cards, smooth transitions on state changes, cursor pointers on clickable elements.

**Depends On**: Tasks 5.3.1

**Actions**:
- ⬜ **5.3.2.1**: UPDATE apps/web/src/components/projects/ProjectCard.tsx: ADD hover:shadow-md transition-shadow cursor-pointer (`apps/web/src/components/projects/ProjectCard.tsx`)
- ⬜ **5.3.2.2**: UPDATE apps/web/src/components/sessions/SessionLane.tsx: ADD hover effect, transition styles (`apps/web/src/components/sessions/SessionLane.tsx`)
- ⬜ **5.3.2.3**: UPDATE apps/web/src/components/phases/AgentCard.tsx: ADD hover effect, transition styles (`apps/web/src/components/phases/AgentCard.tsx`)

#### ⬜ Task 5.3.3: Add breadcrumb navigation

**File**: `apps/web/src/components/shared/Breadcrumbs.tsx`

**Description**: Create breadcrumb component for deep navigation: Projects > Project Name > Session Name > Phase. Add to relevant pages.

**Actions**:
- ⬜ **5.3.3.1**: CREATE FILE apps/web/src/components/shared/Breadcrumbs.tsx with items array prop, separator, Link for each item (`apps/web/src/components/shared/Breadcrumbs.tsx`)
- ⬜ **5.3.3.2**: UPDATE apps/web/src/app/projects/[slug]/page.tsx: ADD Breadcrumbs (Projects > {project.name}) (`apps/web/src/app/projects/[slug]/page.tsx`)
- ⬜ **5.3.3.3**: UPDATE apps/web/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx: ADD Breadcrumbs (Projects > {project.name} > {session.title}) (`apps/web/src/app/projects/[slug]/sessions/[sessionSlug]/page.tsx`)
- ⬜ **5.3.3.4**: UPDATE apps/web/src/app/agents/[agentId]/page.tsx: ADD Breadcrumbs (back to session) (`apps/web/src/app/agents/[agentId]/page.tsx`)

---

---
*Auto-generated from plan.json on 2026-02-11 16:21*