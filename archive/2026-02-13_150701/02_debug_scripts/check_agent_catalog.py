"""
Verificar estado de utm_agent_catalog y campos necesarios
"""
from connect_supabase_dev import get_postgres_connection

def check_agent_catalog_structure():
    """Verifica la estructura de utm_agent_catalog"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VERIFICACIÓN: utm_agent_catalog")
    print("=" * 80)
    
    # Mostrar estructura actual
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'utm_agent_catalog'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]
    
    print("\nEstructura actual:\n")
    for col_name, data_type, max_len, nullable, default in columns:
        length = f"({max_len})" if max_len else ""
        null = "NULL" if nullable == "YES" else "NOT NULL"
        default_str = f" DEFAULT {default}" if default else ""
        print(f"  • {col_name:25} {data_type}{length:15} {null:10}{default_str}")
    
    # Verificar si faltan campos requeridos
    print("\n" + "=" * 80)
    print("ANÁLISIS DE CAMPOS REQUERIDOS (según Backlog v3.8)")
    print("=" * 80)
    
    required_fields = {
        'display_name': 'VARCHAR(100)',
        'description': 'TEXT'
    }
    
    missing_fields = []
    for field, field_type in required_fields.items():
        if field in column_names:
            print(f"\n✓ Campo '{field}' EXISTE")
        else:
            print(f"\n❌ Campo '{field}' FALTA - Tipo requerido: {field_type}")
            missing_fields.append((field, field_type))
    
    # Mostrar agentes actuales
    print("\n" + "=" * 80)
    print("AGENTES REGISTRADOS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT agent_id, name, role_description, is_active
        FROM utm_agent_catalog
        ORDER BY agent_id;
    """)
    
    agents = cursor.fetchall()
    print(f"\nTotal agentes: {len(agents)}\n")
    for agent_id, name, role_desc, is_active in agents:
        status = "✓" if is_active else "✗"
        print(f"  {status} {agent_id:15} | {name:25} | {role_desc[:50] if role_desc else 'Sin descripción'}")
    
    cursor.close()
    conn.close()
    
    return missing_fields

if __name__ == "__main__":
    missing = check_agent_catalog_structure()
    
    if missing:
        print("\n" + "=" * 80)
        print("⚠️  ACCIÓN REQUERIDA")
        print("=" * 80)
        print("\nFaltan campos en utm_agent_catalog. Se requiere migración SQL:")
        print("\n```sql")
        print("ALTER TABLE utm_agent_catalog")
        for i, (field, field_type) in enumerate(missing):
            comma = "," if i < len(missing) - 1 else ";"
            print(f"  ADD COLUMN {field} {field_type}{comma}")
        print("```")
    else:
        print("\n" + "=" * 80)
        print("✅ TODOS LOS CAMPOS REQUERIDOS EXISTEN")
        print("=" * 80)
