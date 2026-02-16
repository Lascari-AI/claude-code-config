# Nile Adaptive Shopping - Agent Expert Demo

> **Note:** This is a *rough* proof of concept. Agents are not ready to be shopping recommendation engines like this. Focus on the **Agent Experts pattern**, not the actual use case here. Nile is simply a vehicle to showcase this pattern so you can understand how to apply it to your own products.

A full-stack application demonstrating the **Product Agent Expert** pattern using the Claude Agent SDK (Custom Agent). The agent learns from user behavior and personalizes the shopping experience without human intervention.

## Core Concept: Act → Learn → Reuse

```
ACT    → User views product, adds to cart, or checks out
LEARN  → System updates user's Expertise JSONB in database
REUSE  → Agent uses expertise to generate personalized home page
```

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- uv (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Anthropic API key
- Note on model performance for the generative UI:
  - You'll want to update `apps/nile/server/src/services/agent_expert.py: L322` to use the model you want to use. It's set to haiku, which will be 'fast' releative to the others but not as powerful.

### Step 1: Environment
```bash
# Create server/.env with your API key
echo "ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY" > server/.env

# or copy from the root .env file
cp ../../.env server/.env
```

### Step 2: Backend (Terminal 1)
```bash
cd server
uv sync                                    # Install dependencies
uv run python seed_data.py                 # Seed 100 products
uv run uvicorn src.main:app --port 8000    # Start backend
```

### Step 3: Frontend (Terminal 2)
```bash
cd client
npm install                                # Install dependencies
npm run dev                                # Start frontend
```

### Step 4: Open App
Navigate to `http://localhost:5173`

## Configuration

### Vite Proxy (client/vite.config.ts)
Frontend proxies `/api/*` to backend:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

### CORS (server/src/config.py)
```python
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

### Database
SQLite at: `server/data/nile.db`

## Reset / Fresh Start
```bash
# Delete database and re-seed
rm server/data/nile.db
cd server && uv run python seed_data.py

# Clear user expertise in-app: Ctrl+K then Ctrl+C
```

## Architecture

```
├── client/                     # Vue 3 + TypeScript + Pinia
│   ├── src/
│   │   ├── views/              # Page components
│   │   ├── components/         # UI components (7 adaptive types)
│   │   ├── stores/             # Pinia stores (cart, expertise, products)
│   │   └── services/api.ts     # API client
│   └── public/images/products/ # 400+ product images
│
├── server/                     # FastAPI + SQLAlchemy + Claude Agent SDK
│   ├── src/
│   │   ├── routers/            # API endpoints
│   │   ├── services/           # Agent Expert implementation
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── prompts/experts/    # Agent system prompts
│   └── seed_data.py            # 100 products with reviews
│
└── README.md                   # This file
```

## Key Files

### Agent Expert (Claude Agent SDK)
- `server/src/services/agent_expert.py` - Main agent implementation
  - Uses `@tool` decorator for custom tools
  - `ClaudeSDKClient` for agent execution
  - Two tools: `get_products_by_ids`, `find_related_products`

### System Prompt
- `server/src/prompts/experts/shopping_expert_system_prompt.md`
  - Defines tool usage workflow
  - Component type selection rules
  - Output JSON format specification

### Expertise Data Structure
Stored in `expertise` table as JSONB:
```python
{
    "viewed_products": [{"product_id": 1, "viewed_at": "...", "view_count": 2}],
    "added_to_cart": [{"product_id": 1, "added_at": "...", "add_count": 1}],
    "checked_out": [{"product_id": 1, "checked_out_at": "...", "purchase_count": 1}]
}
```

Priority: `checked_out` > `added_to_cart` > `viewed_products`

### Action Tracking
- `server/src/routers/expertise.py` - Tracks user actions
  - `POST /api/expertise/track` - Records view/cart/checkout actions
  - Updates `total_improvements` counter

### Home Page Generation
- `server/src/routers/home.py` - Orchestrates personalization
  - If `total_improvements < 1`: Returns generic home
  - Otherwise: Calls `ShoppingAgentExpert.generate_home_page()`

## Adaptive UI Components

The frontend renders different components based on agent recommendations:

| Component         | Purpose                                 |
| ----------------- | --------------------------------------- |
| `generic-slogan`  | Welcome text for new users              |
| `specific-slogan` | Personalized greeting based on behavior |
| `specific-upsell` | Single product upsell with full details |
| `basic-square`    | Simple product grid                     |
| `carousel`        | Horizontal scrolling product list       |
| `card`            | Standard product cards                  |
| `super-card`      | Premium display for high-interest items |

Components: `client/src/components/products/`

## API Endpoints

### Products
- `GET /api/products` - List products (limit, offset)
- `GET /api/products/{id}` - Get product details

### Cart
- `GET /api/cart` - Get user's cart
- `POST /api/cart/add` - Add to cart
- `DELETE /api/cart/{id}` - Remove from cart

### Orders
- `POST /api/orders/checkout` - Create order from cart
- `GET /api/orders` - List user's orders
- `GET /api/orders/{id}` - Get order details

### Expertise
- `POST /api/expertise/track` - Track action (`view_product_details`, `add_to_cart`, `checkout`)
- `GET /api/expertise` - Get user's expertise data

### Home (Agent-Powered)
- `GET /api/home` - Get personalized home page sections

## Database Schema

```sql
-- Users
users (id, name, created_at)

-- Products
products (id, name, description, price, category, brand, rating, shipping_speed, image_file_path)

-- Reviews
reviews (id, product_id, review_text, rating, reviewer_name, review_date)

-- Cart
cart_items (id, user_id, product_id, quantity)

-- Orders
order_items (id, user_id, product_id, quantity, price_at_purchase, created_at)

-- Expertise (Agent Memory)
expertise (id, user_id, total_improvements, last_improvement_at, expertise_data JSONB)
```

## Testing the Agent

1. Login with any name (creates user if not exists)
2. View some products → triggers `view_product_details` action
3. Add to cart → triggers `add_to_cart` action
4. Checkout → triggers `checkout` action
5. Return to home → Agent generates personalized sections

Press `Ctrl+K` to open the Expertise Panel and see:
- ACT → LEARN → REUSE cycle indicator
- Real-time action log with phase colors
- System prompt preview

## Claude Agent SDK Pattern

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

@tool("get_products_by_ids", "Get products by IDs", {"product_ids": list})
async def get_products_by_ids_tool(args: dict) -> dict:
    # Query database, return products
    return {"content": [{"type": "text", "text": json.dumps(products)}]}

# Create MCP server with tools
server = create_sdk_mcp_server(name="shopping", version="1.0.0", tools=[...])

# Configure agent
options = ClaudeAgentOptions(
    mcp_servers={"shopping": server},
    allowed_tools=["mcp__shopping__get_products_by_ids", ...],
    system_prompt=system_prompt,
    model="claude-sonnet-4-20250514"
)

# Run agent
async with ClaudeSDKClient(options=options) as client:
    await client.query(user_prompt)
    async for message in client.receive_response():
        # Process response
```

## Dependencies

### Server
- `fastapi` - Web framework
- `sqlalchemy` - ORM
- `anthropic` - Claude API
- `claude-agent-sdk` - Agent SDK with MCP tools
- `pydantic` - Data validation

### Client
- `vue` - UI framework
- `pinia` - State management
- `vue-router` - Routing
- `axios` - HTTP client
