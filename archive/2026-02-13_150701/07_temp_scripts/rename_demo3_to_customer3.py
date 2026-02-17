#!/usr/bin/env python3
"""
Renombrar client_id de DEMO3 a CUSTOMER3
"""
from connect_supabase_dev import get_postgres_connection

try:
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("Actualizando client_id DEMO3 → CUSTOMER3...")
    
    # Actualizar tenant
    cursor.execute("""
        UPDATE utm_tenants 
        SET client_id = 'CUSTOMER3', 
            org_name = 'Customer Organization 3',
            updated_at = NOW()
        WHERE client_id = 'DEMO3';
    """)
    
    print("✅ Tenant actualizado")
    
    # Verificar
    cursor.execute("""
        SELECT t.client_id, t.org_name, u.username, u.email, u.role
        FROM utm_tenants t
        JOIN utm_users u ON t.tenant_id = u.tenant_id
        WHERE t.client_id = 'CUSTOMER3';
    """)
    
    result = cursor.fetchone()
    if result:
        client_id, org_name, username, email, role = result
        print(f"\n✅ Verificación:")
        print(f"   Client ID: {client_id}")
        print(f"   Org Name:  {org_name}")
        print(f"   Username:  {username}")
        print(f"   Email:     {email}")
        print(f"   Role:      {role}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Client ID actualizado exitosamente")
    print("\nAhora puedes usar:")
    print("  - Username: demo3")
    print("  - Client:   CUSTOMER3")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
