# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import payments, products, orders, wishlist, ai, auth, reviews, daraja_service, profiles, analytics, upload, cart, delivery, categories
from app.routers.admin import router as admin_router
from app.routers.webhooks.whatsapp import router as whatsapp_webhook_router

app = FastAPI(title="GWV-xuk API")

# CORS: set CORS_ORIGINS as a comma-separated list, e.g.
# CORS_ORIGINS="https://x-uk.com,https://admin.x-uk.com,http://localhost:5173"
_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
if not _origins:
    # Sensible dev defaults so the React frontend is not blocked locally
    _origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://10.44.134.253:5173",
        "http://10.44.134.253:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registering your product routes
app.include_router(products.router)
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(wishlist.router)
app.include_router(ai.router)  # Include the AI router
app.include_router(reviews.router)  # Include the Reviews router
app.include_router(profiles.router)  # Include the Profiles router
app.include_router(analytics.router)  # Include the Analytics router
app.include_router(upload.router)  # Include the Upload router
app.include_router(cart.router)
app.include_router(delivery.router)
app.include_router(categories.router)  # Public storefront categories
app.include_router(admin_router)  # Admin API — all /admin/* routes require an admin
app.include_router(whatsapp_webhook_router)  # Public webhook — Meta calls us
# Note: daraja_service is a utility class, not a router, so it's not registered here.


@app.get("/")
async def root():
    return {"message": "Database connection configured!"}


@app.get("/health")
async def health():
    """Lightweight liveness probe for uptime monitors / load balancers."""
    return {"status": "ok"}
