
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def update_demo3_model():
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    # Admin context to bypass RLS issues for update if possible, 
    # but strictly we should use tenant_id if RLS allows update on own rows.
    # Trying with tenant_id first as it's safer logic.
    db = SupabasePersistence(tenant_id=tenant_id)
    
    print(f"--- Updating Model Config for Tenant: {tenant_id} ---")
    
    # 1. Resolve which model Agent S uses
    res = db.client.table("utm_agent_matrix").select("model_id").eq("tenant_id", tenant_id).eq("agent_id", "agent-s").execute()
    
    if not res.data:
        print("❌ No matrix entry for agent-s found.")
        return

    model_id = res.data[0]['model_id']
    print(f"Agent-S uses Model: {model_id}")
    
    # 2. Update that model in Catalog
    updates = {
        "deployment_id": "gpt-4.1",
        "api_version": "2025-01-01-preview"
    }
    
    # Note: Model Catalog might be shared or tenant specific. 
    # If shared, this changes it for everyone using this model_id.
    # Check if model has tenant_id column? Usually catalog is global or per-tenant.
    # Assuming per-tenant or we are updating a specific instance.
    
    print(f"Updating {model_id} with: {updates}")
    
    try:
        # Try updating
        u_res = db.client.table("utm_model_catalog").update(updates).eq("model_id", model_id).execute()
        print("✅ Update successful!")
        print(u_res.data)
    except Exception as e:
        print(f"❌ Update failed: {e}")

if __name__ == "__main__":
    asyncio.run(update_demo3_model())
