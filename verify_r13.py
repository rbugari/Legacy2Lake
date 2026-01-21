import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# Set PYTHONPATH manually for the script
import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def verify_schema():
    print("--- Verificando Esquema Release 1.3 ---")
    db = SupabasePersistence()
    
    # 1. List Projects
    projects = await db.list_projects()
    if not projects:
        print("[!] No se encontraron proyectos para probar.")
        return
    
    project_id = projects[0]['id']
    print(f"[*] Usando Proyecto: {projects[0]['name']} ({project_id})")
    
    # 2. Test Design Registry Table
    print("[*] Intentando inicializar Design Registry...")
    success = await db.initialize_design_registry(project_id)
    if success:
        print("[OK] Design Registry inicializado con éxito.")
    else:
        print("[FAIL] Error al inicializar Design Registry.")
        
    # 3. Verify Registry Entries
    registry = await db.get_design_registry(project_id)
    print(f"[OK] Se encontraron {len(registry)} entradas en el registro.")
    for entry in registry[:3]:
        print(f"    - {entry['category']}: {entry['key']} = {entry['value']}")

    # 4. Test Assets Metadata
    print("[*] Verificando columnas business_entity y target_name en assets...")
    assets = await db.get_project_assets(project_id)
    if assets:
        asset_id = assets[0]['id']
        test_entity = "SALES_DOMAIN"
        test_target = "dim_test_v1"
        
        print(f"[*] Actualizando asset {asset_id} con metadata 1.3...")
        patch_success = await db.update_asset_metadata(asset_id, {
            "business_entity": test_entity,
            "target_name": test_target
        })
        
        if patch_success:
            print("[OK] Metadata 1.3 actualizada correctamente.")
            # Verify update
            updated_assets = await db.get_project_assets(project_id)
            updated_asset = next((a for a in updated_assets if a['id'] == asset_id), None)
            if updated_asset and updated_asset.get('business_entity') == test_entity:
                print(f"[OK] Verificación de lectura: {updated_asset['business_entity']} / {updated_asset['target_name']}")
            else:
                print("[FAIL] La metadata no parece haberse guardado correctamente.")
        else:
            print("[FAIL] Error al parchar metadata del asset.")
    else:
        print("[!] No hay assets en este proyecto para probar metadata.")

if __name__ == "__main__":
    asyncio.run(verify_schema())
