import os
from dotenv import load_dotenv
from supabase import create_client

# read the .env file
load_dotenv()

# read keys from .env file
SUPABASE_URL   = os.getenv("SUPABASE_URL")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY")
SECRET_KEY     = os.getenv("SECRET_KEY")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")

# connect to supabase database
# this one line creates the connection
# app.py imports this and uses it for all database calls
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)