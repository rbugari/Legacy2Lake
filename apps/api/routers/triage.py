"""
Triage Router  
Handles discovery, triage, and asset analysis operations.
This is a major router with complex logic extracted from main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import uuid

from routers.dependencies import get_db, get_identity
from services.persistence_service import SupabasePersistence, PersistenceService
from services.discovery_service import DiscoveryService
from services.agent_a_service import AgentAService
from services.agent_s_service import AgentSService
from services.lock_service import LockService, ProcessLockError

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
        agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
        prompt = await agent_a._load_prompt()
        
    # Extract tech info from config or settings
    def get_tech(key):
        if not meta: return None
        # Try settings first as it's the standard for new projects
        val = meta.get("settings", {}).get(key)
        if not val:
            # Fallback to config
            val = meta.get("config", {}).get(key)
        return val

    return {
        "assets": assets,
        "prompt": prompt,
        "source_tech": get_tech("source_tech"),
        "target_tech": get_tech("target_tech")
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
async def run_triage(
    project_id: str, 
    params: TriageParams, 
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Re-runs the triage (discovery) process using agentic reasoning."""
    
    # === PERMISSION CHECK ===
    # Only COLLABORATOR, MANAGER, and ADMIN can execute phases
    role = identity.get("role", "VIEWER")
    if role == "VIEWER":
        raise HTTPException(
            status_code=403,
            detail="VIEWER users have read-only access. Only COLLABORATOR, MANAGER, and ADMIN can execute project phases."
        )
    
    # === PROCESS LOCKING ===
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    
    # Get username for lock
    tenant_id = identity.get("tenant_id")
    username = identity.get("username", "Unknown User")
    if not username or username == "Unknown User":
        # Fetch from database if not in identity
        try:
            tenant = await db.get_tenant_by_id(tenant_id)
            username = tenant.get("username", "Unknown User") if tenant else "Unknown User"
        except:
            username = "Unknown User"
    
    # Generate or get session ID
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Try to acquire lock
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=tenant_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown"
        )
        lock_id = lock['lock_id']
        
    except ProcessLockError as e:
        # Process is locked by another user/session
        raise HTTPException(
            status_code=423,  # 423 Locked
            detail={
                "error": "Process already running",
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    
    # === MAIN TRIAGE LOGIC ===
    try:
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

        import datetime
    
        # 0. Clear previous logs for TRIAGE phase
        try:
            await db.clear_execution_logs(project_uuid, phase="TRIAGE")
        except Exception as e:
            print(f"WARNING: Could not clear TRIAGE DB logs: {e}")

        log_lines = []
    
        # Helper to persist log incrementally
        async def _log(msg: str, agent: str = "SYSTEM"):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_msg = f"[{now}] [{agent}] {msg}"
            log_lines.append(formatted_msg)
        
            # 1. Database Logging (Primary for real-time streaming)
            await db.log_execution(project_uuid, "TRIAGE", msg, step=agent)
        
            # 2. Storage Logging (Fallback / Historical)
            try:
                current_log_content = "\n".join(log_lines)
                storage = PersistenceService.get_storage()
                proj_base = PersistenceService.ensure_solution_dir(project_folder, tenant_id=db.tenant_id)
                log_key = f"{proj_base.rstrip('/')}/triage.log"
                storage.save_file(log_key, current_log_content)
            except Exception as e:
                print(f"DEBUG: Triage Log Error: {e}")
            
        async def _check_cancellation():
            """Check if cancellation has been requested for this project."""
            try:
                return await db.check_cancellation(project_uuid)
            except: return False

        # 1. Reset cancellation flag and clear previous logs for TRIAGE phase
        try:
            await db.update_project_metadata(project_uuid, {"cancellation_requested": False})
            await db.clear_execution_logs(project_uuid, phase="TRIAGE")
        except Exception as e:
            print(f"WARNING: Could not reset flag or clear TRIAGE DB logs: {e}")

        # Clear previous log in storage
        await _log("--- Triage Started ---", agent="SYSTEM")
    
        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return {"log": "\n".join(log_lines), "status": "cancelled"}

        await _log(f"Initializing Legacy2Lake Triage Agent for Project: {project_id}")

        # 1. Deep Scan (The Scanner / Pre-processing)
        await _log("Running Deep Scanner (Python Engine)...", agent="SCANNER")
    
        # Fetch persistent human context
        user_context = await db.get_project_context(project_uuid)
        if user_context:
            await _log(f"Found {len(user_context)} human context overrides. Injecting into scanner...", agent="SCANNER")
        
        manifest = DiscoveryService.generate_manifest(project_folder, tenant_id=db.tenant_id, user_context=user_context)
        manifest["project_id"] = project_uuid
    
        file_count = len(manifest["file_inventory"])
        tech_stats = manifest["tech_stats"]
        await _log(f"Scanned {file_count} files.", agent="SCANNER")
        await _log(f"Tech Stack Detected: {tech_stats}", agent="SCANNER")
    
        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return {"log": "\n".join(log_lines), "status": "cancelled"}
    
        # 2. Agent A Analysis (The Detective)
        await _log("Invoking Agent A (Mesh Architect)...", agent="ORCHESTRATOR")
        if params.system_prompt:
            await _log("Applying custom System Prompt override.", agent="ORCHESTRATOR")
    
        # Resolve Model info for logging before calling agent
        llm_config = await db.resolve_agent_model("agent-a")
        if llm_config:
            provider = llm_config.get('provider', 'UNKNOWN').upper()
            model = llm_config.get('deployment') or llm_config.get('model_name', 'UNKNOWN')
            await _log(f"Initiating Agent A (Detective) via {provider} using model {model}", agent="AGENT_A")
        else:
            await _log("FAILED: LLM configuration for 'agent-a' is missing or invalid for this tenant.", agent="AGENT_A")
            return {
                "log": "\n".join(log_lines),
                "error": "LLM Configuration Missing. Please define Agent Matrix and Provider Vault for this tenant."
            }

        agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
        try:
            prompt = params.system_prompt
            if params.user_context:
                prompt = (prompt or "") + f"\n\n[USER CONTEXT CONSTRAINTS]:\n{params.user_context}"
            
            result = await agent_a.analyze_manifest(manifest, system_prompt_override=prompt)
        
            if "error" in result:
                await _log(f"Agent A failed: {result['error']}", agent="AGENT_A")
                return {"log": "\n".join(log_lines), **result}
             
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
        
            await _log(f"Analysis Complete. Total Nodes (AI + Inferred): {len(rf_nodes)}", agent="AGENT_A")
        
        except Exception as e:
            await _log(f"CRITICAL Architecture Analysis Failed: {e}", agent="AGENT_A")
            return {"log": "\n".join(log_lines), "error": str(e)}

        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return {"log": "\n".join(log_lines), "status": "cancelled"}

        # 3. Agent S (The Scout / Forensic)
        await _log("Invoking Agent S (Scout) for Forensic Assessment...", agent="ORCHESTRATOR")
        agent_s = AgentSService(tenant_id=db.tenant_id, client_id=db.client_id)
    
        # Extract simple file list for Scout
        scout_files = [f["path"] for f in manifest["file_inventory"]]
    
        try:
            scout_report = await agent_s.assess_repository(scout_files)
        
            score = scout_report.get("completeness_score", 0)
            gaps = len(scout_report.get("detected_gaps", []))
            await _log(f"Scout Assessment: Score {score}/100, Gaps Found: {gaps}", agent="AGENT_S")
        
        except Exception as e:
            logger.error(f"Agent S Failed: {e}", "Triage")
            await _log(f"Agent S Failed: {e}", agent="AGENT_S")
            scout_report = {}

        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return {"log": "\n".join(log_lines), "status": "cancelled"}

        # 4. Persistence (Supabase)
        await _log("Persisting Mesh Graph and Discovered Assets...", agent="DATABASE")
    
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
                "selected": True if category == "CORE" else False
            })
    
        saved_assets = await db.batch_save_assets(project_uuid, db_assets)
        asset_map = {a["source_path"]: (a.get("id") or a.get("object_id")) for a in saved_assets}

        # Transform Agent Nodes to ReactFlow Nodes
        final_nodes = []
        graph_eligible = [n for n in rf_nodes if n.get("category") != "IGNORED"]
    
        for i, n in enumerate(graph_eligible):
            n_id = n.get("id") or f"node_{i}" 
            n_uuid = asset_map.get(n_id, n_id)
        
            final_nodes.append({
                "id": n_uuid,
                "type": "custom", 
                "position": {"x": 200 + (i % 5 * 250), "y": 100 + (i // 5 * 150)},
                "data": { 
                    "label": n.get("label") or n.get("id") or f"Node {i}", 
                    "category": n.get("category", "CORE"),
                    "complexity": n.get("complexity", "LOW"),
                    "status": "pending"
                }
            })
        
        final_edges = []
        for e in rf_edges:
            e_from = e.get('from') or e.get('source')
            e_to = e.get('to') or e.get('target')
        
            if not e_from or not e_to: continue
        
            src_uid = asset_map.get(e_from, e_from)
            tgt_uid = asset_map.get(e_to, e_to)
        
            final_edges.append({
                "id": f"e{src_uid}-{tgt_uid}",
                "source": src_uid,
                "target": tgt_uid,
                "label": e.get('type') or e.get('label') or 'SEQUENTIAL'
            })
        
        await db.save_project_layout(project_uuid, {"nodes": final_nodes, "edges": final_edges})
    
        # Release 3.7: Persist Support Intelligence and Total Lines for reports/dashboard
        total_lines = sum(item.get("lines", 0) for item in manifest["file_inventory"])
    
        settings_update = {
            "lines_generated": total_lines # Map input lines to this field for the dashboard
        }
        if manifest.get("support_intelligence"):
            settings_update["support_intelligence"] = manifest["support_intelligence"]
        
        if scout_report:
            settings_update["scout_assessment"] = scout_report
        
        await db.update_project_settings(project_uuid, settings_update)
    
        await _log(f"Graph and Assets saved to database. Total Lines: {total_lines}", agent="DATABASE")
    
        # Map back to assets list for the frontend
        final_assets = []
        for item in manifest["file_inventory"]:
            agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
            item_uuid = asset_map.get(item["path"])
        
            if item_uuid:
                final_assets.append({
                    "id": item_uuid,
                    "name": item["name"],
                    "type": agent_node["category"] if agent_node else "IGNORED",
                    "status": "analyzed" if agent_node else "unlinked",
                    "tags": str(item["signatures"]),
                    "lines": item["lines"],
                    "selected": True if (agent_node and agent_node["category"] == "CORE") else False,
                    "dependencies": []
                })

            # === SUCCESS: Release lock ===
            if lock_id:
                try:
                    await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
                except Exception as e:
                    print(f"WARNING: Failed to release lock {lock_id}: {e}")
        
            return {
                "assets": final_assets,
                "nodes": final_nodes,
                "edges": final_edges,
                "log": "\n".join(log_lines)
            }
        
    except Exception as e:
        # === ERROR: Release lock before re-raising ===
        if lock_id:
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
            except:
                pass  # Best effort release
        raise e
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
    return {"contexts": context}
