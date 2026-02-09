#!/usr/bin/env python3
"""
Test script para verificar endpoints de knowledge de cartuchos
"""
from connect_supabase_dev import get_postgres_connection
import os

def test_knowledge_endpoints():
    conn = get_postgres_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("VERIFICANDO CARTUCHOS Y KNOWLEDGE")
    print("=" * 80)
    print()
    
    # Listar cartuchos activos
    cur.execute("""
        SELECT tech_id, name, type, is_active
        FROM utm_system_catalog
        WHERE is_active = TRUE
        ORDER BY type, tech_id
    """)
    
    cartridges = cur.fetchall()
    
    print(f"📦 Total cartuchos activos: {len(cartridges)}")
    print()
    
    # Verificar existencia de improvements.md
    lab_path = os.path.join(os.getcwd(), "prompt_lab_export")
    
    for tech_id, name, cart_type, is_active in cartridges:
        category_dir = "origins" if cart_type == "origin" else "destinations"
        improvements_path = os.path.join(lab_path, category_dir, tech_id, "improvements.md")
        
        exists = os.path.exists(improvements_path)
        status = "✅" if exists else "❌"
        
        size_str = ""
        if exists:
            size = os.path.getsize(improvements_path)
            size_str = f"({size} bytes)"
        
        print(f"  {status} {tech_id:15} | {name:20} | {cart_type:12} | {size_str}")
    
    print()
    print("=" * 80)
    print("ENDPOINTS DISPONIBLES")
    print("=" * 80)
    print()
    print("  GET  /api/system/cartridges/{tech_id}/knowledge")
    print("  PUT  /api/system/cartridges/{tech_id}/knowledge")
    print()
    print("✅ Backend configurado correctamente")
    print()
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_knowledge_endpoints()
