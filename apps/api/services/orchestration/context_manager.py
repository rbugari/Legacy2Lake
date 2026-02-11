"""
Context Manager - Sprint 2 Enhancement
Centralized context sharing between agents with caching and deduplication
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

try:
    from apps.api.utils.logger import logger
except ImportError:
    from utils.logger import logger


class ContextCache:
    """In-memory cache for expensive context computations"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.utcnow() > entry["expires_at"]:
            del self.cache[key]
            return None
        
        logger.debug(f"Cache HIT: {key}", "ContextCache")
        return entry["value"]
    
    def set(self, key: str, value: Any):
        """Set cached value with expiration"""
        self.cache[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.ttl),
            "cached_at": datetime.utcnow()
        }
        logger.debug(f"Cache SET: {key}", "ContextCache")
    
    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        logger.debug("Cache cleared", "ContextCache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "entries": list(self.cache.keys())
        }


class SharedContext:
    """
    Centralized context manager for agent orchestration.
    Reduces redundant computations and improves context propagation.
    """
    
    def __init__(self, project_uuid: str, tenant_id: Optional[str] = None):
        self.project_uuid = project_uuid
        self.tenant_id = tenant_id
        
        # Context data
        self._schema_context: Optional[Dict[str, Any]] = None
        self._topology_context: Optional[Dict[str, Any]] = None
        self._intelligence_context: Optional[Dict[str, Any]] = None
        self._package_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Caching
        self.cache = ContextCache(ttl_seconds=300)  # 5 minutes
        
        # Metrics
        self.context_load_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def set_schema_context(self, schema_context: Dict[str, Any]):
        """Set schema context from Librarian"""
        self._schema_context = schema_context
        self.cache.set("schema_context", schema_context)
        logger.info(f"Schema context set: {len(schema_context.get('tables', []))} tables", "SharedContext")
    
    def get_schema_context(self) -> Optional[Dict[str, Any]]:
        """Get schema context"""
        cached = self.cache.get("schema_context")
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        return self._schema_context
    
    def set_topology_context(self, topology_context: Dict[str, Any]):
        """Set topology context from Topology Architect"""
        self._topology_context = topology_context
        self.cache.set("topology_context", topology_context)
        logger.info(
            f"Topology context set: {len(topology_context.get('dag_execution', []))} phases",
            "SharedContext"
        )
    
    def get_topology_context(self) -> Optional[Dict[str, Any]]:
        """Get topology context"""
        cached = self.cache.get("topology_context")
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        return self._topology_context
    
    def set_intelligence_context(self, intelligence: Dict[str, Any]):
        """Set intelligence context (support + scout)"""
        self._intelligence_context = intelligence
        self.cache.set("intelligence_context", intelligence)
        logger.info("Intelligence context set", "SharedContext")
    
    def get_intelligence_context(self) -> Optional[Dict[str, Any]]:
        """Get intelligence context"""
        cached = self.cache.get("intelligence_context")
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        return self._intelligence_context
    
    def add_package_metadata(self, package_name: str, metadata: Dict[str, Any]):
        """Add metadata for a specific package"""
        self._package_metadata[package_name] = metadata
        self.cache.set(f"package:{package_name}", metadata)
    
    def get_package_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific package"""
        cache_key = f"package:{package_name}"
        cached = self.cache.get(cache_key)
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        return self._package_metadata.get(package_name)
    
    def get_neighbor_packages(self, package_name: str, max_neighbors: int = 10) -> List[Dict[str, Any]]:
        """
        Get neighboring packages for context window.
        Useful for Agent C to understand related transformations.
        """
        cache_key = f"neighbors:{package_name}"
        cached = self.cache.get(cache_key)
        if cached:
            self.cache_hits += 1
            return cached
        
        # Find packages in same phase or with dependencies
        topology = self.get_topology_context()
        if not topology:
            return []
        
        neighbors = []
        current_phase = None
        
        # Find current package's phase
        for phase in topology.get("dag_execution", []):
            if package_name in phase.get("packages", []):
                current_phase = phase
                break
        
        if current_phase:
            # Get packages from same phase
            for pkg in current_phase.get("packages", [])[:max_neighbors]:
                if pkg != package_name and pkg in self._package_metadata:
                    neighbors.append(self._package_metadata[pkg])
        
        self.cache.set(cache_key, neighbors)
        self.cache_misses += 1
        return neighbors
    
    def build_agent_context(
        self, 
        package_name: str,
        include_neighbors: bool = True,
        include_intelligence: bool = True
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for agent execution.
        Consolidates all relevant context for a package.
        """
        context = {
            "project_uuid": self.project_uuid,
            "package": self.get_package_metadata(package_name),
            "schema": self.get_schema_context(),
            "topology": self.get_topology_context()
        }
        
        if include_neighbors:
            context["neighbors"] = self.get_neighbor_packages(package_name)
        
        if include_intelligence:
            intel = self.get_intelligence_context()
            if intel:
                context["support_intelligence"] = intel.get("support_intel", [])
                context["scout_assessment"] = intel.get("scout_assessment", {})
        
        self.context_load_count += 1
        return context
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context manager statistics"""
        return {
            "context_loads": self.context_load_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0
            ),
            "cached_packages": len(self._package_metadata),
            "cache_details": self.cache.get_stats()
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.cache.clear()
        logger.info("Shared context cache cleared", "SharedContext")
    
    def summary(self) -> str:
        """Get human-readable summary"""
        stats = self.get_stats()
        return (
            f"Context Stats: {stats['context_loads']} loads, "
            f"{stats['cache_hits']} hits, "
            f"{stats['cache_misses']} misses "
            f"({stats['cache_hit_rate']:.1%} hit rate)"
        )
