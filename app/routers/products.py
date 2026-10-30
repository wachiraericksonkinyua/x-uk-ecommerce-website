from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query
from app.database import supabase
from app.dependencies import require_admin, get_optional_user
from app.routers.reviews import list_product_reviews
import uuid
from typing import List, Optional

router = APIRouter(prefix="/products", tags=["products"])


# @router.get("/")
# async def get_products():
#     response = supabase.table("products").select("*").execute()
#     return {"data": response.data}
@router.get("/")
def get_products(
    search: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    color: Optional[str] = Query(None, description="Filter by color"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: price or created_at"),
    order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    try:
        query = supabase.table("products").select("*, product_images(image_url)")
        
        if search:
            term = search.strip()
            query = query.or_(
                f"name.ilike.%{term}%,brand.ilike.%{term}%,description.ilike.%{term}%"
            )
        if category:
            term = category.strip()
            matched_id = None
            try:
                category_match = (
                    supabase.table("categories")
                    .select("id")
                    .or_(f"slug.ilike.%{term}%,name.ilike.%{term}%")
                    .limit(1)
                    .execute()
                )
                if category_match.data:
                    matched_id = category_match.data[0].get("id")
            except Exception:
                matched_id = None
            if matched_id:
                query = query.or_(
                    f"category.ilike.%{term}%,category_id.eq.{matched_id}"
                )
            else:
                query = query.ilike("category", f"%{term}%")
        if brand:
            query = query.ilike("brand", f"%{brand.strip()}%")
        if color:
            query = query.ilike("color", f"%{color.strip()}%")
        if min_price is not None:
            query = query.gte("price", min_price)
        if max_price is not None:
            query = query.lte("price", max_price)

        sort_field = sort_by or "created_at"
        order_value = (order or "desc").lower()
        is_desc = order_value == "desc"
        query = query.order(sort_field, desc=is_desc)

        response = query.execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_product(
    name: str = Form(...),
    price: float = Form(...),
    brand: str = Form(...),
    images: List[UploadFile] = File(...),
    description: str = Form(...),
    color: str = Form(...),
    admin_user = Depends(require_admin)
):
    # 1. Create the product record first
    new_product = {"name": name, "price": price, "brand": brand, "description": description, "color": color}
    product_response = supabase.table("products").insert(new_product).execute()

    # Safely extract the ID from the response data
    product_data = product_response.data
    if not isinstance(product_data, list) or len(product_data) == 0:
        return {"error": "Failed to create product"}

    created_product = product_data[0]
    if not isinstance(created_product, dict):
        return {"error": "Failed to create product"}

    product_id = created_product.get("id")
    if product_id is None:
        return {"error": "Failed to create product"}

    # 2. Loop through each image and upload it
    for image in images:
        file_bytes = await image.read()

        # Safely get the file extension, default to 'jpg' if missing
        if image.filename and "." in image.filename:
            file_extension = image.filename.split(".")[-1]
        else:
            file_extension = "jpg"

        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"phones/{unique_filename}"

        supabase.storage.from_("product-images").upload(file_path, file_bytes)
        image_url = supabase.storage.from_("product-images").get_public_url(
            file_path
        )

        # 3. Save the image URL in the product_images table
        new_image = {"product_id": product_id, "image_url": image_url}
        supabase.table("product_images").insert(new_image).execute()

    return {"message": "Product and multiple images added successfully!"}


@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    brand: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    admin_user = Depends(require_admin)
):
    # 1. Build a dictionary containing only the fields the user actually provided
    update_data = {}
    if name: update_data["name"] = name
    if price: update_data["price"] = price
    if brand: update_data["brand"] = brand
    if description: update_data["description"] = description
    if color: update_data["color"] = color
    if stock_quantity is not None: update_data["stock_quantity"] = stock_quantity

    # 2. Stop the function if they didn't send anything to update
    if not update_data:
        return {"error": "No new data provided"}

    # 3. Push the changes to the exact product row
    supabase.table("products").update(update_data).eq("id", product_id).execute()
    
    return {"message": f"Product {product_id} updated perfectly!"}


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    admin_user = Depends(require_admin)
                               ):
    # Note: To avoid paying for dead storage, you should ideally write a quick loop here 
    # to fetch the image URLs and delete them from the Supabase storage bucket first!
    
    # Delete the main product record from the database
    supabase.table("products").delete().eq("id", product_id).execute()
    
    return {"message": f"Product {product_id} is completely gone."}

@router.get("/{product_id}/reviews")
def get_product_reviews_alias(product_id: str, current_user = Depends(get_optional_user)):
    """Public reviews for a product (approved only unless fetched by an admin)."""
    return list_product_reviews(product_id, current_user)


@router.get("/{product_id}")
async def get_single_product(product_id: str):
    # Fetch the product and its related images simultaneously
    response = supabase.table("products").select("*, product_images(image_url)").eq("id", product_id).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return {"data": response.data[0]}

