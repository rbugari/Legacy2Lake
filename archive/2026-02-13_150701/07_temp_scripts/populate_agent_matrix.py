"""
Populate utm_agent_matrix for CUSTOMER3 tenant.
Links each agent with appropriate model and LLM parameters.
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
    
    # Agent Matrix Configuration
    # Links each agent to a model from utm_model_catalog
    agent_configs = [
        {
            "agent_id": "agent-s",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Technology Scout - Identifies source/target technologies"
        },
        {
            "agent_id": "agent-a",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Discovery Agent - Analyzes codebase structure"
        },
        {
            "agent_id": "agent-c",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Code Generator - Creates migration code"
        },
        {
            "agent_id": "agent-b",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Cartographer - Maps data flows and dependencies"
        },
        {
            "agent_id": "agent-p",
            "model_id": "azure-gpt-35-turbo",
            "provider": "azure",
            "description": "Profiling Agent - Analyzes data patterns"
        },
        {
            "agent_id": "agent-r",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Refactoring Agent - Modernizes code"
        },
        {
            "agent_id": "agent-o",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Operations Auditor - Reviews operational aspects"
        },
        {
            "agent_id": "agent-f",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Compliance Auditor - Checks regulatory compliance"
        },
        {
            "agent_id": "agent-g",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Governance Agent - Reviews governance policies"
        },
        {
            "agent_id": "agent-d",
            "model_id": "azure-gpt-4o",
            "provider": "azure",
            "description": "Architectural Auditor - Evaluates architecture quality"
        }
    ]
    
    print("=" * 70)
    print("POPULATING AGENT MATRIX")
    print("=" * 70)
    
    inserted_count = 0
    for config in agent_configs:
        data = {
            "tenant_id": tenant_id,
            "agent_id": config["agent_id"],
            "model_id": config["model_id"],
            "provider": config["provider"],
            "is_active": True
        }
        
        try:
            # Check if already exists
            existing = client.table("utm_agent_matrix").select("*").eq(
                "tenant_id", tenant_id
            ).eq("agent_id", config["agent_id"]).execute()
            
            if existing.data:
                print(f"⏭️  {config['agent_id']:15} - Already configured, skipping")
            else:
                client.table("utm_agent_matrix").insert(data).execute()
                print(f"✅ {config['agent_id']:15} → {config['model_id']:20} (provider={config['provider']})")
                print(f"   {config['description']}")
                inserted_count += 1
                
        except Exception as e:
            print(f"❌ {config['agent_id']:15} - Error: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ Configuration complete! Inserted {inserted_count} new agent configs")
    print("=" * 70)
    
    # Verify
    print("\nVerifying configuration...")
    matrix_res = client.table("utm_agent_matrix").select("agent_id, model_id, is_active").eq(
        "tenant_id", tenant_id
    ).eq("is_active", True).execute()
    
    print(f"\nActive agent configurations: {len(matrix_res.data)}")
    for entry in matrix_res.data:
        print(f"  ✅ {entry['agent_id']} → {entry['model_id']}")

if __name__ == "__main__":
    main()
