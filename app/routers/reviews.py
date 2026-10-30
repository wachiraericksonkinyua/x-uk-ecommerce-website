from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.database import supabase
from app.dependencies import get_current_user, get_optional_user, user_is_admin

router = APIRouter(prefix="/reviews", tags=["Reviews"])

class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)#ge stands for "greater than or equal to" and le stands for "less than or equal to". This means that the rating must be between 1 and 5, inclusive.
    comment: str

@router.post("/")
def add_review(payload: ReviewCreate, current_user = Depends(get_current_user)):
    try:
        #check if user has a completed order containing this product before allowing them to leave a review
        orders_res = supabase.table("orders").select("items").eq("user_id", current_user.id).execute()#here we are querying the "orders" table in the Supabase database to check if the user has any completed orders that include the product they want to review. We filter the orders by the authenticated user's id.

        has_purchased = False #here we are initializing a variable called has_purchased to False. This variable will be used to track whether the user has purchased the product they want to review.
        if orders_res.data:
            for order in orders_res.data:
                if not isinstance(order, dict):
                    continue

                items = order.get("items") or []
                if not isinstance(items, list):
                    continue

                # Order items store the product id under "id" (fall back to "product_id")
                if any(
                    isinstance(item, dict)
                    and (item.get("id") == payload.product_id or item.get("product_id") == payload.product_id)
                    for item in items
                ):
                    has_purchased = True
                    break
                    
        if not has_purchased:
            raise HTTPException(
                status_code=403, 
                detail="Verified buyer check failed. You can only review products you have purchased."
            )

        # If verified, save the review attributed to the authenticated user.
        # New reviews are unapproved until an admin moderates them.
        response = supabase.table("reviews").insert({
            "product_id": payload.product_id,
            "user_id": current_user.id,
            "rating": payload.rating,
            "comment": payload.comment,
            "is_approved": False,
        }).execute()
        return {"success": True, "message": "Review added successfully", "data": response.data}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def list_product_reviews(product_id: str, current_user=None):
    """Return a product's reviews.

    Guests and regular customers only see approved reviews; admins see all of
    them so they can moderate.
    """
    try:
        query = supabase.table("reviews").select("*").eq("product_id", product_id)
        if not user_is_admin(current_user):
            query = query.eq("is_approved", True)
        response = query.execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{product_id}")
def get_product_reviews(product_id: str, current_user = Depends(get_optional_user)):
    return list_product_reviews(product_id, current_user)