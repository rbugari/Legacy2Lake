"""
Initialize utm_prompts Table - v4.0
====================================

Purpose:
    Load all prompt files (.md) from apps/api/prompts/ into utm_prompts table.
    This is a ONE-TIME migration script to populate the database with existing prompts.

Usage:
    python scripts/init_prompts_v4.py

Requirements:
    - Database must have utm_prompts table (run migrations/sprint_v4.0_prompts.sql first)
    - Service role access to Supabase
    - All prompt files must exist in apps/api/prompts/

Author: Legacy2Lake Engineering
Date: 2026-02-15
Version: v4.0
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    print("❌ Failed to import required modules. Run from project root.")
    sys.exit(1)


# ================================================================
# PROMPT DEFINITIONS
# ================================================================

PROMPTS_TO_LOAD = [
    # Agent Prompts (Core AI Agents)
    {
        "prompt_id": "agent_a_discovery",
        "file": "agent_a_discovery.md",
        "agent_id": "agent-a",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent A (Architect) - Discovery and forensic analysis"
    },
    {
        "prompt_id": "agent_b_cartographer",
        "file": "agent_b_cartographer.md",
        "agent_id": "agent-b",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent B (Topology) - Dependency mapping and orchestration planning"
    },
    {
        "prompt_id": "agent_c_interpreter",
        "file": "agent_c_interpreter.md",
        "agent_id": "agent-c",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent C (Coder/Developer) - Code generation and transpilation"
    },
    {
        "prompt_id": "agent_d_auditor",
        "file": "agent_d_auditor.md",
        "agent_id": "agent-d",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent D (Deliverer) - Package generation and handover"
    },
    {
        "prompt_id": "agent_f_critic",
        "file": "agent_f_critic.md",
        "agent_id": "agent-f",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent F (Critic) - Code review and compliance validation"
    },
    {
        "prompt_id": "agent_g_governance",
        "file": "agent_g_governance.md",
        "agent_id": "agent-g",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent G (Governance) - Documentation and runbook generation"
    },
    {
        "prompt_id": "agent_s_scout",
        "file": "agent_s_scout.md",
        "agent_id": "agent-s",
        "tech_stack": None,
        "pattern_type": None,
        "description": "Agent S (Scout) - Technology detection and gap analysis"
    },
    
    # Cartridge Prompts (Code Generation Templates)
    {
        "prompt_id": "cartridge_databricks_direct",
        "file": "cartridge_databricks_direct.md",
        "agent_id": "agent-c",
        "tech_stack": "databricks",
        "pattern_type": "direct",
        "description": "Databricks Direct Translation (1:1 conversion, no patterns)"
    },
    {
        "prompt_id": "cartridge_databricks_bronze",
        "file": "cartridge_databricks_bronze.md",
        "agent_id": "agent-c",
        "tech_stack": "databricks",
        "pattern_type": "bronze",
        "description": "Databricks Bronze Layer (Raw ingestion with Medallion pattern)"
    },
    {
        "prompt_id": "cartridge_databricks_silver",
        "file": "cartridge_databricks_silver.md",
        "agent_id": "agent-c",
        "tech_stack": "databricks",
        "pattern_type": "silver",
        "description": "Databricks Silver Layer (Cleaned/transformed with Medallion pattern)"
    },
    {
        "prompt_id": "cartridge_databricks_gold",
        "file": "cartridge_databricks_gold.md",
        "agent_id": "agent-c",
        "tech_stack": "databricks",
        "pattern_type": "gold",
        "description": "Databricks Gold Layer (Business/aggregated with Medallion pattern)"
    },
    {
        "prompt_id": "cartridge_pyspark_direct",
        "file": "cartridge_pyspark_direct.md",
        "agent_id": "agent-c",
        "tech_stack": "pyspark",
        "pattern_type": "direct",
        "description": "PySpark Direct Translation (Generic PySpark without Delta Lake)"
    },
    
    # Shared Prompts (Used by multiple agents)
    {
        "prompt_id": "coding_standards",
        "file": "coding_standards.md",
        "agent_id": None,  # Shared across agents
        "tech_stack": None,
        "pattern_type": None,
        "description": "Global coding standards and best practices"
    },
]


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def get_prompts_directory() -> Path:
    """Get the prompts directory path"""
    return Path(__file__).parent.parent / "apps" / "api" / "prompts"


def validate_prompt_files() -> tuple[List[str], List[str]]:
    """
    Validate that all prompt files exist.
    
    Returns:
        Tuple of (existing_files, missing_files)
    """
    prompts_dir = get_prompts_directory()
    existing = []
    missing = []
    
    for prompt_def in PROMPTS_TO_LOAD:
        file_path = prompts_dir / prompt_def["file"]
        if file_path.exists():
            existing.append(prompt_def["file"])
        else:
            missing.append(prompt_def["file"])
    
    return existing, missing


async def load_prompt_to_db(
    db: SupabasePersistence,
    prompt_def: Dict[str, Any],
    prompts_dir: Path,
    dry_run: bool = False
) -> bool:
    """
    Load a single prompt file to the database.
    
    Args:
        db: Database persistence service
        prompt_def: Prompt definition dictionary
        prompts_dir: Path to prompts directory
        dry_run: If True, don't actually insert (for testing)
    
    Returns:
        True if successful, False otherwise
    """
    file_path = prompts_dir / prompt_def["file"]
    
    if not file_path.exists():
        logger.error(f"❌ File not found: {file_path}", "InitPrompts")
        return False
    
    try:
        # Read file content
        content = file_path.read_text(encoding='utf-8')
        
        if len(content) == 0:
            logger.warning(f"⚠️  Empty file: {prompt_def['file']}", "InitPrompts")
            return False
        
        # Prepare metadata
        metadata = {
            "description": prompt_def.get("description", ""),
            "source_file": prompt_def["file"],
            "char_count": len(content),
            "loaded_by": "init_prompts_v4.py",
            "loaded_at": "2026-02-15"
        }
        
        if dry_run:
            logger.info(
                f"[DRY RUN] Would load: {prompt_def['prompt_id']} ({len(content)} chars)",
                "InitPrompts"
            )
            return True
        
        # Save to database
        await db.save_prompt(
            prompt_id=prompt_def["prompt_id"],
            content=content,
            agent_id=prompt_def.get("agent_id"),
            tech_stack=prompt_def.get("tech_stack"),
            pattern_type=prompt_def.get("pattern_type"),
            metadata=metadata
        )
        
        logger.info(
            f"✅ Loaded: {prompt_def['prompt_id']} ({len(content)} chars) - {prompt_def.get('description', '')}",
            "InitPrompts"
        )
        return True
        
    except Exception as e:
        logger.error(
            f"❌ Failed to load {prompt_def['prompt_id']}: {str(e)}",
            "InitPrompts"
        )
        return False


# ================================================================
# MAIN EXECUTION
# ================================================================

async def main(dry_run: bool = False, skip_validation: bool = False):
    """
    Main initialization function.
    
    Args:
        dry_run: If True, don't actually insert to DB (for testing)
        skip_validation: If True, skip file validation step
    """
    print("=" * 70)
    print("v4.0 Prompts Initialization Script")
    print("=" * 70)
    print()
    
    # Step 1: Validate files exist
    if not skip_validation:
        print("📋 Step 1: Validating prompt files...")
        existing, missing = validate_prompt_files()
        
        print(f"   ✅ Found: {len(existing)} files")
        if missing:
            print(f"   ⚠️  Missing: {len(missing)} files")
            for f in missing:
                print(f"      - {f}")
            
            user_input = input("\nContinue anyway? (y/N): ")
            if user_input.lower() != 'y':
                print("❌ Aborted by user")
                return
        print()
    
    # Step 2: Initialize database connection
    print("📋 Step 2: Connecting to database...")
    try:
        db = SupabasePersistence()
        print("   ✅ Connected to Supabase")
        print()
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return
    
    # Step 3: Load prompts
    print(f"📋 Step 3: Loading {len(PROMPTS_TO_LOAD)} prompts...")
    if dry_run:
        print("   ⚠️  DRY RUN MODE - No actual database writes")
    print()
    
    prompts_dir = get_prompts_directory()
    success_count = 0
    failed_count = 0
    
    for i, prompt_def in enumerate(PROMPTS_TO_LOAD, 1):
        print(f"   [{i}/{len(PROMPTS_TO_LOAD)}] {prompt_def['prompt_id']}...", end=" ")
        
        success = await load_prompt_to_db(db, prompt_def, prompts_dir, dry_run)
        
        if success:
            success_count += 1
            print("✅")
        else:
            failed_count += 1
            print("❌")
    
    # Step 4: Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   Total prompts: {len(PROMPTS_TO_LOAD)}")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    if dry_run:
        print()
        print("   ⚠️  DRY RUN - No changes made to database")
    
    print()
    
    if success_count == len(PROMPTS_TO_LOAD):
        print("🎉 All prompts loaded successfully!")
        print()
        print("📋 Next Steps:")
        print("   1. Verify prompts: SELECT * FROM utm_prompts;")
        print("   2. Test prompt loading in Agent C/F/G services")
        print("   3. Monitor utm_prompts_history table for automatic versioning")
    elif failed_count > 0:
        print("⚠️  Some prompts failed to load. Check logs above.")
    
    print()


# ================================================================
# CLI ENTRY POINT
# ================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize utm_prompts table with existing prompt files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no database writes)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip file validation step"
    )
    
    args = parser.parse_args()
    
    # Run async main
    asyncio.run(main(dry_run=args.dry_run, skip_validation=args.skip_validation))
