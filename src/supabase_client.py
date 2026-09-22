"""Optional Supabase connection, loaded only when explicitly requested."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@lru_cache(maxsize=1)
def get_supabase():
    """Create the client lazily so local CSV processing needs no credentials."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in .env."
        )
    from supabase import create_client

    return create_client(url, key)


# Backward-compatible access for scripts that explicitly need a client.
class _LazyClient:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)


supabase = _LazyClient()
