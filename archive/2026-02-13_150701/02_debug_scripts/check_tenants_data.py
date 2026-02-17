"""Check tenants data"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("Checking utm_tenants table...")
try:
    res = client.table('utm_tenants').select('*').execute()
    print(f"Found {len(res.data)} tenants")
    
    if res.data:
        print("\nColumns:")
        for key in res.data[0].keys():
            print(f"  - {key}")
        
        print("\nFirst tenant:")
        import json
        print(json.dumps(res.data[0], indent=2, default=str))
    else:
        print("\n⚠️  Table is empty - trying to see schema...")
        
except Exception as e:
    print(f"Error: {e}")

# Check if there's an "old" tenants table still
print("\n\nChecking if utm_tenants_old exists...")
try:
    res_old = client.table('utm_tenants_old').select('*').limit(1).execute()
    print(f"Found utm_tenants_old with {len(res_old.data)} records")
    if res_old.data:
        print("Columns:")
        for key in res_old.data[0].keys():
            print(f"  - {key}")
except Exception as e:
    print(f"utm_tenants_old doesn't exist or error: {e}")
