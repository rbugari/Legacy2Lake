"""
Check medulla structure in utm_objects for SSIS packages
"""
import json
import os
from supabase import create_client
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"SUPABASE_KEY: {'*' * 10 if SUPABASE_KEY else 'None'}")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Project ID
project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

print("=" * 80)
print("Checking SSIS Package Medulla Structure")
print("=" * 80)

# Get all SSIS CORE assets
response = client.table("utm_objects").select("*").eq("project_id", project_id).eq("type", "CORE").execute()

print(f"\nFound {len(response.data)} CORE assets")

for asset in response.data:
    name = asset.get("source_name", "unknown")
    metadata = asset.get("metadata", {})
    
    print(f"\n{'=' * 80}")
    print(f"Asset: {name}")
    print(f"{'=' * 80}")
    
    # Check if logical_medulla exists
    if "logical_medulla" not in metadata:
        print("❌ NO logical_medulla in metadata")
        print(f"Metadata keys: {list(metadata.keys())}")
        continue
    
    medulla = metadata.get("logical_medulla", {})
    print(f"✅ logical_medulla exists")
    print(f"Medulla keys: {list(medulla.keys())}")
    
    # Check data_flow_logic
    if "data_flow_logic" not in medulla:
        print("❌ NO data_flow_logic in medulla")
    else:
        data_flow_logic = medulla.get("data_flow_logic", [])
        print(f"✅ data_flow_logic exists with {len(data_flow_logic)} components")
        
        if data_flow_logic:
            print(f"\nFirst component structure:")
            first_comp = data_flow_logic[0]
            print(f"  Keys: {list(first_comp.keys())}")
            print(f"  Type: {first_comp.get('type')}")
            print(f"  Intent: {first_comp.get('intent')}")
            
            if "raw_properties" in first_comp:
                raw_props = first_comp.get("raw_properties", {})
                print(f"  Raw properties keys: {list(raw_props.keys())}")
                
                # Check for SQL command or table name
                if "SqlCommand" in raw_props:
                    sql = raw_props["SqlCommand"]
                    print(f"  SqlCommand: length={len(sql)}, value='{sql}'")
                if "OpenRowset" in raw_props:
                    print(f"  ✅ OpenRowset: '{raw_props['OpenRowset']}'")
                if "TableOrViewName" in raw_props:
                    print(f"  ✅ TableOrViewName: '{raw_props['TableOrViewName']}'")
                if not any(k in raw_props for k in ["SqlCommand", "OpenRowset", "TableOrViewName"]):
                    print(f"  ⚠️ No SqlCommand/OpenRowset/TableOrViewName found")

print("\n" + "=" * 80)
print("Analysis complete")
print("=" * 80)
