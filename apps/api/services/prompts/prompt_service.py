"""
Prompt Service - v4.0 Zero-Hardcode Core

Manages dynamic prompts stored in database (utm_prompts table).
Replaces hardcoded templates with database-driven prompt system.

Features:
- Load prompts from database by agent, tech stack, and pattern
- Global prompts (no tenant customization in v4.0)
- Caching for performance
- Version tracking via automatic trigger

Author: Legacy2Lake Engineering
Date: February 14, 2026
Version: v4.0.0
"""

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import hashlib


class Prompt:
    """Represents a single prompt from the database"""
    
    def __init__(self, data: Dict[str, Any]):
        self.prompt_id: str = data.get("prompt_id", "")
        self.content: str = data.get("content", "")
        self.tech_stack: Optional[str] = data.get("tech_stack")
        self.pattern_type: Optional[str] = data.get("pattern_type")
        self.agent_id: Optional[str] = data.get("agent_id")
        self.is_active: bool = data.get("is_active", True)
        self.metadata: Dict[str, Any] = data.get("metadata", {})
        self.created_at: str = data.get("created_at", "")
        self.updated_at: str = data.get("updated_at", "")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "prompt_id": self.prompt_id,
            "content": self.content,
            "tech_stack": self.tech_stack,
            "pattern_type": self.pattern_type,
            "agent_id": self.agent_id,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def get_content_hash(self) -> str:
        """Get SHA256 hash of content for versioning"""
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()


class PromptService:
    """
    Service for managing dynamic prompts from database.
    
    v4.0: Global prompts only (no tenant customization).
    Tenant customization will be added in v5.0+.
    """
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Initialize Prompt Service
        
        Args:
            tenant_id: Not used in v4.0 (prompts are global)
            client_id: Not used in v4.0 (prompts are global)
        """
        self.tenant_id = tenant_id  # Reserved for v5.0+
        self.client_id = client_id  # Reserved for v5.0+
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        
        # In-memory cache (will be replaced with Redis in production)
        self._cache: Dict[str, Prompt] = {}
        self._cache_ttl: int = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def get_prompt(
        self,
        prompt_id: str,
        use_cache: bool = True
    ) -> Optional[Prompt]:
        """
        Get a single prompt by ID
        
        Args:
            prompt_id: Unique prompt identifier (e.g., 'agent_c_bronze_pyspark')
            use_cache: Whether to use cached version (default: True)
            
        Returns:
            Prompt object or None if not found
        """
        try:
            # Check cache first
            if use_cache and self._is_cached(prompt_id):
                logger.info(
                    f"[PromptService] Cache hit for prompt: {prompt_id}",
                    "PromptService"
                )
                return self._cache[prompt_id]
            
            # Query database
            logger.info(
                f"[PromptService] Loading prompt from DB: {prompt_id}",
                "PromptService"
            )
            
            response = (
                self.db.client
                .table("utm_prompts")
                .select("*")
                .eq("prompt_id", prompt_id)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
            
            if response.data:
                prompt = Prompt(response.data)
                self._cache_prompt(prompt_id, prompt)
                return prompt
            else:
                logger.warning(
                    f"[PromptService] Prompt not found: {prompt_id}",
                    "PromptService"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"[PromptService] Error loading prompt {prompt_id}: {e}",
                "PromptService"
            )
            # Return None on error instead of raising
            return None
    
    async def get_active_prompt(
        self,
        agent_id: Optional[str] = None,
        tech_stack: Optional[str] = None,
        pattern_type: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Prompt]:
        """
        Get active prompt by filters (agent, tech_stack, pattern)
        
        Args:
            agent_id: Agent identifier (e.g., 'agent-c')
            tech_stack: Technology (e.g., 'pyspark', 'snowflake')
            pattern_type: Pattern type (e.g., 'bronze', 'silver', 'gold')
            use_cache: Whether to use cached version (default: True)
            
        Returns:
            First matching Prompt object or None if not found
        """
        try:
            # Build cache key
            cache_key = self._build_cache_key(agent_id, tech_stack, pattern_type)
            
            # Check cache first
            if use_cache and self._is_cached(cache_key):
                logger.info(
                    f"[PromptService] Cache hit for prompt: {cache_key}",
                    "PromptService"
                )
                return self._cache[cache_key]
            
            # Build query
            logger.info(
                f"[PromptService] Loading prompt from DB: agent={agent_id}, tech={tech_stack}, pattern={pattern_type}",
                "PromptService"
            )
            
            query = self.db.client.table("utm_prompts").select("*").eq("is_active", True)
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            if tech_stack:
                query = query.eq("tech_stack", tech_stack)
            if pattern_type:
                query = query.eq("pattern_type", pattern_type)
            
            response = query.limit(1).execute()
            
            if response.data and len(response.data) > 0:
                prompt = Prompt(response.data[0])
                self._cache_prompt(cache_key, prompt)
                return prompt
            else:
                logger.warning(
                    f"[PromptService] No active prompt found for: agent={agent_id}, tech={tech_stack}, pattern={pattern_type}",
                    "PromptService"
                )
                return None
                
        except Exception as e:
            logger.error(
                f"[PromptService] Error loading prompt: {e}",
                "PromptService"
            )
            raise
    
    async def list_prompts(
        self,
        agent_id: Optional[str] = None,
        tech_stack: Optional[str] = None,
        pattern_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Prompt]:
        """
        List prompts with optional filters
        
        Args:
            agent_id: Filter by agent
            tech_stack: Filter by technology
            pattern_type: Filter by pattern
            is_active: Filter by active status
            
        Returns:
            List of Prompt objects
        """
        try:
            query = self.db.client.table("utm_prompts").select("*")
            
            if agent_id:
                query = query.eq("agent_id", agent_id)
            if tech_stack:
                query = query.eq("tech_stack", tech_stack)
            if pattern_type:
                query = query.eq("pattern_type", pattern_type)
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            response = query.order("prompt_id").execute()
            
            prompts = [Prompt(data) for data in response.data]
            
            logger.info(
                f"[PromptService] Listed {len(prompts)} prompts",
                "PromptService"
            )
            
            return prompts
            
        except Exception as e:
            logger.error(
                f"[PromptService] Error listing prompts: {e}",
                "PromptService"
            )
            raise
    
    async def create_prompt(
        self,
        prompt_id: str,
        content: str,
        tech_stack: Optional[str] = None,
        pattern_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> Prompt:
        """
        Create a new prompt (ADMIN only)
        
        Args:
            prompt_id: Unique identifier
            content: Prompt template content
            tech_stack: Target technology
            pattern_type: Pattern type
            agent_id: Agent that uses this prompt
            metadata: Additional metadata
            created_by: User ID who created the prompt
            
        Returns:
            Created Prompt object
        """
        try:
            data = {
                "prompt_id": prompt_id,
                "content": content,
                "tech_stack": tech_stack,
                "pattern_type": pattern_type,
                "agent_id": agent_id,
                "metadata": metadata or {},
                "created_by": created_by,
                "is_active": True
            }
            
            response = (
                self.db.client
                .table("utm_prompts")
                .insert(data)
                .execute()
            )
            
            prompt = Prompt(response.data[0])
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(
                f"[PromptService] Created prompt: {prompt_id}",
                "PromptService"
            )
            
            return prompt
            
        except Exception as e:
            logger.error(
                f"[PromptService] Error creating prompt {prompt_id}: {e}",
                "PromptService"
            )
            raise
    
    async def update_prompt(
        self,
        prompt_id: str,
        content: Optional[str] = None,
        tech_stack: Optional[str] = None,
        pattern_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        updated_by: Optional[str] = None
    ) -> Prompt:
        """
        Update an existing prompt (ADMIN only)
        
        Note: Update trigger will automatically save version to utm_prompts_history
        
        Args:
            prompt_id: Prompt to update
            content: New content (if provided)
            tech_stack: New tech_stack (if provided)
            pattern_type: New pattern_type (if provided)
            agent_id: New agent_id (if provided)
            metadata: New metadata (if provided)
            is_active: New active status (if provided)
            updated_by: User ID who updated the prompt
            
        Returns:
            Updated Prompt object
        """
        try:
            update_data = {}
            
            if content is not None:
                update_data["content"] = content
            if tech_stack is not None:
                update_data["tech_stack"] = tech_stack
            if pattern_type is not None:
                update_data["pattern_type"] = pattern_type
            if agent_id is not None:
                update_data["agent_id"] = agent_id
            if metadata is not None:
                update_data["metadata"] = metadata
            if is_active is not None:
                update_data["is_active"] = is_active
            if updated_by is not None:
                update_data["updated_by"] = updated_by
            
            if not update_data:
                raise ValueError("No fields to update")
            
            response = (
                self.db.client
                .table("utm_prompts")
                .update(update_data)
                .eq("prompt_id", prompt_id)
                .execute()
            )
            
            if not response.data:
                raise ValueError(f"Prompt not found: {prompt_id}")
            
            prompt = Prompt(response.data[0])
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(
                f"[PromptService] Updated prompt: {prompt_id}",
                "PromptService"
            )
            
            return prompt
            
        except Exception as e:
            logger.error(
                f"[PromptService] Error updating prompt {prompt_id}: {e}",
                "PromptService"
            )
            raise
    
    async def delete_prompt(self, prompt_id: str) -> bool:
        """
        Delete a prompt (ADMIN only)
        
        Note: Consider using soft delete (is_active=false) instead
        
        Args:
            prompt_id: Prompt to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            response = (
                self.db.client
                .table("utm_prompts")
                .delete()
                .eq("prompt_id", prompt_id)
                .execute()
            )
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(
                f"[PromptService] Deleted prompt: {prompt_id}",
                "PromptService"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"[PromptService] Error deleting prompt {prompt_id}: {e}",
                "PromptService"
            )
            raise
    
    async def get_prompt_history(
        self,
        prompt_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a prompt (ADMIN only, read-only)
        
        Args:
            prompt_id: Prompt to get history for
            limit: Maximum number of history records to return
            
        Returns:
            List of history records (most recent first)
        """
        try:
            response = (
                self.db.client
                .table("utm_prompts_history")
                .select("*")
                .eq("prompt_id", prompt_id)
                .order("changed_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            logger.info(
                f"[PromptService] Retrieved {len(response.data)} history records for: {prompt_id}",
                "PromptService"
            )
            
            return response.data
            
        except Exception as e:
            logger.error(
                f"[PromptService] Error retrieving history for {prompt_id}: {e}",
                "PromptService"
            )
            raise
    
    # Cache management methods
    
    def _build_cache_key(
        self,
        agent_id: Optional[str],
        tech_stack: Optional[str],
        pattern_type: Optional[str]
    ) -> str:
        """Build cache key from filters"""
        parts = []
        if agent_id:
            parts.append(f"agent:{agent_id}")
        if tech_stack:
            parts.append(f"tech:{tech_stack}")
        if pattern_type:
            parts.append(f"pattern:{pattern_type}")
        return "|".join(parts) if parts else "default"
    
    def _is_cached(self, key: str) -> bool:
        """Check if a key is in cache and not expired"""
        if key not in self._cache:
            return False
        
        timestamp = self._cache_timestamps.get(key)
        if not timestamp:
            return False
        
        age = (datetime.now() - timestamp).total_seconds()
        return age < self._cache_ttl
    
    def _cache_prompt(self, key: str, prompt: Prompt):
        """Cache a prompt"""
        self._cache[key] = prompt
        self._cache_timestamps[key] = datetime.now()
    
    def _invalidate_cache(self):
        """Clear all cached prompts"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("[PromptService] Cache invalidated", "PromptService")
    
    def clear_cache(self):
        """Public method to clear cache"""
        self._invalidate_cache()
