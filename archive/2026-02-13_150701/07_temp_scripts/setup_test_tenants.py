"""
Multi-Tenant Test Environment Setup
Creates 3 test tenants for isolation and security testing
"""
import os
import uuid
from supabase import create_client, Client
from datetime import datetime

# Configuration
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

# Test Tenants Configuration
TEST_TENANTS = [
    {
        "tenant_id": "aaaaaaaa-1111-4111-8111-111111111111",  # UUID format for Alpha
        "name": "Alpha Testing Corp",
        "subdomain": "alpha-test",
        "plan": "ENTERPRISE",  # Valid tier: STANDARD, PREMIUM, ENTERPRISE
        "max_users": 50,
        "max_projects": 10,
        "features": ["agent_c", "agent_f", "agent_g", "orchestration"],
    },
    {
        "tenant_id": "bbbbbbbb-2222-4222-8222-222222222222",  # UUID format for Beta
        "name": "Beta Testing Inc",
        "subdomain": "beta-test",
        "plan": "PREMIUM",  # Valid tier: STANDARD, PREMIUM, ENTERPRISE
        "max_users": 20,
        "max_projects": 5,
        "features": ["agent_c", "agent_f"],
    },
    {
        "tenant_id": "cccccccc-3333-4333-8333-333333333333",  # UUID format for Gamma
        "name": "Gamma Testing LLC",
        "subdomain": "gamma-test",
        "plan": "STANDARD",  # Valid tier: STANDARD, PREMIUM, ENTERPRISE
        "max_users": 5,
        "max_projects": 2,
        "features": ["agent_c"],
    }
]

def setup_supabase():
    """Initialize Supabase client"""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return client

def create_tenant(client: Client, tenant_config: dict) -> bool:
    """Create a tenant in utm_tenants table"""
    try:
        # Check if tenant already exists
        existing = client.table("utm_tenants").select("*").eq("tenant_id", tenant_config["tenant_id"]).execute()
        
        if existing.data:
            print(f"   ⚠️  Tenant {tenant_config['tenant_id']} already exists, skipping...")
            return True
        
        # Create tenant record
        tenant_data = {
            "tenant_id": tenant_config["tenant_id"],
            "display_name": tenant_config["name"],
            "tier": tenant_config["plan"],
            "is_active": True,
            "org_logo_url": None,
            "suspended_at": None,
            "suspension_reason": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = client.table("utm_tenants").insert(tenant_data).execute()
        
        if result.data:
            print(f"   ✅ Tenant {tenant_config['tenant_id']} created successfully")
            return True
        else:
            print(f"   ❌ Failed to create tenant {tenant_config['tenant_id']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error creating tenant {tenant_config['tenant_id']}: {e}")
        return False

def create_test_user(client: Client, tenant_id: str, username: str) -> dict:
    """Create a test user for a tenant"""
    try:
        user_id = f"{tenant_id}-user-{username}"
        
        # Check if user exists
        existing = client.table("utm_users").select("*").eq("user_id", user_id).execute()
        
        if existing.data:
            print(f"      User {username} already exists")
            return existing.data[0]
        
        user_data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": f"{username}@{tenant_id}.test",
            "full_name": f"{username.title()} User",
            "role": "admin" if username == "admin" else "developer",
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = client.table("utm_users").insert(user_data).execute()
        
        if result.data:
            print(f"      ✅ User {username} created")
            return result.data[0]
        else:
            print(f"      ❌ Failed to create user {username}")
            return None
            
    except Exception as e:
        print(f"      ❌ Error creating user {username}: {e}")
        return None

def create_test_project(client: Client, tenant_id: str, project_name: str, user_id: str) -> dict:
    """Create a test project for a tenant"""
    try:
        project_id = f"{tenant_id}-project-{project_name}"
        
        # Check if project exists
        existing = client.table("utm_projects").select("*").eq("project_id", project_id).execute()
        
        if existing.data:
            print(f"      Project {project_name} already exists")
            return existing.data[0]
        
        project_data = {
            "project_id": project_id,
            "project_uuid": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": f"{project_name.title()} Project",
            "description": f"Test project for {tenant_id} isolation testing",
            "source_tech": "mssql",
            "target_tech": "pyspark",
            "status": "active",
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = client.table("utm_projects").insert(project_data).execute()
        
        if result.data:
            print(f"      ✅ Project {project_name} created")
            return result.data[0]
        else:
            print(f"      ❌ Failed to create project {project_name}")
            return None
            
    except Exception as e:
        print(f"      ❌ Error creating project {project_name}: {e}")
        return None

def create_test_prompt(client: Client, tenant_id: str, prompt_id: str) -> bool:
    """Create a test prompt for a tenant"""
    try:
        # Check if prompt exists
        existing = client.table("utm_prompts").select("*").eq("tenant_id", tenant_id).eq("prompt_id", prompt_id).execute()
        
        if existing.data:
            return True
        
        prompt_data = {
            "tenant_id": tenant_id,
            "prompt_id": prompt_id,
            "content": f"# Test Prompt for {tenant_id}\n\nThis is a test prompt for multi-tenant isolation testing.\n\nTenant: {tenant_id}\nPrompt ID: {prompt_id}",
            "version": "1.0.0",
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = client.table("utm_prompts").insert(prompt_data).execute()
        return bool(result.data)
        
    except Exception as e:
        print(f"      ❌ Error creating prompt {prompt_id}: {e}")
        return False

def setup_test_environment():
    """Setup complete multi-tenant test environment"""
    print("\n" + "="*80)
    print("🧪 MULTI-TENANT TEST ENVIRONMENT SETUP")
    print("="*80)
    
    client = setup_supabase()
    
    results = {
        "tenants_created": 0,
        "users_created": 0,
        "projects_created": 0,
        "prompts_created": 0
    }
    
    for tenant_config in TEST_TENANTS:
        tenant_id = tenant_config["tenant_id"]
        print(f"\n📦 Setting up tenant: {tenant_id}")
        print(f"   Name: {tenant_config['name']}")
        print(f"   Plan: {tenant_config['plan']}")
        
        # 1. Create tenant
        if create_tenant(client, tenant_config):
            results["tenants_created"] += 1
            
            # 2. Create test users
            print(f"\n   👥 Creating users for {tenant_id}:")
            admin_user = create_test_user(client, tenant_id, "admin")
            if admin_user:
                results["users_created"] += 1
            
            dev_user = create_test_user(client, tenant_id, "developer")
            if dev_user:
                results["users_created"] += 1
            
            # 3. Create test projects
            if admin_user:
                print(f"\n   📊 Creating projects for {tenant_id}:")
                project1 = create_test_project(client, tenant_id, "project1", admin_user["user_id"])
                if project1:
                    results["projects_created"] += 1
                
                project2 = create_test_project(client, tenant_id, "project2", admin_user["user_id"])
                if project2:
                    results["projects_created"] += 1
            
            # 4. Create test prompts
            print(f"\n   📝 Creating prompts for {tenant_id}:")
            for prompt_id in ["agent_c_interpreter", "cartridge_pyspark_bronze", "test_prompt_isolation"]:
                if create_test_prompt(client, tenant_id, prompt_id):
                    results["prompts_created"] += 1
                    print(f"      ✅ Prompt {prompt_id} created")
    
    print("\n" + "="*80)
    print("📊 SETUP SUMMARY")
    print("="*80)
    print(f"✅ Tenants created: {results['tenants_created']}/{len(TEST_TENANTS)}")
    print(f"✅ Users created: {results['users_created']}/{len(TEST_TENANTS) * 2}")
    print(f"✅ Projects created: {results['projects_created']}/{len(TEST_TENANTS) * 2}")
    print(f"✅ Prompts created: {results['prompts_created']}/{len(TEST_TENANTS) * 3}")
    
    print("\n📋 Test Tenant Credentials:")
    for tenant in TEST_TENANTS:
        print(f"\n{tenant['name']}:")
        print(f"  Tenant ID: {tenant['tenant_id']}")
        print(f"  Admin User: admin@{tenant['tenant_id']}.test")
        print(f"  Dev User: developer@{tenant['tenant_id']}.test")
        print(f"  Plan: {tenant['plan']}")
        print(f"  Features: {', '.join(tenant['features'])}")
    
    return results

if __name__ == "__main__":
    try:
        results = setup_test_environment()
        
        if results["tenants_created"] == len(TEST_TENANTS):
            print("\n🎉 Multi-tenant test environment setup COMPLETE!")
            exit(0)
        else:
            print("\n⚠️  Setup completed with warnings. Check output above.")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
