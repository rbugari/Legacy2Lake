"""
Check utm_projects table structure
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0ad4-e0e5-424a-ad93-0c8ae586a8f4"

# Try different project ID columns
for col in ["project_id", "id", "uuid"]:
    try:
        result = supabase.table("utm_projects").select("*").eq(col, project_id).execute()
        if result.data:
            print(f"✅ Found project using column: {col}")
            print(f"   Columns: {list(result.data[0].keys())}")
            break
    except Exception as e:
        print(f"❌ Column {col} doesn't exist: {e}")

# If nothing worked, get first project
try:
    result = supabase.table("utm_projects").select("*").limit(1).execute()
    if result.data:
        print(f"\n📋 Sample project columns:")
        for key in result.data[0].keys():
            print(f"   - {key}: {result.data[0][key]}")
except Exception as e:
    print(f"\n❌ Error: {e}")
