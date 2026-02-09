#!/usr/bin/env python3
"""
Verificar que la columna phases está poblada correctamente
"""
from connect_supabase_dev import get_postgres_connection

def verify_phases():
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("VERIFICANDO COLUMNA PHASES")
    print("=" * 80)
    print()
    
    # Query for agents with phases
    cur.execute("""
        SELECT 
            agent_id,
            display_name,
            phases,
            array_length(phases, 1) as phase_count
        FROM utm_agent_catalog
        WHERE is_active = TRUE
        ORDER BY agent_id
    """)
    
    agents = cur.fetchall()
    
    for agent_id, display_name, phases, phase_count in agents:
        phases_str = ", ".join(phases) if phases else "❌ No phases"
        count_str = f"({phase_count} phases)" if phase_count else ""
        print(f"  {agent_id:12} | {display_name:30} | {phases_str} {count_str}")
    
    print()
    print(f"📊 Total: {len(agents)} agentes activos")
    print()
    
    # Summary by phase
    print("=" * 80)
    print("RESUMEN POR FASE")
    print("=" * 80)
    print()
    
    cur.execute("""
        SELECT 
            phase,
            array_agg(agent_id ORDER BY agent_id) as agents,
            count(*) as agent_count
        FROM (
            SELECT agent_id, unnest(phases) as phase
            FROM utm_agent_catalog
            WHERE is_active = TRUE
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
                ELSE 999
            END
    """)
    
    phases = cur.fetchall()
    
    for phase, agents, count in phases:
        agents_str = ", ".join(agents)
        print(f"  📍 {phase.upper():15} ({count} agentes): {agents_str}")
    
    print()
    print("✅ VERIFICACIÓN COMPLETADA")
    print()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_phases()
