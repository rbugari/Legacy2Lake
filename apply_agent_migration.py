"""
Aplicar migración: add_agent_display_names.sql
"""
from connect_supabase_dev import get_postgres_connection
import os

def apply_migration():
    """Aplica la migración SQL para agregar display_name y description"""
    
    migration_file = "supabase_migrations/add_agent_display_names.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Archivo de migración no encontrado: {migration_file}")
        return False
    
    # Leer el archivo SQL
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("APLICANDO MIGRACIÓN: add_agent_display_names.sql")
    print("=" * 80)
    
    try:
        # Ejecutar la migración
        cursor.execute(sql)
        conn.commit()
        
        print("\n✅ Migración aplicada exitosamente")
        
        # El script ya incluye la verificación al final, mostrar resultados
        print("\n" + "=" * 80)
        print("AGENTES ACTUALIZADOS")
        print("=" * 80 + "\n")
        
        cursor.execute("""
            SELECT 
                agent_id,
                name,
                display_name,
                LEFT(description, 60) as description_preview,
                is_active
            FROM utm_agent_catalog
            ORDER BY agent_id;
        """)
        
        agents = cursor.fetchall()
        for agent_id, name, display_name, desc, is_active in agents:
            status = "✓" if is_active else "✗"
            print(f"{status} {agent_id:12} | {display_name or 'N/A':25} | {desc or 'Sin descripción'}...")
        
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
    success = apply_migration()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ TAREA #3 DEL BACKLOG v3.8 COMPLETADA")
        print("=" * 80)
        print("\nProximos pasos:")
        print("  1. Actualizar UI para mostrar display_name en lugar de agent_id")
        print("  2. Agregar tooltips con description en interfaz de agentes")
        print("  3. Actualizar documentación técnica con nuevos nombres")
