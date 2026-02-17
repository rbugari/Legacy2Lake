#!/usr/bin/env python3
"""
Check all active process locks
"""
from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cur = conn.cursor()

# Get all active locks
cur.execute("""
    SELECT lock_id, project_id, process_type, locked_by_username, 
           expires_at, status
    FROM utm_process_locks
    WHERE status = 'active'
    ORDER BY expires_at DESC
""")

locks = cur.fetchall()

if locks:
    print(f"Found {len(locks)} active lock(s):\n")
    for lock in locks:
        lock_id, project_id, process_type, username, expires_at, status = lock
        print(f"Lock ID: {lock_id}")
        print(f"  Project: {project_id}")
        print(f"  Process: {process_type}")
        print(f"  Locked by: {username}")
        print(f"  Expires: {expires_at}")
        print(f"  Status: {status}")
        print()
else:
    print("No active locks found")

cur.close()
conn.close()
