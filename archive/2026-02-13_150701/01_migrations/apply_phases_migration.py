"""
Aplicar migración para agregar phases a agentes
"""
from connect_supabase_dev import get_postgres_connection
import os

def apply_phases_migration():
    """Aplica la migración para agregar columna phases"""
    
    migration_file = "supabase_migrations/add_agent_phases.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Archivo de migración no encontrado: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("APLICANDO MIGRACIÓN: add_agent_phases.sql")
    print("=" * 80)
    
    try:
        cursor.execute(sql)
        conn.commit()
        
        print("\n✅ Migración aplicada exitosamente")
        
        print("\n" + "=" * 80)
        print("AGENTES CON FASES ASIGNADAS")
        print("=" * 80 + "\n")
        
        cursor.execute("""
            SELECT 
                agent_id,
                display_name,
                phases,
                array_length(phases, 1) as phase_count
            FROM utm_agent_catalog
            WHERE is_active = TRUE
            ORDER BY agent_id;
        """)
        
        agents = cursor.fetchall()
        for agent_id, display_name, phases, phase_count in agents:
            phases_str = ", ".join(phases) if phases else "Sin asignar"
            print(f"  {agent_id:12} | {display_name:30} | {phases_str}")
        
        print(f"\n📊 Total agentes: {len(agents)}")
        
        # Mostrar resumen por fase
        print("\n" + "=" * 80)
        print("RESUMEN POR FASE")
        print("=" * 80 + "\n")
        
        cursor.execute("""
            SELECT 
                phase,
                array_agg(agent_id ORDER BY agent_id) as agents,
                count(*) as agent_count
            FROM (
                SELECT agent_id, unnest(phases) as phase
                FROM utm_agent_catalog
                WHERE is_active = TRUE AND phases IS NOT NULL
            ) sub
            GROUP BY phase
            ORDER BY 
                CASE phase
                    WHEN 'discovery' THEN 1
                    WHEN 'triage' THEN 2
                    WHEN 'drafting' THEN 3
                    WHEN 'refinement' THEN 4
                    WHEN 'certification' THEN 5
                    WHEN 'governance' THEN 6
                    ELSE 99
                END;
        """)
        
        phases_summary = cursor.fetchall()
        for phase, agents_list, count in phases_summary:
            agents_str = ", ".join(agents_list)
            print(f"  📍 {phase.upper():15} ({count} agentes): {agents_str}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error al aplicar migración: {str(e)}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = apply_phases_migration()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ COLUMNA PHASES AGREGADA EXITOSAMENTE")
        print("=" * 80)
        print("\nBeneficios:")
        print("  • Filtrado de agentes por fase")
        print("  • Mejor organización del proceso")
        print("  • Facilita creación de nuevos agentes")
