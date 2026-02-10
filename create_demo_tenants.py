"""
Script para crear tenants DEMO de prueba con usuarios MANAGER
"""
from connect_supabase_dev import get_postgres_connection
import bcrypt
import uuid
from datetime import datetime

def main():
    print("="*60)
    print("CREAR TENANTS DEMO DE PRUEBA")
    print("="*60)
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # Definir tenants DEMO a crear
    demo_tenants = [
        {
            'client_id': 'DEMO1',
            'org_name': 'Demo Organization 1',
            'tier': 'STANDARD'
        },
        {
            'client_id': 'DEMO2',
            'org_name': 'Demo Organization 2',
            'tier': 'PREMIUM'
        },
        {
            'client_id': 'DEMO3',
            'org_name': 'Demo Organization 3',
            'tier': 'STANDARD'
        }
    ]
    
    print(f"\nCreando {len(demo_tenants)} tenants DEMO...\n")
    
    created_users = []
    
    for tenant_data in demo_tenants:
        # Generar UUID para tenant
        tenant_id = str(uuid.uuid4())  # Convertir a string para psycopg2
        client_id = tenant_data['client_id']
        org_name = tenant_data['org_name']
        tier = tenant_data['tier']
        
        # 1. Crear tenant
        print(f"📦 {client_id}:")
        cursor.execute("""
            INSERT INTO utm_tenants (tenant_id, client_id, org_name, tier, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (client_id) DO UPDATE SET
                org_name = EXCLUDED.org_name,
                tier = EXCLUDED.tier
            RETURNING tenant_id;
        """, (tenant_id, client_id, org_name, tier, True, datetime.now()))
        
        tenant_id = cursor.fetchone()[0]
        print(f"   ✅ Tenant creado: {tenant_id}")
        
        # 2. Crear usuario MANAGER (primer usuario del tenant)
        username = client_id.lower()
        email = f"{username}@demo.local"
        password = "demo123"  # Password por defecto
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO utm_users (
                user_id,
                tenant_id,
                email,
                username,
                password_hash_bcrypt,
                role,
                is_active,
                display_name,
                created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id) DO UPDATE SET
                email = EXCLUDED.email,
                role = 'MANAGER',
                updated_at = NOW()
            RETURNING user_id;
        """, (
            tenant_id,  # ⚠️ user_id = tenant_id (backward compatibility!)
            tenant_id,
            email,
            username,
            password_hash,
            'MANAGER',
            True,
            f"Manager {org_name}",
            datetime.now()
        ))
        
        user_id = cursor.fetchone()[0]
        print(f"   ✅ Usuario MANAGER creado")
        print(f"      Email: {email}")
        print(f"      Password: {password}")
        print(f"      Tier: {tier}")
        print()
        
        created_users.append({
            'client_id': client_id,
            'email': email,
            'password': password,
            'tier': tier
        })
    
    # Commit
    conn.commit()
    
    # Verificación
    print("="*60)
    print("VERIFICACIÓN")
    print("="*60)
    
    cursor.execute("""
        SELECT 
            t.client_id,
            t.org_name,
            t.tier,
            u.email,
            u.username,
            u.role,
            (t.tenant_id = u.user_id) AS backward_compatible
        FROM utm_tenants t
        JOIN utm_users u ON u.tenant_id = t.tenant_id
        ORDER BY t.created_at;
    """)
    
    results = cursor.fetchall()
    print(f"\n✅ {len(results)} usuarios creados exitosamente\n")
    print("   " + "-"*75)
    print(f"   {'Cliente':<10} {'Email':<25} {'Role':<10} {'Tier':<10} {'BC'}")
    print("   " + "-"*75)
    
    for client_id, org_name, tier, email, username, role, backward_compat in results:
        bc = "✅" if backward_compat else "❌"
        print(f"   {client_id:<10} {email:<25} {role:<10} {tier:<10} {bc}")
    
    cursor.close()
    conn.close()
    
    # Resumen con credenciales
    print("\n" + "="*60)
    print("CREDENCIALES DE ACCESO")
    print("="*60)
    
    for user in created_users:
        print(f"\n{user['client_id']} ({user['tier']}):")
        print(f"  Email:    {user['email']}")
        print(f"  Password: {user['password']}")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETADO")
    print("="*60)
    print("\nPróximos pasos:")
    print("1. Usar estas credenciales para login en el frontend")
    print("2. Crear proyecto de prueba")
    print("3. Testear invitación de usuarios adicionales")
    print("4. Verificar permisos por rol (crear COLLABORATORs y VIEWERs)")

if __name__ == "__main__":
    main()
