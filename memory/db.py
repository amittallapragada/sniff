from functools import lru_cache

from config import settings
from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
