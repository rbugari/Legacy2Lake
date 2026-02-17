"""
Ejecutar Triage manualmente para el proyecto ttt y verificar que se guarden datos Sprint 8.5
"""
import asyncio
import sys
import os
from pathlib import Path
from supabase import create_client, Client
import json

# Supabase credentials  
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Add to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

# Now import internal modules
from services.agent_c_service import AgentCService
from persistence.supabase_persistence import SupabasePersistence

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

async def run_manual_triage():
    """Run Triage manually and check Sprint 8.5 data generation"""
    print("\n" + "="*80)
    print("EJECUTAR TRIAGE MANUAL - PROYECTO TTT")
    print("="*80)
    
    # Initialize services
    db = SupabasePersistence(supabase_client=supabase, tenant_id=tenant_id)
    agent_c = AgentCService()
    
    # Get CORE object (the one with logical_medulla)
    result = supabase.table("utm_objects") \
        .select("object_id, object_name, source_path, type, metadata") \
        .eq("project_id", project_id) \
        .eq("type", "CORE") \
        .limit(1) \
        .execute()
    
    if not result.data or len(result.data) == 0:
        print("❌ No se encontró objeto CORE en el proyecto")
        return False
    
    asset = result.data[0]
    asset_id = asset.get("object_id")
    
    print(f"\n✅ Asset encontrado:")
    print(f"   ID: {asset_id}")
    print(f"   Name: {asset.get('object_name')}")
    print(f"   Type: {asset.get('type')}")
    print(f"   Path: {asset.get('source_path')}")
    
    # Check if has medulla
    metadata = asset.get('metadata', {})
    if isinstance(metadata, str):
        import json
        metadata = json.loads(metadata)
    
    if not metadata.get('logical_medulla'):
        print("\n❌ Asset no tiene logical_medulla - Discovery no corrió correctamente")
        return False
    
    print(f"\n✅ logical_medulla presente ({len(str(metadata['logical_medulla']))} chars)")
    
    # Now run transpile_task which should trigger Sprint 8.5 extraction
    print("\n" + "="*80)
    print("EJECUTANDO transpile_task (TRIAGE/DRAFTING)")
    print("="*80)
    
    try:
        result = await agent_c.transpile_task(
            asset_id=asset_id,
            project_id=project_id,
            tech_id="pyspark",
            layer="bronze",
            system_prompt=None,
            user_context=None,
            db=db
        )
        
        print(f"\n✅ transpile_task completado")
        print(f"   Code length: {len(result.get('bronze_code', ''))} chars")
        
    except Exception as e:
        print(f"\n❌ Error en transpile_task: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify Sprint 8.5 data was saved
    print("\n" + "="*80)
    print("VERIFICAR DATOS SPRINT 8.5 GUARDADOS")
    print("="*80)
    
    result = supabase.table("utm_objects") \
        .select("object_id, source_connection, source_type, transformations, complexity_score, data_flow_analysis") \
        .eq("object_id", asset_id) \
        .execute()
    
    if result.data and len(result.data) > 0:
        obj = result.data[0]
        
        has_data = False
        if obj.get('source_connection'):
            print(f"✅ source_connection: {obj.get('source_connection')[:100]}...")
            has_data = True
        else:
            print(f"❌ source_connection: NULL")
        
        if obj.get('source_type'):
            print(f"✅ source_type: {obj.get('source_type')}")
            has_data = True
        else:
            print(f"❌ source_type: NULL")
        
        if obj.get('transformations'):
            import json
            trans = json.loads(obj.get('transformations')) if isinstance(obj.get('transformations'), str) else obj.get('transformations')
            print(f"✅ transformations: {len(trans)} items")
            has_data = True
        else:
            print(f"❌ transformations: NULL")
        
        if obj.get('complexity_score') is not None:
            print(f"✅ complexity_score: {obj.get('complexity_score')}")
            has_data = True
        else:
            print(f"❌ complexity_score: NULL")
        
        if obj.get('data_flow_analysis'):
            dfa = json.loads(obj.get('data_flow_analysis')) if isinstance(obj.get('data_flow_analysis'), str) else obj.get('data_flow_analysis')
            print(f"✅ data_flow_analysis: {len(str(dfa))} chars")
            has_data = True
        else:
            print(f"❌ data_flow_analysis: NULL")
        
        if has_data:
            print("\n✅ ÉXITO - Datos Sprint 8.5 guardados correctamente")
            return True
        else:
            print("\n❌ FALLO - No se guardaron datos Sprint 8.5")
            return False
    else:
        print("❌ No se pudo recuperar el objeto después del UPDATE")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_manual_triage())
    sys.exit(0 if success else 1)
