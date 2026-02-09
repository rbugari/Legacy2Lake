#!/usr/bin/env python3
"""
Check and force-expire old locks
"""
from connect_supabase_dev import get_postgres_connection
from datetime import datetime, timezone

conn = get_postgres_connection()
cur = conn.cursor()

print("=== ALL LOCKS (including expired) ===\n")

# Get all locks
cur.execute("""
    SELECT lock_id, project_id, process_type, locked_by_username, 
           expires_at, status
    FROM utm_process_locks
    ORDER BY expires_at DESC
    LIMIT 10
""")

locks = cur.fetchall()

if locks:
    now = datetime.now(timezone.utc)
    print(f"Current time (UTC): {now}\n")
    print(f"Found {len(locks)} lock(s):\n")
    for lock in locks:
        lock_id, project_id, process_type, username, expires_at, status = lock
        is_expired = expires_at < now if expires_at else False
        expired_marker = " ⚠️ EXPIRED" if is_expired and status == 'active' else ""
        print(f"Lock ID: {lock_id}")
        print(f"  Project: {project_id}")
        print(f"  Process: {process_type}")
        print(f"  Locked by: {username}")
        print(f"  Expires: {expires_at}{expired_marker}")
        print(f"  Status: {status}")
        print()
else:
    print("No locks found in database")

print("\n=== FORCE EXPIRING STALE LOCKS ===\n")

# Force expire any active locks that are past expiration
cur.execute("""
    UPDATE utm_process_locks
    SET status = 'expired'
    WHERE status = 'active' AND expires_at < NOW()
    RETURNING lock_id, process_type, locked_by_username
""")

expired = cur.fetchall()
conn.commit()

if expired:
    print(f"Expired {len(expired)} stale lock(s):")
    for lock_id, process_type, username in expired:
        print(f"  - {process_type} by {username} (ID: {lock_id})")
else:
    print("No stale locks to expire")

cur.close()
conn.close()
