"""
Verificar el estado de la tabla utm_process_locks
"""
from connect_supabase_dev import get_postgres_connection

def check_process_locks_table():
    """Verifica si la tabla utm_process_locks existe y su estructura"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VERIFICACIÓN: utm_process_locks")
    print("=" * 80)
    
    # Verificar si la tabla existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'utm_process_locks'
        );
    """)
    
    exists = cursor.fetchone()[0]
    
    if exists:
        print("\n✓ Tabla utm_process_locks EXISTE\n")
        
        # Mostrar estructura
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'utm_process_locks'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("Estructura actual:\n")
        for col_name, data_type, max_len, nullable, default in columns:
            length = f"({max_len})" if max_len else ""
            null = "NULL" if nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  • {col_name:25} {data_type}{length:15} {null:10}{default_str}")
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM utm_process_locks;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Registros actuales: {count}")
        
        # Si hay registros, mostrar algunos
        if count > 0:
            cursor.execute("""
                SELECT lock_id, project_id, process_type, locked_by_user_id, 
                       locked_at, expires_at, status
                FROM utm_process_locks
                ORDER BY locked_at DESC
                LIMIT 5;
            """)
            locks = cursor.fetchall()
            print("\nÚltimos 5 locks:\n")
            for lock in locks:
                print(f"  • {lock}")
    else:
        print("\n❌ Tabla utm_process_locks NO EXISTE")
        print("\n💡 Según el backlog v3.8, esta tabla es CRÍTICA")
        print("   Necesita ser creada con el schema definido.")
    
    cursor.close()
    conn.close()
    
    return exists

if __name__ == "__main__":
    check_process_locks_table()
