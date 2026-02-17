"""
Verify Parser Catalog Migration - Zero-Hardcode v4.0

Tests that utm_parser_catalog and utm_source_tech_catalog are working correctly.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

print("=" * 80)
print("Parser Catalog Verification - Zero-Hardcode v4.0")
print("=" * 80)
print()

# Test 1: List all technologies
print("1️⃣  Testing list_supported_technologies()...")
try:
    result = supabase.rpc("list_supported_technologies", {}).execute()
    techs = result.data
    
    print(f"   ✅ Found {len(techs)} technologies:")
    for tech in techs:
        status = "✅" if tech["has_parser"] else "⚪"
        print(f"      {status} {tech['tech_name']} ({tech['tech_id']}) - {tech['vendor']}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 2: Resolve SSIS parser
print("2️⃣  Testing resolve_parser_by_tech('SSIS')...")
try:
    result = supabase.rpc("resolve_parser_by_tech", {"p_source_tech": "SSIS"}).execute()
    
    if result.data and len(result.data) > 0:
        parser = result.data[0]
        print(f"   ✅ Resolved: {parser['parser_name']}")
        print(f"      Config keys: {list(parser['medulla_config'].keys())}")
        print(f"      Main key: {parser['medulla_config']['main_key']}")
        print(f"      SQL keys: {parser['medulla_config']['sql_keys']}")
    else:
        print("   ❌ No parser found for SSIS")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 3: Resolve Oracle parser
print("3️⃣  Testing resolve_parser_by_tech('Oracle')...")
try:
    result = supabase.rpc("resolve_parser_by_tech", {"p_source_tech": "Oracle"}).execute()
    
    if result.data and len(result.data) > 0:
        parser = result.data[0]
        print(f"   ✅ Resolved: {parser['parser_name']}")
        print(f"      Config keys: {list(parser['medulla_config'].keys())}")
    else:
        print("   ❌ No parser found for Oracle")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 4: Resolve DataStage parser
print("4️⃣  Testing resolve_parser_by_tech('DataStage')...")
try:
    result = supabase.rpc("resolve_parser_by_tech", {"p_source_tech": "DataStage"}).execute()
    
    if result.data and len(result.data) > 0:
        parser = result.data[0]
        print(f"   ✅ Resolved: {parser['parser_name']}")
        print(f"      Transformation types: {parser['medulla_config']['transformation_types']}")
        print(f"      Complexity weights: {list(parser['medulla_config']['complexity_weights'].keys())}")
    else:
        print("   ❌ No parser found for DataStage")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 5: Test alias resolution (case-insensitive)
print("5️⃣  Testing alias resolution (case variations)...")
test_cases = [
    ("ssis", "SSIS"),
    ("SQL SERVER", "SSIS"),
    ("sqlserver", "SSIS"),
    ("PL/SQL", "Oracle"),
    ("PLSQL", "Oracle"),
    ("IBM DataStage", "DataStage"),
    ("informatica", "Informatica")
]

for alias, expected_tech in test_cases:
    try:
        result = supabase.rpc("resolve_parser_by_tech", {"p_source_tech": alias}).execute()
        
        if result.data and len(result.data) > 0:
            parser = result.data[0]
            print(f"   ✅ '{alias}' → {parser['parser_name']}")
        else:
            print(f"   ❌ '{alias}' → NOT FOUND (expected {expected_tech})")
    except Exception as e:
        print(f"   ❌ '{alias}' → Error: {e}")

print()

# Test 6: Count parsers by status
print("6️⃣  Parser Registry Status...")
try:
    result = supabase.table("utm_parser_catalog").select("*").execute()
    parsers = result.data
    
    active = sum(1 for p in parsers if p["is_active"])
    inactive = len(parsers) - active
    
    print(f"   Total parsers: {len(parsers)}")
    print(f"   ✅ Active: {active}")
    print(f"   ⚪ Inactive: {inactive}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

# Test 7: Verify parser catalog entries
print("7️⃣  Parser Catalog Details...")
try:
    result = supabase.table("utm_parser_catalog").select("parser_id, parser_name, tech_id, priority, is_active").order("priority").execute()
    
    for parser in result.data:
        status = "✅" if parser["is_active"] else "⚪"
        print(f"   {status} {parser['parser_id']} (priority={parser['priority']})")
        print(f"      {parser['parser_name']} [{parser['tech_id']}]")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    print()

print("=" * 80)
print("✅ Parser Catalog Verification Complete")
print("=" * 80)
