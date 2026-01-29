
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def fix_settings():
    db = SupabasePersistence()
    # DEMO3
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    # Correct settings format expected by frontend
    new_settings = {
        "source_tech": "Microsoft SSIS",
        "target_tech": "Databricks (PySpark)"
    }
    
    print(f"Updating TEST9 (Tenant {tenant_id}) settings to: {new_settings}")
    
    try:
        res = db.client.table("utm_projects").update({"settings": new_settings}).eq("name", "TEST9").eq("tenant_id", tenant_id).execute()
        print("✅ Success:", res.data)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_settings())
