
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def update_demo_vault():
    print("--- Updating DEMO Vault Credentials ---")
    
    # User Provided Keys (Load from Env)
    GROQ_KEY = os.getenv("GROQ_API_KEY")
    AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    # Admin DB
    db = SupabasePersistence(tenant_id=None)
    
    # Get DEMO Tenant ID
    res = db.client.table("utm_tenants").select("tenant_id").eq("username", "DEMO").execute()
    if not res.data:
        print("[Error] DEMO tenant not found!")
        return
        
    tenant_id = res.data[0]["tenant_id"]
    print(f"Target Tenant: {tenant_id}")
    
    credentials = [
        {
            "tenant_id": tenant_id,
            "provider_name": "groq",
            "api_key": GROQ_KEY,
            "base_url": "https://api.groq.com/openai/v1",
            "is_active": True
        },
        {
            "tenant_id": tenant_id,
            "provider_name": "azure",
            "api_key": AZURE_KEY,
            "base_url": AZURE_ENDPOINT, 
            # Note: Azure base_url in standard SDK usually needs the full endpoint.
            # We store it as is.
            "is_active": True
        }
    ]
    
    for cred in credentials:
        try:
            # Upsert by tenant_id + provider_name?
            # Table constraint might be unique(tenant_id, provider_name).
            # Let's check if exists first to be safe or use upsert if constraint exists.
            
            existing = db.client.table("utm_provider_vault")\
                .select("id")\
                .eq("tenant_id", tenant_id)\
                .eq("provider_name", cred["provider_name"])\
                .execute()
                
            if existing.data:
                print(f"[Update] Updating {cred['provider_name']}...")
                db.client.table("utm_provider_vault")\
                    .update(cred)\
                    .eq("id", existing.data[0]["id"])\
                    .execute()
            else:
                print(f"[Insert] Adding {cred['provider_name']}...")
                db.client.table("utm_provider_vault").insert(cred).execute()
                
        except Exception as e:
            print(f"[Error] Failed to update {cred['provider_name']}: {e}")
            
    print("--- Vault Update Complete ---")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(update_demo_vault())
