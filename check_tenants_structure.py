"""Check utm_tenants structure"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# Get one tenant to see structure
res = client.table('utm_tenants').select('*').limit(1).execute()

if res.data:
    print("utm_tenants columns:")
    for key in res.data[0].keys():
        print(f"  - {key}")
    print("\nSample tenant:")
    print(res.data[0])
else:
    print("No tenants in database")
