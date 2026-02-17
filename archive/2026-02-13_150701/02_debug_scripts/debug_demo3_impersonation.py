"""
Debug impersonation vs database state for demo3/TEST1
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

print("="*80)
print("🔍 DEBUG: demo3 Impersonation vs Database Reality")
print("="*80)

# 1. Find ALL users with "demo3" in username/email
print("\n1️⃣  Buscando TODOS los usuarios con 'demo3'...")
demo3_users = client.table("utm_users").select("user_id, username, email, tenant_id, role").or_("username.ilike.%demo3%,email.ilike.%demo3%").execute()

print(f"   Encontrados: {len(demo3_users.data)} usuario(s)")
for u in demo3_users.data:
    print(f"\n   👤 {u.get('username')} ({u.get('email')})")
    print(f"      User ID: {u.get('user_id')}")
    print(f"      Tenant ID: {u.get('tenant_id')}")
    print(f"      Role: {u.get('role')}")

# 2. Find ALL projects named "TEST1" (sin filtrar por tenant)
print("\n2️⃣  Buscando TODOS los proyectos llamados 'TEST1'...")
test1_projects = client.table("utm_projects").select("project_id, name, tenant_id, stage, status, settings, created_at").eq("name", "TEST1").execute()

print(f"   Encontrados: {len(test1_projects.data)} proyecto(s)")
for p in test1_projects.data:
    print(f"\n   📁 TEST1")
    print(f"      Project ID: {p.get('project_id')}")
    print(f"      Tenant ID: {p.get('tenant_id')}")
    print(f"      Stage: {p.get('stage')}")
    print(f"      Status: {p.get('status')}")
    print(f"      Created: {p.get('created_at')}")
    
    settings = p.get('settings', {})
    if isinstance(settings, dict):
        print(f"      Source: {settings.get('source_tech', 'N/A')}")
        print(f"      Target: {settings.get('target_tech', 'N/A')}")
    
    # Find which user owns this tenant
    tenant_info = client.table("utm_users").select("username, email").eq("tenant_id", p.get('tenant_id')).limit(1).execute()
    if tenant_info.data:
        print(f"      Tenant Owner: {tenant_info.data[0].get('username')} ({tenant_info.data[0].get('email')})")

# 3. Cross-reference: Which tenants do demo3 users belong to?
print("\n3️⃣  Proyectos por cada tenant de 'demo3'...")
for u in demo3_users.data:
    tid = u.get('tenant_id')
    username = u.get('username')
    
    projects = client.table("utm_projects").select("name, stage, status").eq("tenant_id", tid).execute()
    
    print(f"\n   👤 {username} (Tenant: {tid})")
    print(f"      Proyectos: {len(projects.data)}")
    for p in projects.data:
        print(f"         - {p.get('name')} (Stage: {p.get('stage')}, Status: {p.get('status')})")

# 4. Check if there's a tenant record confusion
print("\n4️⃣  Verificando tabla utm_tenants...")
tenants_with_demo3 = client.table("utm_tenants").select("tenant_id, client_id, tier").execute()

demo3_tenant_ids = set(u.get('tenant_id') for u in demo3_users.data)
print(f"   Tenant IDs asociados a usuarios 'demo3': {demo3_tenant_ids}")

for tid in demo3_tenant_ids:
    tenant_record = client.table("utm_tenants").select("*").eq("tenant_id", tid).execute()
    if tenant_record.data:
        t = tenant_record.data[0]
        print(f"\n   🏢 Tenant {tid}")
        print(f"      Client ID: {t.get('client_id')}")
        print(f"      Tier: {t.get('tier')}")
        
        # Count users and projects
        user_count = client.table("utm_users").select("user_id", count="exact").eq("tenant_id", tid).execute()
        proj_count = client.table("utm_projects").select("project_id", count="exact").eq("tenant_id", tid).execute()
        
        print(f"      Users: {user_count.count}")
        print(f"      Projects: {proj_count.count}")

print("\n" + "="*80)
print("🎯 CONCLUSIÓN")
print("="*80)

if len(demo3_users.data) > 1:
    print("⚠️  HAY MÚLTIPLES USUARIOS CON 'demo3' - Posible confusión de impersonación")
elif len(demo3_users.data) == 1 and len(test1_projects.data) == 0:
    print("❌ Usuario demo3 existe pero NO hay proyecto TEST1 en su tenant")
    print("   → La UI muestra datos incorrectos o impersonación está rota")
elif len(demo3_users.data) == 1 and len(test1_projects.data) == 1:
    if test1_projects.data[0].get('tenant_id') == demo3_users.data[0].get('tenant_id'):
        print("✅ TEST1 pertenece al tenant correcto de demo3")
    else:
        print("⚠️  TEST1 existe pero pertenece a OTRO tenant (problema de impersonación)")
else:
    print("❓ Situación inesperada - revisar datos manualmente")

print("\n💡 RECOMENDACIÓN:")
print("   Ver logs de impersonación en la API para verificar qué tenant_id se está usando")
