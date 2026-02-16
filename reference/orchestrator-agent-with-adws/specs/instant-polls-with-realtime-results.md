# Plan: Instant Polls with Real-Time Results

## Task Description
Create a lightweight instant polls application in `apps/polls/` that allows users to create multiple-choice polls, share them via URL (no authentication required), and view real-time results with simple bar chart visualization. The app will use SQLite for storage with basic duplicate vote prevention based on browser fingerprinting.

## Objective
Build a complete, self-contained polling application with:
- Poll creation (title + multiple choice options)
- Shareable unique URLs for each poll
- Vote submission with duplicate prevention
- Real-time results visualization using simple bar charts
- SQLite database for persistent storage

## Problem Statement
Users need a quick, frictionless way to create and share polls without requiring account registration or complex setup. The solution must be lightweight, easy to deploy, and provide immediate feedback through real-time results visualization.

## Solution Approach
Build a FastAPI backend with SQLite storage and a simple HTML/JavaScript frontend served as static files. Use WebSocket for real-time vote updates and browser fingerprinting (combination of IP + User-Agent hash) for duplicate vote prevention. Keep the architecture simple and self-contained within the `apps/polls/` directory.

## Relevant Files
Use these files to understand patterns:

- `apps/pomodoro_timer/main.py` - CLI app structure, Typer patterns
- `apps/pomodoro_timer/storage.py` - Local storage patterns
- `apps/orchestrator_3_stream/backend/main.py` - FastAPI patterns, WebSocket handling
- `apps/orchestrator_3_stream/backend/modules/config.py` - Configuration patterns
- `apps/orchestrator_3_stream/backend/modules/logger.py` - Logging patterns

### New Files
The following files will be created:

```
apps/polls/
├── pyproject.toml           # UV project configuration
├── .python-version          # Python 3.12
├── .env.sample              # Environment template
├── README.md                # Usage documentation
├── main.py                  # FastAPI application entry point
├── modules/
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite operations
│   ├── models.py            # Pydantic models
│   └── websocket_manager.py # WebSocket connection manager
├── static/
│   ├── index.html           # Poll creation page
│   ├── poll.html            # Poll voting/results page
│   ├── css/
│   │   └── styles.css       # Styling
│   └── js/
│       ├── create.js        # Poll creation logic
│       └── poll.js          # Voting and results logic
├── start.sh                 # Launcher script
└── tests/
    ├── __init__.py
    ├── conftest.py          # Pytest fixtures
    └── test_polls.py        # Integration tests
```

## Implementation Phases

### Phase 1: Foundation
- Set up project structure with UV
- Create SQLite database schema and models
- Implement core database operations (CRUD for polls and votes)
- Set up configuration management

### Phase 2: Core Implementation
- Build FastAPI REST endpoints for poll management
- Implement WebSocket for real-time updates
- Add duplicate vote prevention logic
- Create Pydantic models for request/response validation

### Phase 3: Integration & Polish
- Build frontend HTML/CSS/JS for poll creation and voting
- Implement bar chart visualization
- Add shareable link generation
- Write integration tests
- Create documentation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Initialize Project Structure
- Create `apps/polls/` directory
- Initialize UV project with `uv init --python 3.12`
- Add dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `python-dotenv`, `rich`, `aiosqlite`
- Create `.python-version` file with `3.12`
- Create directory structure: `modules/`, `static/`, `static/css/`, `static/js/`, `tests/`

### 2. Create Configuration Module
- Create `modules/config.py` with environment variable loading
- Define settings: `DATABASE_PATH`, `HOST`, `PORT`, `DEBUG`
- Use python-dotenv to load from `.env`
- Create `.env.sample` template

### 3. Define Pydantic Models
- Create `modules/models.py` with the following models:
  - `PollOption` - id, text
  - `Poll` - id (UUID), title, options, created_at, is_closed
  - `Vote` - id, poll_id, option_id, voter_fingerprint, created_at
  - `PollCreate` - title, options (list of strings)
  - `VoteCreate` - option_id
  - `PollResults` - poll with vote counts per option

### 4. Implement SQLite Database Layer
- Create `modules/database.py` with async SQLite operations
- Implement schema initialization (CREATE TABLE IF NOT EXISTS)
- Tables needed:
  - `polls`: id (TEXT PRIMARY KEY), title, options (JSON), created_at, is_closed
  - `votes`: id (INTEGER PRIMARY KEY AUTOINCREMENT), poll_id, option_id, voter_fingerprint, created_at, UNIQUE(poll_id, voter_fingerprint)
- Implement functions:
  - `init_db()` - create tables
  - `create_poll(poll: PollCreate) -> Poll`
  - `get_poll(poll_id: str) -> Poll | None`
  - `add_vote(poll_id: str, option_id: str, fingerprint: str) -> bool`
  - `get_results(poll_id: str) -> dict`
  - `has_voted(poll_id: str, fingerprint: str) -> bool`

### 5. Create WebSocket Manager
- Create `modules/websocket_manager.py`
- Implement connection manager for broadcasting vote updates
- Support per-poll rooms (clients subscribe to specific poll updates)
- Methods: `connect()`, `disconnect()`, `broadcast_to_poll()`

### 6. Build FastAPI Application
- Create `main.py` with FastAPI app
- Mount static files at `/static`
- Implement lifespan context manager for database initialization
- Define API endpoints:
  - `POST /api/polls` - Create new poll, returns poll with shareable URL
  - `GET /api/polls/{poll_id}` - Get poll details
  - `POST /api/polls/{poll_id}/vote` - Submit vote
  - `GET /api/polls/{poll_id}/results` - Get current results
  - `WebSocket /ws/{poll_id}` - Real-time updates
- Implement voter fingerprinting from request (IP + User-Agent hash)
- Serve `index.html` at `/` and `poll.html` at `/p/{poll_id}`

### 7. Create Frontend - Poll Creation Page
- Create `static/index.html` with:
  - Title input field
  - Dynamic option inputs (add/remove)
  - Create poll button
  - Display shareable link after creation
- Create `static/js/create.js`:
  - Handle option add/remove
  - Submit poll creation via fetch
  - Display generated shareable URL

### 8. Create Frontend - Poll Voting Page
- Create `static/poll.html` with:
  - Poll title display
  - Radio buttons for options
  - Vote button
  - Bar chart results section
  - "Already voted" state handling
- Create `static/js/poll.js`:
  - Load poll data on page load
  - Handle vote submission
  - Connect to WebSocket for real-time updates
  - Render bar chart with CSS (div-based, no library needed)
  - Show current vote counts and percentages

### 9. Create Stylesheet
- Create `static/css/styles.css`:
  - Clean, minimal design
  - Responsive layout
  - Bar chart styling (horizontal bars with percentage)
  - Form styling
  - Disabled state for voted users

### 10. Create Launcher Script
- Create `start.sh` bash script
- Load environment variables
- Run with uvicorn via UV

### 11. Write Integration Tests
- Create `tests/conftest.py` with fixtures:
  - Temporary SQLite database
  - Test client (httpx AsyncClient)
- Create `tests/test_polls.py`:
  - Test poll creation
  - Test voting
  - Test duplicate vote prevention
  - Test results calculation
  - Use ephemeral database (create/cleanup per test)

### 12. Create Documentation
- Create `README.md` with:
  - Project overview
  - Setup instructions
  - API documentation
  - Usage examples

## Testing Strategy

### Unit Tests
- Test Pydantic model validation
- Test database operations with ephemeral SQLite
- Test voter fingerprint generation

### Integration Tests
- Test full poll lifecycle: create → vote → results
- Test duplicate vote prevention (same fingerprint blocked)
- Test WebSocket connection and broadcast
- All tests use real SQLite (no mocks per CLAUDE.md rules)

### Test Data Management
- Each test creates its own temporary database file
- Database cleaned up automatically via pytest fixtures
- Start and end in identical state (ephemeral approach)

## Acceptance Criteria
- [ ] User can create a poll with 2-10 options via web form
- [ ] System generates unique shareable URL for each poll
- [ ] User can vote on a poll without authentication
- [ ] Same browser/IP combination cannot vote twice on same poll
- [ ] Results display as horizontal bar chart with percentages
- [ ] Results update in real-time via WebSocket when others vote
- [ ] SQLite database persists polls and votes across restarts
- [ ] All tests pass with `uv run pytest`
- [ ] App starts successfully with `./start.sh` or `uv run python main.py`

## Validation Commands
Execute these commands to validate the task is complete:

- `cd apps/polls && uv run python -m py_compile main.py modules/*.py` - Verify Python syntax
- `cd apps/polls && uv run pytest -v` - Run all tests
- `cd apps/polls && uv run python main.py &; sleep 2; curl http://localhost:8003/api/polls -X POST -H "Content-Type: application/json" -d '{"title":"Test","options":["A","B"]}'; kill %1` - Test API endpoint
- `cd apps/polls && ls static/*.html static/js/*.js static/css/*.css` - Verify frontend files exist

## Notes

### Dependencies to Install
```bash
cd apps/polls
uv add fastapi "uvicorn[standard]" pydantic python-dotenv rich aiosqlite pytest httpx
```

### SQLite Duplicate Prevention
The `votes` table uses a UNIQUE constraint on `(poll_id, voter_fingerprint)` to prevent duplicate votes. The fingerprint is a SHA-256 hash of `IP_ADDRESS + USER_AGENT`.

### Real-Time Updates Architecture
- Each poll has a WebSocket "room"
- When a vote is submitted, the server broadcasts updated results to all connected clients in that poll's room
- Frontend updates bar chart without page reload

### Port Configuration
Default port is 8003 (to avoid conflicts with other apps in the monorepo).

### No External Chart Libraries
Bar charts are implemented with pure HTML/CSS using percentage-width divs. This keeps the frontend lightweight with zero dependencies.
