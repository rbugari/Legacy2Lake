#!/usr/bin/env python3
"""
Muestra la estructura detallada de las tablas v3.9
"""
from connect_supabase_dev import get_postgres_connection

def show_table_structure(cursor, table_name):
    print(f"\n{'='*70}")
    print(f"TABLA: {table_name}")
    print('='*70)
    
    # Get columns
    cursor.execute(f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    
    print(f"\n{'Columna':<25} {'Tipo':<20} {'Nullable':<10} {'Default'}")
    print('-'*70)
    
    for col in columns:
        col_name, data_type, max_len, nullable, default = col
        type_str = f"{data_type}"
        if max_len:
            type_str += f"({max_len})"
        
        default_str = str(default)[:30] if default else ''
        print(f"{col_name:<25} {type_str:<20} {nullable:<10} {default_str}")
    
    # Get count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total de registros: {count}")

try:
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("="*70)
    print("TABLAS v3.9 - ESTRUCTURA DETALLADA")
    print("="*70)
    
    # Show structure of new tables
    show_table_structure(cursor, "utm_users")
    show_table_structure(cursor, "utm_user_invitations")
    show_table_structure(cursor, "utm_tenants")
    
    # Show sample data from utm_users
    print("\n" + "="*70)
    print("DATOS DE EJEMPLO: utm_users")
    print("="*70)
    
    cursor.execute("""
        SELECT 
            user_id,
            tenant_id,
            email,
            username,
            role,
            is_active,
            created_at
        FROM utm_users
        ORDER BY created_at DESC
        LIMIT 5;
    """)
    
    users = cursor.fetchall()
    if users:
        print(f"\n{'user_id':<38} {'tenant_id':<38} {'email':<25} {'username':<15} {'role':<12} {'active'}")
        print('-'*150)
        for user in users:
            user_id, tenant_id, email, username, role, is_active, created_at = user
            match_icon = '✅' if str(user_id) == str(tenant_id) else '  '
            print(f"{match_icon} {str(user_id):<36} {str(tenant_id):<36} {email:<25} {username:<15} {role:<12} {is_active}")
    else:
        print("\n⚠️  No hay usuarios creados")
    
    # Show sample data from utm_tenants
    print("\n" + "="*70)
    print("DATOS DE EJEMPLO: utm_tenants")
    print("="*70)
    
    cursor.execute("""
        SELECT 
            tenant_id,
            org_name,
            tier,
            is_active,
            created_at
        FROM utm_tenants
        ORDER BY created_at DESC
        LIMIT 5;
    """)
    
    tenants = cursor.fetchall()
    if tenants:
        print(f"\n{'tenant_id':<38} {'org_name':<20} {'tier':<12} {'active':<8} {'created_at'}")
        print('-'*100)
        for tenant in tenants:
            tenant_id, org_name, tier, is_active, created_at = tenant
            print(f"{str(tenant_id):<38} {org_name:<20} {tier:<12} {is_active!s:<8} {created_at}")
    else:
        print("\n⚠️  No hay tenants creados")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ Las tablas v3.9 están correctamente creadas en la base de datos")
    print("="*70)
    
except Exception as e:
    print(f"❌ Error: {e}")
