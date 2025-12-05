"""
Competitor discovery/match endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.crawler import CrawlerService
from app.services.ai_extractor import AIExtractorService
from app.services.matcher import MatcherService

router = APIRouter(prefix="/matches", tags=["matches"])


class MatchCandidate(BaseModel):
    """Match candidate model (in-memory, not stored)"""
    url: str
    retailer_name: str
    product_name: str
    extracted_data: dict
    confidence_score: float
    spec_similarity: float
    semantic_similarity: float


class ApproveCandidateRequest(BaseModel):
    """Request to approve a candidate"""
    product_id: UUID
    url: str
    retailer_name: str
    product_name: str
    extracted_data: dict


@router.post("/discover/{product_id}", response_model=List[MatchCandidate])
async def discover_competitors(
    product_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger Phantom Matchmaker discovery for a product
    Returns candidates in-memory (not stored in database)
    """
    supabase = get_supabase()
    
    # Get product
    product_response = supabase.table("my_products").select("*").eq("id", str(product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not product_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = product_response.data[0]
    
    # Generate search queries from product name
    search_query = product["name"]
    
    # List of retailers to search
    retailers = ["amazon", "homedepot", "walmart", "lowes"]
    
    crawler = CrawlerService()
    extractor = AIExtractorService()
    matcher = MatcherService()
    
    from app.models.schema import ProductSchema
    schema = ProductSchema(**product["schema"])
    
    candidates = []
    
    # Search each retailer
    for retailer in retailers:
        try:
            # Search retailer
            urls = await crawler.search_retailer(retailer, search_query, max_results=5)
            
            # Process each URL
            for url in urls:
                try:
                    # Crawl URL
                    crawled_content = await crawler.crawl_url(url)
                    
                    # Extract data
                    extracted_data = await extractor.extract_from_content(crawled_content, schema)
                    
                    # Calculate confidence score
                    scores = await matcher.calculate_confidence_score(
                        product["name"],
                        product["data"],
                        extracted_data.get("name", "Unknown Product"),
                        extracted_data,
                        schema
                    )
                    
                    candidates.append({
                        "url": url,
                        "retailer_name": retailer.capitalize(),
                        "product_name": extracted_data.get("name", "Unknown Product"),
                        "extracted_data": extracted_data,
                        "confidence_score": scores["confidence_score"],
                        "spec_similarity": scores["spec_similarity"],
                        "semantic_similarity": scores["semantic_similarity"]
                    })
                except Exception as e:
                    # Skip URLs that fail
                    continue
        except Exception as e:
            # Skip retailers that fail
            continue
    
    # Sort by confidence score (highest first)
    candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
    
    # Return top candidates
    return candidates[:10]


@router.post("/approve", response_model=dict, status_code=status.HTTP_201_CREATED)
async def approve_candidate(
    request: ApproveCandidateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Approve a match candidate and create competitor listing
    """
    supabase = get_supabase()
    
    # Verify product belongs to user
    product_response = supabase.table("my_products").select("*").eq("id", str(request.product_id)).eq("user_id", current_user["user_id"]).execute()
    
    if not product_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = product_response.data[0]
    
    # Validate extracted data against product schema
    from app.models.schema import ProductSchema
    from app.services.schema_validator import SchemaValidator
    
    schema = ProductSchema(**product["schema"])
    is_valid, errors = SchemaValidator.validate_data_against_schema(request.extracted_data, schema)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extracted data validation failed: {', '.join(errors)}"
        )
    
    # Normalize data
    normalized_data = SchemaValidator.normalize_data(request.extracted_data, schema)
    
    # Create competitor listing
    response = supabase.table("competitor_listings").insert({
        "my_product_id": str(request.product_id),
        "url": request.url,
        "retailer_name": request.retailer_name,
        "product_name": request.product_name,
        "data": normalized_data,
        "user_id": current_user["user_id"]
    }).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create competitor listing"
        )
    
    return {"listing_id": response.data[0]["id"], "message": "Candidate approved and added to monitoring"}

