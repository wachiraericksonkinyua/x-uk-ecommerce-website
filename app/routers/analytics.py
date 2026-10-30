from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.dependencies import require_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def get_analytics_summary(_admin_user = Depends(require_admin)):
    """
    Admin endpoint to get:
    1. Total daily revenue (for today)
    2. Count of pending orders
    3. Products with low stock (< 5)
    """
    try:
        # 1. Total Daily Revenue
        today = datetime.now().strftime("%Y-%m-%d")
        # Assuming created_at is stored in ISO format
        orders_response = supabase.table("orders").select("total_amount, status, created_at").execute()
        orders = orders_response.data or []

        daily_revenue = 0.0
        for order in orders:
            if not isinstance(order, dict):
                continue

            status = order.get("status")
            created_at = order.get("created_at")
            total_amount = order.get("total_amount")

            if status == "Paid" and isinstance(created_at, str) and created_at.startswith(today):
                try:
                    if isinstance(total_amount, (int, float, str)) and not isinstance(total_amount, bool):
                        daily_revenue += float(total_amount)
                except (TypeError, ValueError):
                    continue

        # 2. Pending Orders
        pending_orders = [
            order for order in orders
            if isinstance(order, dict) and order.get("status") == "Pending PIN"
        ]

        # 3. Low Stock Products
        products_response = supabase.table("products").select("name, stock_quantity").lt("stock_quantity", 5).execute()
        low_stock_products = products_response.data or []
        
        return {
            "daily_revenue": daily_revenue,
            "pending_orders_count": len(pending_orders),
            "low_stock_products": low_stock_products
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
