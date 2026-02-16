"""API Routers for Nile."""
from .auth import router as auth_router
from .cart import router as cart_router
from .expertise import router as expertise_router
from .home import router as home_router
from .orders import router as orders_router
from .products import router as products_router

__all__ = [
    "auth_router",
    "products_router",
    "cart_router",
    "orders_router",
    "expertise_router",
    "home_router"
]
