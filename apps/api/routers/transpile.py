"""
Transpile & Orchestration Router
Handles code generation, transpilation, and migration orchestration.
Migrated from main.py for better modularity.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

from routers.dependencies import get_db
from services.persistence_service import SupabasePersistence, PersistenceService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.migration_orchestrator import MigrationOrchestrator

router = APIRouter(prefix="/transpile", tags=["Transpilation & Orchestration"])


# --- Models ---

class TranspileRequest(BaseModel):
    node_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class TranspileAllRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class OptimizeRequest(BaseModel):
    code: str
    optimizations: Optional[List[str]] = []
    context: Optional[Dict[str, Any]] = None


# --- Single Task Transpilation ---

@router.post("/task")
async def transpile_task(payload: TranspileRequest):
    """Chain Agent C (Interpreter) and Agent F (Critic) for a robust result."""
    node_data = payload.node_data
    context = payload.context or {}
    
    # 1. Generate initial code (Agent C)
    agent_c = AgentCService()
    c_result = await agent_c.transpile_task(node_data, context)
    
    if "error" in c_result:
        return c_result

    # 2. Audit and Optimize (Agent F)
    agent_f = AgentFService()
    f_result = await agent_f.review_code(node_data, c_result["pyspark_code"])
    
    # 3. Persistence (Local & Supabase)
    solution_name = context.get("solution_name", "DefaultProject")
    task_name = node_data.get("name", "UnnamedTask")
    
    local_path = PersistenceService.save_transformation(
        solution_name, 
        task_name, 
        f_result.get("optimized_code") or c_result["pyspark_code"]
    )
    
    # 4. Persistence (Supabase)
    asset_id = context.get("asset_id")
    if asset_id:
        db = SupabasePersistence()
        await db.save_transformation(
            asset_id,
            node_data.get("description", ""),
            f_result.get("optimized_code") or c_result["pyspark_code"]
        )

    return {
        "interpreter": c_result,
        "critic": f_result,
        "final_code": f_result.get("optimized_code") or c_result["pyspark_code"],
        "saved_at": local_path
    }


# --- Batch Transpilation ---

@router.post("/all")
async def transpile_all(payload: TranspileAllRequest):
    """Iteratively transpile all nodes in a mesh."""
    nodes = payload.nodes
    context = payload.context or {}
    
    results = []
    agent_c = AgentCService()
    agent_f = AgentFService()
    db = SupabasePersistence()
    
    solution_name = context.get("solution_name", "BulkProject")
    asset_id = context.get("asset_id")

    for node in nodes:
        node_data = node.get("data", {})
        # Skip purely decorative or empty nodes
        if not node_data.get("label"):
            continue
            
        # 1. Generate
        c_res = await agent_c.transpile_task(node_data, context)
        if "error" in c_res:
            results.append({"node": node_data.get("label"), "status": "FAILED", "error": c_res["error"]})
            continue
            
        # 2. Audit
        f_res = await agent_f.review_code(node_data, c_res["pyspark_code"])
        final_code = f_res.get("optimized_code") or c_res["pyspark_code"]
        
        # 3. Save Local
        local_path = PersistenceService.save_transformation(
            solution_name,
            node_data.get("name", node_data.get("label")),
            final_code
        )
        
        # 4. Save Supabase
        if asset_id:
            await db.save_transformation(
                asset_id,
                node_data.get("description", ""),
                final_code
            )
        
        results.append({
            "node": node_data.get("label"),
            "status": "SUCCESS",
            "score": f_res.get("score"),
            "path": local_path
        })
        
    return {"summary": results, "solution_path": os.path.join(PersistenceService.BASE_DIR, solution_name)}


# --- Optimization ---

@router.post("/optimize")
async def optimize_task_code(payload: OptimizeRequest):
    """Re-runs Agent F with specific optimization flags."""
    code = payload.code
    optimizations = payload.optimizations or []
    
    if not code:
        return {"error": "No code provided"}
        
    agent_f = AgentFService()
    result = await agent_f.review_code({"optimizations": optimizations}, code)
    
    return {
        "original": code,
        "optimized": result.get("optimized_code") or code,
        "score": result.get("score"),
        "suggestions": result.get("suggestions", [])
    }


# --- Full Migration Orchestration ---

@router.post("/orchestrate")
async def trigger_orchestration(payload: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Triggers the full Migration Orchestrator (Agents C -> F -> G)."""
    print(f"DEBUG: Entering trigger_orchestration with payload: {payload}")
    project_id = payload.get("project_id")
    limit = payload.get("limit", 0)
    
    if not project_id:
        return {"error": "project_id is required"}
        
    # 1. Resolve Project Name
    project_name = project_id
    if "-" in project_id:
        print(f"DEBUG: Resolving project name for ID: {project_id}")
        n = await db.get_project_name_by_id(project_id)
        print(f"DEBUG: Resolved project name: {n}")
        if n: 
            project_name = n

    print(f"DEBUG: Instantiating MigrationOrchestrator for {project_name} (UUID: {project_id})")
    orchestrator = MigrationOrchestrator(
        project_name, 
        project_uuid=project_id, 
        tenant_id=db.tenant_id, 
        client_id=db.client_id
    )

    print("DEBUG: Running full migration...")
    result = await orchestrator.run_full_migration(limit=limit)
    print("DEBUG: Migration complete.")
    return result
