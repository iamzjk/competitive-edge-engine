"""
Supabase database client setup
"""
from supabase import create_client, Client
from app.config import settings

# Use service_role key for backend to bypass RLS
# The backend handles authorization via JWT tokens and user_id filtering
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_supabase() -> Client:
    """Get Supabase client"""
    return supabase

