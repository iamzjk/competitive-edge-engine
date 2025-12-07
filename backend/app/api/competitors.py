"""
Competitor listing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID

from app.models.competitor import CompetitorListing, CompetitorListingCreate, CompetitorListingUpdate
from app.middleware.auth import get_current_user
from app.database import get_supabase

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/", response_model=List[CompetitorListing])
async def list_competitors(
    product_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all competitor listings for the current user"""
    supabase = get_supabase()
    
    query = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"])
    
    if product_id:
        query = query.eq("my_product_id", str(product_id))
    
    response = query.execute()
    
    return response.data


@router.get("/{listing_id}", response_model=CompetitorListing)
async def get_competitor(listing_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get a competitor listing by ID"""
    supabase = get_supabase()
    
    response = supabase.table("competitor_listings").select("*").eq("id", str(listing_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor listing not found"
        )
    
    return response.data[0]


@router.post("/manual", response_model=CompetitorListing, status_code=status.HTTP_201_CREATED)
async def create_competitor_manual(
    competitor: CompetitorListingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Manually create a competitor listing (triggers immediate crawl)"""
    # Verify product belongs to user
    supabase = get_supabase()
    product_response = supabase.table("my_products").select("id").eq("id", str(competitor.my_product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not product_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Create competitor listing
    response = supabase.table("competitor_listings").insert({
        "my_product_id": str(competitor.my_product_id),
        "url": competitor.url,
        "retailer_name": competitor.retailer_name,
        "product_name": competitor.product_name,
        "data": competitor.data,
        "image_url": competitor.image_url,
        "user_id": current_user["user_id"]
    }).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create competitor listing"
        )
    
    # TODO: Trigger immediate crawl (will be implemented in crawl service)
    
    return response.data[0]


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(listing_id: UUID, current_user: dict = Depends(get_current_user)):
    """Delete a competitor listing"""
    supabase = get_supabase()
    
    response = supabase.table("competitor_listings").delete().eq("id", str(listing_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor listing not found"
        )
    
    return None

