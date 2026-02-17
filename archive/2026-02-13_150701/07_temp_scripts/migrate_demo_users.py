"""
Script para migrar usuarios DEMO como administradores de sus tenants
Crea registros en utm_users para cada tenant DEMO existente
"""
from connect_supabase_dev import get_postgres_connection
import bcrypt

def main():
    print("="*60)
    print("MIGRACIÓN USUARIOS DEMO → ADMINS")
    print("="*60)
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # 1. Verificar estructura actual de utm_tenants_old (backup)
    print("\n1. Verificando datos de tenants antiguos...")
    cursor.execute("""
        SELECT tenant_id, client_id, created_at
        FROM utm_tenants_old
        WHERE client_id LIKE 'DEMO%' OR client_id LIKE 'demo%'
        ORDER BY created_at;
    """)
    
    old_tenants = cursor.fetchall()
    print(f"   Encontrados: {len(old_tenants)} tenants DEMO en utm_tenants_old")
    
    if len(old_tenants) == 0:
        print("\n⚠️  No hay tenants DEMO en utm_tenants_old")
        print("   Verificando utm_tenants nuevo...")
        
        cursor.execute("""
            SELECT tenant_id, client_id, org_name, created_at
            FROM utm_tenants
            WHERE client_id LIKE 'DEMO%' OR client_id LIKE 'demo%'
            ORDER BY created_at;
        """)
        new_tenants = cursor.fetchall()
        print(f"   Encontrados: {len(new_tenants)} tenants DEMO en utm_tenants")
        
        if len(new_tenants) == 0:
            print("\n❌ No hay tenants DEMO para migrar")
            cursor.close()
            conn.close()
            return
        
        # Si hay tenants en la nueva tabla, migrar desde ahí
        print("\n2. Creando usuarios ADMIN desde utm_tenants...")
        for tenant_id, client_id, org_name, created_at in new_tenants:
            create_user_from_new_tenant(cursor, tenant_id, client_id, org_name, created_at)
    else:
        # Migrar desde utm_tenants_old
        print("\n2. Restaurando tenants a utm_tenants...")
        cursor.execute("""
            INSERT INTO utm_tenants (tenant_id, client_id, org_name, is_active, created_at)
            SELECT 
                tenant_id,
                client_id,
                COALESCE(client_id, 'Organization') AS org_name,
                COALESCE(is_active, TRUE),
                created_at
            FROM utm_tenants_old
            WHERE client_id LIKE 'DEMO%' OR client_id LIKE 'demo%'
            ON CONFLICT (tenant_id) DO NOTHING;
        """)
        
        inserted = cursor.rowcount
        print(f"   {inserted} tenants insertados/actualizados")
        
        print("\n3. Creando usuarios ADMIN desde utm_tenants_old...")
        for tenant_id, client_id, created_at in old_tenants:
            create_user_from_old_tenant(cursor, tenant_id, client_id, created_at)
    
    # Commit cambios
    conn.commit()
    
    # 4. Verificar resultados
    print("\n4. Verificación final...")
    cursor.execute("""
        SELECT 
            t.client_id,
            t.org_name,
            u.user_id,
            u.email,
            u.username,
            u.role,
            (t.tenant_id = u.user_id) AS backward_compatible
        FROM utm_tenants t
        JOIN utm_users u ON u.tenant_id = t.tenant_id
        WHERE t.client_id LIKE 'DEMO%' OR t.client_id LIKE 'demo%'
        ORDER BY t.created_at;
    """)
    
    results = cursor.fetchall()
    print(f"\n   Usuarios DEMO creados: {len(results)}")
    print("\n   Detalle:")
    print("   " + "-"*80)
    print(f"   {'Cliente':<15} {'Email':<30} {'Role':<12} {'BackCompat'}")
    print("   " + "-"*80)
    
    for client_id, org_name, user_id, email, username, role, backward_compat in results:
        compat = "✅" if backward_compat else "❌"
        print(f"   {client_id:<15} {email:<30} {role:<12} {compat}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*60)
    print("\nPróximos pasos:")
    print("1. Testear login con credenciales DEMO")
    print("2. Verificar permisos de ADMIN")
    print("3. Crear proyecto de prueba")
    print("4. Invitar usuario adicional")

def create_user_from_old_tenant(cursor, tenant_id, client_id, created_at):
    """Crea usuario desde datos de utm_tenants_old"""
    
    # Generar email y username
    username = client_id.lower()
    email = f"{username}@legacy.local"
    
    # Password por defecto (bcrypt de "demo123")
    # En producción, esto debería forzar cambio de password
    default_password = "demo123"
    password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
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
            username = EXCLUDED.username,
            role = 'ADMIN',
            updated_at = NOW();
    """, (
        tenant_id,  # user_id = tenant_id (backward compatibility!)
        tenant_id,
        email,
        username,
        password_hash,
        'ADMIN',
        True,
        f"Admin {client_id}",
        created_at
    ))
    
    print(f"   ✅ {client_id}: {email} (password: demo123)")

def create_user_from_new_tenant(cursor, tenant_id, client_id, org_name, created_at):
    """Crea usuario desde datos de utm_tenants nueva"""
    
    # Generar email y username
    username = client_id.lower()
    email = f"{username}@legacy.local"
    
    # Password por defecto
    default_password = "demo123"
    password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
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
            username = EXCLUDED.username,
            role = 'ADMIN',
            updated_at = NOW();
    """, (
        tenant_id,  # user_id = tenant_id (backward compatibility!)
        tenant_id,
        email,
        username,
        password_hash,
        'ADMIN',
        True,
        f"Admin {org_name}",
        created_at
    ))
    
    print(f"   ✅ {client_id}: {email} (password: demo123)")

if __name__ == "__main__":
    main()
