"""
Re-parse SSIS asset to extract connections properly (after parser fix)
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client
from apps.utm.cartridges.ssis.parser import SSISCartridge

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("="*70)
print("🔄 Re-parsing SSIS asset to extract connections")
print("="*70)

# Get asset
result = supabase.table("utm_objects").select("object_id, source_name, metadata, source_path").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()

if not result.data:
    print("❌ Asset not found")
    exit(1)

asset = result.data
object_id = asset["object_id"]
source_path = asset.get("source_path", "")

print(f"\n📦 Asset: {asset['source_name']}")
print(f"   Object ID: {object_id[:8]}...")
print(f"   Source Path: {source_path}")

# Check if file exists locally
if not os.path.exists(source_path):
    print(f"\n⚠️  File not found at: {source_path}")
    print("   Skipping re-parse (connections will remain empty)")
    exit(0)

# Re-parse with corrected parser
print("\n🔍 Re-parsing SSIS file...")
parser = SSISCartridge()
meta_obj = parser.parse(source_path)

summary = meta_obj.metadata.get("summary", {})
connections = summary.get("connection_managers", [])

print(f"\n✅ Extracted {len(connections)} connection(s)")
for conn in connections:
    print(f"   - {conn['name']}: {conn['connection_string'][:60] if conn['connection_string'] else 'No connection string'}...")

# Update metadata with corrected connections
metadata = asset.get("metadata", {})
metadata["connections"] = connections

print("\n💾 Updating utm_objects...")
supabase.table("utm_objects").update({"metadata": metadata}).eq("object_id", object_id).execute()

print("✅ Updated successfully!")

# Re-run origin extraction with new connections
print("\n🔄 Re-running origin extraction...")
import sys
sys.path.insert(0, os.path.dirname(__file__))
exec(open("test_complete_extraction.py").read())
