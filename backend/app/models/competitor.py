"""
Competitor listing models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CompetitorListingBase(BaseModel):
    """Base competitor listing model"""
    my_product_id: UUID
    url: str
    retailer_name: str
    product_name: str
    data: Dict[str, Any] = Field(..., description="Competitor data matching product schema")
    image_url: Optional[str] = None


class CompetitorListingCreate(CompetitorListingBase):
    """Competitor listing creation model"""
    pass


class CompetitorListingUpdate(BaseModel):
    """Competitor listing update model"""
    retailer_name: Optional[str] = None
    product_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    last_crawled_at: Optional[datetime] = None


class CompetitorListing(CompetitorListingBase):
    """Competitor listing model with database fields"""
    id: UUID
    user_id: UUID
    image_url: Optional[str] = None
    last_crawled_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

