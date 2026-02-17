"""Check if SSIS file exists"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

r = supabase.table('utm_objects').select('source_path').eq('source_name', 'DimCustomers.dtsx').single().execute()
path = r.data['source_path']
exists = os.path.exists(path) if path else False

print(f"Path: {path}")
print(f"Exists: {exists}")

if not exists and path:
    # Try to find the file in workspace
    import glob
    matches = glob.glob("**/*DimCustomers.dtsx", recursive=True)
    if matches:
        print(f"\nFound alternative paths:")
        for m in matches:
            print(f"  - {m}")
