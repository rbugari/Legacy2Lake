"""
Test the new schema extraction from generated code
"""
from connect_supabase_dev import get_supabase_client
import re

def extract_schema_from_code(code: str, table_name: str):
    """
    Extract schema from generated PySpark/SQL code (Sprint 13).
    """
    columns = []
    
    # Pattern 1: inferred_schema = [("col", "type"), ...]
    pattern1 = r'inferred_schema\s*=\s*\[((?:\s*\(["\'][\w_]+["\']\s*,\s*["\'][\w_]+["\']\)\s*,?\s*)*)\]'
    match1 = re.search(pattern1, code, re.DOTALL)
    
    if match1:
        schema_str = match1.group(1)
        # Parse tuples: ("column", "type")
        tuple_pattern = r'\(["\'](\w+)["\']\s*,\s*["\'](\w+)["\']\)'
        for col_match in re.finditer(tuple_pattern, schema_str):
            col_name = col_match.group(1)
            col_type = col_match.group(2)
            columns.append({
                'name': col_name,
                'type': col_type,
                'nullable': True,
                'is_primary_key': False,
                'is_foreign_key': False
            })
    
    if columns:
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_key': [],
            'foreign_keys': [],
            'row_count': None
        }
    
    return None

def test_extraction():
    supabase = get_supabase_client()
    
    # Get the generated code
    result = supabase.table("utm_objects") \
        .select("object_id, source_name, generated_code, schema_metadata") \
        .eq("project_id", "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4") \
        .not_.is_("generated_code", "null") \
        .order("updated_at", desc=True) \
        .limit(1) \
        .execute()
    
    if result.data and len(result.data) > 0:
        obj = result.data[0]
        code = obj.get('generated_code', '')
        table_name = obj.get('source_name', 'unknown')
        current_schema = obj.get('schema_metadata', {})
        
        print(f"\n=== TESTING SCHEMA EXTRACTION ===")
        print(f"Table: {table_name}")
        print(f"Code Length: {len(code)} chars")
        print(f"\nCurrent schema_metadata columns: {len(current_schema.get('columns', []))}")
        
        # Test extraction
        extracted = extract_schema_from_code(code, table_name)
        
        if extracted:
            print(f"\n✅ EXTRACTED SCHEMA:")
            print(f"Table: {extracted['table_name']}")
            print(f"Columns: {len(extracted['columns'])}")
            for col in extracted['columns']:
                print(f"  - {col['name']}: {col['type']}")
            
            # Update the database
            print(f"\n🔄 Updating database...")
            update_result = supabase.table("utm_objects") \
                .update({
                    "schema_metadata": extracted,
                    "column_count": len(extracted['columns'])
                }) \
                .eq("object_id", obj['object_id']) \
                .execute()
            
            print(f"✅ Database updated! Now schema has {len(extracted['columns'])} columns")
        else:
            print(f"\n❌ Could not extract schema from code")
    else:
        print("No generated code found")

if __name__ == "__main__":
    test_extraction()
