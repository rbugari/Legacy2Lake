"""
Update deployment_id to match actual Azure deployment: gpt-4.1
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
    print("UPDATING TO ACTUAL AZURE DEPLOYMENT")
    print("=" * 80)
    print("""
Based on your .env configuration:
  - AZURE_OPENAI_DEPLOYMENT_ID="gpt-4.1"
  - AZURE_OPENAI_API_VERSION="2025-01-01-preview"

All models will use the same deployment since you have only one.
    """)
    
    # Update all Azure models to use the actual deployment
    updates = [
        {
            "model_id": "azure-gpt-4o",
            "deployment_id": "gpt-4.1",
            "api_version": "2025-01-01-preview"
        },
        {
            "model_id": "azure-gpt-35-turbo",
            "deployment_id": "gpt-4.1",
            "api_version": "2025-01-01-preview"
        },
        {
            "model_id": "gpt-4.1",
            "deployment_id": "gpt-4.1",
            "api_version": "2025-01-01-preview"
        }
    ]
    
    print("\n📤 Applying updates...\n")
    
    for update in updates:
        try:
            result = client.table("utm_model_catalog").update({
                "deployment_id": update["deployment_id"],
                "api_version": update["api_version"]
            }).eq("tenant_id", tenant_id).eq("model_id", update["model_id"]).execute()
            
            if result.data:
                print(f"✅ {update['model_id']:25} → deployment_id='{update['deployment_id']}', api_version='{update['api_version']}'")
            else:
                print(f"⚠️  {update['model_id']:25} not found (skipped)")
                
        except Exception as e:
            print(f"❌ Error updating {update['model_id']}: {e}")
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    models = client.table("utm_model_catalog").select(
        "model_id, deployment_id, api_version, provider"
    ).eq("tenant_id", tenant_id).execute()
    
    print("\n✅ Updated model catalog:")
    for model in models.data:
        print(f"  • {model.get('model_id'):25} → deployment: {model.get('deployment_id'):15} | API: {model.get('api_version')}")
    
    print("\n" + "=" * 80)
    print("✅ Configuration complete!")
    print("=" * 80)
    print("""
All models now point to your actual Azure deployment 'gpt-4.1'.

Test Agent S again in the web interface.
The 404 DeploymentNotFound error should be resolved.
    """)

if __name__ == "__main__":
    main()
