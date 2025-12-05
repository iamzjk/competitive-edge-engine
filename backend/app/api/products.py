"""
Product CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.models.product import Product, ProductCreate, ProductUpdate
from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.schema_validator import SchemaValidator, SchemaValidationError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[Product])
async def list_products(current_user: dict = Depends(get_current_user)):
    """List all products for the current user"""
    supabase = get_supabase()
    
    response = supabase.table("my_products").select("*").eq("user_id", current_user["user_id"]).execute()
    
    return response.data


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """Create a new product"""
    # Validate schema
    is_valid, errors = SchemaValidator.validate_schema(product.schema)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schema: {', '.join(errors)}"
        )
    
    # Validate data against schema
    is_valid, errors = SchemaValidator.validate_data_against_schema(product.data, product.schema)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data validation failed: {', '.join(errors)}"
        )
    
    # Normalize data
    normalized_data = SchemaValidator.normalize_data(product.data, product.schema)
    
    supabase = get_supabase()
    response = supabase.table("my_products").insert({
        "sku": product.sku,
        "name": product.name,
        "product_type": product.product_type,
        "schema": product.schema.model_dump(),
        "data": normalized_data,
        "user_id": current_user["user_id"]
    }).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )
    
    return response.data[0]


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get a product by ID"""
    supabase = get_supabase()
    
    response = supabase.table("my_products").select("*").eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return response.data[0]


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: UUID, product_update: ProductUpdate, current_user: dict = Depends(get_current_user)):
    """Update a product"""
    supabase = get_supabase()
    
    # Get existing product
    existing_response = supabase.table("my_products").select("*").eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not existing_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    existing_product = existing_response.data[0]
    
    # Build update dict
    update_data = {}
    if product_update.sku is not None:
        update_data["sku"] = product_update.sku
    if product_update.name is not None:
        update_data["name"] = product_update.name
    if product_update.product_type is not None:
        update_data["product_type"] = product_update.product_type
    
    # Handle schema update
    if product_update.schema is not None:
        # Validate new schema
        is_valid, errors = SchemaValidator.validate_schema(product_update.schema)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid schema: {', '.join(errors)}"
            )
        update_data["schema"] = product_update.schema.model_dump()
    
    # Handle data update
    if product_update.data is not None:
        # Use new schema if provided, otherwise use existing
        schema_to_validate = product_update.schema if product_update.schema else existing_product["schema"]
        from app.models.schema import ProductSchema
        schema_obj = ProductSchema(**schema_to_validate)
        
        # Validate data
        is_valid, errors = SchemaValidator.validate_data_against_schema(product_update.data, schema_obj)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data validation failed: {', '.join(errors)}"
            )
        
        # Normalize data
        normalized_data = SchemaValidator.normalize_data(product_update.data, schema_obj)
        update_data["data"] = normalized_data
    
    response = supabase.table("my_products").update(update_data).eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )
    
    return response.data[0]


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID, current_user: dict = Depends(get_current_user)):
    """Delete a product"""
    supabase = get_supabase()
    
    response = supabase.table("my_products").delete().eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return None


@router.get("/{product_id}/schema")
async def get_product_schema(product_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get product schema definition"""
    supabase = get_supabase()
    
    response = supabase.table("my_products").select("schema").eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"schema": response.data[0]["schema"]}

