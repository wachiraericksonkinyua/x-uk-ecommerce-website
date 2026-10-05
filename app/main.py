# app/main.py
from fastapi import FastAPI
from app.routers import payments, products, orders, wishlist, ai

app = FastAPI()

# Registering your product routes
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(wishlist.router)
app.include_router(ai.router)  # Include the AI router

@app.get("/")
async def root():
    return {"message": "Database connection configured!"}