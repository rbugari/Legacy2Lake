"""
Quick check: are there any active locks for the project?
"""
from connect_supabase_dev import get_supabase_client

def check_locks():
    supabase = get_supabase_client()
    
    result = supabase.table("utm_process_locks") \
        .select("*") \
        .eq("project_id", "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4") \
        .eq("status", "active") \
        .execute()
    
    if result.data and len(result.data) > 0:
        print(f"⚠️ Found {len(result.data)} active locks:")
        for lock in result.data:
            print(f"  - {lock['process_type']} (ID: {lock['lock_id'][:8]}...)")
    else:
        print("✅ No active locks - ready to run Discovery")

if __name__ == "__main__":
    check_locks()
