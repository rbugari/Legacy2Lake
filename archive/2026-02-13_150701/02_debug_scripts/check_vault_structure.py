from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cur = conn.cursor()

# utm_vault
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'utm_vault' ORDER BY ordinal_position")
print("utm_vault columns:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

print()

# utm_provider_vault  
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'utm_provider_vault' ORDER BY ordinal_position")
print("utm_provider_vault columns:")
for row in cur.fetchall():
    print(f"  - {row[0]}")

conn.close()
