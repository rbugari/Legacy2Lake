"""
Triage Router  
Handles discovery, triage, and asset analysis operations.
This is a major router with complex logic extracted from main.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

from routers.dependencies import get_db
from services.persistence_service import SupabasePersistence, PersistenceService
from services.discovery_service import DiscoveryService
from services.agent_a_service import AgentAService

router = APIRouter(tags=["Triage & Discovery"])


# --- Models ---

class TriageParams(BaseModel):
    system_prompt: Optional[str] = None
    user_context: Optional[str] = None


class AssetContextPayload(BaseModel):
    source_path: str
    notes: str
    rules: Optional[Dict[str, Any]] = None


# --- Discovery Endpoints ---

@router.get("/discovery/project/{project_id}")
async def get_discovery_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns all assets and the system prompt for a project."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u
        
    assets = await db.get_project_assets(project_uuid)
    meta = await db.get_project_metadata(project_uuid)
    
    # Fallback to default Triage prompt if not customized for project
    prompt = meta.get("prompt") if meta else None
    if not prompt:
        agent_a = AgentAService()
        prompt = agent_a._load_prompt()
        
    return {
        "assets": assets,
        "prompt": prompt
    }


@router.get("/discovery/status/{project_id}")
async def get_discovery_status(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the discovery/triage status for a project."""
    metadata = await db.get_project_metadata(project_id)
    if not metadata:
        uuid = await db.get_project_id_by_name(project_id)
        if uuid: 
            metadata = await db.get_project_metadata(uuid)

    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": metadata.get("status", "TRIAGE"),
        "stage": metadata.get("stage", "1"),
        "is_ready": metadata.get("status") != "TRIAGE" or metadata.get("stage") != "1"
    }


# --- Triage Endpoint ---

@router.post("/projects/{project_id}/triage")
async def run_triage(project_id: str, params: TriageParams, db: SupabasePersistence = Depends(get_db)):
    """Re-runs the triage (discovery) process using agentic reasoning."""
    
    # Resolve UUID and Name correctly
    project_uuid = project_id
    project_folder = project_id
    
    if "-" in project_id:  # Heuristic: if UUID, get name for folder
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
    else:  # If name, get UUID for DB operations
        resolved_uuid = await db.get_project_id_by_name(project_id)
        if resolved_uuid:
            project_uuid = resolved_uuid

    # GOVERNANCE CHECK: TRIAGE is only allowed in TRIAGE mode.
    current_status = await db.get_project_status(project_uuid)
    if current_status == "DRAFTING":
        return {
            "assets": [],
            "log": "[ERROR] Project is in DRAFTING mode. Triage is locked. Unlock project to modify scope.",
            "error": "Project is in DRAFTING mode"
        }

    log_lines = []
    log_lines.append(f"[Start] Initializing Shift-T Triage Agent for Project: {project_id} (Folder: {project_folder})")
    
    # Helper to persist log incrementally
    def _log(msg: str):
        log_lines.append(msg)
        try:
            path = PersistenceService.ensure_solution_dir(project_folder)
            with open(os.path.join(path, "triage.log"), "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        except:
            pass
            
    # Clear previous log
    try:
        path = PersistenceService.ensure_solution_dir(project_folder)
        with open(os.path.join(path, "triage.log"), "w", encoding="utf-8") as f:
            f.write(f"--- Triage Started for {project_id} ---\n")
    except:
        pass
    
    _log(f"[Start] Initializing Shift-T Triage Agent for Project: {project_id}")

    # 1. Deep Scan (The Scanner / Pre-processing)
    _log("[Step 1] Running Deep Scanner (Python Engine)...")
    
    # Fetch persistent human context
    user_context = await db.get_project_context(project_uuid)
    if user_context:
        _log(f"   > Found {len(user_context)} human context overrides. Injecting into scanner...")
        
    manifest = DiscoveryService.generate_manifest(project_folder, user_context=user_context)
    manifest["project_id"] = project_uuid
    
    file_count = len(manifest["file_inventory"])
    tech_stats = manifest["tech_stats"]
    _log(f"   > Scanned {file_count} files.")
    _log(f"   > Tech Stack Detected: {tech_stats}")
    
    # 2. Agent A Analysis (The Detective)
    _log("[Step 2] Invoking Agent A (Mesh Architect)...")
    if params.system_prompt:
        _log("   > Applying custom System Prompt override.")
    
    agent_a = AgentAService()
    try:
        prompt = params.system_prompt
        if params.user_context:
            prompt = (prompt or "") + f"\n\n[USER CONTEXT CONSTRAINTS]:\n{params.user_context}"
            
        result = await agent_a.analyze_manifest(manifest, system_prompt_override=prompt)
        
        if "error" in result:
            _log(f"[ERROR] Agent A failed: {result['error']}")
            return {"log": "\n".join(log_lines), "error": result['error']}
             
        rf_nodes = result.get("mesh_graph", {}).get("nodes", [])
        rf_edges = result.get("mesh_graph", {}).get("edges", [])
        
        # Auto-Promotion Fallback: Ensure CORE-likely physical assets are in the graph
        for item in manifest["file_inventory"]:
            if item["name"].lower() in ['triage.log', 'thumbs.db', '.ds_store', 'desktop.ini']:
                continue
                 
            if not any(n["id"] == item["path"] for n in rf_nodes):
                ext = item["name"].split('.')[-1].lower() if '.' in item["name"] else ''
                if ext in ['dtsx', 'sql', 'py', 'spark', 'scala']:
                    rf_nodes.append({
                        "id": item["path"],
                        "label": item["name"],
                        "category": "CORE",
                        "complexity": "LOW",
                        "confidence": 0.5,
                        "business_entity": "SYSTEM_INFERRED",
                        "target_name": item["name"]
                    })
        
        _log(f"   > Analysis Complete. Total Nodes (AI + Inferred): {len(rf_nodes)}")
        
    except Exception as e:
        _log(f"[CRITICAL] Architecture Analysis Failed: {e}")
        return {"log": "\n".join(log_lines), "error": str(e)}

    # 3. Persistence (Supabase)
    _log("[Step 3] Persisting Mesh Graph and Discovered Assets...")
    
    db_assets = []
    for item in manifest["file_inventory"]:
        agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
        category = agent_node["category"] if agent_node else "IGNORED" 
        if not agent_node:
            category = DiscoveryService._map_extension_to_type(
                item["name"].split('.')[-1].lower() if '.' in item["name"] else 'none'
            )

        db_assets.append({
            "filename": item["name"],
            "type": category,
            "source_path": item["path"],
            "metadata": {**item.get("metadata", {}), "size": item["size"]},
            "selected": True if category != "IGNORED" else False
        })
    
    saved_assets = await db.batch_save_assets(project_uuid, db_assets)
    asset_map = {a["source_path"]: (a.get("id") or a.get("object_id")) for a in saved_assets}

    # Transform Agent Nodes to ReactFlow Nodes
    final_nodes = []
    graph_eligible = [n for n in rf_nodes if n.get("category") != "IGNORED"]
    
    for i, n in enumerate(graph_eligible):
        n_uuid = asset_map.get(n["id"], n["id"])
        
        final_nodes.append({
            "id": n_uuid,
            "type": "custom", 
            "position": {"x": 200 + (i % 5 * 250), "y": 100 + (i // 5 * 150)},
            "data": { 
                "label": n["label"], 
                "category": n.get("category", "CORE"),
                "complexity": n.get("complexity", "LOW"),
                "status": "pending"
            }
        })
        
    final_edges = []
    for e in rf_edges:
        src_uid = asset_map.get(e['from'], e['from'])
        tgt_uid = asset_map.get(e['to'], e['to'])
        
        final_edges.append({
            "id": f"e{src_uid}-{tgt_uid}",
            "source": src_uid,
            "target": tgt_uid,
            "label": e.get('type', 'SEQUENTIAL')
        })
        
    await db.save_project_layout(project_uuid, {"nodes": final_nodes, "edges": final_edges})
    _log("[Success] Graph and Assets saved to database.")
    
    # Map back to assets list for the frontend
    final_assets = []
    for item in manifest["file_inventory"]:
        agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
        item_uuid = asset_map.get(item["path"])
        
        if item_uuid:
            final_assets.append({
                "id": item_uuid,
                "name": item["name"],
                "type": agent_node["category"] if agent_node else "CORE",
                "status": "analyzed" if agent_node else "unlinked",
                "tags": str(item["signatures"]),
                "selected": True if (agent_node and agent_node["category"] != "IGNORED") else False,
                "dependencies": []
            })

    return {
        "assets": final_assets,
        "nodes": final_nodes,
        "edges": final_edges,
        "log": "\n".join(log_lines)
    }


# --- Graph Sync ---

@router.post("/projects/{project_id}/sync-graph")
async def sync_project_graph(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Rebuilds the graph layout based on assets currently marked as 'selected'."""
    project_uuid = project_id
    if len(project_id) < 32:
        project_uuid = await db.get_project_id_by_name(project_id)

    if not project_uuid:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Fetch assets marked as selected
    assets = await db.get_project_assets(project_uuid)
    selected_assets = [a for a in assets if a.get("selected")]

    # 2. Fetch current layout to preserve positions for existing nodes
    current_layout = await db.get_project_layout(project_uuid)
    existing_nodes = {n["id"]: n for n in current_layout.get("nodes", [])}
    existing_edges = current_layout.get("edges", [])

    # 3. Build new node list
    final_nodes = []
    for i, asset in enumerate(selected_assets):
        asset_id = asset["id"]
        
        if asset_id in existing_nodes:
            final_nodes.append(existing_nodes[asset_id])
        else:
            final_nodes.append({
                "id": asset_id,
                "type": "custom",
                "position": {"x": 200 + (len(final_nodes) % 5 * 250), "y": 100 + (len(final_nodes) // 5 * 150)},
                "data": {
                    "label": asset["filename"],
                    "category": asset.get("type", "CORE"),
                    "complexity": asset.get("metadata", {}).get("complexity", "LOW"),
                    "status": "pending"
                }
            })

    # 4. Filter edges
    node_ids = {n["id"] for n in final_nodes}
    final_edges = [e for e in existing_edges if e["source"] in node_ids and e["target"] in node_ids]

    # 5. Save and return
    new_layout = {"nodes": final_nodes, "edges": final_edges}
    await db.save_project_layout(project_uuid, new_layout)

    return {
        "success": True,
        "nodes": final_nodes,
        "edges": final_edges
    }


# --- Asset Context ---

@router.patch("/projects/{project_id}/prompt")
async def update_project_prompt(project_id: str, payload: Dict[str, str], db: SupabasePersistence = Depends(get_db)):
    """Updates the customized system prompt for a project."""
    success = await db.update_project_prompt(project_id, payload.get("prompt"))
    return {"success": success}


@router.patch("/assets/{asset_id}")
async def patch_asset(asset_id: str, updates: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Updates asset metadata (type, selected status)."""
    success = await db.update_asset_metadata(asset_id, updates)
    return {"success": success}


@router.post("/projects/{project_id}/context")
async def save_context(project_id: str, payload: AssetContextPayload, db: SupabasePersistence = Depends(get_db)):
    """Saves human context for an asset."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u

    success = await db.save_asset_context(
        project_uuid,
        payload.source_path,
        payload.notes,
        payload.rules
    )
    return {"success": success}


@router.get("/projects/{project_id}/context")
async def get_context(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Retrieves all context entries for a project."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u
            
    context = await db.get_project_context(project_uuid)
    return {"context": context}
