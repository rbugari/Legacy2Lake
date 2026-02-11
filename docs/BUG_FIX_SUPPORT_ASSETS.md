# Bug Fix: SUPPORT Assets in Graph and Migration List

**Date:** February 10, 2026  
**Severity:** HIGH (Risk of failed audits)  
**Status:** ✅ FIXED

---

## 🐛 Bug Description

### Problem
SUPPORT assets were incorrectly appearing in the graph visualization and migration list, even though they had `selected=False`. This created a critical risk:

1. **Visual Confusion**: Users saw SUPPORT assets in the graph when they shouldn't be there
2. **Checkbox Desynchronization**: The "Include in Migration" checkbox didn't match the graph
3. **Audit Risk**: If SUPPORT assets were accidentally migrated, audits would fail
4. **Design Violation**: SUPPORT assets are meant for agent context only, NOT for migration

### Expected Behavior
- **CORE Assets**: 
  - ✅ Appear in graph
  - ✅ `selected=True`
  - ✅ Included in migration
  
- **SUPPORT Assets**: 
  - ❌ Do NOT appear in graph
  - ❌ `selected=False`
  - ❌ NOT included in migration
  - ✅ Available as context for agents
  
- **IGNORED Assets**: 
  - ❌ Completely excluded from everything

---

## 🔍 Root Cause Analysis

### File: `apps/api/routers/triage.py`
### Line: 363

**Original Code (INCORRECT):**
```python
# Transform Agent Nodes to ReactFlow Nodes
final_nodes = []
graph_eligible = [n for n in rf_nodes if n.get("category") != "IGNORED"]  # ❌ BUG HERE
```

**Issue:** This filter allowed both CORE **and** SUPPORT assets into the graph, when only CORE should be included.

**Logic Flow:**
1. Triage runs, discovers 100 files
2. Agent S classifies: 60 CORE, 30 SUPPORT, 10 IGNORED
3. Backend creates assets with correct `selected` flags:
   - CORE: `selected=True` ✅
   - SUPPORT: `selected=False` ✅
   - IGNORED: Not stored ✅
4. **BUG**: Graph construction uses incorrect filter
5. Result: Graph contains 90 nodes (60 CORE + 30 SUPPORT) ❌
6. Frontend shows all 90 in graph, but only 60 have checkboxes checked
7. User confusion: "Why are these in the graph if they're not selected?"

---

## ✅ Solution

### Code Change

**File:** `apps/api/routers/triage.py`  
**Line:** 363-365

```python
# Transform Agent Nodes to ReactFlow Nodes
final_nodes = []
# FIX: Only CORE assets go to the graph. SUPPORT assets provide context but are NOT migrated.
graph_eligible = [n for n in rf_nodes if n.get("category") == "CORE"]  # ✅ FIXED
```

### Impact
- **Before Fix**: Graph contained CORE + SUPPORT (incorrect)
- **After Fix**: Graph contains only CORE (correct)
- **SUPPORT assets**: Still persisted in database for agent context, but NOT in graph
- **Backward Compatibility**: ✅ 100% compatible (existing projects unaffected until re-triaged)

---

## 🧪 Testing & Verification

### Automated Test

Run the verification script:
```bash
python verify_support_asset_fix.py
```

**Expected Output:**
```
TEST 1: CORE Assets
  Total CORE assets: 60
  CORE in graph: 60
  CORE selected: 60
  ✓ PASS: All CORE assets in graph and selected

TEST 2: SUPPORT Assets (Critical Fix)
  Total SUPPORT assets: 30
  SUPPORT in graph: 0
  SUPPORT selected: 0
  ✓ PASS: SUPPORT assets NOT in graph (correct!)

TEST 3: IGNORED Assets
  Total IGNORED assets: 0
  IGNORED in graph: 0
  IGNORED selected: 0
  ✓ PASS: IGNORED assets NOT in graph (correct!)
```

### Manual Test Steps

1. **Start Backend:**
   ```bash
   python run.py
   ```

2. **Open Frontend:**
   - Navigate to any project
   - Go to **Triage** stage

3. **Upload Source Files:**
   - Upload a mix of files (e.g., 10 SQL scripts, 5 config files, 2 README.md)

4. **Run Triage:**
   - Click "Run Triage"
   - Wait for Agent S to classify assets

5. **Verify Fix:**
   - **Graph Visualization:**
     - ✅ Should show only CORE assets (e.g., 10 SQL scripts)
     - ❌ Should NOT show SUPPORT assets (e.g., config files, readme)
   
   - **Asset List (right panel):**
     - CORE assets: Checkbox ✅ checked, visible in graph
     - SUPPORT assets: Checkbox ❌ unchecked, NOT in graph
   
   - **Toggle Checkbox:**
     - Uncheck a CORE asset → disappears from graph ✅
     - Check a CORE asset → reappears in graph ✅
     - SUPPORT assets never appear in graph regardless of checkbox ✅

---

## 📊 Before/After Comparison

### Before Fix

```
PROJECT: Customer_Migration
├── Assets Discovered: 100 files
├── Classification:
│   ├── CORE: 60 (main ETL scripts)
│   ├── SUPPORT: 30 (config files, DDL scripts, documentation)
│   └── IGNORED: 10 (temp files, backups)
│
├── Graph Nodes: 90 ❌ INCORRECT
│   ├── CORE: 60
│   └── SUPPORT: 30 ❌ SHOULD NOT BE HERE
│
└── Migration List: 60 ✅ Correct
    └── CORE: 60 (selected=True)
    
⚠️ PROBLEM: Graph shows 90 nodes, but only 60 are selected for migration
```

### After Fix

```
PROJECT: Customer_Migration
├── Assets Discovered: 100 files
├── Classification:
│   ├── CORE: 60 (main ETL scripts)
│   ├── SUPPORT: 30 (config files, DDL scripts, documentation)
│   └── IGNORED: 10 (temp files, backups)
│
├── Graph Nodes: 60 ✅ CORRECT
│   └── CORE: 60 (all selected=True)
│
├── Migration List: 60 ✅ Correct
│   └── CORE: 60 (selected=True)
│
└── Context for Agents: 90 ✅ Correct
    ├── CORE: 60 (migration + context)
    └── SUPPORT: 30 (context only, not migrated)
    
✅ RESULT: Graph and migration list are synchronized, SUPPORT provides context only
```

---

## 🎯 Why This Matters

### Business Impact

1. **Audit Compliance:**
   - SUPPORT assets (like config files) are NOT business logic
   - Including them in migration scope would fail audit reviews
   - Users must clearly see what's being migrated vs. what's just context

2. **User Trust:**
   - Graph must accurately represent migration scope
   - Checkbox state must match graph visibility
   - No surprises during final review

3. **Agent Intelligence:**
   - SUPPORT assets still provide valuable context
   - Agents can reference config files, DDL scripts, etc.
   - But these don't become migration deliverables

### Technical Alignment

The fix enforces the **design principle** established in [STAGE_2_TRIAGE.md](../docs/stages/STAGE_2_TRIAGE.md):

> **SUPPORT**: Required for the build but not migrated directly (e.g., config files, DDL scripts).

---

## 🔄 Migration Strategy for Existing Projects

### For Projects Already Triaged

**Option 1: Re-run Triage (Recommended)**
- Go to Triage stage
- Click "Run Triage" again
- New graph will be generated with fix applied

**Option 2: Manual Cleanup (Alternative)**
If re-triaging is not desired, manually:
1. Uncheck all SUPPORT assets in the list
2. They will automatically disappear from the graph via `sync-graph`

### For New Projects
- ✅ Fix is automatically applied
- No action needed

---

## 📝 Related Files Modified

1. **apps/api/routers/triage.py** (Line 363-365)
   - Changed filter from `!= IGNORED` to `== CORE`
   - Added explanatory comment

2. **verify_support_asset_fix.py** (NEW)
   - Automated verification script
   - Tests all three asset categories
   - Provides clear pass/fail output

3. **BUG_FIX_SUPPORT_ASSETS.md** (THIS FILE)
   - Complete documentation of bug and fix

---

## 🚀 Deployment Checklist

- [x] Code fix applied to `triage.py`
- [x] Verification script created
- [x] Documentation written
- [ ] Manual testing completed (pending user confirmation)
- [ ] Existing projects re-triaged (if needed)
- [ ] Production deployment (when ready)

---

## 📞 Support

If you encounter issues with SUPPORT assets after this fix:

1. **Run verification script:**
   ```bash
   python verify_support_asset_fix.py
   ```

2. **Check project ID:**
   - Ensure you're testing a project that was triaged AFTER the fix

3. **Re-run triage:**
   - Sometimes the easiest solution is to click "Run Triage" again

4. **Report issues:**
   - Include project ID
   - Include verification script output
   - Include screenshot of graph + asset list

---

## 🎓 Lessons Learned

1. **Filter Logic is Critical:**
   - Always be explicit with filters (use `==` not `!=` when possible)
   - Negative filters (`!= IGNORED`) are harder to reason about

2. **Test All Asset Categories:**
   - CORE: Must be in graph
   - SUPPORT: Must NOT be in graph
   - IGNORED: Must NOT exist at all

3. **Documentation Matters:**
   - Clear design principles prevent bugs
   - When code diverges from docs, bugs appear

4. **User-Reported Bugs are Valuable:**
   - This bug was caught by user observation
   - Real-world usage reveals edge cases

---

**Document Version:** 1.0  
**Last Updated:** February 10, 2026  
**Status:** ✅ Complete
