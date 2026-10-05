# app/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

# This is now the single source of truth for your database!
supabase: Client = create_client(url, key)