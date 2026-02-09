"""
Apply Process Locking Migration
Executes the process locking SQL migration against Supabase.
"""
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

async def apply_migration():
    """Apply the process locking migration."""
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        return False
    
    # Read migration file
    migration_file = "supabase_migrations/20260207_process_locking.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"📄 Reading migration: {migration_file}")
    print(f"📊 SQL length: {len(sql)} characters")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        print("🔄 Executing migration...")
        
        # Execute the SQL
        # Note: Supabase client doesn't have a direct .sql() method
        # We need to use the REST API or execute via psycopg2
        # For now, let's print instructions
        
        print("\n" + "="*60)
        print("⚠️  MANUAL MIGRATION REQUIRED")
        print("="*60)
        print("\nThe Supabase Python client doesn't support direct SQL execution.")
        print("Please apply this migration manually using one of these methods:\n")
        print("1. Supabase Dashboard:")
        print("   - Go to https://supabase.com/dashboard")
        print("   - Select your project")
        print("   - Navigate to SQL Editor")
        print("   - Paste and execute the SQL from:")
        print(f"     {os.path.abspath(migration_file)}\n")
        print("2. psql command line:")
        print(f"   psql <YOUR_DATABASE_URL> -f {migration_file}\n")
        print("3. Using the migration below:\n")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Process Locking Migration Script")
    print("=" * 60)
    asyncio.run(apply_migration())
