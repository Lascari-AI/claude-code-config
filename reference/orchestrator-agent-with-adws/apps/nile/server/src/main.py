"""Main FastAPI application for Nile."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import API_PREFIX
from .database import init_db
from .models import Expertise
from .routers import (
    auth_router,
    cart_router,
    expertise_router,
    home_router,
    orders_router,
    products_router,
)
from .services.agent_expert import ShoppingAgentExpert
from .services.websocket_manager import home_ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print("Application shutting down")


app = FastAPI(
    title="Nile API",
    description="Adaptive Shopping with Agent Expert",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(products_router, prefix=API_PREFIX)
app.include_router(cart_router, prefix=API_PREFIX)
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(expertise_router, prefix=API_PREFIX)
app.include_router(home_router, prefix=API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nile-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Nile API",
        "docs": "/docs",
        "health": "/health"
    }


# Initialize agent expert singleton
_agent_expert = ShoppingAgentExpert()


@app.websocket("/ws/home/{user_id}")
async def websocket_home_stream(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for streaming personalized home page sections.

    Flow:
    1. Frontend connects to /ws/home/{user_id}
    2. Backend accepts connection and starts agent
    3. Agent calls stream_section tool for each section
    4. Each section is immediately pushed to frontend via WebSocket
    5. Agent completes, backend sends 'complete' message
    """
    from sqlalchemy import select

    from .database import async_session

    await home_ws_manager.connect(user_id, websocket)

    try:
        # Wait for client to send "start" message
        data = await websocket.receive_json()
        if data.get("action") != "start":
            await home_ws_manager.stream_error(user_id, "Expected 'start' action")
            return

        # Get user expertise from database
        async with async_session() as db:
            result = await db.execute(
                select(Expertise).where(Expertise.user_id == user_id)
            )
            expertise = result.scalar_one_or_none()

            # Create empty expertise for new users - agent will use find_related_products for defaults
            if not expertise:
                expertise = Expertise(
                    user_id=user_id,
                    expertise_data={"viewed_products": [], "added_to_cart": [], "checked_out": []},
                    total_improvements=0
                )

            # Run the streaming agent (handles both new and returning users)
            await _agent_expert.generate_home_page_streaming(
                user_id=user_id,
                expertise=expertise,
                db=db,
                ws_manager=home_ws_manager
            )

        # Keep connection alive until client disconnects
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        home_ws_manager.disconnect(user_id)
    except Exception as e:
        await home_ws_manager.stream_error(user_id, str(e))
        home_ws_manager.disconnect(user_id)
