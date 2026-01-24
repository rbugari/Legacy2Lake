"""
Simplified Migration Runner
Uses psycopg2 if available, otherwise provides manual instructions.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def parse_supabase_url():
    """Extract database connection info from Supabase URL."""
    url = os.getenv("SUPABASE_URL", "").strip()
    
    if not url:
        return None
    
    # Supabase URL format: https://PROJECT_REF.supabase.co
    # Database is at: db.PROJECT_REF.supabase.co:5432
    
    if "supabase.co" in url:
        project_ref = url.replace("https://", "").replace(".supabase.co", "")
        return {
            "host": f"db.{project_ref}.supabase.co",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": os.getenv("SUPABASE_DB_PASSWORD", "")  # Need separate env var
        }
    return None


def run_migration_manual():
    """Provide instructions for manual migration."""
    print("=" * 70)
    print("📋 MANUAL MIGRATION INSTRUCTIONS")
    print("=" * 70)
    print()
    print("Since direct SQL execution isn't available, please follow these steps:")
    print()
    print("1. Go to your Supabase Dashboard:")
    print("   https://supabase.com/dashboard/project/YOUR_PROJECT/editor")
    print()
    print("2. Navigate to: SQL Editor")
    print()
    print("3. Create a new query and paste the contents of:")
    print(f"   📄 {Path(__file__).parent / 'supabase_migrations' / '004_security_improvements.sql'}")
    print()
    print("4. Click 'Run' to execute the migration")
    print()
    print("5. Verify the migration succeeded by checking for:")
    print("   - New column: utm_tenants.password_hash_bcrypt")
    print("   - New table: utm_vault")
    print("   - New table: utm_audit_log")
    print()
    print("=" * 70)
    print()
    
    # Open the SQL file to show the user
    migration_file = Path(__file__).parent / "supabase_migrations" / "004_security_improvements.sql"
    print("📄 Migration SQL content:")
    print("-" * 70)
    with open(migration_file, 'r', encoding='utf-8') as f:
        print(f.read())
    print("-" * 70)


def main():
    print("\n🔧 Legacy2Lake - Database Migration Tool\n")
    
    # Check if we have psycopg2
    try:
        import psycopg2
        print("✅ psycopg2 found - attempting direct connection...")
        
        db_info = parse_supabase_url()
        if not db_info or not db_info['password']:
            print("⚠️  Database connection info incomplete")
            print("   Please set SUPABASE_DB_PASSWORD in .env")
            print()
            run_migration_manual()
            return
        
        # Try to connect
        print(f"📡 Connecting to {db_info['host']}...")
        conn = psycopg2.connect(**db_info)
        cursor = conn.cursor()
        
        # Read and execute migration
        migration_file = Path(__file__).parent / "supabase_migrations" / "004_security_improvements.sql"
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("⚙️  Executing migration...")
        cursor.execute(sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        cursor.close()
        conn.close()
        
    except ImportError:
        print("⚠️  psycopg2 not installed")
        print()
        run_migration_manual()
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        run_migration_manual()


if __name__ == "__main__":
    main()
