"""
Verify utm_agent_matrix configuration for CUSTOMER3 tenant.
Shows which agents are configured with LLM models.
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    client = create_client(url, key)
    
    # Get CUSTOMER3 tenant_id
    tenant_res = client.table("utm_tenants").select("tenant_id").eq("client_id", "CUSTOMER3").execute()
    if not tenant_res.data:
        print("❌ CUSTOMER3 tenant not found")
        return
    
    tenant_id = tenant_res.data[0]["tenant_id"]
    print(f"✅ CUSTOMER3 Tenant ID: {tenant_id}\n")
    
    # Check agent_matrix for this tenant
    print("=" * 70)
    print("AGENT MATRIX CONFIGURATION (Tenant-level)")
    print("=" * 70)
    
    matrix_res = client.table("utm_agent_matrix").select("*").eq("tenant_id", tenant_id).execute()
    
    if not matrix_res.data:
        print("⚠️  NO AGENT MATRIX ENTRIES FOUND for this tenant")
        print("   Each agent needs configuration linking it to a model.\n")
    else:
        print(f"Found {len(matrix_res.data)} agent configurations:\n")
        for entry in matrix_res.data:
            status = "✅ ACTIVE" if entry.get("is_active") else "❌ INACTIVE"
            print(f"  {status}")
            print(f"    Agent ID: {entry.get('agent_id')}")
            print(f"    Model ID: {entry.get('model_id')}")
            print(f"    Temperature: {entry.get('temperature', 'N/A')}")
            print(f"    Max Tokens: {entry.get('max_tokens', 'N/A')}")
            print()
    
    # Show available models for this tenant
    print("=" * 70)
    print("AVAILABLE MODELS (from utm_model_catalog)")
    print("=" * 70)
    
    models_res = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    if not models_res.data:
        print("⚠️  NO MODELS FOUND in utm_model_catalog for this tenant\n")
    else:
        print(f"Found {len(models_res.data)} models:\n")
        for model in models_res.data:
            status = "✅" if model.get("is_active") else "❌"
            print(f"  {status} {model.get('model_id')} (Provider: {model.get('provider_name')})")
    
    # Show available agents (global)
    print("\n" + "=" * 70)
    print("AVAILABLE AGENTS (from utm_agent_catalog - Global)")
    print("=" * 70)
    
    agents_res = client.table("utm_agent_catalog").select("*").eq("is_active", True).execute()
    
    if agents_res.data:
        print(f"Found {len(agents_res.data)} active agents:\n")
        for agent in agents_res.data:
            print(f"  • {agent.get('agent_id')} - {agent.get('display_name')}")
            print(f"    Purpose: {agent.get('purpose', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    
    if not matrix_res.data:
        print("""
You need to populate utm_agent_matrix with configurations that link:
  - agent_id (from utm_agent_catalog)
  - model_id (from utm_model_catalog) 
  - tenant_id (CUSTOMER3)
  - temperature, max_tokens (LLM parameters)

Example configuration:
  INSERT INTO utm_agent_matrix (tenant_id, agent_id, model_id, temperature, max_tokens)
  VALUES 
    ('{tenant_id}', 'agent-s', 'azure-gpt-4o', 0.7, 4000),
    ('{tenant_id}', 'agent-a', 'azure-gpt-4o', 0.5, 8000);
        """)

if __name__ == "__main__":
    main()
