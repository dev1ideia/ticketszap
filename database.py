# database.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

URL_SUPABASE = os.getenv("URL_SUPABASE")
KEY_SUPABASE = os.getenv("KEY_SUPABASE")

# Cria a instância uma única vez
supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)