#!/usr/bin/env python3
from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cur = conn.cursor()

cur.execute("""
    SELECT agent_id, name 
    FROM utm_agent_catalog 
    ORDER BY agent_id
""")

print("Agentes en la tabla:")
print("-" * 60)
for agent_id, name in cur.fetchall():
    print(f"  {agent_id:15} | {name}")

cur.close()
conn.close()
