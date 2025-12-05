"""
Product template models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.schema import ProductSchema


class ProductTemplateBase(BaseModel):
    """Base template model"""
    name: str
    schema: ProductSchema
    is_system: bool = False


class ProductTemplateCreate(ProductTemplateBase):
    """Template creation model"""
    pass


class ProductTemplate(ProductTemplateBase):
    """Template model with database fields"""
    id: UUID
    user_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

