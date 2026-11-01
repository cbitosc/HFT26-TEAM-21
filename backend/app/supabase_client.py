"""
Supabase client factory.

Two clients:
- anon_client()       — uses the anon key; subject to RLS
- service_client()    — uses the service_role key; bypasses RLS for admin ops
                        NEVER expose this client or its key to the frontend.
"""

from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache(maxsize=1)
def anon_client() -> Client:
    """Lazy-initialised Supabase client using the anon/public key."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError(
            "Supabase is not configured. "
            "Set SUPABASE_URL and SUPABASE_ANON_KEY in backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache(maxsize=1)
def service_client() -> Client:
    """
    Lazy-initialised Supabase admin client using the service_role key.
    Use exclusively for server-side administrative operations (role promotions).
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "Supabase service_role key is not configured. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env"
        )
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
