#!/usr/bin/env python3
"""
Force release stuck process lock
"""
from connect_supabase_dev import get_postgres_connection

conn = get_postgres_connection()
cur = conn.cursor()

# Get the drafting lock
cur.execute("""
    SELECT lock_id, project_id, locked_by_username, expires_at, status
    FROM utm_process_locks
    WHERE process_type = 'drafting' AND status = 'active'
""")

lock = cur.fetchone()

if lock:
    lock_id, project_id, username, expires_at, status = lock
    print(f"Found active drafting lock:")
    print(f"  Lock ID: {lock_id}")
    print(f"  Project: {project_id}")
    print(f"  Locked by: {username}")
    print(f"  Expires: {expires_at}")
    print(f"  Status: {status}")
    print()
    
    # Force release
    cur.execute("""
        UPDATE utm_process_locks 
        SET status = 'released' 
        WHERE lock_id = %s
    """, (lock_id,))
    
    conn.commit()
    print(f"✅ Lock released successfully!")
else:
    print("No active drafting locks found")

cur.close()
conn.close()
