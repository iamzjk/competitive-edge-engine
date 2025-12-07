"""
Product models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.schema import ProductSchema


class ProductBase(BaseModel):
    """Base product model"""
    model_config = ConfigDict()
    
    sku: Optional[str] = None
    name: str
    product_type: str = Field(..., description="Product type identifier")
    schema: ProductSchema  # Note: shadows BaseModel.schema but required for API compatibility
    data: Dict[str, Any] = Field(..., description="Product data matching the schema")


class ProductCreate(ProductBase):
    """Product creation model"""
    pass


class ProductUpdate(BaseModel):
    """Product update model"""
    model_config = ConfigDict()
    
    sku: Optional[str] = None
    name: Optional[str] = None
    product_type: Optional[str] = None
    schema: Optional[ProductSchema] = None  # Note: shadows BaseModel.schema but required for API compatibility
    data: Optional[Dict[str, Any]] = None


class Product(ProductBase):
    """Product model with database fields"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

