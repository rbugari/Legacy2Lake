"""
Test manual de extracción de esquema con el Pattern 4
"""
import re

# El código que se generó (solo la parte relevante)
code = """
# L2L MODERNIZATION TRACE: DimCustomers Bronze Ingestion (PySpark Delta)
def execute_task(spark, config):
    import pyspark.sql.functions as F
    from delta.tables import DeltaTable

    # [EXTRACT]
    # Schema is unknown; placeholder schema enforced for seven columns as per medulla.
    # Columns: custid, contactname, city, country, address, phone, postalcode
    bronze_table_name = f"{config['bronze_prefix']}DimCustomers"
    bronze_table_path = f"{config['bronze_path']}/{bronze_table_name}"

    enforced_schema = \"\"\"
        custid INT,
        contactname STRING,
        city STRING,
        country STRING,
        address STRING,
        phone STRING,
        postalcode STRING
    \"\"\"
"""

print("\n" + "="*60)
print("TEST PATTERN 4 - Extracción de enforced_schema")
print("="*60)

# Test Pattern 4
pattern4 = r'(?:enforced_schema|schema)\s*=\s*"""(.*?)"""'
match4 = re.search(pattern4, code, re.DOTALL)

if match4:
    print("\n✅ Pattern 4 MATCH encontrado!")
    schema_block = match4.group(1)
    print(f"\nSchema block capturado:")
    print(schema_block)
    
    columns = []
    # Parse each line: col_name TYPE,
    line_pattern = r'^\s*(\w+)\s+([\w\(\)]+)\s*,?\s*$'
    
    print(f"\n📋 Parseando líneas...")
    for line in schema_block.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        print(f"   Línea: '{line}'")
        col_match = re.match(line_pattern, line)
        if col_match:
            col_name = col_match.group(1).lower()
            col_type = col_match.group(2).upper()
            print(f"      ✅ Match: {col_name} -> {col_type}")
            columns.append({
                'name': col_name,
                'type': col_type,
                'nullable': True,
                'is_primary_key': False,
                'is_foreign_key': False
            })
        else:
            print(f"      ❌ No match")
    
    if columns:
        print(f"\n✅ EXTRACCIÓN EXITOSA!")
        print(f"Total columnas: {len(columns)}")
        print(f"\nColumnas extraídas:")
        for col in columns:
            print(f"   - {col['name']}: {col['type']}")
    else:
        print(f"\n❌ No se pudieron extraer columnas")
else:
    print("\n❌ Pattern 4 NO encontró match")

print("\n" + "="*60)
