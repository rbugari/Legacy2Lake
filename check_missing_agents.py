"""
Verificar qué son agent-b y agent-d
"""
from connect_supabase_dev import get_postgres_connection

def check_missing_agents():
    """Verifica información sobre los agentes faltantes"""
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("=" * 80)
    print("INFORMACIÓN DE AGENTES FALTANTES")
    print("=" * 80)
    
    # Buscar prompts de agent-b y agent-d
    missing_agents = ['agent_b_%', 'agent_d_%']
    
    for pattern in missing_agents:
        agent_id = pattern.split('_')[1]
        print(f"\n{'='*80}")
        print(f"AGENT-{agent_id.upper()}")
        print(f"{'='*80}")
        
        cursor.execute("""
            SELECT prompt_id, LEFT(content, 200) as preview
            FROM utm_prompts
            WHERE prompt_id LIKE %s
            AND tenant_id IS NULL
            AND is_active = TRUE
            ORDER BY prompt_id
            LIMIT 3;
        """, (pattern,))
        
        prompts = cursor.fetchall()
        
        if prompts:
            print(f"\nPrompts encontrados: {len(prompts)}\n")
            for prompt_id, preview in prompts:
                print(f"📄 {prompt_id}")
                print(f"   Preview: {preview}...")
                print()
        else:
            print(f"\nNo se encontraron prompts para este agente")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_missing_agents()
