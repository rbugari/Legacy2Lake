
import asyncio
import os
import uuid
import hashlib
from dotenv import load_dotenv

# Ensure we can import from apps
import sys
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def migrate_demo():
    print("--- Starting Migration to DEMO Tenant ---")
    
    # Init DB with no context (Super Admin)
    db = SupabasePersistence(tenant_id=None)
    
    # 1. Create Client 'DEMO'
    client_name = "DEMO"
    client_id = None
    
    res = db.client.table("utm_clients").select("client_id").eq("name", client_name).execute()
    if res.data:
        client_id = res.data[0]["client_id"]
        print(f"[Info] Found existing Client DEMO: {client_id}")
    else:
        res = db.client.table("utm_clients").insert({"name": client_name}).execute()
        client_id = res.data[0]["client_id"]
        print(f"[Success] Created Client DEMO: {client_id}")

    # 2. Create Tenant 'DEMO' with password 'DEMO123!'
    username = "DEMO"
    password_plain = "DEMO123!"
    # Simple hash for MVP (SHA256)
    password_hash = hashlib.sha256(password_plain.encode()).hexdigest()
    
    tenant_id = None
    res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if res.data:
        tenant_id = res.data[0]["tenant_id"]
        print(f"[Info] Found existing Tenant DEMO: {tenant_id}")
    else:
        res = db.client.table("utm_tenants").insert({
            "client_id": client_id,
            "username": username,
            "password_hash": password_hash,
            "role": "ADMIN"
        }).execute()
        tenant_id = res.data[0]["tenant_id"]
        print(f"[Success] Created Tenant DEMO: {tenant_id}")

    # 3. Migrate ALL existing Projects to DEMO
    # Find projects with NULL tenant_id
    res = db.client.table("utm_projects").select("project_id").is_("tenant_id", "null").execute()
    projects = res.data or []
    print(f"[Info] Found {len(projects)} orphan projects to migrate.")
    
    for p in projects:
        # Update Project
        db.client.table("utm_projects").update({
            "tenant_id": tenant_id,
            "client_id": client_id
        }).eq("project_id", p["project_id"]).execute()
        
        # Update Objects
        db.client.table("utm_objects").update({
            "tenant_id": tenant_id,
            "client_id": client_id
        }).eq("project_id", p["project_id"]).execute()
        
    print(f"[Success] Migrated projects to DEMO.")

    # 4. Migrate .env Keys to Vault
    # Read .env manually
    env_keys = {
        "azure": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "groq": ["GROQ_API_KEY"]
    }
    
    print("[Info] Scanning .env for keys...")
    
    for provider, keys in env_keys.items():
        api_key = None
        base_url = None
        
        for k in keys:
            val = os.getenv(k)
            if val:
                if "KEY" in k: api_key = val
                if "ENDPOINT" in k: base_url = val
        
        if api_key:
            print(f"[Info] Found key for {provider}. Saving to Vault...")
            
            # Upsert into Vault
            try:
                data = {
                    "tenant_id": tenant_id,
                    "provider_name": provider,
                    "api_key": api_key, # Plaintext for MVP as requested
                    "is_active": True
                }
                if base_url: data["base_url"] = base_url
                
                # Check exist
                existing = db.client.table("utm_provider_vault").select("id").eq("tenant_id", tenant_id).eq("provider_name", provider).execute()
                
                if existing.data:
                    db.client.table("utm_provider_vault").update(data).eq("id", existing.data[0]["id"]).execute()
                else:
                    db.client.table("utm_provider_vault").insert(data).execute()
                    
            except Exception as e:
                print(f"[Error] Failed to save {provider} key: {e}")

    print("--- Migration Complete ---")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(migrate_demo())
