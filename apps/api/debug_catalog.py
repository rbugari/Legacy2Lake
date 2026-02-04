from supabase import create_client
import os
import json

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

res = supabase.table("utm_system_catalog").select("*").execute()
print(json.dumps(res.data, indent=2))
