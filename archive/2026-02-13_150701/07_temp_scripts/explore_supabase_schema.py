"""
Explorar el esquema de la base de datos de Supabase usando el cliente
"""
from supabase import create_client, Client
import json

def explore_database():
    """Explora la estructura de la base de datos"""
    url = "https://qdsdfityyxmalyipqbfm.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"
    
    try:
        supabase: Client = create_client(url, key)
        print("=" * 70)
        print("EXPLORACIÓN DE BASE DE DATOS - SUPABASE DEV")
        print("=" * 70)
        
        # Ejecutar query SQL personalizada para listar tablas
        print("\n--- Tablas en esquema 'public' ---\n")
        
        # Intentar obtener una lista de tablas usando la API REST
        # Como no tenemos acceso directo a información_schema, 
        # vamos a probar con las tablas comunes del proyecto
        
        common_tables = [
            "tenant", "tenants", "Tenant", "Tenants",
            "user", "users", "User", "Users",
            "project", "projects", "Project", "Projects",
            "solution", "solutions", "Solution", "Solutions",
            "prompt", "prompts", "Prompt", "Prompts",
            "global_config", "GlobalConfig", "config",
            "agent", "agents", "Agent", "Agents",
            "model", "models", "Model", "Models",
            "provider", "providers", "Provider", "Providers",
            "catalog", "catalogs", "Catalog", "Catalogs",
            "job", "jobs", "Job", "Jobs",
            "execution", "executions", "Execution", "Executions"
        ]
        
        found_tables = []
        
        for table in common_tables:
            try:
                response = supabase.table(table).select("*", count="exact").limit(1).execute()
                count = response.count if hasattr(response, 'count') else 'desconocido'
                found_tables.append({
                    'name': table,
                    'count': count,
                    'sample': response.data[0] if response.data else None
                })
                print(f"✓ {table:20} - {count} registros")
            except Exception:
                pass
        
        if not found_tables:
            print("No se encontraron tablas con nombres comunes.")
            print("\nProbablemente necesitas:")
            print("  1. Ejecutar las migraciones de Supabase")
            print("  2. O las tablas tienen nombres diferentes")
        else:
            print(f"\n--- Tablas encontradas: {len(found_tables)} ---\n")
            
            # Mostrar estructura de alguna tabla encontrada
            if found_tables:
                print("\n--- Muestra de datos de primera tabla ---\n")
                first_table = found_tables[0]
                print(f"Tabla: {first_table['name']}")
                print(f"Total registros: {first_table['count']}")
                if first_table['sample']:
                    print("\nEstructura (columnas):")
                    for key in first_table['sample'].keys():
                        print(f"  • {key}")
                    print("\nPrimer registro:")
                    print(json.dumps(first_table['sample'], indent=2, default=str))
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    explore_database()
