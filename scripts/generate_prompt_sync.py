import os
import json
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load production environment
# Using hardcoded project URL for wdmlnvppkhjjeuiutnjl as per previous successful calls
PROD_SUPABASE_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
# Need to get Service Role Key from environment or user might have provided it
# Since I'm an agent with MCP access, I can just use the MCP tool directly or 
# write a script that I execute if I have the key.
# Actually, I'll use the MCP tool mcp_supabase-prod_execute_sql which is much easier and safer.

def get_local_prompts():
    prompt_dir = r"c:\proyectos_dev\UTM\apps\api\prompts"
    prompts = {}
    for filename in os.listdir(prompt_dir):
        if filename.endswith(".md"):
            prompt_id = filename.replace(".md", "")
            with open(os.path.join(prompt_dir, filename), "r", encoding="utf-8") as f:
                content = f.read()
                prompts[prompt_id] = content
    return prompts

def generate_update_sql(prompts):
    sql_statements = []
    
    # 1. Cleanup placeholder tenant overrides (length < 100)
    sql_statements.append("-- Cleanup placeholder tenant overrides")
    sql_statements.append("DELETE FROM utm_prompts WHERE tenant_id IS NOT NULL AND length(content) < 100;")
    
    # 2. Update/Insert Global Prompts
    sql_statements.append("-- Sync Global Prompts")
    for prompt_id, content in prompts.items():
        # Escape single quotes for SQL
        escaped_content = content.replace("'", "''")
        stmt = f"""
INSERT INTO utm_prompts (prompt_id, content, version_number, is_active, tenant_id)
VALUES ('{prompt_id}', '{escaped_content}', 1, true, NULL)
ON CONFLICT (prompt_id, tenant_id, version_number)
DO UPDATE SET content = EXCLUDED.content, is_active = true;
"""
        sql_statements.append(stmt)
        
    return "\n".join(sql_statements)

if __name__ == "__main__":
    prompts = get_local_prompts()
    sql = generate_update_sql(prompts)
    with open("sync_prompts.sql", "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"Generated sync_prompts.sql with {len(prompts)} prompts.")
