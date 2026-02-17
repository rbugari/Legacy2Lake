"""
Verify Azure OpenAI configuration for CUSTOMER3.
Shows provider vault credentials and model catalog entries.
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
    
    # Check Provider Vault
    print("=" * 70)
    print("PROVIDER VAULT (utm_provider_vault)")
    print("=" * 70)
    
    vault_res = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
    
    if not vault_res.data:
        print("⚠️  No providers configured\n")
    else:
        for provider in vault_res.data:
            status = "✅ ACTIVE" if provider.get("is_active") else "❌ INACTIVE"
            print(f"\n{status} Provider: {provider.get('provider_name')}")
            print(f"  Base URL: {provider.get('base_url', 'N/A')}")
            print(f"  API Key: {'*' * 20}{provider.get('api_key', '')[-8:] if provider.get('api_key') else 'NOT SET'}")
            print(f"  Model Name: {provider.get('model_name', 'N/A')}")
            
            # Check if base_url looks correct
            base_url = provider.get('base_url', '')
            if base_url and 'openai.azure.com' in base_url:
                # Extract deployment name from URL pattern
                # Azure URL: https://{resource}.openai.azure.com/openai/deployments/{deployment-name}/...
                if '/deployments/' in base_url:
                    parts = base_url.split('/deployments/')
                    if len(parts) > 1:
                        deployment = parts[1].split('/')[0]
                        print(f"  🔍 Deployment Name in URL: {deployment}")
    
    # Check Model Catalog
    print("\n" + "=" * 70)
    print("MODEL CATALOG (utm_model_catalog)")
    print("=" * 70)
    
    models_res = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    if not models_res.data:
        print("⚠️  No models configured\n")
    else:
        print(f"\nFound {len(models_res.data)} models:\n")
        for model in models_res.data:
            status = "✅" if model.get("is_active") else "❌"
            print(f"{status} Model ID: {model.get('model_id')}")
            print(f"   Provider: {model.get('provider_name', 'N/A')}")
            print(f"   Context Window: {model.get('context_window', 'N/A')}")
            print()
    
    # Check Agent Matrix
    print("=" * 70)
    print("AGENT MATRIX (utm_agent_matrix)")
    print("=" * 70)
    
    matrix_res = client.table("utm_agent_matrix").select("*").eq("tenant_id", tenant_id).eq("is_active", True).execute()
    
    print(f"\nActive configurations: {len(matrix_res.data)}")
    for entry in matrix_res.data:
        print(f"  • {entry.get('agent_id')} → {entry.get('model_id')} (provider: {entry.get('provider')})")
    
    # Diagnosis
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    
    if vault_res.data:
        azure_provider = [p for p in vault_res.data if p.get('provider_name') == 'azure']
        if azure_provider:
            base_url = azure_provider[0].get('base_url', '')
            print(f"""
The error 'DeploymentNotFound' means the deployment name in the Azure URL 
doesn't exist in your Azure OpenAI resource.

Current base_url: {base_url}

Azure OpenAI URL format:
  https://YOUR-RESOURCE.openai.azure.com/openai/deployments/DEPLOYMENT-NAME/chat/completions?api-version=2024-02-15-preview

The DEPLOYMENT-NAME must match exactly what you created in Azure Portal.

Common deployment names:
  - gpt-4o
  - gpt-4
  - gpt-35-turbo
  - gpt-4-turbo

Check your Azure Portal → Azure OpenAI → Deployments to see the exact name.
            """)

if __name__ == "__main__":
    main()
