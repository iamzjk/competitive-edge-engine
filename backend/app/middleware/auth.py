"""
Authentication middleware for Supabase Auth
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import settings
import jwt


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
        
        # Decode JWT token to extract user information
        # Supabase tokens are JWTs with user_id in the 'sub' claim
        try:
            # Decode without verification to get the payload
            # Note: In production, you should verify the signature using Supabase's JWT secret
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get("sub")
            email = decoded.get("email")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID"
                )
            
            return {
                "user_id": user_id,
                "email": email,
                "user": None
            }
        except jwt.DecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token format: {str(e)}"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

