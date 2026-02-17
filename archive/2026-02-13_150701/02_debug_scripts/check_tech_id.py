#!/usr/bin/env python3
from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cur = conn.cursor()

# Check columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'utm_system_catalog'
    ORDER BY ordinal_position
""")
cols = [row[0] for row in cur.fetchall()]
print("Columnas en utm_system_catalog:")
for col in cols:
    print(f"  - {col}")

print("\n" + "=" * 60)

# Check if tech_id column exists
if 'tech_id' in cols:
    print("✅ Columna 'tech_id' existe")
    
    # Try to fetch ssis
    cur.execute("""
        SELECT id, tech_id, name, type 
        FROM utm_system_catalog 
        WHERE tech_id = 'ssis'
    """)
    result = cur.fetchone()
    if result:
        print(f"✅ SSIS encontrado: {result}")
    else:
        print("❌ SSIS no encontrado por tech_id")
        
        # Check all records
        cur.execute("SELECT id, name, type FROM utm_system_catalog LIMIT 5")
        print("\nPrimeros 5 registros:")
        for row in cur.fetchall():
            print(f"  {row}")
else:
    print("❌ Columna 'tech_id' NO existe")
    print("\nEsto explica el error 404!")

cur.close()
conn.close()
