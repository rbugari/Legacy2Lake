
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def fix_orphan():
    username = "user_saas_5786"
    model_match = "mini"
    
    print(f"--- Fixing Orphaned Model '{model_match}' for {username} ---")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Get Tenant
    user_res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if not user_res.data:
        print("User not found")
        return
    tenant_id = user_res.data[0]["tenant_id"]
    print(f"Target Tenant ID: {tenant_id}")
    
    # Find Orphan
    print("Searching for orphaned model...")
    res = db.client.table("utm_model_catalog").select("*")\
        .ilike("model_id", f"%{model_match}%")\
        .is_("tenant_id", "null")\
        .execute()
        
    if not res.data:
        # Try label matches too
        res = db.client.table("utm_model_catalog").select("*")\
            .ilike("label", f"%{model_match}%")\
            .is_("tenant_id", "null")\
            .execute()

    if res.data:
        for m in res.data:
            print(f"Found Orphan: {m.get('label')} ({m.get('model_id')})")
            print(f"Assigning to tenant {tenant_id}...")
            
            db.client.table("utm_model_catalog")\
                .update({"tenant_id": tenant_id})\
                .eq("model_id", m["model_id"])\
                .execute()
            print("Done.")
    else:
        print("No orphaned models found.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(fix_orphan())
