"""
Authentication endpoints
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user.get("email"),
    }

