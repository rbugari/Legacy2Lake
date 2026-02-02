import os
import asyncio
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv

# Try to import services from the app structure
try:
    from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
    from apps.api.utils.logger import logger
except ImportError:
    # Fallback for direct script execution if paths aren't set
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
    from apps.api.utils.logger import logger

load_dotenv()

class DatabaseCleaner:
    def __init__(self, dry_run: bool = True):
        self.db = SupabasePersistence() # Service Role Key highly recommended
        self.dry_run = dry_run
        self.stats = {
            "deleted_records": 0,
            "found_orphans": 0,
            "errors": 0
        }

    async def audit_all_tables(self):
        """Audits all tables and prints summary."""
        print("\n--- Database Cleanup Audit ---")
        tables = [
            "utm_projects", "utm_objects", "utm_logical_steps", 
            "utm_transformations", "utm_execution_logs", "utm_file_inventory",
            "utm_asset_context", "utm_tenants", "utm_clients"
        ]
        
        for table in tables:
            try:
                res = self.db.client.table(table).select("*", count="exact").limit(0).execute()
                count = res.count if hasattr(res, "count") else 0
                print(f"[OK] Table {table:25} | Records: {count}")
            except Exception as e:
                print(f"[ERR] Table {table:25} | Error: {e}")

    async def clean_orphaned_records(self):
        """Finds and deletes records with missing parents."""
        print(f"\n--- Cleaning Orphaned Records (Dry Run: {self.dry_run}) ---")
        
        # 1. Objects without Projects
        await self._purge_orphans(
            child_table="utm_objects",
            parent_table="utm_projects",
            child_fk="project_id",
            parent_pk="project_id",
            child_pk="object_id"
        )
        
        # 2. Transformations without Objects
        await self._purge_orphans(
            child_table="utm_transformations",
            parent_table="utm_objects",
            child_fk="asset_id",
            parent_pk="object_id",
            child_pk="id"
        )
        
        # 3. Logical Steps without Objects
        await self._purge_orphans(
            child_table="utm_logical_steps",
            parent_table="utm_objects",
            child_fk="object_id",
            parent_pk="object_id",
            child_pk="step_id"
        )
        
        # 4. Logs without Projects
        await self._purge_orphans(
            child_table="utm_execution_logs",
            parent_table="utm_projects",
            child_fk="project_id",
            parent_pk="project_id",
            child_pk="id"
        )

        # 5. File Inventory without Projects
        await self._purge_orphans(
            child_table="utm_file_inventory",
            parent_table="utm_projects",
            child_fk="project_id",
            parent_pk="project_id",
            child_pk="id"
        )

        # 6. Asset Context without Projects
        await self._purge_orphans(
            child_table="utm_asset_context",
            parent_table="utm_projects",
            child_fk="project_id",
            parent_pk="project_id",
            child_pk="id"
        )

    async def sync_storage(self):
        """Identifies and deletes R2 storage folders for non-existent projects."""
        print(f"\n--- Syncing Storage (Dry Run: {self.dry_run}) ---")
        
        try:
            # Get valid project names (normalized)
            res = self.db.client.table("utm_projects").select("name").execute()
            valid_names = {p["name"] for p in res.data}
            
            # Get storage provider
            storage = PersistenceService.get_storage()
            
            # List root folders
            root_items = storage.list_files("", recursive=False)
            
            for item in root_items:
                if item["type"] == "folder":
                    folder_name = item["name"]
                    # Check if folder_name is a tenant ID (UUID-like) or a project name
                    if folder_name not in valid_names and "-" not in folder_name:
                        print(f"[!] Found potential orphan folder: {folder_name}")
                        if not self.dry_run:
                            storage.delete_directory(folder_name)
                            print(f"    [DEL] Deleted folder: {folder_name}")
                    
                    # If it's a tenant folder, check subfolders
                    if "-" in folder_name:
                        sub_items = storage.list_files(folder_name, recursive=False)
                        for sub in sub_items:
                            if sub["type"] == "folder":
                                proj_folder = sub["name"]
                                if proj_folder not in valid_names:
                                    print(f"[!] Found orphan project folder in tenant {folder_name}: {proj_folder}")
                                    if not self.dry_run:
                                        storage.delete_directory(sub["path"])
                                        print(f"    [DEL] Deleted folder: {sub['path']}")
                                        
        except Exception as e:
            print(f"Error syncing storage: {e}")

    async def _purge_orphans(self, child_table: str, parent_table: str, child_fk: str, parent_pk: str, child_pk: str = "id"):
        """Generic orphan purger."""
        try:
            # Efficiently find orphans using a LEFT JOIN / NOT EXISTS equivalent query
            # Supabase query for orphans (simplified logic):
            # We fetch all parent IDs first (usually manageable)
            parent_res = self.db.client.table(parent_table).select(parent_pk).execute()
            if not parent_res.data and parent_res.data != []:
                 print(f"[!] Warning: No data returned for parent table {parent_table}")
            
            parent_ids = {p[parent_pk] for p in parent_res.data}
            
            # Fetch all children (might be large, but we'll paginate if needed)
            try:
                child_res = self.db.client.table(child_table).select(f"{child_fk}, {child_pk}").execute()
            except Exception as e:
                print(f"[ERR] Selection failed for {child_table} with columns {child_fk}, {child_pk}: {e}")
                # Fallback to see what's actually in there
                fallback = self.db.client.table(child_table).select("*").limit(1).execute()
                if fallback.data:
                    print(f"    [TIP] Sample columns in {child_table}: {list(fallback.data[0].keys())}")
                else:
                    print(f"    [?] Table {child_table} appears to be empty or inaccessible.")
                raise e
            
            orphans = [c for c in child_res.data if c[child_fk] not in parent_ids]
            
            if orphans:
                print(f"[SCAN] Found {len(orphans)} orphans in '{child_table}' pointing to non-existent '{parent_table}'")
                if not self.dry_run:
                    # Batch delete orphans
                    orphan_ids = [o[child_pk] for o in orphans]
                    
                    # Supabase limit on 'in' is high but let's be safe
                    for i in range(0, len(orphan_ids), 100):
                        chunk = orphan_ids[i:i + 100]
                        self.db.client.table(child_table).delete().in_(child_pk, chunk).execute()
                    
                    print(f"    [OK] Purged {len(orphans)} records from {child_table}")
                    self.stats["deleted_records"] += len(orphans)
            else:
                print(f"[OK] No orphans found in '{child_table}'")
                
        except Exception as e:
            print(f"❌ Error purging orphans from {child_table}: {e}")
            self.stats["errors"] += 1

async def main():
    parser = argparse.ArgumentParser(description="Legacy2Lake Database and Storage Cleanup Utility")
    parser.add_argument("--audit", action="store_true", help="Report status only")
    parser.add_argument("--purge", action="store_true", help="Delete orphaned records (IRREVERSIBLE)")
    parser.add_argument("--sync", action="store_true", help="Sync R2 storage (IRREVERSIBLE)")
    parser.add_argument("--force", action="store_true", help="Apply changes (disable dry run)")
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner(dry_run=not args.force)
    
    if args.audit or (not args.purge and not args.sync):
        await cleaner.audit_all_tables()
        # Even in audit mode, we check for orphans but don't delete
        cleaner.dry_run = True 
        await cleaner.clean_orphaned_records()
        await cleaner.sync_storage()
    
    if args.purge:
        await cleaner.clean_orphaned_records()
        
    if args.sync:
        await cleaner.sync_storage()
        
    print("\n--- Cleanup Finished ---")
    print(f"Summary: Found {cleaner.stats['found_orphans']} orphans, Deleted {cleaner.stats['deleted_records']} records, Errors: {cleaner.stats['errors']}")

if __name__ == "__main__":
    asyncio.run(main())
