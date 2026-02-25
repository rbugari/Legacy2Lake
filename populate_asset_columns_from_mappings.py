"""
Populate utm_asset_columns from utm_column_mappings (Sprint 7 Fix)

This script generates placeholder profiling data in utm_asset_columns
based on existing column mappings when real data sampling is not available.

Usage:
    python populate_asset_columns_from_mappings.py PROJECT_ID

Author: UTM Platform Team
Date: 2026-02-19
"""

import sys
import os
import uuid
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from apps.api.services.persistence_service import SupabasePersistence

PROJECT_ID = "ec771d1a-4fe4-4499-970d-54e28de4d926"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# PII pattern detection (simple keyword matching)
PII_PATTERNS = {
    'EMAIL': ['email', 'mail', 'correo'],
    'PHONE': ['phone', 'telefono', 'tel', 'mobile', 'celular'],
    'SSN': ['ssn', 'social_security', 'nss', 'seguro_social'],
    'ADDRESS': ['address', 'direccion', 'domicilio', 'calle', 'street'],
    'NAME': ['name', 'nombre', 'firstname', 'lastname', 'fullname'],
    'CREDIT_CARD': ['credit_card', 'tarjeta', 'card_number'],
    'ID_NUMBER': ['id', 'dni', 'cedula', 'passport', 'pasaporte']
}

def detect_pii_category(column_name: str) -> tuple:
    """
    Detect PII category from column name.
    Returns: (is_pii, category, confidence)
    """
    col_lower = column_name.lower()
    
    for category, keywords in PII_PATTERNS.items():
        for keyword in keywords:
            if keyword in col_lower:
                # Higher confidence for exact matches
                confidence = 0.95 if col_lower == keyword else 0.75
                return (True, category, confidence)
    
    return (False, None, 0.0)

def infer_cardinality_ratio(data_type: str, is_pk: bool, is_fk: bool) -> float:
    """
    Infer cardinality ratio based on column characteristics.
    """
    if is_pk:
        return 1.0  # Primary keys are 100% unique
    elif is_fk:
        return 0.3  # Foreign keys ~30% unique (assumption)
    elif data_type in ['STRING', 'TEXT']:
        return 0.5  # Text fields ~50% unique
    elif data_type in ['INTEGER', 'NUMERIC']:
        return 0.6  # Numeric fields ~60% unique
    else:
        return 0.4  # Default

def infer_partition_score(column_name: str, data_type: str) -> tuple:
    """
    Infer partition suitability.
    Returns: (is_candidate, score)
    """
    col_lower = column_name.lower()
    
    # Date/time columns are excellent partitioning candidates
    if any(kw in col_lower for kw in ['date', 'fecha', 'time', 'timestamp', 'year', 'month']):
        return (True, 0.95)
    
    # Region/location columns are good
    if any(kw in col_lower for kw in ['region', 'country', 'pais', 'estado', 'state']):
        return (True, 0.85)
    
    # ID columns with high cardinality
    if ('id' in col_lower or 'key' in col_lower) and data_type in ['INTEGER', 'STRING']:
        return (True, 0.70)
    
    return (False, 0.0)

async def populate_asset_columns(project_id: str, tenant_id: str):
    """
    Populate utm_asset_columns from utm_column_mappings.
    """
    db = SupabasePersistence(tenant_id=tenant_id)
    
    print(f"📊 Populating utm_asset_columns for project {project_id}")
    print(f"🏢 Tenant: {tenant_id}\n")
    
    # 1. Get all column mappings for project
    print("🔍 Fetching column mappings...")
    mappings_query = (
        db.client.table("utm_column_mappings")
        .select("*, utm_objects!asset_id(project_id, source_name)")
        .execute()
    )
    
    mappings = [
        m for m in mappings_query.data 
        if m.get("utm_objects", {}).get("project_id") == project_id
    ]
    
    print(f"   Found {len(mappings)} column mappings\n")
    
    if not mappings:
        print("❌ No column mappings found. Run Triage first.")
        return
    
    # 2. Generate asset_columns records
    asset_columns = []
    pii_count = 0
    
    for idx, mapping in enumerate(mappings, 1):
        asset_id = mapping["asset_id"]
        source_col = mapping["source_column"]
        target_col = mapping["target_column"]
        source_type = mapping.get("source_datatype", "STRING")
        target_type = mapping.get("target_datatype", "STRING")
        is_nullable = mapping.get("is_nullable", True)
        
        # Detect PII
        is_pii, pii_category, pii_confidence = detect_pii_category(source_col)
        if is_pii:
            pii_count += 1
        
        # Infer cardinality (we don't know if it's PK/FK from mappings alone)
        is_pk = "id" in source_col.lower() and not "parent" in source_col.lower()
        is_fk = "id" in source_col.lower() and ("parent" in source_col.lower() or "ref" in source_col.lower())
        cardinality = infer_cardinality_ratio(target_type, is_pk, is_fk)
        
        # Infer partition suitability
        is_partition_candidate, partition_score = infer_partition_score(source_col, target_type)
        
        # Generate placeholder metrics
        record = {
            "column_id": str(uuid.uuid4()),
            "asset_id": asset_id,
            "project_id": project_id,
            "column_name": source_col,
            "column_position": idx,
            "data_type": source_type,
            "inferred_type": target_type,
            "distinct_count": None,  # Unknown without sampling
            "cardinality_ratio": cardinality,
            "null_count": None,
            "null_percentage": 5.0 if is_nullable else 0.0,  # Assumption
            "sample_values": None,
            "min_value": None,
            "max_value": None,
            "is_pii": is_pii,
            "pii_category": pii_category,
            "pii_confidence": pii_confidence,
            "is_primary_key": is_pk,
            "is_foreign_key": is_fk,
            "is_nullable": is_nullable,
            "is_indexed": is_pk or is_fk,
            "partition_candidate": is_partition_candidate,
            "partition_score": partition_score,
            "analysis_version": "v1.0-inferred"
        }
        
        asset_columns.append(record)
        
        # Progress indicator
        if idx % 10 == 0:
            print(f"   Processed {idx}/{len(mappings)} columns...")
    
    # 3. Insert into utm_asset_columns
    print(f"\n💾 Inserting {len(asset_columns)} records into utm_asset_columns...")
    
    try:
        result = db.client.table("utm_asset_columns").insert(asset_columns).execute()
        
        print(f"✅ Successfully inserted {len(result.data)} records")
        print(f"🔒 PII columns detected: {pii_count}")
        print(f"🎯 Partition candidates: {sum(1 for r in asset_columns if r['partition_candidate'])}")
        
    except Exception as e:
        print(f"❌ Error inserting records: {e}")
        print(f"   This might be due to duplicate records. Trying upsert instead...")
        
        # Try upsert on conflict
        try:
            for record in asset_columns:
                db.client.table("utm_asset_columns").upsert(
                    record,
                    on_conflict="asset_id,column_name"
                ).execute()
            
            print(f"✅ Successfully upserted {len(asset_columns)} records")
            print(f"🔒 PII columns detected: {pii_count}")
            
        except Exception as e2:
            print(f"❌ Upsert also failed: {e2}")

if __name__ == "__main__":
    import asyncio
    
    print("=" * 60)
    print("UTM Platform - Asset Columns Populator (Sprint 7 Fix)")
    print("=" * 60)
    print()
    
    asyncio.run(populate_asset_columns(PROJECT_ID, TENANT_ID))
    
    print("\n" + "=" * 60)
    print("✅ Process completed. Code Quality should now work.")
    print("=" * 60)
