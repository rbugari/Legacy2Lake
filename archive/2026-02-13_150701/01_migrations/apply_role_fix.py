#!/usr/bin/env python3
"""
Ejecuta migración 018: Cambiar roles ADMIN → MANAGER
"""
try:
    from connect_supabase_dev import get_postgres_connection
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("⚠️  psycopg2 not installed. Installing...")
    import os
    os.system("pip install psycopg2-binary")
    from connect_supabase_dev import get_postgres_connection
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

print("="*60)
print("MIGRACIÓN 018: ADMIN → MANAGER")
print("="*60)
print()
print("Conceptos:")
print("  🛡️  ADMIN = Dueño de plataforma (escudo naranja)")
print("      - NO pertenece a ningún tenant")
print("      - Maneja agentes, catálogos, configuración global")
print()
print("  👥 Usuarios de tenant:")
print("      - MANAGER: Crea proyectos, invita usuarios")
print("      - COLLABORATOR: Trabaja en proyectos, no borra")
print("      - VIEWER: Solo lectura")
print("="*60)
print()

# Read the migration script
with open("supabase_migrations/018_v3.9_fix_roles_admin_to_manager.sql", "r") as f:
    sql = f.read()

try:
    # Connect to PostgreSQL
    conn = get_postgres_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    print("📡 Conectado a PostgreSQL")
    
    # Execute the SQL
    cursor.execute(sql)
    
    print("✅ Migración ejecutada exitosamente!")
    print()
    
    # Verify changes
    cursor.execute("""
        SELECT role, COUNT(*) as count
        FROM utm_users
        GROUP BY role
        ORDER BY role;
    """)
    
    roles = cursor.fetchall()
    
    print("📊 Roles actuales en utm_users:")
    for role, count in roles:
        print(f"   {role}: {count} usuarios")
    
    print()
    
    # Show updated users
    cursor.execute("""
        SELECT email, username, role
        FROM utm_users
        ORDER BY created_at;
    """)
    
    users = cursor.fetchall()
    print("👥 Usuarios actualizados:")
    for email, username, role in users:
        print(f"   {email:25} ({username:10}) → {role}")
    
    cursor.close()
    conn.close()
    
    print()
    print("="*60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
