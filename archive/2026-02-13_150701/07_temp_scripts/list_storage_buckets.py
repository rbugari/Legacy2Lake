"""
List Supabase Storage buckets
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

print("="*70)
print("🗄️  Listing Supabase Storage Buckets")
print("="*70)

try:
    buckets = supabase.storage.list_buckets()
    
    if buckets:
        print(f"\n📋 Found {len(buckets)} buckets:")
        for bucket in buckets:
            print(f"\n   Name: {bucket['name']}")
            print(f"   ID: {bucket.get('id', 'N/A')}")
            print(f"   Public: {bucket.get('public', False)}")
            print(f"   Created: {bucket.get('created_at', 'N/A')}")
    else:
        print("\n⚠️ No buckets found")
        
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*70)
