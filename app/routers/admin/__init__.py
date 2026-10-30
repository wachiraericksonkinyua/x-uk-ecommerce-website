"""Admin API — every route under /admin requires an authenticated admin.

The parent router applies `require_admin` once, so individual modules cannot
forget the check. Sub-routers only declare their own prefix + tags.
"""
from fastapi import APIRouter, Depends

from app.dependencies import require_admin
from app.routers.admin import (
    categories,
    customers,
    dashboard,
    delivery,
    inventory,
    leads,
    orders,
    products,
    reviews,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)

router.include_router(dashboard.router)
router.include_router(orders.router)
router.include_router(products.router)
router.include_router(categories.router)
router.include_router(customers.router)
router.include_router(inventory.router)
router.include_router(delivery.router)
router.include_router(reviews.router)
router.include_router(leads.router)
