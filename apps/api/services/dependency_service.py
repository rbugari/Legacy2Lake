"""
Dependency Resolver Service - Calculates execution order for assets
Phase A - Dependency Management

Uses topological sorting to determine the correct execution order
based on asset dependencies.
"""

from typing import List, Dict, Set, Optional
from collections import defaultdict, deque
from supabase import Client

class DependencyService:
    """Service for resolving asset dependencies and execution order"""
    
    def __init__(self, supabase_client: Client):
        self.db = supabase_client
    
    async def get_dependencies(self, project_id: str) -> Dict[str, List[str]]:
        """
        Get dependency graph for a project.
        Returns: {asset_id: [list of asset_ids it depends on]}
        """
        # Fetch all assets with their dependencies
        result = self.db.table('utm_objects')\
            .select('object_id, metadata')\
            .eq('project_id', project_id)\
            .execute()
        
        graph = {}
        for row in (result.data or []):
            asset_id = row['object_id']
            metadata = row.get('metadata') or {}
            depends_on = metadata.get('depends_on') or []
            graph[asset_id] = depends_on if isinstance(depends_on, list) else []
        
        return graph
    
    def resolve_execution_order(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Topological sort to determine execution order.
        Returns ordered list of asset_ids.
        Raises ValueError if circular dependency detected.
        """
        # Calculate in-degrees
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Queue of nodes with no dependencies
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for dependent nodes
            for other_node in graph:
                if node in graph[other_node]:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        # Check for cycles
        if len(result) != len(graph):
            raise ValueError("Circular dependency detected in asset graph")
        
        return result
    
    def get_dependency_levels(self, graph: Dict[str, List[str]]) -> Dict[int, List[str]]:
        """
        Group assets by dependency level.
        Level 0 = no dependencies (can run in parallel)
        Level N = depends on level N-1
        """
        levels = defaultdict(list)
        processed = set()
        
        def get_level(node: str) -> int:
            if node in processed:
                # Already calculated
                for lvl, nodes in levels.items():
                    if node in nodes:
                        return lvl
            
            deps = graph.get(node, [])
            if not deps:
                levels[0].append(node)
                processed.add(node)
                return 0
            
            max_dep_level = max(get_level(dep) for dep in deps if dep in graph)
            level = max_dep_level + 1
            levels[level].append(node)
            processed.add(node)
            return level
        
        for node in graph:
            get_level(node)
        
        return dict(levels)
    
    async def detect_cycles(self, project_id: str) -> Optional[List[str]]:
        """
        Detect circular dependencies.
        Returns None if no cycle, or list of assets in cycle if found.
        """
        graph = await self.get_dependencies(project_id)
        
        try:
            self.resolve_execution_order(graph)
            return None  # No cycle
        except ValueError:
            # Find the cycle
            visited = set()
            rec_stack = set()
            cycle = []
            
            def dfs(node: str, path: List[str]) -> bool:
                visited.add(node)
                rec_stack.add(node)
                path.append(node)
                
                for dep in graph.get(node, []):
                    if dep not in visited:
                        if dfs(dep, path):
                            return True
                    elif dep in rec_stack:
                        # Cycle found
                        cycle.extend(path[path.index(dep):])
                        return True
                
                rec_stack.remove(node)
                return False
            
            for node in graph:
                if node not in visited:
                    if dfs(node, []):
                        return cycle
            
            return []  # Shouldn't reach here
    
    async def get_execution_plan(self, project_id: str) -> Dict:
        """
        Get complete execution plan with order and levels.
        """
        graph = await self.get_dependencies(project_id)
        
        # Check for cycles
        cycle = await self.detect_cycles(project_id)
        if cycle:
            return {
                "error": "Circular dependency detected",
                "cycle": cycle,
                "execution_order": [],
                "levels": {}
            }
        
        # Calculate order and levels
        execution_order = self.resolve_execution_order(graph)
        levels = self.get_dependency_levels(graph)
        
        return {
            "execution_order": execution_order,
            "levels": levels,
            "total_assets": len(execution_order),
            "max_level": max(levels.keys()) if levels else 0
        }
