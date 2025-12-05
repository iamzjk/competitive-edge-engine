"""
Product template endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from app.models.template import ProductTemplate, ProductTemplateCreate
from app.middleware.auth import get_current_user
from app.database import get_supabase
from app.services.schema_validator import SchemaValidator

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=List[ProductTemplate])
async def list_templates(current_user: dict = Depends(get_current_user)):
    """List available templates (system + user's)"""
    supabase = get_supabase()
    
    # Get system templates and user's templates
    response = supabase.table("product_templates").select("*").or_(
        f"is_system.eq.true,user_id.eq.{current_user['user_id']}"
    ).execute()
    
    return response.data


@router.get("/{template_id}", response_model=ProductTemplate)
async def get_template(template_id: UUID, current_user: dict = Depends(get_current_user)):
    """Get a template by ID"""
    supabase = get_supabase()
    
    response = supabase.table("product_templates").select("*").eq("id", str(template_id)).or_(
        f"is_system.eq.true,user_id.eq.{current_user['user_id']}"
    ).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return response.data[0]


@router.post("/", response_model=ProductTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(template: ProductTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Create a custom template"""
    # Validate schema
    is_valid, errors = SchemaValidator.validate_schema(template.schema)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schema: {', '.join(errors)}"
        )
    
    supabase = get_supabase()
    response = supabase.table("product_templates").insert({
        "name": template.name,
        "schema": template.schema.model_dump(),
        "is_system": False,
        "user_id": current_user["user_id"]
    }).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create template"
        )
    
    return response.data[0]


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: UUID, current_user: dict = Depends(get_current_user)):
    """Delete a user template (cannot delete system templates)"""
    supabase = get_supabase()
    
    # Verify it's a user template
    existing_response = supabase.table("product_templates").select("*").eq("id", str(template_id)).execute()
    
    if not existing_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template = existing_response.data[0]
    if template.get("is_system"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system templates"
        )
    
    if template.get("user_id") != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other users' templates"
        )
    
    response = supabase.table("product_templates").delete().eq("id", str(template_id)).eq("user_id", current_user["user_id"]).execute()
    
    return None

