"""
Inspect utm_prompts table schema in Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("="*80)
print("🔍 Inspecting utm_prompts table schema...")
print("="*80)

# Try to query the table to see if it exists
try:
    result = client.table("utm_prompts").select("*").limit(1).execute()
    print(f"\n✅ Table exists! Found {len(result.data)} sample records")
    
    if result.data:
        print("\n📋 Sample record structure:")
        for key, value in result.data[0].items():
            value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            print(f"  - {key}: {type(value).__name__} = {value_preview}")
    else:
        print("\n⚠️ Table exists but is empty")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTable might not exist yet. Need to create migration.")

# Try to get schema from information_schema
print("\n" + "="*80)
print("📊 Attempting to query information_schema...")
print("="*80)

try:
    # Use RPC or direct SQL if available
    schema_query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = 'utm_prompts'
    ORDER BY ordinal_position;
    """
    
    # Supabase doesn't directly expose information_schema, so let's just list what we know
    print("\nBased on code analysis, expected schema:")
    print("  - tenant_id: UUID (nullable, for tenant-specific overrides)")
    print("  - prompt_id: TEXT (e.g., 'agent_c_interpreter', 'cartridge_pyspark_bronze')")
    print("  - version_number: INTEGER")
    print("  - content: TEXT")
    print("  - is_active: BOOLEAN")
    print("  - changelog: TEXT")
    print("  - created_at: TIMESTAMP")
    print("  - updated_at: TIMESTAMP")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
