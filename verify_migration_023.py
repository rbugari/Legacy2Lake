"""
Verify migration 023 was applied successfully.
Shows complete Azure OpenAI configuration.
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
    
    print("=" * 80)
    print("COMPLETE AZURE OPENAI CONFIGURATION")
    print("=" * 80)
    
    # 1. Provider Vault
    print("\n1️⃣  PROVIDER VAULT (utm_provider_vault)")
    print("-" * 80)
    vault_res = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
    
    if vault_res.data:
        for provider in vault_res.data:
            status = "✅" if provider.get("is_active") else "❌"
            print(f"\n{status} Provider: {provider.get('provider_name')}")
            print(f"   Base URL: {provider.get('base_url')}")
            print(f"   API Key: {'*' * 20}{provider.get('api_key', '')[-8:] if provider.get('api_key') else 'NOT SET'}")
    else:
        print("⚠️  No providers configured")
    
    # 2. Model Catalog
    print("\n\n2️⃣  MODEL CATALOG (utm_model_catalog)")
    print("-" * 80)
    models_res = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    if models_res.data:
        for model in models_res.data:
            status = "✅" if model.get("is_active", True) else "❌"
            print(f"\n{status} Model: {model.get('model_id')}")
            print(f"   Provider: {model.get('provider', 'NOT SET')}")
            print(f"   Deployment ID: {model.get('deployment_id', 'NOT SET')} ⚠️" if not model.get('deployment_id') else f"   Deployment ID: {model.get('deployment_id')} ✅")
            print(f"   API Version: {model.get('api_version', 'NOT SET')}")
            print(f"   Context Window: {model.get('context_window', 'N/A')}")
    else:
        print("⚠️  No models configured")
    
    # 3. Agent Matrix
    print("\n\n3️⃣  AGENT MATRIX (utm_agent_matrix)")
    print("-" * 80)
    matrix_res = client.table("utm_agent_matrix").select("*").eq("tenant_id", tenant_id).eq("is_active", True).execute()
    
    if matrix_res.data:
        print(f"\nActive configurations: {len(matrix_res.data)}")
        for entry in matrix_res.data:
            print(f"  • {entry.get('agent_id'):15} → {entry.get('model_id'):20} (provider: {entry.get('provider')})")
    else:
        print("⚠️  No agent configurations")
    
    # 4. Configuration Test
    print("\n\n4️⃣  CONFIGURATION TEST")
    print("-" * 80)
    
    issues = []
    
    # Check if models have deployment_id
    models_without_deployment = [m for m in models_res.data if not m.get('deployment_id')]
    if models_without_deployment:
        issues.append(f"❌ {len(models_without_deployment)} model(s) missing deployment_id")
        for m in models_without_deployment:
            print(f"   ⚠️  {m.get('model_id')} needs deployment_id")
    
    # Check if models have api_version
    models_without_version = [m for m in models_res.data if not m.get('api_version')]
    if models_without_version:
        issues.append(f"❌ {len(models_without_version)} model(s) missing api_version")
    
    # Check if provider has base_url
    if vault_res.data:
        providers_without_url = [p for p in vault_res.data if not p.get('base_url')]
        if providers_without_url:
            issues.append(f"❌ {len(providers_without_url)} provider(s) missing base_url")
    
    if not issues:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nYour configuration is ready. Try Agent S again in the web interface.")
    else:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        
        print("\n📋 NEXT STEPS:")
        if models_without_deployment:
            print("\n   To fix deployment_id, run:")
            print("   UPDATE utm_model_catalog")
            print("   SET deployment_id = 'your-deployment-name'")
            print(f"   WHERE model_id = 'azure-gpt-4o' AND tenant_id = '{tenant_id}';")
            print("\n   Get the exact deployment name from:")
            print("   Azure Portal → Azure OpenAI → Your Resource → Deployments")
    
    # 5. Full Connection String Test
    print("\n\n5️⃣  AZURE CONNECTION TEST")
    print("-" * 80)
    
    if vault_res.data and models_res.data:
        azure_provider = next((p for p in vault_res.data if 'azure' in p.get('provider_name', '').lower()), None)
        azure_model = next((m for m in models_res.data if m.get('provider') == 'azure' and m.get('deployment_id')), None)
        
        if azure_provider and azure_model:
            base_url = azure_provider.get('base_url', '')
            deployment = azure_model.get('deployment_id')
            api_version = azure_model.get('api_version')
            
            # Construct full URL
            if base_url:
                if not base_url.endswith('/'):
                    base_url += '/'
                full_url = f"{base_url}openai/deployments/{deployment}/chat/completions?api-version={api_version}"
                
                print(f"\nFull Azure OpenAI URL that will be used:")
                print(f"   {full_url}")
                
                # Extract resource name
                if 'openai.azure.com' in base_url:
                    resource = base_url.split('//')[1].split('.')[0]
                    print(f"\n   Resource Name: {resource}")
                    print(f"   Deployment: {deployment}")
                    print(f"   API Version: {api_version}")
                    
                    print("\n   ⚠️  Verify this matches your Azure Portal:")
                    print(f"      https://portal.azure.com → Azure OpenAI → {resource} → Deployments")
                    print(f"      Make sure deployment '{deployment}' exists and is deployed")

if __name__ == "__main__":
    main()
