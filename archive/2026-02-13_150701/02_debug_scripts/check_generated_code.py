"""
Check what's actually stored in generated_code field
"""
from connect_supabase_dev import get_supabase_client

def check_generated_code():
    supabase = get_supabase_client()
    
    # Query the most recent object with generated_code
    result = supabase.table("utm_objects") \
        .select("object_id, source_name, generated_code, tech_id, layer, updated_at") \
        .eq("project_id", "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4") \
        .not_.is_("generated_code", "null") \
        .order("updated_at", desc=True) \
        .limit(1) \
        .execute()
    
    if result.data and len(result.data) > 0:
        obj = result.data[0]
        print("\n=== GENERATED CODE DATA ===")
        print(f"Object ID: {obj.get('object_id')}")
        print(f"Source Name: {obj.get('source_name')}")
        print(f"Tech ID: {obj.get('tech_id')}")
        print(f"Layer: {obj.get('layer')}")
        print(f"Updated At: {obj.get('updated_at')}")
        print(f"\nGenerated Code Length: {len(obj.get('generated_code', ''))} chars")
        print(f"\n--- First 500 chars of generated_code ---")
        code = obj.get('generated_code', '')
        print(code[:500])
        print("\n--- Last 200 chars of generated_code ---")
        print(code[-200:] if len(code) > 200 else code)
    else:
        print("No objects with generated_code found")

if __name__ == "__main__":
    check_generated_code()
