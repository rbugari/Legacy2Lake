#!/usr/bin/env python3
"""Force unlock a project by releasing all process locks"""
import sys
sys.path.insert(0, 'C:/proyectos_dev/UTM')

from apps.api.services.persistence_service import SupabasePersistence
import asyncio

async def force_unlock(project_id: str):
    """Release all locks for a project"""
    db = SupabasePersistence()
    
    print(f"Buscando locks para proyecto: {project_id}")
    
    # Get all active locks
    result = db.client.table('utm_process_locks') \
        .select('*') \
        .eq('project_id', project_id) \
        .eq('status', 'active') \
        .execute()
    
    if not result.data:
        print("No hay locks activos")
        return
    
    print(f"Encontrados {len(result.data)} locks activos:")
    for lock in result.data:
        print(f"   - {lock}")
    
    # Delete all locks (instead of UPDATE to avoid unique constraint issues)
    delete_result = db.client.table('utm_process_locks') \
        .delete() \
        .eq('project_id', project_id) \
        .eq('status', 'active') \
        .execute()
    
    print(f"Locks eliminados: {len(delete_result.data) if delete_result.data else 0}")

if __name__ == "__main__":
    project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
    asyncio.run(force_unlock(project_id))
