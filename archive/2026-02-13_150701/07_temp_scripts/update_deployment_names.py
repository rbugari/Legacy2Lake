"""
Update deployment names in utm_model_catalog.
Use this after checking your actual deployment names in Azure Portal.
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
    print("UPDATE AZURE DEPLOYMENT NAMES")
    print("=" * 80)
    print("""
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to: Azure OpenAI → gpt4-testing-soprasteriaspain → Deployments
3. Copy the EXACT deployment names you see there
4. Update the 'deployments' dictionary below with your actual names
    """)
    
    # ⚠️ EDIT THESE VALUES TO MATCH YOUR AZURE PORTAL ⚠️
    # Replace the deployment names with the exact names from your Azure Portal
    deployments = {
        "azure-gpt-4o": "gpt-4o",          # ← Change this to your actual deployment name
        "azure-gpt-35-turbo": "gpt-35-turbo"  # ← Change this to your actual deployment name
    }
    
    print("\n📝 Current deployment mapping:")
    for model_id, deployment_name in deployments.items():
        print(f"   {model_id:25} → {deployment_name}")
    
    print("\n" + "=" * 80)
    
    # Ask for confirmation
    print("\n⚠️  This will update the database with the deployment names above.")
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("\n❌ Update cancelled")
        return
    
    print("\n📤 Updating deployment names...")
    
    for model_id, deployment_name in deployments.items():
        try:
            result = client.table("utm_model_catalog").update({
                "deployment_id": deployment_name
            }).eq("tenant_id", tenant_id).eq("model_id", model_id).execute()
            
            if result.data:
                print(f"✅ Updated {model_id} → deployment_id = '{deployment_name}'")
            else:
                print(f"⚠️  Model {model_id} not found (skipped)")
                
        except Exception as e:
            print(f"❌ Error updating {model_id}: {e}")
    
    # Verify
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    models = client.table("utm_model_catalog").select("model_id, deployment_id, api_version").eq(
        "tenant_id", tenant_id
    ).execute()
    
    print("\nUpdated model catalog:")
    for model in models.data:
        print(f"  • {model.get('model_id'):25} → {model.get('deployment_id'):20} (API: {model.get('api_version')})")
    
    print("\n✅ Update complete! Test Agent S again in the web interface.")

if __name__ == "__main__":
    main()
