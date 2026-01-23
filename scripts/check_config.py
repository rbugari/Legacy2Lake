
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def check_configuration():
    print("--- [HARD CHECK] Validating Configuration ---")
    
    # 1. Admin DB to fetch Matrix
    admin_db = SupabasePersistence(tenant_id=None)
    
    # Fetch all active matrix configs
    matrix_res = admin_db.client.table("utm_agent_matrix").select("*").eq("is_active", True).execute()
    matrix = matrix_res.data
    
    # 2. Group by Tenant? 
    # For MVP, we assume we are checking for a specific Tenant (e.g. DEMO) because Matrix might be Global or Tenant-Specific?
    # Wait, utm_agent_matrix currently has NO tenant_id, so it implies Global Default defaults.
    # But utm_provider_vault IS tenant-specific.
    # So we must check: "For Tenant X, do they have credentials for the Global Matrix requirements?"
    
    # Let's target the DEMO tenant for now
    DEMO_TENANT_ID = "d127a303-fd01-44b3-a7b3-827238d76d1f" # From previous sql result
    print(f"Target Tenant: {DEMO_TENANT_ID}")
    
    # Fetch Tenant Credentials
    vault_res = admin_db.client.table("utm_provider_vault")\
        .select("provider_name")\
        .eq("tenant_id", DEMO_TENANT_ID)\
        .eq("is_active", True)\
        .execute()
        
    available_providers = {r["provider_name"] for r in vault_res.data}
    print(f"Available Credentials: {available_providers}")
    
    print("\n--- Analyzing Agents ---")
    all_good = True
    for agent in matrix:
        required_provider = agent["provider"]
        required_model = agent["model_id"]
        
        status = "[OK]" if required_provider in available_providers else "[MISSING CREDENTIAL]"
        if required_provider not in available_providers:
            all_good = False
            
        print(f"{status} Agent {agent['agent_id']} -> Requires {required_provider}/{required_model}")
        
    print("\n--- Result ---")
    if all_good:
        print("✅ Configuration Optimized. All Agents have credentials.")
    else:
        print("❌ Configuration Incomplete. Missing credentials for some agents.")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(check_configuration())
