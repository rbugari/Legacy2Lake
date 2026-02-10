#!/usr/bin/env python3
"""
Test de operaciones MANAGER - CUSTOMER3
Crear MANAGER y COLLABORATOR, probar APIs
"""
import asyncio
from supabase import create_client
import ssl
import httpcore
import bcrypt

# Bypass SSL certificate verification
_original_start_tls = httpcore._backends.sync.SyncStream.start_tls

def _patched_start_tls(self, *args, **kwargs):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    kwargs['ssl_context'] = ssl_context
    return _original_start_tls(self, *args, **kwargs)

httpcore._backends.sync.SyncStream.start_tls = _patched_start_tls

# Configuración de DEV
DEV_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
DEV_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

def hash_password_bcrypt(password: str) -> str:
    """Generate secure bcrypt hash."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


async def test_manager_operations():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*90)
    print("TEST: OPERACIONES MANAGER - CUSTOMER3")
    print("="*90)
    
    # 1. Obtener tenant CUSTOMER3
    print("\n📋 1. IDENTIFICAR TENANT CUSTOMER3")
    print("-" * 90)
    
    res = client.table("utm_tenants").select("*").ilike("org_name", "%customer%3%").execute()
    
    if not res.data:
        print("❌ Tenant CUSTOMER3 no encontrado")
        return
    
    tenant = res.data[0]
    tenant_id = tenant["tenant_id"]
    client_id = tenant["client_id"]
    org_name = tenant["org_name"]
    
    print(f"✅ Tenant encontrado:")
    print(f"   tenant_id: {tenant_id}")
    print(f"   client_id: {client_id}")
    print(f"   org_name: {org_name}")
    
    # 2. Obtener MANAGER actual
    print("\n👤 2. MANAGER ACTUAL DEL TENANT")
    print("-" * 90)
    
    res_manager = client.table("utm_users").select("*").eq("tenant_id", tenant_id).eq("role", "MANAGER").execute()
    
    if res_manager.data:
        current_manager = res_manager.data[0]
        print(f"✅ MANAGER actual: {current_manager['username']} ({current_manager['email']})")
        print(f"   role: {current_manager['role']}")
    else:
        print("❌ No hay MANAGER en este tenant")
        return
    
    # 3. CREAR NUEVO MANAGER (DEMO33)
    print("\n👨‍💼 3. CREAR NUEVO MANAGER: DEMO33")
    print("-" * 90)
    
    # Verificar si ya existe
    res_check = client.table("utm_users").select("*").eq("email", "rfbugari@gmail.com").execute()
    
    if res_check.data:
        print(f"⚠️  Usuario ya existe: {res_check.data[0]['username']}")
        demo33_user_id = res_check.data[0]['user_id']
    else:
        # Crear nuevo MANAGER
        new_manager = {
            "tenant_id": tenant_id,
            "email": "rfbugari@gmail.com",
            "username": "DEMO33",
            "password_hash_bcrypt": hash_password_bcrypt("demo123"),
            "role": "MANAGER",
            "is_active": True,
            "display_name": "DEMO33 Manager"
        }
        
        res_create = client.table("utm_users").insert(new_manager).execute()
        demo33_user_id = res_create.data[0]["user_id"]
        
        print(f"✅ MANAGER creado exitosamente:")
        print(f"   user_id: {demo33_user_id}")
        print(f"   username: DEMO33")
        print(f"   email: rfbugari@gmail.com")
        print(f"   password: demo123")
        print(f"   role: MANAGER")
    
    # 4. CREAR COLLABORATOR (DEMO34)
    print("\n👨‍💻 4. CREAR COLLABORATOR: DEMO34")
    print("-" * 90)
    
    # Verificar si ya existe
    res_check_collab = client.table("utm_users").select("*").eq("email", "ramirofbugari@gmail.com").execute()
    
    if res_check_collab.data:
        print(f"⚠️  Usuario ya existe: {res_check_collab.data[0]['username']}")
        demo34_user_id = res_check_collab.data[0]['user_id']
    else:
        # Crear nuevo COLLABORATOR
        new_collaborator = {
            "tenant_id": tenant_id,
            "email": "ramirofbugari@gmail.com",
            "username": "DEMO34",
            "password_hash_bcrypt": hash_password_bcrypt("demo123"),
            "role": "COLLABORATOR",
            "is_active": True,
            "display_name": "DEMO34 Collaborator"
        }
        
        res_create_collab = client.table("utm_users").insert(new_collaborator).execute()
        demo34_user_id = res_create_collab.data[0]["user_id"]
        
        print(f"✅ COLLABORATOR creado exitosamente:")
        print(f"   user_id: {demo34_user_id}")
        print(f"   username: DEMO34")
        print(f"   email: ramirofbugari@gmail.com")
        print(f"   password: demo123")
        print(f"   role: COLLABORATOR")
    
    # 5. LISTAR TODOS LOS USUARIOS DEL TENANT
    print("\n👥 5. USUARIOS DEL TENANT CUSTOMER3")
    print("-" * 90)
    
    res_all_users = client.table("utm_users").select("*").eq("tenant_id", tenant_id).execute()
    
    print(f"\nTotal usuarios: {len(res_all_users.data)}\n")
    
    for user in res_all_users.data:
        role_icon = "👑" if user["role"] == "MANAGER" else "👨‍💻" if user["role"] == "COLLABORATOR" else "👁️"
        active = "✅" if user.get("is_active", True) else "❌"
        print(f"{role_icon} {user['username']}")
        print(f"   Email: {user['email']}")
        print(f"   Role: {user['role']}")
        print(f"   Active: {active}")
        print()
    
    # 6. VERIFICAR PROVEEDORES DEL TENANT
    print("\n🔌 6. PROVEEDORES LLM DEL TENANT")
    print("-" * 90)
    
    res_providers = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
    
    if res_providers.data:
        for provider in res_providers.data:
            print(f"✅ {provider['provider_name']}")
            print(f"   Base URL: {provider.get('base_url', 'N/A')}")
            api_key = provider.get('api_key', '')
            masked = api_key[:15] + '...' if len(api_key) > 15 else api_key
            print(f"   API Key: {masked}")
            print()
    else:
        print("⚠️  No hay proveedores configurados")
    
    # 7. VERIFICAR MODELOS DEL TENANT
    print("\n📦 7. MODELOS LLM HABILITADOS")
    print("-" * 90)
    
    res_models = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    
    if res_models.data:
        for model in res_models.data:
            print(f"✅ {model['model_id']} ({model['provider']})")
            print(f"   Label: {model.get('label', 'N/A')}")
            print()
    else:
        print("⚠️  No hay modelos habilitados")
    
    # 8. SIMULAR CAMBIO DE PASSWORD (DEMO34)
    print("\n🔑 8. TEST: CAMBIO DE PASSWORD (DEMO34)")
    print("-" * 90)
    
    new_password = "newpassword456"
    new_hash = hash_password_bcrypt(new_password)
    
    client.table("utm_users").update({
        "password_hash_bcrypt": new_hash
    }).eq("user_id", demo34_user_id).execute()
    
    print(f"✅ Password actualizado para DEMO34")
    print(f"   Nueva password: {new_password}")
    
    # Revertir
    client.table("utm_users").update({
        "password_hash_bcrypt": hash_password_bcrypt("demo123")
    }).eq("user_id", demo34_user_id).execute()
    
    print(f"✅ Password revertido a: demo123")
    
    # 9. TEST: DESACTIVAR/ACTIVAR USUARIO
    print("\n🔄 9. TEST: ACTIVAR/DESACTIVAR USUARIO")
    print("-" * 90)
    
    # Desactivar
    client.table("utm_users").update({
        "is_active": False
    }).eq("user_id", demo34_user_id).execute()
    
    print(f"✅ Usuario DEMO34 desactivado")
    
    # Reactivar
    client.table("utm_users").update({
        "is_active": True
    }).eq("user_id", demo34_user_id).execute()
    
    print(f"✅ Usuario DEMO34 reactivado")
    
    # RESUMEN FINAL
    print("\n" + "="*90)
    print("✅ RESUMEN DE OPERACIONES")
    print("="*90)
    print(f"""
Tenant: {org_name} ({client_id})
Tenant ID: {tenant_id}

Usuarios creados:
├─ 👑 DEMO33 (rfbugari@gmail.com) - MANAGER
│  └─ Password: demo123
│
└─ 👨‍💻 DEMO34 (ramirofbugari@gmail.com) - COLLABORATOR
   └─ Password: demo123

Proveedores LLM: {len(res_providers.data)} configurados
Modelos habilitados: {len(res_models.data)} modelos

⚠️ PRÓXIMOS PASOS:
1. Login con DEMO33 o DEMO34 en la UI
2. DEMO33 (MANAGER) puede:
   - Configurar proveedores LLM
   - Agregar/quitar modelos
   - Crear proyectos
   - Invitar más usuarios
3. DEMO34 (COLLABORATOR) puede:
   - Ver y editar proyectos
   - Generar código
   - NO puede invitar usuarios ni configurar proveedores

🔐 CREDENCIALES:
- Username: DEMO33 o DEMO34
- Password: demo123
- Email: rfbugari@gmail.com o ramirofbugari@gmail.com
""")
    for agent in agents.data:
        print(f"   • {agent['agent_id']}: {agent['display_name']}")
    print(f"   ... (total: {len(agents.data)} agentes)")
    print("\n   ⚠️  Como MANAGER NO puedo crear nuevos agentes (solo ADMIN)")
    
    print("\n🔧 CARTUCHOS DE TECNOLOGÍA:")
    cartridges = client.table("utm_system_catalog").select("tech_id, name, type").execute()
    
    origins = [c for c in cartridges.data if c.get('type') == 'origin']
    destinations = [c for c in cartridges.data if c.get('type') == 'destination']
    
    print(f"\n   ORIGINS ({len(origins)}):")
    for tech in origins[:5]:
        print(f"   • {tech.get('tech_id', 'N/A')}: {tech['name']}")
    
    print(f"\n   DESTINATIONS ({len(destinations)}):")
    for tech in destinations[:5]:
        print(f"   • {tech.get('tech_id', 'N/A')}: {tech['name']}")
    
    print("\n   ⚠️  Como MANAGER puedo SELECCIONAR de estos cartuchos,")
    print("      pero NO puedo crear nuevos (solo ADMIN)")
    
    input("\n[Presiona ENTER para continuar...]")
    
    # 5. VER PROYECTOS DEL TENANT
    print("\n\n📋 Paso 5: PROYECTOS DEL TENANT")
    print("-" * 90)
    
    projects = client.table("utm_projects").select("*").eq("tenant_id", tenant_id).execute()
    
    if not projects.data:
        print("\n⚠️  No hay proyectos creados")
        print("   Como MANAGER, puedo crear proyectos vía UI")
    else:
        print(f"\n✅ Proyectos del tenant: {len(projects.data)}")
        for proj in projects.data[:5]:
            project_name = proj.get("name", "Unnamed")
            source_tech = proj.get("source_tech", "N/A")
            target_tech = proj.get("target_tech", "N/A")
            created_at = proj.get("created_at", "")
            
            print(f"\n   📁 {project_name}")
            print(f"      {source_tech} → {target_tech}")
            print(f"      Creado: {created_at[:10]}")
    
    input("\n[Presiona ENTER para continuar...]")
    
    # 6. VER USUARIOS DEL TENANT
    print("\n\n📋 Paso 6: USUARIOS DEL TENANT")
    print("-" * 90)
    
    users = client.table("utm_users").select("*").eq("tenant_id", tenant_id).execute()
    
    print(f"\n✅ Usuarios del tenant: {len(users.data)}")
    for user in users.data:
        username = user.get("username", "unknown")
        email = user.get("email", "N/A")
        role = user.get("role", "N/A")
        is_active = user.get("is_active", True)
        
        status = "✓" if is_active else "✗"
        emoji = "👑" if role == "MANAGER" else "👤" if role == "COLLABORATOR" else "👁️"
        
        print(f"\n   {status} {emoji} {username} ({role})")
        print(f"      Email: {email}")
    
    print("\n   ✅ Como MANAGER puedo:")
    print("      • Invitar COLLABORATOR a proyectos específicos")
    print("      • Invitar VIEWER a proyectos específicos")


if __name__ == "__main__":
    asyncio.run(test_manager_operations())

