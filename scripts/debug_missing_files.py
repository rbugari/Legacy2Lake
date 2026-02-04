import os
import sys
import boto3
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from services.persistence_service import PersistenceService

load_dotenv()

PROJECT_NAME = "DEMO3"

def debug_files():
    print(f"--- Debugging Files for {PROJECT_NAME} ---")
    
    # 1. Direct R2 List via Boto3 (Raw Truth)
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")
    
    print(f"Checking Bucket: {bucket}")
    
    s3 = boto3.client('s3',
        endpoint_url=endpoint,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        region_name="auto"
    )
    
    # List everything starting with DEMO3
    print(f"\n[Raw Listing] Content with prefix '{PROJECT_NAME}':")
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=PROJECT_NAME)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                print(f" - {obj['Key']} (Size: {obj['Size']})")
        else:
            print(" - NO OBJECTS FOUND.")
    except Exception as e:
        print(f"AWS Error: {e}")

    # 2. PersistenceService Logic
    print(f"\n[App Logic] PersistenceService.get_project_files('{PROJECT_NAME}', None)...")
    try:
        # Simulate the exact call finding nothing
        files = PersistenceService.get_project_files(PROJECT_NAME, None)
        print(f"Returned {len(files)} top-level items.")
        import json
        print(json.dumps(files, indent=2))
        
        # Check for Triage
        triage = next((n for n in files if n["name"] == "Triage"), None)
        if triage:
            print(f"✅ 'Triage' folder found in app logic with {len(triage.get('children', []))} children.")
        else:
            print("❌ 'Triage' folder NOT found in app logic.")
            
    except Exception as e:
        print(f"App Logic Error: {e}")

    print(f"\n[Resolution] Resolving Project Info...")
    from services.persistence_service import SupabasePersistence
    import asyncio
    
    db = SupabasePersistence()
    
    # List all
    print("\n[Project Listing] Listing all projects in DB to find DEMO3...")
    # List all
    print("\n[Project Listing] Listing all projects in DB to find DEMO3...")
    try:
        all_projects = asyncio.run(db.list_projects())
        found_demo3 = False
        
        with open("debug_projects_list.txt", "w", encoding="utf-8") as f:
            for p in all_projects:
                line = f"[{p.get('project_id')}] {p.get('name')} (Tenant: {p.get('tenant_id')})"
                print(line)
                f.write(line + "\n")
                if str(p.get('name')).upper() == PROJECT_NAME.upper():
                    found_demo3 = True
                    print(f"✅ FOUND MATCH: {p.get('name')} (ID: {p.get('project_id')})")
                    # Update uuid variable with the finding
                    uuid = p.get('project_id')
                
        if not found_demo3:
            print(f"⚠️ 'DEMO3' not found in project list! Checking if it's an ID...")
            
        # Skip get_project_id_by_name if we already found it via list
        if not found_demo3:
             async def get_uuid():
                 return await db.get_project_id_by_name(PROJECT_NAME)
             uuid = asyncio.run(get_uuid())

        print(f"Resolved UUID for {PROJECT_NAME}: {uuid}")
        
        if uuid:
            # Check both Normalized Name and UUID in R2
            print(f"\n[Raw Listing] Content with prefix '{uuid}':")
            try:
                resp = s3.list_objects_v2(Bucket=bucket, Prefix=uuid)
                if 'Contents' in resp:
                    for obj in resp['Contents']:
                        print(f" - {obj['Key']} (Size: {obj['Size']})")
                else:
                    print(f" - NO OBJECTS FOUND for UUID {uuid}.")
            except Exception as e:
                print(f"AWS Error: {e}")
                
    except Exception as e:
        print(f"DB Error: {e}")


    print(f"\n[Tenant Listing] Checking for Tenant named '{PROJECT_NAME}'...")
    try:
        tenants = db.client.table("utm_tenants").select("*").execute()
        if tenants.data:
            for t in tenants.data:
                print(f" - [{t['tenant_id']}] {t.get('name')} (Role: {t.get('role')})")
                if t.get('name') == PROJECT_NAME:
                    print(f"✅ FOUND TENANT MATCH: {t.get('name')} (ID: {t['tenant_id']})")
    except Exception as e:
        print(f"Tenant List Error: {e}")

    # Check Local Solutions
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "solutions"))
    print(f"\n[Local Check] checking {base_dir}")
    
    candidates = [PROJECT_NAME]
    if uuid: candidates.append(uuid)
    
    for c in candidates:
        p = os.path.join(base_dir, c)
        if os.path.exists(p):
             print(f"✅ Found local folder: {c}")
        else:
             print(f"❌ Local folder not found: {c}")

    # List R2 Root (Top Level Folders)
    print(f"\n[R2 Root Scan] Listing top-level prefixes in {bucket}...")
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Delimiter='/')
        if 'CommonPrefixes' in resp:
            print("Found Folders:")
            for p in resp['CommonPrefixes']:
                print(f" 📂 {p['Prefix']}")
        else:
            print("No folders found at root.")
            
        # Check for files at root
    except Exception as e:
        print(f"AWS Error: {e}")

    # List contents of the specific tenant for TEST9
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    print(f"\n[R2 Tenant Scan] Listing contents of tenant '{tenant_id}'...")
    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=tenant_id)
        if 'Contents' in resp:
            for obj in resp['Contents']:
                if "test9" in obj['Key'].lower():
                     print(f" - {obj['Key']} (Size: {obj['Size']})")
        else:
            print(f" - EMPTY or NOT FOUND")
    except Exception as e:
        print(f"AWS Error: {e}")
        
    # Also check if it's at the root "TEST9" or "test9"
    print(f"\n[R2 Root Check] Checking for 'TEST9' or 'test9' at root...")
    for p in ["TEST9", "test9"]:
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=p)
            if 'Contents' in resp:
                print(f"FOUND content in '{p}':")
                for obj in resp['Contents']:
                     print(f" - {obj['Key']}")
            else:
                print(f" '{p}' is empty.")
        except Exception: pass

if __name__ == "__main__":
    debug_files()
