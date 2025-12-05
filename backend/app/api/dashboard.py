"""
Dashboard endpoints
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.comparator import ComparatorService
from app.services.alert_calculator import AlertCalculatorService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    """
    Get dashboard summary cards data (price drops, spec disadvantages, price increases)
    """
    supabase = get_supabase()
    
    # Get all products and their competitor listings
    products_response = supabase.table("my_products").select("*").eq("user_id", current_user["user_id"]).execute()
    
    if not products_response.data:
        return {
            "summary": {
                "price_drops": {"count": 0, "percentage_change": 0},
                "spec_disadvantages": {"count": 0, "percentage_change": 0},
                "price_increases": {"count": 0, "percentage_change": 0}
            }
        }
    
    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"]).execute()
    
    comparator = ComparatorService()
    alert_calculator = AlertCalculatorService()
    
    # Build comparison results
    comparison_results = []
    
    for listing in listings_response.data:
        # Get product
        product = next((p for p in products_response.data if p["id"] == listing["my_product_id"]), None)
        if not product:
            continue
        
        # Compare
        from app.models.schema import ProductSchema
        schema = ProductSchema(**product["schema"])
        comparison = comparator.compare(product["data"], listing["data"], schema)
        comparison_results.append({
            "listing_id": listing["id"],
            "comparison": comparison
        })
    
    # Get price history for trends
    price_history_response = supabase.table("price_history").select("*").in_(
        "listing_id", [l["id"] for l in listings_response.data]
    ).order("recorded_at", desc=True).execute()
    
    # Calculate alerts
    summary = alert_calculator.calculate_summary(comparison_results, price_history_response.data)
    
    return summary


@router.get("/listings")
async def get_dashboard_listings(current_user: dict = Depends(get_current_user)):
    """
    Get all competitor listings with computed comparisons
    """
    supabase = get_supabase()
    
    # Get all products
    products_response = supabase.table("my_products").select("*").eq("user_id", current_user["user_id"]).execute()
    
    # Get all competitor listings
    listings_response = supabase.table("competitor_listings").select("*").eq("user_id", current_user["user_id"]).execute()
    
    comparator = ComparatorService()
    
    listings_with_comparison = []
    
    for listing in listings_response.data:
        # Get product
        product = next((p for p in products_response.data if p["id"] == listing["my_product_id"]), None)
        if not product:
            continue
        
        # Compare
        from app.models.schema import ProductSchema
        schema = ProductSchema(**product["schema"])
        comparison = comparator.compare(product["data"], listing["data"], schema)
        
        listings_with_comparison.append({
            **listing,
            "comparison": comparison
        })
    
    return listings_with_comparison

