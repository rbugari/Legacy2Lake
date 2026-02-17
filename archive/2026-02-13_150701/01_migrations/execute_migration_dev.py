"""
Script para ejecutar la migración v3.9 en ambiente de desarrollo
Ejecuta los scripts SQL en el orden correcto con validación
"""
import os
import sys
from pathlib import Path

# Importar conexión desde el módulo existente
try:
    from connect_supabase_dev import get_postgres_connection, POSTGRES_CONN_STRING
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    print("⚠️  psycopg2 no está instalado. Instalando...")
    os.system("pip install psycopg2-binary")
    from connect_supabase_dev import get_postgres_connection, POSTGRES_CONN_STRING
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Scripts a ejecutar en orden
MIGRATION_SCRIPTS = [
    "010_v3.9_create_users_table.sql",
    "011_v3.9_create_invitations_table.sql",
    "012_v3.9_refactor_tenants.sql",
    "013_v3.9_add_user_ref_projects.sql",
    "014_v3.9_add_user_ref_locks.sql",
    "015_v3.9_data_migration.sql",
    "016_v3.9_update_rls_policies.sql"
]

def execute_sql_file(conn, filepath: Path, script_name: str):
    """Ejecuta un archivo SQL y reporta resultados"""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script_name}")
    print(f"{'='*60}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = conn.cursor()
        
        # Ejecutar el script
        cursor.execute(sql_content)
        
        # Capturar mensajes NOTICE/RAISE NOTICE
        for notice in conn.notices:
            print(notice.strip())
        conn.notices.clear()
        
        # Commit si es exitoso
        conn.commit()
        
        print(f"✅ {script_name} ejecutado exitosamente")
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ ERROR en {script_name}:")
        print(f"   {str(e)}")
        conn.rollback()
        return False

def main():
    """Ejecuta todos los scripts de migración"""
    print("="*60)
    print("MIGRACIÓN v3.9 - AMBIENTE DE DESARROLLO")
    print("="*60)
    print(f"Fecha: {Path(__file__).stat().st_mtime}")
    print(f"Scripts a ejecutar: {len(MIGRATION_SCRIPTS)}")
    
    # Ruta base de los scripts
    base_path = Path(__file__).parent / "supabase_migrations"
    
    if not base_path.exists():
        print(f"❌ ERROR: Carpeta {base_path} no encontrada")
        return
    
    # Conectar a la base de datos
    print("\n🔌 Conectando a Supabase Dev...")
    print(f"   URL: {POSTGRES_CONN_STRING.split('@')[1].split('/')[0]}")
    try:
        conn = get_postgres_connection()
        # Habilitar autocommit para que cada script se ejecute en su propia transacción
        # pero comentamos esto porque los scripts tienen BEGIN/COMMIT
        # conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")
        print(f"   Detalles: {str(e)}")
        return
    
    # Ejecutar cada script
    success_count = 0
    failed_scripts = []
    
    for script_name in MIGRATION_SCRIPTS:
        script_path = base_path / script_name
        
        if not script_path.exists():
            print(f"\n⚠️  ADVERTENCIA: {script_name} no encontrado, saltando...")
            continue
        
        success = execute_sql_file(conn, script_path, script_name)
        
        if success:
            success_count += 1
        else:
            failed_scripts.append(script_name)
            
            # Preguntar si continuar
            print("\n⚠️  ¿Continuar con los siguientes scripts? (s/n): ", end='')
            response = input().lower()
            if response != 's':
                print("❌ Migración abortada por el usuario")
                break
    
    # Cerrar conexión
    conn.close()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE MIGRACIÓN")
    print("="*60)
    print(f"Scripts ejecutados exitosamente: {success_count}/{len(MIGRATION_SCRIPTS)}")
    
    if failed_scripts:
        print(f"\n❌ Scripts fallidos:")
        for script in failed_scripts:
            print(f"   - {script}")
    else:
        print("\n✅ Todos los scripts ejecutados exitosamente")
        print("\n📝 Próximos pasos:")
        print("   1. Verificar datos migrados con queries de validación")
        print("   2. Testear login con usuarios existentes")
        print("   3. Crear usuario nuevo para probar invitaciones")
        print("   4. Verificar RLS policies funcionando")
    
    print("="*60)

if __name__ == "__main__":
    main()
