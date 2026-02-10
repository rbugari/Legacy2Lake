"""
Verify RLS status for utm_project_members table
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("=" * 70)
print("CHECKING RLS STATUS FOR utm_project_members")
print("=" * 70)

# Query to check RLS status
query = """
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE tablename = 'utm_project_members';
"""

try:
    result = client.rpc('exec_sql', {'sql': query}).execute()
    print("\n✅ Query executed")
    print(result.data)
except Exception as e:
    print(f"\n⚠️  Cannot use exec_sql RPC, trying alternative...\n")
    
    # Alternative: Check policies
    try:
        # Try to query the table directly with service role
        test = client.table("utm_project_members").select("*").limit(1).execute()
        print("\n✅ Can query utm_project_members with SERVICE_ROLE_KEY")
        print(f"   Returned {len(test.data)} rows")
        
        if len(test.data) == 0:
            print("\n📋 Table is empty (no members assigned yet)")
        else:
            print("\n📋 Sample data:")
            print(test.data[0])
            
    except Exception as e2:
        error_msg = str(e2)
        if "permission denied" in error_msg.lower():
            print("\n❌ STILL BLOCKED BY RLS!")
            print("\n📝 You MUST run this SQL in Supabase Dashboard:")
            print("=" * 70)
            print("ALTER TABLE utm_project_members DISABLE ROW LEVEL SECURITY;")
            print("=" * 70)
            print("\nSteps:")
            print("1. Go to: https://supabase.com/dashboard")
            print("2. Select your project")
            print("3. SQL Editor")
            print("4. Run the ALTER TABLE command above")
            print("5. Verify with: SELECT relrowsecurity FROM pg_class WHERE relname = 'utm_project_members';")
            print("   (Should return 'f' for false)")
        else:
            print(f"\n❌ Unexpected error: {error_msg}")

print("\n" + "=" * 70)
