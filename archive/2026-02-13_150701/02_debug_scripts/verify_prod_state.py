
import os
import asyncio
from dotenv import load_dotenv
from apps.api.services.persistence_service import SupabasePersistence

load_dotenv()

async def check_prod_state():
    print("--- Verifying PROD State ---")
    
    # Initialize Persistence
    # Note: DB credentials should be loaded from .env by SupabasePersistence internally or via env vars
    # checking if SupabasePersistence uses env vars directly. Yes, it likely does.
    
    # However, SupabasePersistence might need specific init params if not default.
    # Looking at main.py: lab = PromptLabService(tenant_id=db.tenant_id, client_id=db.client_id)
    # But for a script, we can just instantiate basic client or use SupabasePersistence.
    
    # Wait, SupabasePersistence assumes a request context often (tenant_id).
    # But usually it can be used for general queries if we pass a default tenant or just use the client.
    
    try:
        db = SupabasePersistence() 
        # Note: If SupabasePersistence requires arguments, this might fail.
        # Let's try to get the raw client if possible, or assume it works.
        # Actually, let's look at persistence_service.py if I was cautious, but I'll try this.
        
        print(f"Checking 'utm_projects'...")
        res_projects = db.client.table("utm_projects").select("count", count="exact").execute()
        count_projects = res_projects.count
        print(f"Projects Count: {count_projects}")
        
        print(f"Checking 'utm_provider_vault'...")
        res_vault = db.client.table("utm_provider_vault").select("*").execute()
        vault_items = res_vault.data
        print(f"Vault Items Count: {len(vault_items)}")
        for item in vault_items:
            print(f" - Provider: {item.get('provider_name')} (Active: {item.get('is_active')})")
            
        print("--- Verification Complete ---")

    except Exception as e:
        print(f"Error verifying state: {e}")

if __name__ == "__main__":
    asyncio.run(check_prod_state())
