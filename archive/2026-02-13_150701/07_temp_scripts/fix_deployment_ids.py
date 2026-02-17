"""
Update deployment_id in utm_model_catalog for CUSTOMER3.
The deployment_id must match the exact deployment name in Azure OpenAI.
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
    
    print("=" * 70)
    print("CURRENT MODEL CATALOG")
    print("=" * 70)
    
    models = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    if not models.data:
        print("⚠️  No models found")
        return
    
    print("\nCurrent configuration:")
    for model in models.data:
        print(f"\n  Model ID: {model.get('model_id')}")
        print(f"  Deployment ID: {model.get('deployment_id', 'NOT SET')}")
        print(f"  Provider: {model.get('provider_name', 'N/A')}")
        print(f"  API Version: {model.get('api_version', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDED DEPLOYMENT NAMES")
    print("=" * 70)
    print("""
Based on common Azure OpenAI deployment naming conventions:

1. If your Azure deployment is named "gpt-4o":
   - Update azure-gpt-4o → deployment_id = "gpt-4o"
   
2. If your Azure deployment is named "gpt-35-turbo":
   - Update azure-gpt-35-turbo → deployment_id = "gpt-35-turbo"
   
3. Check your Azure Portal:
   Azure OpenAI → Your Resource → Deployments
   Copy the exact "Deployment name" shown there.

Common patterns:
  - gpt-4o (most common)
  - gpt4o (no dashes)
  - gpt-4 (older)
  - gpt-35-turbo or gpt-3.5-turbo
    """)
    
    print("\n" + "=" * 70)
    print("UPDATE DEPLOYMENTS")
    print("=" * 70)
    
    # Proposed updates based on common patterns
    # Note: Currently only updating 'provider' field since deployment_id doesn't exist yet
    updates = [
        {
            "model_id": "azure-gpt-4o",
            "provider": "azure"
        },
        {
            "model_id": "azure-gpt-35-turbo",
            "provider": "azure"
        }
    ]
    
    print("\nApplying basic provider updates...")
    print("(deployment_id column will be added via migration)\n")
    
    for update in updates:
        try:
            result = client.table("utm_model_catalog").update({
                "provider": update["provider"]
            }).eq("tenant_id", tenant_id).eq("model_id", update["model_id"]).execute()
            
            if result.data:
                print(f"✅ Updated {update['model_id']}")
                print(f"   provider = '{update['provider']}'")
            else:
                print(f"⚠️  No rows updated for {update['model_id']} (might not exist)")
                
        except Exception as e:
            print(f"❌ Error updating {update['model_id']}: {e}")
    
    # Verify
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    models_after = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    print("\nUpdated configuration:")
    for model in models_after.data:
        print(f"\n  ✅ {model.get('model_id')}")
        print(f"     Provider: {model.get('provider')}")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("""
1. Verify the deployment names match your Azure Portal
2. If not, manually update utm_model_catalog with correct deployment_id
3. Test Agent S again in the web interface
4. If still getting 404, check:
   - API key is valid
   - Deployment is deployed (not just created)
   - Base URL includes correct resource name
    """)

if __name__ == "__main__":
    main()
