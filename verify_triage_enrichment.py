import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def verify_triage_results(project_id):
    db = SupabasePersistence()
    print(f"--- Verificando Resultados de Triaje (Project: {project_id}) ---")
    
    # 1. Fetch Assets
    assets = await db.get_project_assets(project_id)
    if not assets:
        print("[!] No se encontraron assets para este proyecto.")
        return
    
    print(f"[*] Se encontraron {len(assets)} assets.")
    
    # 2. Check for Metadata 1.3
    count_tagged = 0
    for asset in assets:
        t_name = asset.get('target_name')
        b_entity = asset.get('business_entity')
        if t_name or b_entity:
            count_tagged += 1
            print(f"    - Asset: {asset['filename']}")
            print(f"      > Target Name Sugerido: {t_name}")
            print(f"      > Entidad Negocio: {b_entity}")
            print(f"      > Load Strategy: {asset.get('load_strategy')}")
            print(f"      > PII: {asset.get('is_pii')}")
    
    if count_tagged == 0:
        print("[!] Ningún asset tiene metadata de la Release 1.3 asignada automáticamente.")
    else:
        print(f"[OK] {count_tagged} assets fueron enriquecidos con metadata de negocio.")

    # 3. Check Design Registry
    registry = await db.get_design_registry(project_id)
    print(f"[*] Design Registry entries: {len(registry)}")
    # If empty, suggest initializing it
    if not registry:
        print("[!] El registro de diseño está vacío. Probablemente el usuario no lo inicializó en la UI.")

if __name__ == "__main__":
    # Using the project ID from the user logs: 2f28aa44-b44e-4f9f-bf35-db93d38fb1e1
    pid = "2f28aa44-b44e-4f9f-bf35-db93d38fb1e1"
    asyncio.run(verify_triage_results(pid))
