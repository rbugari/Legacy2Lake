# v4.0 Zero-Hardcode Generation - Installation Guide

**Feature:** Dynamic Prompts System  
**Date:** February 15, 2026  
**Status:** ✅ Ready for Production

---

## 📋 Overview

This migration implements the **Zero-Hardcode Generation** feature from v4.0, which moves all prompts from hardcoded files to a database-driven system with automatic versioning.

### What's Included

1. **Database Tables:**
   - `utm_prompts` - Main prompts table (GLOBAL, no tenant isolation)
   - `utm_prompts_history` - Automatic version history via trigger

2. **Automatic Versioning:**
   - Trigger saves old version to history before any UPDATE
   - No manual intervention needed
   - History is READ-ONLY for ADMIN analysis

3. **Initialization Script:**
   - Loads all 13 existing prompt files to database
   - One-time migration to populate initial data

---

## 🚀 Installation Steps

### Step 1: Run SQL Migration

Execute the migration on your Supabase database:

```bash
# Option A: Via Supabase Dashboard
# 1. Go to SQL Editor
# 2. Paste contents of migrations/sprint_v4.0_prompts.sql
# 3. Click "Run"

# Option B: Via psql
psql -h <your-host> -U postgres -d postgres -f migrations/sprint_v4.0_prompts.sql
```

**Expected Output:**
```
✅ v4.0 Prompts System: Migration successful
   - utm_prompts table created
   - utm_prompts_history table created
   - Automatic versioning trigger active
   - Indexes created
   - Permissions granted

📋 Next Step: Run scripts/init_prompts_v4.py to load initial prompts
```

### Step 2: Load Initial Prompts

Run the initialization script to populate prompts from existing .md files:

```bash
# Dry run first (recommended)
python scripts/init_prompts_v4.py --dry-run

# Actual load
python scripts/init_prompts_v4.py
```

**Expected Output:**
```
======================================================================
v4.0 Prompts Initialization Script
======================================================================

📋 Step 1: Validating prompt files...
   ✅ Found: 13 files

📋 Step 2: Connecting to database...
   ✅ Connected to Supabase

📋 Step 3: Loading 13 prompts...
   [1/13] agent_a_discovery... ✅
   [2/13] agent_b_cartographer... ✅
   [3/13] agent_c_interpreter... ✅
   [4/13] agent_d_auditor... ✅
   [5/13] agent_f_critic... ✅
   [6/13] agent_g_governance... ✅
   [7/13] agent_s_scout... ✅
   [8/13] cartridge_databricks_direct... ✅
   [9/13] cartridge_databricks_bronze... ✅
   [10/13] cartridge_databricks_silver... ✅
   [11/13] cartridge_databricks_gold... ✅
   [12/13] cartridge_pyspark_direct... ✅
   [13/13] coding_standards... ✅

======================================================================
📊 SUMMARY
======================================================================
   Total prompts: 13
   ✅ Successful: 13
   ❌ Failed: 0

🎉 All prompts loaded successfully!

📋 Next Steps:
   1. Verify prompts: SELECT * FROM utm_prompts;
   2. Test prompt loading in Agent C/F/G services
   3. Monitor utm_prompts_history table for automatic versioning
```

### Step 3: Verify Installation

Check that prompts were loaded correctly:

```sql
-- Count prompts
SELECT COUNT(*) FROM utm_prompts;
-- Expected: 13

-- View all prompts
SELECT prompt_id, agent_id, tech_stack, pattern_type, 
       LENGTH(content) as char_count, created_at
FROM utm_prompts
ORDER BY prompt_id;

-- Verify trigger exists
SELECT tgname, tgtype, tgenabled 
FROM pg_trigger 
WHERE tgrelid = 'utm_prompts'::regclass;
-- Expected: prompt_version_trigger
```

---

## 🧪 Testing

### Test 1: Prompt Loading (Backend)

The system automatically loads prompts from DB. Test by triggering code generation:

```bash
# Start backend
python run.py

# Trigger a migration (via UI or API)
# Watch logs for:
# DEBUG: Loaded prompt cartridge_databricks_direct from DB (Tenant)
```

### Test 2: Automatic Versioning (Trigger)

Update a prompt and verify history is saved:

```sql
-- Update a prompt
UPDATE utm_prompts 
SET content = 'TEST CONTENT v2' 
WHERE prompt_id = 'agent_c_interpreter';

-- Check history table (should have 1 entry with old content)
SELECT prompt_id, LEFT(content, 50) as content_preview, changed_at
FROM utm_prompts_history
WHERE prompt_id = 'agent_c_interpreter'
ORDER BY changed_at DESC;
```

### Test 3: Get Prompt Method

Test via Python:

```python
from apps.api.services.persistence_service import SupabasePersistence

async def test():
    db = SupabasePersistence()
    
    # Load a prompt
    content = await db.get_prompt("agent_c_interpreter")
    print(f"Loaded: {len(content)} chars")
    
    # Should NOT be empty
    assert len(content) > 0

import asyncio
asyncio.run(test())
```

---

## 📊 Database Schema

### utm_prompts (Main Table)

```sql
CREATE TABLE utm_prompts (
    prompt_id TEXT PRIMARY KEY,           -- e.g., 'agent_c_interpreter'
    content TEXT NOT NULL,                -- Full prompt content
    tech_stack TEXT,                      -- 'databricks', 'pyspark', NULL
    pattern_type TEXT,                    -- 'direct', 'bronze', 'silver', 'gold', NULL
    agent_id TEXT,                        -- 'agent-c', 'agent-f', NULL
    is_active BOOLEAN DEFAULT true,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### utm_prompts_history (Auto-Created by Trigger)

```sql
CREATE TABLE utm_prompts_history (
    history_id UUID PRIMARY KEY,
    prompt_id TEXT NOT NULL,
    content TEXT NOT NULL,
    tech_stack TEXT,
    pattern_type TEXT,
    agent_id TEXT,
    metadata JSONB,
    changed_by UUID,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔧 Maintenance

### View Prompt History

```sql
-- Get history for a specific prompt
SELECT * FROM get_prompt_history('agent_c_interpreter', 10);

-- Or manually query
SELECT history_id, 
       LEFT(content, 100) as preview, 
       LENGTH(content) as chars,
       changed_at
FROM utm_prompts_history
WHERE prompt_id = 'agent_c_interpreter'
ORDER BY changed_at DESC
LIMIT 10;
```

### Add New Prompt

```python
from apps.api.services.persistence_service import SupabasePersistence

async def add_new_prompt():
    db = SupabasePersistence()
    
    await db.save_prompt(
        prompt_id="agent_x_new",
        content="Your prompt content here...",
        agent_id="agent-x",
        tech_stack="databricks",
        pattern_type="custom",
        metadata={"version": "1.0", "author": "Engineering Team"}
    )

import asyncio
asyncio.run(add_new_prompt())
```

### Update Existing Prompt

```python
# Same method - trigger automatically saves old version
await db.save_prompt(
    prompt_id="agent_c_interpreter",
    content="Updated prompt content..."
)

# Old version is now in utm_prompts_history
```

---

## ⚠️ Important Notes

### Multi-Tenancy

- **Prompts are GLOBAL** - no `tenant_id` column
- All tenants use the same prompts
- Tenant-specific customization happens at the data level (project settings, design registry)
- This simplifies the system and reduces complexity

### Versioning

- **Automatic versioning via trigger** - no manual action needed
- History is READ-ONLY for ADMIN analysis
- **NO UI for rollback** - this is intentional (keeps v4.0 simple)
- If you need to restore an old version:
  1. Query utm_prompts_history
  2. Copy old content
  3. UPDATE utm_prompts manually (creates new history entry)

### File System vs Database

- After migration, prompts are loaded from **DATABASE first**
- Files in `apps/api/prompts/` are now **reference only**
- To update prompts: use `save_prompt()` method or SQL UPDATE
- Files will be deprecated in future versions

---

## 🐛 Troubleshooting

### Issue: Script fails with "Module not found"

**Solution:**
```bash
# Make sure you're in project root
cd c:\proyectos_dev\UTM

# Run with proper Python path
python scripts/init_prompts_v4.py
```

### Issue: "Table utm_prompts does not exist"

**Solution:**
Run the SQL migration first:
```bash
# Via Supabase Dashboard SQL Editor
migrations/sprint_v4.0_prompts.sql
```

### Issue: Prompts still loading from files

**Solution:**
Check that `get_prompt()` method in persistence_service.py is querying the database:
```python
# Should see this in logs:
DEBUG: Loaded prompt cartridge_databricks_direct from DB (Tenant)
```

If you see "Loaded from file", the database query is failing.

### Issue: Trigger not firing

**Solution:**
Verify trigger exists:
```sql
SELECT * FROM pg_trigger WHERE tgname = 'prompt_version_trigger';
```

If missing, re-run trigger creation from migration file.

---

## 📈 Performance

### Database Impact

- **Minimal** - Prompts loaded once per agent invocation
- **Cached** - Agent services cache prompts in memory
- **History table growth** - ~1 KB per version saved
  - Example: 10 updates/month × 13 prompts = ~130 KB/month
  - Negligible compared to other tables

### Query Performance

```sql
-- Primary lookup (used by get_prompt())
-- Uses index: idx_utm_prompts_agent
EXPLAIN ANALYZE
SELECT content FROM utm_prompts 
WHERE prompt_id = 'agent_c_interpreter' 
  AND is_active = true;

-- Expected: Index Scan, <1ms
```

---

## ✅ Success Criteria

After completing this migration, verify:

- [ ] SQL migration executed successfully
- [ ] 13 prompts loaded to utm_prompts table
- [ ] Trigger `prompt_version_trigger` exists
- [ ] Backend logs show "Loaded prompt X from DB"
- [ ] Code generation still works (Agent C/F/G)
- [ ] Updating a prompt creates history entry
- [ ] No hardcoded template warnings in logs

---

## 📚 Related Documentation

- [v4.0_FINAL_SCOPE.md](../docs/planning/v4.0_FINAL_SCOPE.md) - Complete v4.0 scope
- [v4.0_QUICK_REFERENCE.md](../docs/planning/v4.0_QUICK_REFERENCE.md) - Quick reference
- [DATABASE_SCHEMA.md](../docs/DATABASE_SCHEMA.md) - Full database schema

---

**Status:** ✅ Ready for deployment  
**Next:** Test in staging environment before production rollout
