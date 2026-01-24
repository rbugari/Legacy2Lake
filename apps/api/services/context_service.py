"""
Context Service - Manages user-specific context injection for solutions

Handles CRUD operations for utm_solution_context table which stores
user-editable context that gets injected into agent prompts.
"""

from supabase import Client
from typing import Optional


class ContextService:
    """Service for managing solution-specific user context"""
    
    def __init__(self, supabase_client):
        self.db = supabase_client
    
    async def get_context(
        self, 
        project_id: str, 
        context_type: str
    ) -> dict | None:
        """Get user context for a specific agent/project"""
        result = self.db.table('utm_solution_context')\
            .select('*')\
            .eq('project_id', project_id)\
            .eq('context_type', context_type)\
            .maybe_single()\
            .execute()
        
        return result.data if result.data else None
    
    async def upsert_context(
        self,
        project_id: str,
        context_type: str,
        user_context: str
    ) -> dict:
        """Create or update user context"""
        result = self.db.table('utm_solution_context')\
            .upsert({
                'project_id': project_id,
                'context_type': context_type,
                'user_context': user_context
            }, on_conflict='project_id,context_type')\
            .execute()
        
        return result.data[0] if result.data else None
    
    async def get_all_for_project(self, project_id: str) -> list[dict]:
        """Get all context entries for a project"""
        result = self.db.table('utm_solution_context')\
            .select('*')\
            .eq('project_id', project_id)\
            .execute()
        
        return result.data or []
    
    async def delete_context(
        self,
        project_id: str,
        context_type: str
    ) -> bool:
        """Delete a specific context entry"""
        result = self.db.table('utm_solution_context')\
            .delete()\
            .eq('project_id', project_id)\
            .eq('context_type', context_type)\
            .execute()
        
        return True if result.data else False
