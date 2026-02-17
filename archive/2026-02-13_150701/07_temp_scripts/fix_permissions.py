#!/usr/bin/env python3
"""
Quick fix: Apply service role permissions to v3.9 tables
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

print("🔧 Fixing service role permissions for v3.9 tables...")
print("=" * 60)

# Read the migration script
with open("supabase_migrations/017_v3.9_fix_service_role_permissions.sql", "r") as f:
    sql = f.read()

try:
    # Connect to PostgreSQL
    conn = get_postgres_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    print("📡 Connected to PostgreSQL")
    
    # Execute the SQL
    cursor.execute(sql)
    
    print("✅ Service role permissions granted successfully!")
    print("\n📊 Permissions granted:")
    print("   - utm_users: ALL to postgres, service_role, authenticated")
    print("   - utm_user_invitations: ALL to postgres, service_role, authenticated")
    print("   - utm_tenants: ALL to postgres, service_role, authenticated")
    print("   - utm_projects: ALL to postgres, service_role, authenticated")
    print("   - utm_asset_context: ALL to postgres, service_role, authenticated")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error executing migration: {e}")
    print("\n🔧 Trying alternative approach: Individual GRANT statements...")
    
    # Try each GRANT individually
    try:
        conn = get_postgres_connection()
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        grants = [
            ("utm_users", "GRANT ALL ON utm_users TO postgres, service_role, authenticated"),
            ("utm_users (anon)", "GRANT SELECT ON utm_users TO anon"),
            ("utm_user_invitations", "GRANT ALL ON utm_user_invitations TO postgres, service_role, authenticated"),
            ("utm_tenants", "GRANT ALL ON utm_tenants TO postgres, service_role, authenticated"),
            ("utm_projects", "GRANT ALL ON utm_projects TO postgres, service_role, authenticated"),
        ]
        
        success_count = 0
        for table_name, grant_sql in grants:
            try:
                cursor.execute(grant_sql)
                print(f"✅ Granted permissions on {table_name}")
                success_count += 1
            except Exception as grant_err:
                print(f"⚠️  Failed for {table_name}: {grant_err}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Permissions fixed ({success_count}/{len(grants)} successful)")
        
    except Exception as conn_err:
        print(f"❌ Connection error: {conn_err}")
        exit(1)

print("\n" + "=" * 60)
print("🚀 Restart the FastAPI server and try logging in again!")
print("   Test with: POST http://127.0.0.1:8085/login")
print("   Credentials: demo1@demo.local / demo123")
