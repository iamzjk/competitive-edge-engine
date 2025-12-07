"""
Competitor discovery/match endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from pydantic import BaseModel
import logging

from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.crawler import CrawlerService
from app.services.ai_extractor import AIExtractorService
from app.services.matcher import MatcherService

logger = logging.getLogger(__name__)

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
    # Crawling strategy:
    # - Depth 0: Crawl listing/search page (e.g., https://www.lowes.com/search?searchTerm=...)
    # - Depth 1: Extract product URLs from listing page and crawl each product page
    # - Max depth: 1 (only go 1 layer deep, don't follow links from product pages)
    for retailer in retailers:
        try:
            logger.info(f"Searching {retailer} for: {search_query}")
            # Step 1: Crawl listing page (depth 0) and extract product URLs (depth 1)
            urls = await crawler.search_retailer(retailer, search_query, max_results=5)
            logger.info(f"Found {len(urls)} product URLs from {retailer} listing page")
            
            if not urls:
                logger.warning(f"No URLs found for {retailer}")
                continue
            
            # Step 2: Crawl each product page (depth 1 - final depth, no further crawling)
            for url in urls:
                try:
                    logger.info(f"Crawling product page (depth 1): {url}")
                    # Crawl product URL - crawler now automatically detects Amazon pages and uses better wait conditions
                    crawled_content = await crawler.crawl_url(url, wait_for_content=False)
                    
                    if not crawled_content.get("success"):
                        logger.warning(f"Failed to crawl {url}: success=False")
                        continue
                    
                    # Verify we got content
                    content_text = crawled_content.get("text", crawled_content.get("html", ""))
                    if not content_text or len(content_text.strip()) < 100:
                        logger.warning(f"Insufficient content from {url}: content length={len(content_text)}")
                        continue
                    
                    logger.info(f"Extracting data from {url} (content length: {len(content_text)} chars)")
                    # Extract data
                    extracted_data = await extractor.extract_from_content(crawled_content, schema)
                    
                    # Verify we got a product name
                    product_name = extracted_data.get("name")
                    if not product_name or product_name.strip().lower() in ["unknown", "unknown product", "n/a", "null", ""]:
                        logger.warning(f"Failed to extract product name from {url}. Extracted data keys: {list(extracted_data.keys())}")
                        # Log a sample of the content for debugging
                        content_sample = content_text[:500] if content_text else "No content"
                        logger.debug(f"Content sample from {url}: {content_sample}")
                        continue
                    
                    logger.info(f"Calculating confidence score for {url}")
                    # Calculate confidence score
                    scores = await matcher.calculate_confidence_score(
                        product["name"],
                        product["data"],
                        product_name,
                        extracted_data,
                        schema
                    )
                    
                    candidates.append({
                        "url": url,
                        "retailer_name": retailer.capitalize(),
                        "product_name": product_name,
                        "extracted_data": extracted_data,
                        "confidence_score": scores["confidence_score"],
                        "spec_similarity": scores["spec_similarity"],
                        "semantic_similarity": scores["semantic_similarity"],
                        "schema": product["schema"]  # Include schema for frontend unit display
                    })
                    logger.info(f"Added candidate from {retailer}: {product_name} (confidence: {scores['confidence_score']:.2f})")
                except Exception as e:
                    # Log URL failures but continue
                    logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
                    continue
        except Exception as e:
            # Log retailer failures but continue
            logger.error(f"Error searching retailer {retailer}: {str(e)}", exc_info=True)
            continue
    
    # Sort by confidence score (highest first)
    candidates.sort(key=lambda x: x["confidence_score"], reverse=True)
    
    logger.info(f"Discovery complete. Found {len(candidates)} candidates total")
    
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
    
    # Normalize data first (handles unit conversions, type conversions, etc.)
    # This ensures data is in the correct format before validation
    normalized_data = SchemaValidator.normalize_data(request.extracted_data, schema)
    
    # Validate normalized data
    is_valid, errors = SchemaValidator.validate_data_against_schema(normalized_data, schema)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extracted data validation failed: {', '.join(errors)}"
        )
    
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

