import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load .env from the main FinSight folder
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or key is missing in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Supabase connected successfully!")