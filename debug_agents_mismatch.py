"""
Diagnosticar discrepancia entre agentes en lista vs base de datos
"""
from connect_supabase_dev import get_postgres_connection

def diagnose_agent_mismatch():
    """Compara agentes en diferentes fuentes"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("DIAGNÓSTICO: DISCREPANCIA DE AGENTES")
    print("=" * 80)
    
    # 1. Agentes en utm_agent_catalog
    print("\n1️⃣  Agentes en utm_agent_catalog (Base de datos):")
    cursor.execute("""
        SELECT agent_id, name, display_name, is_active
        FROM utm_agent_catalog
        ORDER BY agent_id;
    """)
    
    db_agents = cursor.fetchall()
    db_agent_ids = set()
    
    print(f"\nTotal: {len(db_agents)}\n")
    for agent_id, name, display_name, is_active in db_agents:
        status = "✓" if is_active else "✗"
        db_agent_ids.add(agent_id)
        print(f"  {status} {agent_id:12} | {display_name or name:30}")
    
    # 2. Agentes definidos en constants.ts (frontend)
    constants_agents = [
        "agent-s", "agent-a", "agent-b", "agent-c", 
        "agent-f", "agent-g", "agent-p", "agent-r", "agent-o"
    ]
    
    print(f"\n2️⃣  Agentes en constants.ts (Frontend):")
    print(f"\nTotal: {len(constants_agents)}\n")
    for agent_id in constants_agents:
        in_db = "✓" if agent_id in db_agent_ids else "❌"
        print(f"  {in_db} {agent_id}")
    
    # 3. Agentes en PromptsExplorer STAGE_MAP
    stage_map_agents = [
        "agent-s", "agent-a", # triage
        "agent-c", "agent-f", # drafting
        "agent-b", "agent-p", "agent-r", "agent-o", # refinement
        "agent-g" # all
    ]
    
    unique_stage_agents = list(set(stage_map_agents))
    
    print(f"\n3️⃣  Agentes en STAGE_MAP (PromptsExplorer):")
    print(f"\nTotal único: {len(unique_stage_agents)}\n")
    for agent_id in sorted(unique_stage_agents):
        in_db = "✓" if agent_id in db_agent_ids else "❌"
        print(f"  {in_db} {agent_id}")
    
    # 4. Verificar agentes en prompts
    print(f"\n4️⃣  Prompts disponibles en utm_prompts:")
    cursor.execute("""
        SELECT DISTINCT prompt_id
        FROM utm_prompts
        WHERE tenant_id IS NULL
        AND is_active = TRUE
        ORDER BY prompt_id;
    """)
    
    prompts = cursor.fetchall()
    prompt_ids = set([p[0] for p in prompts])
    
    # Extraer agent IDs de prompt_ids (formato: agent_x_name)
    prompt_agent_ids = set()
    for p_id in prompt_ids:
        if p_id.startswith('agent_'):
            parts = p_id.split('_')
            if len(parts) >= 2:
                agent_id = f"agent-{parts[1]}"
                prompt_agent_ids.add(agent_id)
    
    print(f"\nTotal prompts: {len(prompts)}")
    print(f"Agent IDs únicos en prompts: {len(prompt_agent_ids)}\n")
    for agent_id in sorted(prompt_agent_ids):
        in_catalog = "✓" if agent_id in db_agent_ids else "❌"
        print(f"  {in_catalog} {agent_id}")
    
    # 5. Análisis de discrepancias
    print("\n" + "=" * 80)
    print("ANÁLISIS DE DISCREPANCIAS")
    print("=" * 80)
    
    # Agentes en DB pero no en constants
    missing_in_constants = db_agent_ids - set(constants_agents)
    if missing_in_constants:
        print(f"\n⚠️  Agentes en DB pero NO en constants.ts:")
        for agent_id in sorted(missing_in_constants):
            print(f"    • {agent_id}")
    
    # Agentes en constants pero no en DB
    missing_in_db = set(constants_agents) - db_agent_ids
    if missing_in_db:
        print(f"\n⚠️  Agentes en constants.ts pero NO en DB:")
        for agent_id in sorted(missing_in_db):
            print(f"    • {agent_id}")
    
    # Agentes con prompts pero sin entrada en catalog
    orphan_prompts = prompt_agent_ids - db_agent_ids
    if orphan_prompts:
        print(f"\n⚠️  Agentes con prompts pero sin entrada en catalog:")
        for agent_id in sorted(orphan_prompts):
            print(f"    • {agent_id}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"\n  Agentes en catalog:     {len(db_agent_ids)}")
    print(f"  Agentes en constants:   {len(constants_agents)}")
    print(f"  Agentes en STAGE_MAP:   {len(unique_stage_agents)}")
    print(f"  Agentes con prompts:    {len(prompt_agent_ids)}")
    
    if missing_in_constants or missing_in_db or orphan_prompts:
        print("\n⚠️  HAY DISCREPANCIAS - Revisar arriba")
    else:
        print("\n✅ TODO ESTÁ SINCRONIZADO")

if __name__ == "__main__":
    diagnose_agent_mismatch()
