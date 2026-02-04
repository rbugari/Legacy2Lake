import json

def generate_inserts(table_name, data):
    if not data:
        return ""
    
    columns = data[0].keys()
    col_str = ", ".join(columns)
    
    inserts = []
    for row in data:
        values = []
        for col in columns:
            val = row[col]
            if val is None:
                values.append("NULL")
            elif isinstance(val, bool):
                values.append(str(val).lower())
            elif isinstance(val, (int, float)):
                values.append(str(val))
            elif isinstance(val, dict):
                values.append(f"'{json.dumps(val)}'::jsonb")
            else:
                # Escape single quotes
                val_escaped = str(val).replace("'", "''")
                values.append(f"'{val_escaped}'")
        
        insert = f"INSERT INTO {table_name} ({col_str}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING;"
        inserts.append(insert)
    
    return "\n".join(inserts)

# Load data files (I'll process them manually here for now or read from a combined file)
# Since I'm an LLM, I'll just write the final SQL using this logic.
