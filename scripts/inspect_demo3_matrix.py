
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def inspect_matrix():
    # DEMO3
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    # Initialize as Admin to see all
    db = SupabasePersistence()
    print(f"--- Inspecting Agent Matrix for Tenant: {tenant_id} ---")
    
    # 1. Get Agent Matrix for agent-s
    res = db.client.table("utm_agent_matrix").select("*").eq("tenant_id", tenant_id).eq("agent_id", "agent-s").execute()
    matrix = res.data
    
    if not matrix:
        print("❌ No matrix entry for agent-s!")
        return

    config = matrix[0]
    model_id = config['model_id']
    print(f"Agent-S is mapped to Model: {model_id}")
    
    # 2. Get Model Details
    m_res = db.client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
    if not m_res.data:
        print(f"❌ Model {model_id} not found in catalog!")
        return
        
    model = m_res.data[0]
    print(f"Model ID: {model['model_id']}")
    print(f"Provider: {model.get('provider')}")
    print(f"Deployment ID (Catalog): {model.get('deployment_id')}")
    print(f"API Version: {model.get('api_version')}")
    
    # 3. Get Vault for Provider (Admin check)
    v_res = db.client.table("utm_vault").select("provider_name, encrypted_credentials").eq("tenant_id", tenant_id).eq("provider_name", model.get('provider')).execute()
    if v_res.data:
        print("Vault Credentials Found (Encrypted).")
        # We can't decrypt easily here without correct keys/methods but knowing it exists is step 1.
    else:
        print("❌ No Vault entry for this provider!")

if __name__ == "__main__":
    asyncio.run(inspect_matrix())
