"""
Script para conectar a la base de datos de Supabase (Dev)

Proporciona funciones para conectar tanto con el cliente de Supabase
como directamente a PostgreSQL.
"""
import os
from supabase import create_client, Client
import psycopg2
from typing import Optional

# Credenciales de Supabase Dev
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"
POSTGRES_CONN_STRING = "postgresql://postgres:A2321rfb!supa@db.qdsdfityyxmalyipqbfm.supabase.co:5432/postgres"

def get_supabase_client() -> Client:
    """Retorna un cliente de Supabase configurado"""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_postgres_connection():
    """Retorna una conexión directa a PostgreSQL"""
    return psycopg2.connect(POSTGRES_CONN_STRING)

def test_supabase_connection():
    """Prueba la conexión a Supabase y lista algunas tablas"""
    try:
        supabase = get_supabase_client()
        print(f"✓ Conectado exitosamente a Supabase: {SUPABASE_URL}")
        
        # Intentar listar algunas tablas del esquema public
        print("\n--- Consultando tablas UTM ---")
        
        # Listar tablas principales del sistema (con prefijo utm_)
        tables_to_check = [
            "utm_tenants",
            "utm_projects", 
            "utm_prompts",
            "utm_global_config",
            "utm_vault",
            "utm_model_catalog"
        ]
        
        for table in tables_to_check:
            try:
                response = supabase.table(table).select("*", count="exact").limit(0).execute()
                count = response.count if hasattr(response, 'count') else 'N/A'
                print(f"  • {table}: {count} registros")
            except Exception as e:
                print(f"  • {table}: No accesible ({str(e)[:50]}...)")
        
        print("\n✓ Conexión verificada correctamente")
        return True
        
    except Exception as e:
        print(f"✗ Error al conectar a Supabase: {str(e)}")
        return False

def test_postgres_direct():
    """Prueba la conexión directa a PostgreSQL"""
    try:
        print("\n--- Probando conexión directa a PostgreSQL ---")
        conn = get_postgres_connection()
        cursor = conn.cursor()
        
        # Verificar versión
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Conectado a: {version[:50]}...")
        
        # Listar esquemas
        cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
        schemas = cursor.fetchall()
        print(f"\n--- Esquemas disponibles ({len(schemas)}) ---")
        for schema in schemas:
            print(f"  • {schema[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Conexión PostgreSQL verificada correctamente")
        return True
        
    except Exception as e:
        print(f"✗ Error al conectar a PostgreSQL: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN - SUPABASE DEV")
    print("=" * 60)
    
    # Probar con cliente de Supabase
    test_supabase_connection()
    
    print("\n" + "=" * 60)
    
    # Probar conexión directa a PostgreSQL
    test_postgres_direct()
    
    print("\n" + "=" * 60)
