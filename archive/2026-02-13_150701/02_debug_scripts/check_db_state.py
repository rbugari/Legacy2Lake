"""
Script para verificar el estado actual de la base de datos
"""
from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cursor = conn.cursor()

print("="*60)
print("ESTADO ACTUAL DE LA BASE DE DATOS")
print("="*60)

# Verificar qué tablas existen
print("\n1. Tablas utm_ existentes:")
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE 'utm_%'
    ORDER BY table_name;
""")
for row in cursor.fetchall():
    print(f"   - {row[0]}")

# Verificar estructura de utm_tenants
print("\n2. Estructura de utm_tenants:")
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'utm_tenants'
    ORDER BY ordinal_position;
""")
for row in cursor.fetchall():
    print(f"   - {row[0]}: {row[1]} ({row[2]})")

# Verificar si hay datos
print("\n3. Conteo de registros:")
tables_to_check = ['utm_tenants', 'utm_tenants_old', 'utm_users', 'utm_projects']
for table in tables_to_check:
    try:
        cursor.execute(f"SELECT count(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} registros")
    except Exception as e:
        print(f"   - {table}: No existe o error ({str(e)[:50]})")

cursor.close()
conn.close()
print("="*60)
