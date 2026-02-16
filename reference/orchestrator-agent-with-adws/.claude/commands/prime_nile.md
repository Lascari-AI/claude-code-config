---
allowed-tools: Read, Glob, Grep, Bash, Edit, Write, Task
description: Prime agents with comprehensive understanding of the Nile adaptive shopping application
model: opus
---

# Purpose

This prompt primes AI agents with a comprehensive understanding of the **Nile Adaptive Shopping** application. The key files are auto-loaded below. Review them to understand the architecture, the **Agent Expert** pattern, and the **ACT → LEARN → REUSE** cycle.

## Auto-Loaded Context Files

### Application Overview
@apps/nile/README.md

### Backend Core
@apps/nile/server/src/main.py
@apps/nile/server/src/config.py
@apps/nile/server/src/database.py

### Agent Expert (CRITICAL - Claude Agent SDK)
@apps/nile/server/src/services/agent_expert.py
@apps/nile/server/src/prompts/experts/shopping_expert_system_prompt.md

### Backend Models
@apps/nile/server/src/models/__init__.py
@apps/nile/server/src/models/expertise.py
@apps/nile/server/src/models/product.py

### Backend Schemas
@apps/nile/server/src/schemas/home_page.py
@apps/nile/server/src/schemas/expertise.py

### Backend Routers
@apps/nile/server/src/routers/home.py
@apps/nile/server/src/routers/expertise.py

### Frontend Core
@apps/nile/client/src/main.ts
@apps/nile/client/src/App.vue
@apps/nile/client/src/router/index.ts
@apps/nile/client/src/services/api.ts
@apps/nile/client/src/types/index.ts

### Frontend Stores (CRITICAL - ACT/LEARN/REUSE)
@apps/nile/client/src/stores/expertise.ts
@apps/nile/client/src/stores/user.ts

### Frontend Views
@apps/nile/client/src/views/HomeView.vue

## Instructions

- You now have full context of the Nile application loaded above
- Understand the Claude Agent SDK integration for personalized recommendations
- Learn the ACT → LEARN → REUSE cycle that drives personalization
- Be prepared to work on both frontend (Vue 3) and backend (FastAPI) code

## Architecture Summary

**Backend Stack:**
- FastAPI with async endpoints
- SQLAlchemy with aiosqlite (SQLite database at `server/data/nile.db`)
- Claude Agent SDK with MCP tools for personalization
- Pydantic schemas for validation

**Frontend Stack:**
- Vue 3 + TypeScript + Composition API
- Pinia for state management
- Vue Router with auth guards
- Vite with proxy to backend (localhost:5173 → localhost:8000)

## Agent Expert Pattern

The `ShoppingAgentExpert` class in `agent_expert.py`:
- Uses `@tool` decorator to define MCP tools
- Tools: `get_products_by_ids`, `find_related_products`
- Creates MCP server with `create_sdk_mcp_server()`
- Configures agent with `ClaudeAgentOptions`
- Runs agent with `ClaudeSDKClient`

## ACT → LEARN → REUSE Cycle

```
ACT    → User views product, adds to cart, or checks out
         Frontend: expertise.ts trackView/trackAddToCart/trackCheckout
         Backend: POST /api/expertise/action

LEARN  → System updates user's Expertise JSONB in database
         Backend: expertise.py track_action_internal()
         Stores: viewed_products, added_to_cart, checked_out

REUSE  → Agent generates personalized home page sections
         Backend: home.py → agent_expert.generate_home_page()
         Frontend: HomeView.vue renders dynamic components
```

## Expertise Priority

1. `checked_out` - Strongest signal (purchased)
2. `added_to_cart` - Medium signal (intent)
3. `viewed_products` - Weak signal (interest)

## 7 Adaptive UI Components

| Component | Purpose |
|-----------|---------|
| `generic-slogan` | Welcome text for new users |
| `specific-slogan` | Personalized greeting based on behavior |
| `specific-upsell` | Single product upsell with full details |
| `basic-square` | Simple product grid |
| `carousel` | Horizontal scrolling product list |
| `card` | Standard product cards |
| `super-card` | Premium display for high-interest items |

## Key Commands

```bash
# Start backend
cd apps/nile/server && uv run uvicorn src.main:app --port 8000

# Start frontend
cd apps/nile/client && npm run dev

# Seed database
cd apps/nile/server && uv run python seed_data.py

# Reset database
rm apps/nile/server/data/nile.db && cd apps/nile/server && uv run python seed_data.py
```

## Keyboard Shortcuts

- `Ctrl+K` - Toggle Expertise Panel
- `Ctrl+Shift+C` - Clear expertise data

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/home` | Personalized home page (agent-powered) |
| `POST /api/expertise/action` | Track user actions |
| `GET /api/expertise` | Get user expertise data |
| `DELETE /api/expertise` | Clear expertise |
| `GET /api/products` | List products |
| `GET /api/products/{id}` | Product details |
| `POST /api/cart/add` | Add to cart |
| `POST /api/orders/checkout` | Checkout |

## Common Improvements

- Add new component types in `home_page.py` and create Vue component in `client/src/components/products/`
- Modify agent prompt in `shopping_expert_system_prompt.md`
- Add new tools to `agent_expert.py` using `@tool` decorator
- Extend expertise tracking in `expertise.py`
- Add new views/routes in `router/index.ts`

You are now primed to work on the Nile Adaptive Shopping application!
