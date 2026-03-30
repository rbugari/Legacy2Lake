"""
Patch script for wiring evidence persistence in generate_manifest.
Safe to re-run: uses exact string replacement.
"""

with open("apps/api/services/discovery_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# ----------------------------------------------------------------
# 1. Remove unused SSISCartridge import
# ----------------------------------------------------------------
content = content.replace(
    "from apps.utm.cartridges.ssis.parser import SSISCartridge\n",
    ""
)

# ----------------------------------------------------------------
# 2. Init `all_evidence_items` accumulator before the scan loop
# ----------------------------------------------------------------
OLD_INIT = """        inventory = []
        tech_counts = {}"""

NEW_INIT = """        inventory = []
        tech_counts = {}
        all_evidence_items = []"""

content = content.replace(OLD_INIT, NEW_INIT)

# ----------------------------------------------------------------
# 3. Accumulate evidence_items from analysis inside the scan loop
# ----------------------------------------------------------------
OLD_APPEND = """            inventory.append({
                "path": rel_path,
                "name": file_name,
                "type": DiscoveryService._map_extension_to_type(ext),
                "size": file_node["size"],
                "lines": analysis["line_count"],
                "signatures": analysis["signatures"],
                "invocations": analysis["invocations"],
                "snippet": analysis["snippet"], 
                "metadata": analysis.get("metadata", {})
            })"""

NEW_APPEND = """            file_evidence = analysis.get("evidence_items", [])
            all_evidence_items.extend(file_evidence)

            inventory.append({
                "path": rel_path,
                "name": file_name,
                "type": DiscoveryService._map_extension_to_type(ext),
                "size": file_node["size"],
                "lines": analysis["line_count"],
                "signatures": analysis["signatures"],
                "invocations": analysis["invocations"],
                "snippet": analysis["snippet"], 
                "metadata": analysis.get("metadata", {}),
                "evidence_count": len(file_evidence)
            })"""

content = content.replace(OLD_APPEND, NEW_APPEND)

# ----------------------------------------------------------------
# 4. Persist evidence items and return manifest
# ----------------------------------------------------------------
OLD_RETURN = """        # 3. Construct Manifest
        return {
            "project_id": project_id,
            "root_path": triage_path,
            "tech_stats": tech_counts,
            "file_inventory": inventory,
            "support_intelligence": support_intel,
            "user_context": user_context or []
        }"""

NEW_RETURN = """        # 3. Persist V5 Evidence Items to DB (async-safe: fire-and-forget via sync best-effort)
        if all_evidence_items:
            try:
                import asyncio
                supabase_ps = PersistenceService.get_supabase_persistence(tenant_id)
                if supabase_ps:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Running inside async context — schedule as a task
                        asyncio.ensure_future(
                            supabase_ps.save_evidence_items(project_id, all_evidence_items)
                        )
                    else:
                        loop.run_until_complete(
                            supabase_ps.save_evidence_items(project_id, all_evidence_items)
                        )
                    print(f"[Discovery] V5: Queued {len(all_evidence_items)} evidence items for project {project_id}")
            except Exception as ev_err:
                print(f"[Discovery] Warning: Could not persist evidence items: {ev_err}")

        # 4. Construct Manifest
        return {
            "project_id": project_id,
            "root_path": triage_path,
            "tech_stats": tech_counts,
            "file_inventory": inventory,
            "support_intelligence": support_intel,
            "user_context": user_context or [],
            "evidence_items_count": len(all_evidence_items)
        }"""

content = content.replace(OLD_RETURN, NEW_RETURN)

with open("apps/api/services/discovery_service.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Sprint 1 evidence wiring applied successfully.")
