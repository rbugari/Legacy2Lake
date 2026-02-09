"""
Verificación completa del Task #3: Agent Management UX
Valida que la migración se aplicó correctamente
"""
from connect_supabase_dev import get_postgres_connection
import json

def verify_agent_management_implementation():
    """Verifica que la implementación esté completa"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VERIFICACIÓN COMPLETA: TASK #3 - AGENT MANAGEMENT UX")
    print("=" * 80)
    
    # 1. Verificar estructura de tabla
    print("\n1️⃣  Verificando estructura de utm_agent_catalog...")
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'utm_agent_catalog'
        ORDER BY ordinal_position;
    """)
    columns = [row[0] for row in cursor.fetchall()]
    
    required_columns = ['agent_id', 'name', 'role_description', 'is_active', 'display_name', 'description']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"   ❌ Faltan columnas: {missing}")
    else:
        print(f"   ✅ Todas las columnas requeridas están presentes")
    
    # 2. Verificar datos de agentes
    print("\n2️⃣  Verificando datos de agentes...")
    cursor.execute("""
        SELECT 
            agent_id,
            name,
            display_name,
            LEFT(description, 50) as description_preview,
            is_active
        FROM utm_agent_catalog
        WHERE is_active = TRUE
        ORDER BY agent_id;
    """)
    
    agents = cursor.fetchall()
    print(f"   Total agentes activos: {len(agents)}\n")
    
    agents_with_display = 0
    agents_with_description = 0
    
    for agent_id, name, display_name, desc, is_active in agents:
        has_display = display_name is not None and display_name.strip() != ""
        has_desc = desc is not None and desc.strip() != ""
        
        if has_display:
            agents_with_display += 1
        if has_desc:
            agents_with_description += 1
        
        status_display = "✅" if has_display else "❌"
        status_desc = "✅" if has_desc else "❌"
        
        print(f"   {agent_id:12} | {status_display} {display_name or 'MISSING':25} | {status_desc} {desc or 'MISSING'}")
    
    print(f"\n   Agentes con display_name: {agents_with_display}/{len(agents)}")
    print(f"   Agentes con description: {agents_with_description}/{len(agents)}")
    
    # 3. Verificar nombres profesionales específicos
    print("\n3️⃣  Verificando nombres profesionales específicos...")
    
    expected_names = {
        'agent-a': 'Discovery Agent',
        'agent-c': 'Code Generator',
        'agent-f': 'Compliance Auditor',
        'agent-g': 'Governance Agent',
        'agent-s': 'Technology Scout',
        'agent-p': 'Profiling Agent',
        'agent-r': 'Refactoring Agent',
        'agent-o': 'Operations Auditor'
    }
    
    cursor.execute("""
        SELECT agent_id, display_name
        FROM utm_agent_catalog
        WHERE is_active = TRUE;
    """)
    
    actual_names = {row[0]: row[1] for row in cursor.fetchall()}
    
    all_correct = True
    for agent_id, expected_name in expected_names.items():
        actual_name = actual_names.get(agent_id)
        if actual_name == expected_name:
            print(f"   ✅ {agent_id}: '{expected_name}'")
        else:
            print(f"   ❌ {agent_id}: Expected '{expected_name}', got '{actual_name}'")
            all_correct = False
    
    # 4. Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE VERIFICACIÓN")
    print("=" * 80)
    
    checks = [
        ("Estructura de tabla", not bool(missing)),
        ("Agentes con display_name", agents_with_display == len(agents)),
        ("Agentes con description", agents_with_description == len(agents)),
        ("Nombres profesionales correctos", all_correct)
    ]
    
    all_passed = all(check[1] for check in checks)
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 TASK #3 COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print("\nTodos los agentes tienen nombres profesionales.")
        print("La UI puede ahora usar display_name para mostrar nombres amigables.")
        print("\nPróximos pasos:")
        print("  1. Reiniciar backend para cargar nuevos nombres")
        print("  2. Probar frontend para verificar tooltips")
        print("  3. Validar documentación actualizada")
    else:
        print("⚠️  VERIFICACIÓN INCOMPLETA")
        print("=" * 80)
        print("\nAlgunos checks fallaron. Revisar la implementación.")
    
    return all_passed

if __name__ == "__main__":
    verify_agent_management_implementation()
