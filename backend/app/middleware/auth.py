"""
Authentication middleware for Supabase Auth
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.database import get_supabase


security = HTTPBearer()


async def get_current_user(request: Request) -> dict:
    """
    Get current authenticated user from Supabase Auth token
    
    Returns:
        User dict with user_id and other user info
    """
    try:
        # Get token from Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        token = authorization.replace("Bearer ", "")
        
        # Verify token with Supabase
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)
        
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        return {
            "user_id": user_response.user.id,
            "email": user_response.user.email,
            "user": user_response.user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

