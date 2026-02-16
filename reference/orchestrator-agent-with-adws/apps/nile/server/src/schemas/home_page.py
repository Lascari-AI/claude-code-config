"""Home page schemas for adaptive UI - aligned with shopping_expert_system_prompt.md

Two-phase schema design:
1. Agent returns lightweight JSON with just product IDs (AgentSectionRaw)
2. We hydrate with full product data before returning to frontend (HomeSection)
"""
from typing import List, Literal, Optional

from pydantic import BaseModel

ComponentType = Literal[
    "generic-slogan",
    "specific-slogan",
    "specific-upsell",
    "basic-square",
    "carousel",
    "card",
    "super-card"
]


# =============================================================================
# PHASE 1: Raw Agent Response (lightweight - just IDs)
# =============================================================================

class AgentSectionRaw(BaseModel):
    """
    Raw section from agent - uses product_ids instead of full products.
    This is what the agent actually returns (optimized for speed).

    Component Type Reference:
    - specific-slogan: slogan_text, subtitle
    - specific-upsell: title, subtitle, product_id
    - carousel: title, product_ids
    - card: title, product_ids
    - super-card: title, product_id
    - basic-square: title, product_ids
    """
    component_type: ComponentType

    # Text fields (used by slogan types)
    title: Optional[str] = None
    subtitle: Optional[str] = None
    slogan_text: Optional[str] = None

    # Product ID fields (lightweight - just IDs, we hydrate later)
    product_ids: Optional[List[int]] = None  # For carousel, card, basic-square
    product_id: Optional[int] = None  # For specific-upsell, super-card

    class Config:
        extra = "ignore"  # Ignore extra fields agent might return


class AgentHomePageResponseRaw(BaseModel):
    """
    Raw agent response - sections with product IDs only.
    This is parsed first, then hydrated with full product data.
    """
    sections: List[AgentSectionRaw]

    class Config:
        extra = "ignore"  # Ignore extra fields agent might return


# =============================================================================
# PHASE 2: Hydrated Response (full product data for frontend)
# =============================================================================

class HydratedProduct(BaseModel):
    """
    Full product data for frontend display.
    Hydrated from database after parsing agent response.
    """
    id: int
    name: str
    price: float
    category: str
    brand: str
    rating: float
    image_file_path: str
    shipping_speed: str
    description: str

    class Config:
        extra = "ignore"


class HomeSection(BaseModel):
    """
    Hydrated section for frontend - contains full product objects.
    This is what the frontend receives after we hydrate the agent's IDs.

    Component Type Reference:
    - specific-slogan: slogan_text, subtitle
    - specific-upsell: title, subtitle, product
    - carousel: title, products
    - card: title, products
    - super-card: title, product
    - basic-square: title, products
    """
    component_type: ComponentType

    # Text fields (used by slogan types)
    title: Optional[str] = None
    subtitle: Optional[str] = None
    slogan_text: Optional[str] = None

    # Product fields - HYDRATED with full product data
    products: Optional[List[HydratedProduct]] = None  # For carousel, card, basic-square
    product: Optional[HydratedProduct] = None  # For specific-upsell, super-card

    class Config:
        extra = "ignore"


class HomePageResponse(BaseModel):
    """
    Final response to frontend.
    Contains hydrated sections with full product data.
    """
    sections: List[HomeSection]
    is_personalized: bool
