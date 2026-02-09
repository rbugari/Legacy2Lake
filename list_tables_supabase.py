"""
Listar todas las tablas en el esquema public de Supabase
"""
import psycopg2
from psycopg2 import sql

def list_tables():
    """Lista todas las tablas del esquema public"""
    conn_string = "postgresql://postgres:A2321rfb!supa@db.qdsdfityyxmalyipqbfm.supabase.co:5432/postgres"
    
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("TABLAS EN ESQUEMA 'public' - SUPABASE DEV")
        print("=" * 80)
        
        # Listar tablas del esquema public
        query = """
            SELECT 
                table_name,
                (SELECT COUNT(*) 
                 FROM information_schema.columns 
                 WHERE table_schema = 'public' 
                 AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        if not tables:
            print("\n❌ No hay tablas en el esquema 'public'")
            print("\n💡 Probablemente necesitas ejecutar las migraciones:")
            print("   cd supabase_migrations")
            print("   supabase db push")
        else:
            print(f"\n✓ Encontradas {len(tables)} tablas:\n")
            for table_name, col_count in tables:
                print(f"  📋 {table_name:30} ({col_count} columnas)")
            
            # Mostrar detalles de la primera tabla
            if tables:
                print("\n" + "=" * 80)
                print(f"ESTRUCTURA DE TABLA: {tables[0][0]}")
                print("=" * 80)
                
                detail_query = """
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """
                
                cursor.execute(detail_query, (tables[0][0],))
                columns = cursor.fetchall()
                
                print(f"\nColumnas de '{tables[0][0]}':\n")
                for col_name, data_type, max_len, nullable, default in columns:
                    length = f"({max_len})" if max_len else ""
                    null = "NULL" if nullable == "YES" else "NOT NULL"
                    default_str = f" DEFAULT {default}" if default else ""
                    print(f"  • {col_name:25} {data_type}{length:10} {null:10}{default_str}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

if __name__ == "__main__":
    list_tables()
