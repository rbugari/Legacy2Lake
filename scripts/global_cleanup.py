
import os
import sys
import boto3
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import shutil

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

load_dotenv()

async def global_cleanup():
    if len(sys.argv) < 2 or sys.argv[1] != "--confirm":
        print("CRITICAL: This script will WIPE all project data from R2 and Supabase.")
        print("Usage: python scripts/global_cleanup.py --confirm")
        return

    print("!!! STARTING GLOBAL CLEANUP !!!")

    # 1. Cloudflare R2 Cleanup
    print("\n--- Cleaning Cloudflare R2 ---")
    endpoint = os.getenv("R2_ENDPOINT_URL")
    access = os.getenv("R2_ACCESS_KEY_ID")
    secret = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket = os.getenv("R2_BUCKET_NAME")

    if all([endpoint, access, secret, bucket]):
        try:
            s3 = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access,
                aws_secret_access_key=secret,
                region_name="auto"
            )
            
            print(f"Listing objects in bucket: {bucket}")
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket)

            count = 0
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    for i in range(0, len(objects), 1000):
                        batch = objects[i:i+1000]
                        s3.delete_objects(Bucket=bucket, Delete={'Objects': batch})
                        count += len(batch)
            print(f"Successfully deleted {count} objects from R2.")
        except Exception as e:
            print(f"R2 Cleanup Error: {e}")
    else:
        print("R2 Config missing. Skipping storage cleanup.")

    # 2. Supabase Database Cleanup
    print("\n--- Cleaning Supabase Database ---")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Supabase Config missing. Skipping DB cleanup.")
    else:
        try:
            supabase: Client = create_client(url, key)
            
            # Order matters for foreign keys
            # Table Name -> PK or Filter Column
            # Using a valid UUID format for all to avoid 22P02 errors
            uuid_placeholder = "00000000-0000-0000-0000-000000000000"
            tables_to_clear = [
                ("utm_column_mappings", "id"),
                ("utm_logical_steps", "id"),
                ("utm_transformations", "id"),
                ("utm_asset_context", "project_id"),
                ("utm_objects", "object_id"),
                ("utm_execution_logs", "id"),
                ("utm_file_inventory", "id"),
                ("utm_design_registry", "id"),
                ("utm_projects", "project_id")
            ]

            for table, pk in tables_to_clear:
                print(f"Clearing table: {table} ...", end="")
                try:
                    # Service Role key bypasses RLS
                    res = supabase.table(table).delete().neq(pk, uuid_placeholder).execute()
                    print(f" OK (Deleted {len(res.data) if res.data else 0} rows)")
                except Exception as e:
                    # If it's an integer PK, try -1
                    try:
                        res = supabase.table(table).delete().neq(pk, -1).execute()
                        print(f" OK (Deleted {len(res.data) if res.data else 0} rows, int PK)")
                    except:
                        print(f" FAILED: {e}")
        except Exception as e:
            print(f"Supabase Client Error: {e}")

    # 3. Local Solutions Cleanup
    print("\n--- Cleaning Local Solutions ---")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "solutions"))
    if os.path.exists(base_dir):
        print(f"Removing local solutions directory: {base_dir}")
        try:
            shutil.rmtree(base_dir)
            os.makedirs(base_dir, exist_ok=True)
            print("Done.")
        except Exception as e:
            print(f"Error cleaning local directory: {e}")
    else:
        print("Local solutions directory not found.")

    print("\n--- GLOBAL CLEANUP COMPLETE ---")
    print("Environment is now clean and ready for a fresh start.")

if __name__ == "__main__":
    asyncio.run(global_cleanup())
