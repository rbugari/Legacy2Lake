"""
Show structure of utm_agent_matrix table.
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    client = create_client(url, key)
    
    # Query information_schema to get column structure
    query = """
    SELECT 
        column_name, 
        data_type, 
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = 'utm_agent_matrix'
    ORDER BY ordinal_position;
    """
    
    print("=" * 70)
    print("utm_agent_matrix TABLE STRUCTURE")
    print("=" * 70)
    
    result = client.rpc('exec_sql', {'sql': query}).execute()
    
    if result.data:
        print("\nColumns:")
        for col in result.data:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"  • {col['column_name']:25} {col['data_type']:15} {nullable}{default}")
    else:
        # Fallback: just try to select all from table to see what comes back
        print("\nCouldn't query information_schema, trying direct select...")
        sample = client.table("utm_agent_matrix").select("*").limit(1).execute()
        if sample.data and len(sample.data) > 0:
            print("\nColumns found in table (from sample row):")
            for key in sample.data[0].keys():
                print(f"  • {key}")
        else:
            print("Table is empty, trying to get column names differently...")
            # Try empty insert to trigger error with column info
            print("\nNo data in table. Checking migration files for schema...")

if __name__ == "__main__":
    main()
