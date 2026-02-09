"""
Aplicar migración para agregar agentes faltantes
"""
from connect_supabase_dev import get_postgres_connection
import os

def apply_missing_agents_migration():
    """Aplica la migración para agregar agent-b y agent-d"""
    
    migration_file = "supabase_migrations/add_missing_agents.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Archivo de migración no encontrado: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("APLICANDO MIGRACIÓN: add_missing_agents.sql")
    print("=" * 80)
    
    try:
        cursor.execute(sql)
        conn.commit()
        
        print("\n✅ Migración aplicada exitosamente")
        
        print("\n" + "=" * 80)
        print("AGENTES ACTUALIZADOS")
        print("=" * 80 + "\n")
        
        cursor.execute("""
            SELECT 
                agent_id,
                display_name,
                LEFT(description, 60) as description_preview,
                is_active
            FROM utm_agent_catalog
            ORDER BY agent_id;
        """)
        
        agents = cursor.fetchall()
        for agent_id, display_name, desc, is_active in agents:
            status = "✓" if is_active else "✗"
            print(f"{status} {agent_id:12} | {display_name or 'N/A':30} | {desc or 'Sin descripción'}...")
        
        print(f"\n📊 Total agentes: {len(agents)}")
        
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
    success = apply_missing_agents_migration()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ AGENTES FALTANTES AGREGADOS")
        print("=" * 80)
        print("\nAhora todos los agentes están sincronizados:")
        print("  • agent-b (Cartographer) ✓")
        print("  • agent-d (Architectural Auditor) ✓")
