"""
Script para ejecutar solo el script 016 (RLS Policies)
Los scripts 010-014 ya están aplicados
"""
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from connect_supabase_dev import get_postgres_connection, POSTGRES_CONN_STRING

print("="*60)
print("APLICANDO RLS POLICIES v3.9")
print("="*60)

script_path = Path(__file__).parent / "supabase_migrations" / "016_v3.9_update_rls_policies.sql"

if not script_path.exists():
    print(f"❌ ERROR: Script no encontrado: {script_path}")
    exit(1)

print(f"\n🔌 Conectando a Supabase Dev...")
try:
    conn = get_postgres_connection()
    print("✅ Conexión exitosa\n")
except Exception as e:
    print(f"❌ ERROR de conexión: {e}")
    exit(1)

print(f"📄 Ejecutando: 016_v3.9_update_rls_policies.sql")
print("="*60)

try:
    with open(script_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    cursor = conn.cursor()
    cursor.execute(sql_content)
    
    # Capturar mensajes NOTICE
    for notice in conn.notices:
        print(notice.strip())
    conn.notices.clear()
    
    conn.commit()
    cursor.close()
    
    print("\n✅ RLS Policies aplicadas exitosamente")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    conn.rollback()
    exit(1)
finally:
    conn.close()

print("="*60)
print("✅ Migración v3.9 COMPLETADA")
print("="*60)
print("\nPróximos pasos:")
print("1. Crear primer usuario/tenant de prueba")
print("2. Testear login")
print("3. Testear sistema de invitaciones")
print("4. Verificar permisos por rol (ADMIN/COLLABORATOR/VIEWER)")
