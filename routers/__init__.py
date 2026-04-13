import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.auth import router as auth_router
from routers.books import router as books_router
from routers.cart import router as cart_router
from routers.checkout import router as checkout_router
from routers.orders import router as orders_router
from routers.admin import router as admin_router
from routers.profile import router as profile_router

__all__ = [
    "auth",
    "books",
    "cart",
    "checkout",
    "orders",
    "admin",
    "profile",
]