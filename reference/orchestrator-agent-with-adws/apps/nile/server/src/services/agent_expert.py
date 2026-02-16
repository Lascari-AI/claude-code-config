"""Shopping Agent Expert - uses Claude Agent SDK for personalized home pages."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    create_sdk_mcp_server,
    tool,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import ANTHROPIC_API_KEY
from ..models import Expertise, Product
from ..schemas import (
    AgentHomePageResponseRaw,
    AgentSectionRaw,
    HomePageResponse,
    HomeSection,
    HydratedProduct,
)

# Configure logger
logger = logging.getLogger("nile.agent_expert")
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%H:%M:%S"
        )
    )
    logger.addHandler(handler)

# Module-level storage for tool execution context
_current_db: Optional[AsyncSession] = None
_current_user_id: Optional[int] = None
_current_ws_manager: Optional[Any] = None  # HomePageWebSocketManager

# Prompt file paths
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "experts"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "shopping_expert_streaming_system_prompt.md"
_USER_PROMPT_PATH = _PROMPTS_DIR / "shopping_expert_user_prompt.md"


@tool(
    "find_related_products",
    "Search for products by category, brand, price range, or rating. All parameters are optional - only provide the filters you need.",
    {
        "category": str,
        "brand": str,
        "min_price": float,
        "max_price": float,
        "min_rating": float,
        "limit": int,
    },
)
async def find_related_products_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """Find related products by attributes. All parameters are optional.

    Args dict can contain:
        category: Product category (e.g., 'Keyboards', 'Audio', 'Mice')
        brand: Brand name (e.g., 'Keychron', 'Logitech', 'Sony')
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_rating: Minimum rating filter (1-5)
        limit: Max products to return (default: 8)
    """
    global _current_db

    # Extract parameters from args dict (Claude Agent SDK pattern)
    category = args.get("category") if args.get("category") else None
    brand = args.get("brand") if args.get("brand") else None
    min_price = float(args["min_price"]) if args.get("min_price") else None
    max_price = float(args["max_price"]) if args.get("max_price") else None
    min_rating = float(args["min_rating"]) if args.get("min_rating") else None
    limit = int(args.get("limit", 8)) if args.get("limit") else 8

    logger.info("=" * 60)
    logger.info("TOOL CALL: find_related_products")
    logger.info(f"  Raw args: {args}")
    logger.info(
        f"  Parsed: category={category}, brand={brand}, min_price={min_price}, max_price={max_price}, min_rating={min_rating}, limit={limit}"
    )

    if not _current_db:
        logger.error("  Database session not available!")
        raise RuntimeError("Database session not available")

    query = select(Product).options(selectinload(Product.reviews))

    filters_applied = []
    if category:
        query = query.where(Product.category == category)
        filters_applied.append(f"category={category}")
    if brand:
        query = query.where(Product.brand == brand)
        filters_applied.append(f"brand={brand}")
    if min_price is not None:
        query = query.where(Product.price >= min_price)
        filters_applied.append(f"min_price={min_price}")
    if max_price is not None:
        query = query.where(Product.price <= max_price)
        filters_applied.append(f"max_price={max_price}")
    if min_rating is not None:
        query = query.where(Product.rating >= min_rating)
        filters_applied.append(f"min_rating={min_rating}")

    logger.info(
        f"  Filters: {', '.join(filters_applied) if filters_applied else 'none'}"
    )
    logger.info(f"  Limit: {limit}")

    query = query.limit(limit or 8)
    result = await _current_db.execute(query)
    products = result.scalars().all()

    logger.info(f"  Found {len(products)} products")

    product_list = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description[:200] if p.description else "",
            "price": p.price,
            "category": p.category,
            "brand": p.brand,
            "rating": p.rating,
            "shipping_speed": p.shipping_speed,
            "image_file_path": p.image_file_path,
        }
        for p in products
    ]

    for p in product_list:
        logger.debug(f"    - [{p['id']}] {p['name']} (${p['price']}) - {p['category']}")

    logger.info("=" * 60)
    return {"content": [{"type": "text", "text": json.dumps(product_list, indent=2)}]}


@tool(
    "stream_section",
    "Stream a single home page section to the user immediately. Call this for EACH section you want to display. The section will appear on the user's screen right away.",
    {
        "component_type": str,
        "title": str,
        "subtitle": str,
        "slogan_text": str,
        "product_ids": list,
        "product_id": int,
    },
)
async def stream_section_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stream a section to the user's WebSocket immediately.

    Args dict can contain:
        component_type: carousel, card, specific-slogan, specific-upsell, super-card, basic-square
        title: Section title
        subtitle: Section subtitle (for slogans/upsells)
        slogan_text: Slogan text (for specific-slogan)
        product_ids: List of product IDs (for carousel, card, basic-square)
        product_id: Single product ID (for super-card, specific-upsell)
    """
    global _current_db, _current_user_id, _current_ws_manager

    component_type = args.get("component_type")
    title = args.get("title")
    subtitle = args.get("subtitle")
    slogan_text = args.get("slogan_text")

    # Parse product_ids - may come as list, string, or comma-separated string
    raw_product_ids = args.get("product_ids", [])
    if isinstance(raw_product_ids, str):
        # Handle comma-separated string: "26,69,71" -> [26, 69, 71]
        product_ids = [int(x.strip()) for x in raw_product_ids.split(",") if x.strip()]
    elif isinstance(raw_product_ids, list):
        # Handle list - ensure integers
        product_ids = [int(x) for x in raw_product_ids if x]
    else:
        product_ids = []

    # Parse product_id - may come as int or string
    raw_product_id = args.get("product_id")
    product_id = int(raw_product_id) if raw_product_id else None

    logger.info("=" * 60)
    logger.info("TOOL CALL: stream_section")
    logger.info(f"  component_type: {component_type}")
    logger.info(f"  title: {title}")
    logger.info(f"  raw product_ids: {raw_product_ids} -> parsed: {product_ids}")
    logger.info(f"  raw product_id: {raw_product_id} -> parsed: {product_id}")

    if not _current_db or not _current_ws_manager or not _current_user_id:
        logger.error("  Streaming context not available!")
        return {
            "content": [
                {"type": "text", "text": "Error: Streaming context not initialized"}
            ],
            "is_error": True,
        }

    # Collect all product IDs to fetch
    all_ids = set()
    if product_ids:
        all_ids.update(product_ids)
    if product_id:
        all_ids.add(product_id)

    # Hydrate products if needed
    hydrated_products = []
    hydrated_product = None

    if all_ids:
        logger.info(f"  Hydrating {len(all_ids)} product IDs...")
        result = await _current_db.execute(
            select(Product).where(Product.id.in_(all_ids))
        )
        products_by_id = {p.id: p for p in result.scalars().all()}

        # Convert to dict format for JSON
        def to_dict(p: Product) -> dict:
            return {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "brand": p.brand,
                "rating": p.rating,
                "image_file_path": p.image_file_path,
                "shipping_speed": p.shipping_speed,
                "description": p.description[:200] if p.description else "",
            }

        # Hydrate list
        if product_ids:
            hydrated_products = [
                to_dict(products_by_id[pid])
                for pid in product_ids
                if pid in products_by_id
            ]

        # Hydrate single
        if product_id and product_id in products_by_id:
            hydrated_product = to_dict(products_by_id[product_id])

    # Build section data
    section_data = {
        "component_type": component_type,
    }
    if title:
        section_data["title"] = title
    if subtitle:
        section_data["subtitle"] = subtitle
    if slogan_text:
        section_data["slogan_text"] = slogan_text
    if hydrated_products:
        section_data["products"] = hydrated_products
    if hydrated_product:
        section_data["product"] = hydrated_product

    # Stream to WebSocket
    success = await _current_ws_manager.stream_section(_current_user_id, section_data)

    if success:
        logger.info(
            f"  ✅ Streamed '{component_type}' section to user {_current_user_id}"
        )
        logger.info("=" * 60)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Section '{component_type}' streamed successfully",
                }
            ]
        }
    else:
        logger.error(f"  ❌ Failed to stream section to user {_current_user_id}")
        logger.info("=" * 60)
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Warning: User WebSocket not connected, section not delivered",
                }
            ],
        }


class ShoppingAgentExpert:
    """Agent Expert that uses Claude Agent SDK for personalized recommendations."""

    # Limit for each category of products to inject into prompt
    MAX_PRODUCTS_PER_CATEGORY = 10

    def __init__(self):
        logger.info("=" * 80)
        logger.info("INITIALIZING ShoppingAgentExpert")
        logger.info("=" * 80)

        if not ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY is not set!")
            raise ValueError("ANTHROPIC_API_KEY is required")

        # self.model = "claude-opus-4-5-20251101"
        # self.model = "claude-sonnet-4-5-20250929"
        self.model = "claude-haiku-4-5-20251001"

        logger.info(f"Model: {self.model}")

        # Load prompt templates (required files)
        logger.info(f"Loading system prompt: {_SYSTEM_PROMPT_PATH}")
        self.system_prompt_template = _SYSTEM_PROMPT_PATH.read_text()
        logger.info(
            f"  System prompt loaded ({len(self.system_prompt_template)} chars)"
        )

        logger.info(f"Loading user prompt: {_USER_PROMPT_PATH}")
        self.user_prompt_template = _USER_PROMPT_PATH.read_text()
        logger.info(f"  User prompt loaded ({len(self.user_prompt_template)} chars)")

        # Session tracking per user for TRUE session continuity
        self._user_sessions: Dict[int, str] = {}

        # Active client tracking for interruption support
        # When a new request comes in for a user with an active client, we interrupt the old one
        self._active_clients: Dict[int, ClaudeSDKClient] = {}
        self._active_clients_lock = asyncio.Lock()

        logger.info("Session tracking initialized")
        logger.info("ShoppingAgentExpert ready!")
        logger.info("=" * 80)

    async def _interrupt_existing_session(self, user_id: int) -> None:
        """
        Interrupt any existing agent session for this user.

        Called when a new page request comes in to ensure the old agent stops
        and resources are cleaned up before starting a new session.
        """
        async with self._active_clients_lock:
            existing_client = self._active_clients.get(user_id)
            if existing_client:
                logger.info(f"🔄 Interrupting existing session for user {user_id}")
                try:
                    await existing_client.interrupt()
                    logger.info(
                        f"✅ Successfully interrupted session for user {user_id}"
                    )
                except Exception as e:
                    logger.warning(
                        f"⚠️ Error interrupting session for user {user_id}: {e}"
                    )
                finally:
                    # Remove from active clients regardless of interrupt success
                    del self._active_clients[user_id]

    async def _register_active_client(
        self, user_id: int, client: ClaudeSDKClient
    ) -> None:
        """Register a client as active for a user."""
        async with self._active_clients_lock:
            self._active_clients[user_id] = client
            logger.debug(f"Registered active client for user {user_id}")

    async def _unregister_active_client(self, user_id: int) -> None:
        """Unregister a client when done."""
        async with self._active_clients_lock:
            if user_id in self._active_clients:
                del self._active_clients[user_id]
                logger.debug(f"Unregistered active client for user {user_id}")

    async def _fetch_all_categories_and_brands(
        self, db: AsyncSession
    ) -> tuple[List[str], List[str]]:
        """Fetch all unique categories and brands from the product catalog."""
        from sqlalchemy import distinct

        # Get all unique categories
        cat_result = await db.execute(
            select(distinct(Product.category)).where(Product.category.isnot(None))
        )
        categories = [row[0] for row in cat_result.fetchall()]

        # Get all unique brands
        brand_result = await db.execute(
            select(distinct(Product.brand)).where(Product.brand.isnot(None))
        )
        brands = [row[0] for row in brand_result.fetchall()]

        return sorted(categories), sorted(brands)

    async def _prefetch_user_products(
        self, expertise: Expertise, db: AsyncSession
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Pre-fetch all products the user has interacted with.

        Returns products grouped by interaction type, limited to 10 most recent each.
        This eliminates the need for the agent to call get_products_by_ids.
        """
        logger.info("Pre-fetching user products...")

        data = expertise.expertise_data or {}

        # Get 10 most recent product IDs for each category (sorted by timestamp desc)
        def get_recent_ids(entries: List[dict], time_field: str) -> List[int]:
            # Sort by timestamp descending and take first 10
            sorted_entries = sorted(
                entries, key=lambda x: x.get(time_field, ""), reverse=True
            )[: self.MAX_PRODUCTS_PER_CATEGORY]
            return [e.get("product_id") for e in sorted_entries if e.get("product_id")]

        checkout_ids = get_recent_ids(data.get("checked_out", []), "checked_out_at")
        cart_ids = get_recent_ids(data.get("added_to_cart", []), "added_at")
        viewed_ids = get_recent_ids(data.get("viewed_products", []), "viewed_at")

        # Collect all unique IDs
        all_ids = set(checkout_ids + cart_ids + viewed_ids)

        logger.info(
            f"  Checkout IDs (max {self.MAX_PRODUCTS_PER_CATEGORY}): {checkout_ids}"
        )
        logger.info(f"  Cart IDs (max {self.MAX_PRODUCTS_PER_CATEGORY}): {cart_ids}")
        logger.info(
            f"  Viewed IDs (max {self.MAX_PRODUCTS_PER_CATEGORY}): {viewed_ids}"
        )
        logger.info(f"  Total unique IDs: {len(all_ids)}")

        if not all_ids:
            logger.info("  No products to prefetch")
            return {"checked_out": [], "added_to_cart": [], "viewed_products": []}

        # Fetch all products in one query
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.reviews))
            .where(Product.id.in_(all_ids))
        )
        products = {p.id: p for p in result.scalars().all()}

        logger.info(f"  Fetched {len(products)} products from database")

        # Helper to convert product to dict
        def product_to_dict(p: Product) -> Dict[str, Any]:
            return {
                "id": p.id,
                "name": p.name,
                "description": p.description[:200] if p.description else "",
                "price": p.price,
                "category": p.category,
                "brand": p.brand,
                "rating": p.rating,
                "shipping_speed": p.shipping_speed,
                "image_file_path": p.image_file_path,
            }

        # Build categorized product lists (preserving order)
        prefetched = {
            "checked_out": [
                product_to_dict(products[pid])
                for pid in checkout_ids
                if pid in products
            ],
            "added_to_cart": [
                product_to_dict(products[pid]) for pid in cart_ids if pid in products
            ],
            "viewed_products": [
                product_to_dict(products[pid]) for pid in viewed_ids if pid in products
            ],
        }

        logger.info(
            f"  Pre-fetched: {len(prefetched['checked_out'])} purchased, "
            f"{len(prefetched['added_to_cart'])} carted, "
            f"{len(prefetched['viewed_products'])} viewed"
        )

        return prefetched

    def _build_system_prompt(
        self, expertise: Expertise, prefetched_products: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build system prompt with expertise data and pre-fetched products injected."""
        logger.debug("Building system prompt with expertise data and products...")

        # Extract unique categories and brands for recommendations
        all_products = (
            prefetched_products.get("checked_out", [])
            + prefetched_products.get("added_to_cart", [])
            + prefetched_products.get("viewed_products", [])
        )
        categories = list(set(p["category"] for p in all_products if p.get("category")))
        brands = list(set(p["brand"] for p in all_products if p.get("brand")))

        logger.debug(f"  Categories found: {categories}")
        logger.debug(f"  Brands found: {brands}")

        # Build variable replacements - now with full product objects
        variables = {
            "TOTAL_IMPROVEMENTS": str(expertise.total_improvements),
            "CHECKED_OUT_PRODUCTS": json.dumps(
                prefetched_products.get("checked_out", []), indent=2
            ),
            "ADDED_TO_CART_PRODUCTS": json.dumps(
                prefetched_products.get("added_to_cart", []), indent=2
            ),
            "VIEWED_PRODUCTS": json.dumps(
                prefetched_products.get("viewed_products", []), indent=2
            ),
            "USER_CATEGORIES": json.dumps(categories),
            "USER_BRANDS": json.dumps(brands),
        }

        # Replace placeholders in template
        result = self.system_prompt_template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, value)
            logger.debug(f"  Replaced {{{{{key}}}}} ({len(value)} chars)")

        logger.debug(f"  Final system prompt: {len(result)} chars")
        return result

    async def generate_home_page(
        self, user_id: int, expertise: Expertise, db: AsyncSession
    ) -> HomePageResponse:
        """Generate personalized home page using Claude Agent SDK."""
        global _current_db

        logger.info("=" * 80)
        logger.info("GENERATE HOME PAGE REQUEST")
        logger.info("=" * 80)
        logger.info(f"User ID: {user_id}")
        logger.info(f"Total Improvements: {expertise.total_improvements}")

        # Set the db session for tools to access
        _current_db = db
        logger.debug("Database session set for tools")

        try:
            # Pre-fetch user's products (eliminates need for get_products_by_ids tool)
            logger.info("Pre-fetching user products...")
            prefetched_products = await self._prefetch_user_products(expertise, db)

            # Build system prompt with expertise data AND full product objects
            logger.info("Building system prompt with pre-fetched products...")
            system_prompt = self._build_system_prompt(expertise, prefetched_products)

            # Create MCP server with only find_related_products tool
            # (get_products_by_ids is no longer needed - products are in the prompt)
            logger.info("Creating MCP server with tools...")
            shopping_server = create_sdk_mcp_server(
                name="shopping_expert",
                version="1.0.0",
                tools=[find_related_products_tool],
            )
            logger.info(
                "  Tools: find_related_products (products pre-fetched in prompt)"
            )

            # Get existing session for this user (for session continuity)
            existing_session_id = self._user_sessions.get(user_id)
            if existing_session_id:
                logger.info(f"Resuming session: {existing_session_id[:20]}...")
            else:
                logger.info("Starting new session (no previous session for user)")

            # Configure agent options with session resume
            # Disallow all general-purpose tools - agent only needs find_related_products
            logger.info("Configuring ClaudeAgentOptions...")
            options = ClaudeAgentOptions(
                mcp_servers={"shopping": shopping_server},
                allowed_tools=["mcp__shopping__find_related_products"],
                disallowed_tools=[
                    "Read",
                    "Write",
                    "Edit",
                    "Bash",
                    "Glob",
                    "Grep",
                    "Task",
                    "WebFetch",
                    "WebSearch",
                    "BashOutput",
                    "SlashCommand",
                    "TodoWrite",
                    "KillShell",
                    "AskUserQuestion",
                    "Skill",
                    "NotebookEdit",
                    "ExitPlanMode",
                    "EnterPlanMode",
                    "AgentOutputTool",
                ],
                system_prompt=system_prompt,
                model=self.model,
                resume=existing_session_id,
            )

            # Run agent and capture session_id
            logger.info("-" * 40)
            logger.info("STARTING AGENT EXECUTION")
            logger.info("-" * 40)

            response_text = ""
            message_count = 0
            tool_calls = 0

            async with ClaudeSDKClient(options=options) as client:
                logger.info("ClaudeSDKClient connected")
                logger.info(
                    f"Sending user prompt ({len(self.user_prompt_template)} chars)..."
                )

                await client.query(self.user_prompt_template)

                async for message in client.receive_response():
                    message_count += 1
                    message_type = type(message).__name__

                    # Log EVERY message with full details
                    logger.info(f"[MSG {message_count}] {message_type}")

                    if isinstance(message, AssistantMessage):
                        logger.info(f"  Content blocks: {len(message.content)}")
                        for i, block in enumerate(message.content):
                            block_type = type(block).__name__
                            logger.info(f"  [{i+1}] {block_type}")

                            if isinstance(block, TextBlock):
                                response_text = block.text
                                # Log FULL text - no trimming
                                logger.info(f"      Text ({len(response_text)} chars):")
                                logger.info(f"      {response_text}")

                            elif isinstance(block, ToolUseBlock):
                                tool_calls += 1
                                logger.info(f"      Tool: {block.name}")
                                logger.info(f"      ID: {block.id}")
                                # Log FULL input arguments - no trimming
                                if hasattr(block, "input"):
                                    logger.info(f"      Input:")
                                    logger.info(json.dumps(block.input, indent=2))

                            elif isinstance(block, ToolResultBlock):
                                logger.info(
                                    f"      Tool Result for: {getattr(block, 'tool_use_id', 'unknown')}"
                                )
                                # Log FULL result - no trimming
                                if hasattr(block, "content"):
                                    logger.info(f"      Result:")
                                    logger.info(f"      {block.content}")

                            else:
                                # Log any other block type with all its attributes
                                logger.info(
                                    f"      Attributes: {vars(block) if hasattr(block, '__dict__') else block}"
                                )

                    elif isinstance(message, ResultMessage):
                        logger.info(f"  === RESULT MESSAGE ===")
                        if message.session_id:
                            self._user_sessions[user_id] = message.session_id
                            logger.info(f"  Session ID: {message.session_id}")
                        if (
                            hasattr(message, "total_cost_usd")
                            and message.total_cost_usd
                        ):
                            logger.info(f"  Total Cost: ${message.total_cost_usd:.6f}")
                        if hasattr(message, "input_tokens"):
                            logger.info(f"  Input Tokens: {message.input_tokens}")
                        if hasattr(message, "output_tokens"):
                            logger.info(f"  Output Tokens: {message.output_tokens}")
                        # Log all attributes of ResultMessage - no trimming
                        for attr in dir(message):
                            if not attr.startswith("_") and not callable(
                                getattr(message, attr)
                            ):
                                val = getattr(message, attr)
                                if val is not None:
                                    logger.debug(f"  {attr}: {val}")

                    elif isinstance(message, SystemMessage):
                        # SystemMessage: Agent SDK initialization/system info
                        logger.info(f"  === SYSTEM MESSAGE ===")
                        subtype = getattr(message, "subtype", "unknown")
                        logger.info(f"  Subtype: {subtype}")
                        if hasattr(message, "data") and message.data:
                            data = message.data
                            if isinstance(data, dict):
                                logger.info(
                                    f"  Session ID: {data.get('session_id', 'N/A')}"
                                )
                                logger.info(f"  Model: {data.get('model', 'N/A')}")
                                logger.info(
                                    f"  Tools Available: {len(data.get('tools', []))} tools"
                                )
                                logger.debug(f"  Tools: {data.get('tools', [])}")
                                mcp_servers = data.get("mcp_servers", [])
                                for server in mcp_servers:
                                    logger.info(
                                        f"  MCP Server: {server.get('name', 'unknown')} ({server.get('status', 'unknown')})"
                                    )
                            else:
                                logger.info(f"  Data: {data}")

                    elif isinstance(message, UserMessage):
                        # UserMessage: Tool results returned to agent
                        logger.info(f"  === USER MESSAGE (Tool Results) ===")
                        content = getattr(message, "content", [])
                        if content:
                            logger.info(f"  Content blocks: {len(content)}")
                            for i, block in enumerate(content):
                                block_type = type(block).__name__
                                logger.info(f"  [{i+1}] {block_type}")
                                if isinstance(block, ToolResultBlock):
                                    tool_use_id = getattr(
                                        block, "tool_use_id", "unknown"
                                    )
                                    is_error = getattr(block, "is_error", False)
                                    logger.info(f"      Tool Use ID: {tool_use_id}")
                                    logger.info(f"      Is Error: {is_error}")
                                    block_content = getattr(block, "content", None)
                                    if block_content:
                                        # Truncate long results for readability
                                        content_str = str(block_content)
                                        if len(content_str) > 500:
                                            logger.info(
                                                f"      Result Preview: {content_str[:500]}..."
                                            )
                                            logger.debug(
                                                f"      Full Result: {content_str}"
                                            )
                                        else:
                                            logger.info(f"      Result: {content_str}")
                                else:
                                    logger.info(f"      Content: {block}")
                        parent_tool = getattr(message, "parent_tool_use_id", None)
                        if parent_tool:
                            logger.info(f"  Parent Tool Use ID: {parent_tool}")

                    else:
                        # Log unknown message types with all their attributes - no trimming
                        logger.info(f"  Unknown message type - logging all attributes:")
                        if hasattr(message, "__dict__"):
                            for k, v in vars(message).items():
                                logger.info(f"    {k}: {v}")

            logger.info("-" * 40)
            logger.info("AGENT EXECUTION COMPLETE")
            logger.info("-" * 40)
            logger.info(f"Messages received: {message_count}")
            logger.info(f"Tool calls made: {tool_calls}")
            logger.info(f"Response length: {len(response_text)} chars")

            # Validate response
            if not response_text:
                logger.error("Agent returned empty response!")
                raise ValueError("Agent returned empty response")

            # Parse response and hydrate with product data
            logger.info("Parsing agent response and hydrating...")
            result = await self._parse_response(response_text, db)
            logger.info(f"Parsed and hydrated {len(result.sections)} sections")

            for i, section in enumerate(result.sections):
                product_count = len(section.products) if section.products else 0
                logger.info(
                    f"  Section {i+1}: {section.component_type} - {product_count} products"
                )

            logger.info("=" * 80)
            return result

        finally:
            _current_db = None
            logger.debug("Database session cleared")

    async def generate_home_page_streaming(
        self,
        user_id: int,
        expertise: Expertise,
        db: AsyncSession,
        ws_manager: Any,  # HomePageWebSocketManager
    ) -> None:
        """
        Generate personalized home page using streaming - sections pushed via WebSocket as created.

        Instead of returning a response, this method:
        1. Runs the agent with stream_section tool
        2. Agent calls stream_section for each section
        3. Each section is immediately pushed to user's WebSocket
        4. Sends completion signal when done
        """
        global _current_db, _current_user_id, _current_ws_manager

        logger.info("=" * 80)
        logger.info("GENERATE HOME PAGE STREAMING REQUEST")
        logger.info("=" * 80)
        logger.info(f"User ID: {user_id}")
        logger.info(f"Total Improvements: {expertise.total_improvements}")

        # Interrupt any existing session for this user BEFORE starting new one
        await self._interrupt_existing_session(user_id)

        # Set the execution context for tools
        _current_db = db
        _current_user_id = user_id
        _current_ws_manager = ws_manager
        logger.debug("Streaming context set for tools")

        try:
            # Pre-fetch user's products
            logger.info("Pre-fetching user products...")
            prefetched_products = await self._prefetch_user_products(expertise, db)

            # Fetch ALL available categories and brands for discovery
            logger.info("Fetching all available categories and brands...")
            all_categories, all_brands = await self._fetch_all_categories_and_brands(db)
            logger.info(
                f"  Found {len(all_categories)} categories, {len(all_brands)} brands"
            )

            # Build system prompt (streaming version)
            logger.info("Building streaming system prompt...")
            system_prompt = self._build_streaming_system_prompt(
                expertise, prefetched_products, all_categories, all_brands
            )

            # Create MCP server with BOTH tools
            logger.info("Creating MCP server with tools...")
            shopping_server = create_sdk_mcp_server(
                name="shopping_expert",
                version="1.0.0",
                tools=[find_related_products_tool, stream_section_tool],
            )
            logger.info("  Tools: find_related_products, stream_section")

            # Get existing session for this user
            existing_session_id = self._user_sessions.get(user_id)
            if existing_session_id:
                logger.info(f"Resuming session: {existing_session_id[:20]}...")
            else:
                logger.info("Starting new session")

            # Configure agent options
            logger.info("Configuring ClaudeAgentOptions...")
            options = ClaudeAgentOptions(
                mcp_servers={"shopping": shopping_server},
                allowed_tools=[
                    "mcp__shopping__find_related_products",
                    "mcp__shopping__stream_section",
                ],
                disallowed_tools=[
                    "Read",
                    "Write",
                    "Edit",
                    "Bash",
                    "Glob",
                    "Grep",
                    "Task",
                    "WebFetch",
                    "WebSearch",
                    "BashOutput",
                    "SlashCommand",
                    "TodoWrite",
                    "KillShell",
                    "AskUserQuestion",
                    "Skill",
                    "NotebookEdit",
                    "ExitPlanMode",
                    "EnterPlanMode",
                    "AgentOutputTool",
                ],
                system_prompt=system_prompt,
                model=self.model,
                resume=existing_session_id,
            )

            # Run agent
            logger.info("-" * 40)
            logger.info("STARTING STREAMING AGENT EXECUTION")
            logger.info("-" * 40)

            message_count = 0
            tool_calls = 0

            async with ClaudeSDKClient(options=options) as client:
                logger.info("ClaudeSDKClient connected")

                # Register this client so it can be interrupted if user navigates away
                await self._register_active_client(user_id, client)

                # Use streaming-specific user prompt
                streaming_user_prompt = "Generate the personalized home page now. Stream each section as you create it."
                await client.query(streaming_user_prompt)

                async for message in client.receive_response():
                    message_count += 1
                    message_type = type(message).__name__
                    logger.info(f"[MSG {message_count}] {message_type}")

                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, ToolUseBlock):
                                tool_calls += 1
                                logger.info(f"  Tool: {block.name}")
                                if block.name == "mcp__shopping__stream_section":
                                    logger.info(
                                        f"  Streaming section: {block.input.get('component_type')}"
                                    )

                    elif isinstance(message, ResultMessage):
                        if message.session_id:
                            self._user_sessions[user_id] = message.session_id
                        logger.info(f"  Session: {message.session_id}")
                        if (
                            hasattr(message, "total_cost_usd")
                            and message.total_cost_usd
                        ):
                            logger.info(f"  Cost: ${message.total_cost_usd:.6f}")

            logger.info("-" * 40)
            logger.info("STREAMING AGENT EXECUTION COMPLETE")
            logger.info("-" * 40)
            logger.info(f"Messages: {message_count}, Tool calls: {tool_calls}")

            # Send completion signal
            await ws_manager.stream_complete(user_id)
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Streaming agent error: {e}", exc_info=True)
            await ws_manager.stream_error(user_id, str(e))
            raise

        finally:
            # Unregister client and clear context
            await self._unregister_active_client(user_id)
            _current_db = None
            _current_user_id = None
            _current_ws_manager = None
            logger.debug("Streaming context cleared")

    def _build_streaming_system_prompt(
        self,
        expertise: Expertise,
        prefetched_products: Dict[str, List[Dict[str, Any]]],
        all_categories: List[str],
        all_brands: List[str],
    ) -> str:
        """Build system prompt for streaming mode - uses stream_section tool."""
        logger.debug("Building streaming system prompt...")

        # Use the pre-loaded system prompt template
        template = self.system_prompt_template

        # Build variable replacements
        variables = {
            "TOTAL_IMPROVEMENTS": str(expertise.total_improvements),
            "CHECKED_OUT_PRODUCTS": json.dumps(
                prefetched_products.get("checked_out", []), indent=2
            ),
            "ADDED_TO_CART_PRODUCTS": json.dumps(
                prefetched_products.get("added_to_cart", []), indent=2
            ),
            "VIEWED_PRODUCTS": json.dumps(
                prefetched_products.get("viewed_products", []), indent=2
            ),
            "AVAILABLE_CATEGORIES": json.dumps(all_categories),
            "AVAILABLE_BRANDS": json.dumps(all_brands),
        }

        # Replace placeholders
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, value)

        logger.debug(f"  Streaming system prompt: {len(result)} chars")
        return result

    def _extract_json(self, text_content: str) -> str:
        """Extract JSON string from agent response text."""
        logger.debug("Extracting JSON from response...")

        # Look for ```json block first
        if "```json" in text_content:
            logger.debug("  Found ```json block")
            json_str = text_content.split("```json")[1].split("```")[0].strip()
            return json_str

        # Otherwise find the JSON object
        if "{" in text_content:
            logger.debug("  Extracting raw JSON object")
            start = text_content.index("{")
            end = text_content.rindex("}") + 1
            return text_content[start:end]

        logger.error("  No JSON found in response!")
        logger.error(f"  Full response:\n{text_content}")
        raise ValueError("No JSON found in agent response")

    async def _hydrate_sections(
        self, raw_sections: List[AgentSectionRaw], db: AsyncSession
    ) -> List[HomeSection]:
        """
        Hydrate raw sections (with product IDs) into full sections (with product objects).

        This is the key optimization - agent returns just IDs, we fetch full data in one query.
        """
        logger.info("Hydrating sections with product data...")

        # Collect all unique product IDs from all sections
        all_product_ids: set[int] = set()
        for section in raw_sections:
            if section.product_ids:
                all_product_ids.update(section.product_ids)
            if section.product_id:
                all_product_ids.add(section.product_id)

        logger.info(f"  Collected {len(all_product_ids)} unique product IDs to hydrate")

        if not all_product_ids:
            logger.info("  No products to hydrate - returning sections as-is")
            # Return sections without products (slogans, etc.)
            return [
                HomeSection(
                    component_type=s.component_type,
                    title=s.title,
                    subtitle=s.subtitle,
                    slogan_text=s.slogan_text,
                    products=None,
                    product=None,
                )
                for s in raw_sections
            ]

        # Fetch all products in ONE query
        logger.info(f"  Fetching products: {sorted(all_product_ids)}")
        result = await db.execute(
            select(Product).where(Product.id.in_(all_product_ids))
        )
        products_by_id: Dict[int, Product] = {p.id: p for p in result.scalars().all()}
        logger.info(f"  Fetched {len(products_by_id)} products from database")

        # Helper to convert Product model to HydratedProduct schema
        def to_hydrated(p: Product) -> HydratedProduct:
            return HydratedProduct(
                id=p.id,
                name=p.name,
                price=p.price,
                category=p.category,
                brand=p.brand,
                rating=p.rating,
                image_file_path=p.image_file_path,
                shipping_speed=p.shipping_speed,
                description=p.description[:200] if p.description else "",
            )

        # Hydrate each section
        hydrated_sections: List[HomeSection] = []
        for section in raw_sections:
            # Hydrate product list (for carousel, card, basic-square)
            hydrated_products = None
            if section.product_ids:
                hydrated_products = [
                    to_hydrated(products_by_id[pid])
                    for pid in section.product_ids
                    if pid in products_by_id
                ]

            # Hydrate single product (for super-card, specific-upsell)
            hydrated_product = None
            if section.product_id and section.product_id in products_by_id:
                hydrated_product = to_hydrated(products_by_id[section.product_id])

            hydrated_sections.append(
                HomeSection(
                    component_type=section.component_type,
                    title=section.title,
                    subtitle=section.subtitle,
                    slogan_text=section.slogan_text,
                    products=hydrated_products,
                    product=hydrated_product,
                )
            )

            # Log hydration result
            product_count = len(hydrated_products) if hydrated_products else 0
            has_single = "yes" if hydrated_product else "no"
            logger.debug(
                f"  Hydrated {section.component_type}: {product_count} products, single={has_single}"
            )

        logger.info(f"  Hydration complete: {len(hydrated_sections)} sections")
        return hydrated_sections

    async def _parse_response(
        self, text_content: str, db: AsyncSession
    ) -> HomePageResponse:
        """Parse Claude's response and hydrate with full product data."""
        logger.info("Parsing agent response (lightweight IDs)...")

        # Extract JSON string
        json_str = self._extract_json(text_content)
        logger.debug(f"  JSON string length: {len(json_str)} chars")
        logger.debug(f"  JSON content:\n{json_str}")

        # Parse raw response (just IDs, no full products)
        raw_response = AgentHomePageResponseRaw.model_validate_json(json_str)
        logger.info(f"  Parsed {len(raw_response.sections)} raw sections")

        # Log raw section details
        for i, section in enumerate(raw_response.sections):
            id_count = len(section.product_ids) if section.product_ids else 0
            has_single = section.product_id if section.product_id else "none"
            logger.debug(
                f"  Section {i+1}: {section.component_type} | product_ids: {id_count} | product_id: {has_single}"
            )

        # Hydrate sections with full product data
        hydrated_sections = await self._hydrate_sections(raw_response.sections, db)

        # Return final response
        return HomePageResponse(sections=hydrated_sections, is_personalized=True)
