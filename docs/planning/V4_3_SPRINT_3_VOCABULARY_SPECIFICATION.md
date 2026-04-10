# Sprint 3: Post-Drafting Execution Modes — Vocabulary & Semantics Specification

**Status:** IMPLEMENTED  
**Owner:** Engineering + Product  
**Audience:** Backend, Frontend, QA  
**Date:** 2026-04-10

Implementation note (2026-04-10): Mode-aware governance messaging, mode-aware Agent C/Agent F strategy guidance, PromptAssembler hardening aliases, and focused validation tests are now in place.

---

## EXECUTIVE SUMMARY

Sprint 2 implemented the decision gate logic (`drafting_delivery` vs `structured_refinement` vs `intelligent_reengineering`) but uses inconsistent and unclear terminology across backend, frontend, docs, and prompts.

**Sprint 3 Goal:** Establish ONE authoritative vocabulary + consistent UI messaging + clear semantic distinction for all three modes, so that:
- Users understand exactly what each choice means before selecting
- Frontend UI text is unambiguous
- Backend logic matches user expectations
- Prompts reward the chosen strategy

---

## PART 1: SEMANTIC DEFINITIONS

### **Mode 1: `drafting_delivery` (Terminal Path)**

**Internal Name:** `drafting_delivery`  
**Display Name:** "Drafting Delivery" (or "Ready for Handover")  
**Strategy:** Assets are drafted and **finished**. No further modernization or refinement applied.

#### User Intent
- "I trust the LLM's translation. Ship it as-is."
- "I want artifacts in-hand for handover immediately."
- "I don't need multi-layer optimization."

#### Semantic Commitment
- **Refinement stage is SKIPPED entirely.**
- User proceeds directly to Governance (Stage 5) for audit and certification.
- No Agent-F (Refinement) execution.
- Assets are treated as "draft ready," not "optimized."

#### UI Decision Text
**Title:** Drafting Delivery  
**Description:** "Assets are ready for certification as-is. Skip Refinement and proceed directly to Governance review and certification."  
**Recommendation:** For standard SQL-to-Snowflake migrations with straightforward logic.

#### Backend Behavior
- `POST /refine/start` returns 400 with message: "Refinement is not available for projects in Drafting Delivery mode."
- `GET /stages/{project_id}/refinement` shows status: "Skipped (Drafting Delivery selected)".
- User can proceed to Governance by clicking "Skip to Governance" button.

#### Post-Drafting Workflow
```
Drafting Complete 
   ↓ (User selects "Drafting Delivery")
post_drafting_mode = "drafting_delivery"
   ↓
Refinement Stage SKIPPED (UI shows "Not Applicable")
   ↓
Governance Stage Available (User can proceed)
   ↓
Certification Complete
```

---

### **Mode 2: `structured_refinement` (Bounded Modernization)**

**Internal Name:** `structured_refinement`  
**Display Name:** "Structured Refinement"  
**Strategy:** Apply **multi-layer optimization** using medallion architecture (Bronze → Silver → Gold) with deterministic quality rules.

#### User Intent
- "I want the platform to apply quality rules and best practices."
- "Apply medallion-arch patterns but stay within standard practices."
- "Optimize for consistency, performance, and governance compliance."

#### Semantic Commitment
- **Refinement stage RUNS** with Agent-F (Refinement Agent).
- Agent-F sees prompt instruction: *"Apply structured medallion patterns (Bronze → Silver → Gold) with focus on consistency and governance compliance."*
- Refinement is **bounded**: no architectural redesign, no risky rewrites.
- Quality heuristics reward layer separation, naming conventions, performance patterns (indexes, partitions).
- Output is expected to be a "modernized translation," not a "reengineered system."

#### UI Decision Text
**Title:** Structured Refinement  
**Description:** "Apply medallion-layer optimization (Bronze → Silver → Gold) with quality rules. Refinement stage will enhance consistency, governance, and best practices compliance."  
**Recommendation:** For most enterprise migrations seeking modern data architecture within known patterns.

#### Backend Behavior
- `POST /refine/start` returns 200 and triggers Agent-F refinement.
- Refinement prompt includes: *"Mode: structured_refinement. Apply multi-layer medallion patterns with focus on consistency and quality rules."*
- Agent-F output expected to show layer-based optimizations, naming standards, etc.
- User can review refinement output or skip to Governance.

#### Post-Drafting Workflow
```
Drafting Complete 
   ↓ (User selects "Structured Refinement")
post_drafting_mode = "structured_refinement"
   ↓
Refinement Stage AVAILABLE (Run or Skip)
   ↓ (If Run → Agent-F executes with medallion prompt)
Refinement Complete or Skipped
   ↓
Governance Stage Available
   ↓
Certification Complete
```

---

### **Mode 3: `intelligent_reengineering` (Advanced Restructuring)**

**Internal Name:** `intelligent_reengineering`  
**Display Name:** "Intelligent Reengineering"  
**Strategy:** Apply **higher-order transformations** to redesign logic, optimize query patterns, and suggest architectural changes. More risk, higher reward.

#### User Intent
- "I want the platform to suggest improvements and optimizations beyond direct translation."
- "Redesign the data model if it improves performance or alignment."
- "Accept higher risk for potential architectural gains."

#### Semantic Commitment
- **Refinement stage RUNS** with Agent-F (Refinement Agent).
- Agent-F sees prompt instruction: *"Apply intelligent reengineering: redesign data models, optimize query patterns, suggest architectural changes. Accept higher-order transformations."*
- Refinement is **unbounded**: higher risk, more creative, may suggest significant rewrites.
- Quality heuristics reward architectural improvements, query optimization, schema normalization.
- Output is expected to be "intelligently transformed," not just "consistently layered."

#### UI Decision Text
**Title:** Intelligent Reengineering  
**Description:** "Apply advanced optimizations and architectural improvements. Reengineering may suggest schema redesigns, query improvements, and structural changes for better modernization."  
**Recommendation:** For complex legacy systems where architectural redesign and optimization are strategic goals.

#### Backend Behavior
- `POST /refine/start` returns 200 and triggers Agent-F refinement.
- Refinement prompt includes: *"Mode: intelligent_reengineering. Apply advanced optimizations, redesign where beneficial, suggest architectural improvements. Higher-order transformations acceptable."*
- Agent-F output expected to show architectural suggestions, redesigns, optimization patterns, etc.
- User can review reengineered output or revert to Drafting for conservative mode.

#### Post-Drafting Workflow
```
Drafting Complete 
   ↓ (User selects "Intelligent Reengineering")
post_drafting_mode = "intelligent_reengineering"
   ↓
Refinement Stage AVAILABLE (Run or Skip)
   ↓ (If Run → Agent-F executes with reengineering prompt)
Refinement Complete or Skipped
   ↓
Governance Stage Available
   ↓
Certification Complete
```

---

## PART 2: IMPLEMENTATION MAPPING

### **Database Schema**
```sql
ALTER TABLE utm_projects
ADD COLUMN post_drafting_mode VARCHAR(50) 
  CHECK (post_drafting_mode IN (
    'drafting_delivery',        -- Terminal: no refinement
    'structured_refinement',    -- Bounded: medallion patterns
    'intelligent_reengineering' -- Advanced: architectural redesign
  )),
ADD COLUMN post_drafting_mode_set_at TIMESTAMPTZ;
```

**No schema changes needed.** Current schema already supports all three modes.

---

### **Backend Service Layer**

**File:** `apps/api/services/persistence_service.py`

```python
# CURRENT STATE (already implemented)
async def set_post_drafting_mode(self, project_id: str, mode: str) -> bool:
    valid_modes = {'drafting_delivery', 'structured_refinement', 'intelligent_reengineering'}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode}")
    # Persist to DB...

async def get_post_drafting_mode(self, project_id: str) -> Optional[str]:
    # Retrieve from DB...

async def clear_post_drafting_mode(self, project_id: str) -> bool:
    # Reset on Drafting rerun...
```

**No service changes needed.** Current layer already handles all modes correctly.

---

### **Governance Layer Flow Control**

**File:** `apps/api/routers/governance.py`

#### Current Behavior (Good)
```python
if mode == 'drafting_delivery':
    # Terminal path: block refinement
    raise HTTPException(400, detail={
        "message": "Refinement is not available for projects in Drafting Delivery mode.",
        "reason": "You selected the terminal path. Assets proceed directly to Governance."
    })

elif mode in {'structured_refinement', 'intelligent_reengineering'}:
    # Both non-terminal modes allow refinement
    return {"allowed": True}
```

#### ISSUE TO FIX
Error message doesn't distinguish between the two non-terminal modes or explain the difference to users.

**Proposed Fix:**
```python
if mode == 'drafting_delivery':
    raise HTTPException(400, detail={
        "message": "Refinement is not available for projects in Drafting Delivery mode.",
        "reason": "You selected the Drafting Delivery path. Assets proceed directly to Governance for audit and certification.",
        "mode": "drafting_delivery"
    })

elif mode == 'structured_refinement':
    return {
        "allowed": True,
        "mode": "structured_refinement",
        "strategy": "Multi-layer medallion optimization with quality rules"
    }

elif mode == 'intelligent_reengineering':
    return {
        "allowed": True,
        "mode": "intelligent_reengineering",
        "strategy": "Advanced optimizations and architectural improvements"
    }

else:
    raise HTTPException(400, detail={
        "message": "Please select a post-Drafting mode.",
        "options": ["drafting_delivery", "structured_refinement", "intelligent_reengineering"]
    })
```

---

### **Refinement Prompt Layer**

**File:** `apps/api/services/prompt_assembler.py` (or wherever refinement prompts are loaded)

#### ISSUE TO CLARIFY
Agent-F currently receives refinement prompt but does NOT distinguish between `structured_refinement` and `intelligent_reengineering` modes.

**Proposed Fix:** Pass mode to prompt assembler and load mode-specific instructions.

**Example:**
```python
refinement_level_2_prompt = await prompt_service.load_cartridge_prompt(
    cartridge_name="refinement",
    tenant_id=tenant_id,
    project_id=project_id,
    post_drafting_mode=mode  # ← NEW: pass mode explicitly
)

# In prompt template, conditionally include:
if mode == 'structured_refinement':
    REFINEMENT_STRATEGY = "Apply multi-layer medallion patterns (Bronze → Silver → Gold) with focus on consistency, governance, and quality rules."
    
elif mode == 'intelligent_reengineering':
    REFINEMENT_STRATEGY = "Apply advanced optimizations: redesign data models, optimize query patterns, suggest architectural improvements. Higher-order transformations acceptable."
```

**Benefit:** Agent-F receives clear guidance on which strategy to apply.

---

### **Frontend UI Component: PostDraftingDecisionGate**

**File:** `apps/web/app/components/stages/PostDraftingDecisionGate.tsx`

#### Current State
```tsx
const modes = [
  {
    id: "drafting_delivery",
    title: "Drafting Delivery",
    description: "Assets are ready for handover as-is. Skip refinement and proceed to certification.",
  },
  {
    id: "structured_refinement",
    title: "Structured Refinement",
    description: "Apply multi-layer medallion optimization (Bronze → Silver → Gold) with quality rules.",
  },
  // intelligent_reengineering option is MISSING or stubbed
];
```

#### ISSUE
- `intelligent_reengineering` option is not shown or is stubbed.
- Option descriptions are clear but lack risk indicators.

#### Proposed Fix
```tsx
const modes = [
  {
    id: "drafting_delivery",
    title: "Drafting Delivery",
    description: "Assets are ready for certification as-is. Skip Refinement and proceed directly to Governance.",
    details: "No further optimization. Artifacts prepared for handover.",
    recommendation: "Standard SQL → Snowflake migrations with straightforward logic.",
    riskLevel: "low",
  },
  {
    id: "structured_refinement",
    title: "Structured Refinement",
    description: "Apply multi-layer medallion optimization with quality rules and governance compliance.",
    details: "Refinement stage enhances consistency, performance, and best practices within bounded patterns.",
    recommendation: "Most enterprise migrations seeking modern data architecture.",
    riskLevel: "low",
  },
  {
    id: "intelligent_reengineering",
    title: "Intelligent Reengineering",
    description: "Apply advanced optimizations and architectural improvements. Suggest redesigns where beneficial.",
    details: "Refinement stage may propose schema changes, query optimization, and structural improvements.",
    recommendation: "Complex legacy systems where architectural redesign is strategic.",
    riskLevel: "medium", // Higher reward, higher risk
  },
];
```

#### UI Rendering
Each mode card shows:
- Title + Description
- Risk level badge (Low / Medium)
- Details line
- Recommendation context

---

### **Frontend UI Component: RefinementView**

**File:** `apps/web/app/components/stages/RefinementView.tsx`

#### Current State
```tsx
// Refinement state based on post_drafting_mode
const refinementSummary = 
  postDraftingMode === 'drafting_delivery' 
    ? 'Refinement not applicable (Drafting Delivery selected)'
    : 'Ready to optimize and refine';
```

#### ISSUE
- Status label doesn't explain the semantic difference between `structured_refinement` and `intelligent_reengineering`.

#### Proposed Fix
```tsx
const refinementSummary = 
  postDraftingMode === 'drafting_delivery' 
    ? 'Stage skipped (Drafting Delivery selected). Project proceeds directly to Governance.'
    : postDraftingMode === 'structured_refinement'
    ? 'Multi-layer medallion optimization available. Apply quality rules and consistency patterns.'
    : postDraftingMode === 'intelligent_reengineering'
    ? 'Advanced reengineering available. Architectural improvements and redesigns may be suggested.'
    : 'Waiting for mode selection...';

const modeInfoBox = {
  'drafting_delivery': {
    strategy: 'Terminal Path',
    next_stage: 'Governance (audit & certification)',
    action: 'Skip to Governance',
  },
  'structured_refinement': {
    strategy: 'Bounded Medallion Optimization',
    next_stage: 'Run Refinement or Skip to Governance',
    action: 'Run Refinement',
  },
  'intelligent_reengineering': {
    strategy: 'Advanced Architectural Optimization',
    next_stage: 'Run Reengineering or Skip to Governance',
    action: 'Run Reengineering',
  },
};

// Display mode-specific info box
const modeInfo = modeInfoBox[postDraftingMode];
if (modeInfo) {
  return <ModeInfoPanel strategy={modeInfo.strategy} nextStage={modeInfo.next_stage} />;
}
```

---

### **Frontend UI Component: StageHeader / Navigation**

**File:** `apps/web/app/components/stages/RefinementView.tsx` (StageHeader section)

#### Current State
```tsx
<StageHeader 
  stageName="Refinement"
  isApproveDisabled={isRefinementRunning}
/>
```

#### ISSUE
- Header doesn't show which mode was selected.
- "Approve" button label is generic; should reflect actual action.

#### Proposed Fix
```tsx
const headerMessage = 
  postDraftingMode === 'drafting_delivery'
    ? 'Refinement Skipped (Drafting Delivery selected)'
    : postDraftingMode === 'structured_refinement'
    ? 'Structured Refinement - Medallion Optimization'
    : postDraftingMode === 'intelligent_reengineering'
    ? 'Intelligent Reengineering - Advanced Optimization'
    : 'Refinement Ready';

const actionLabel = 
  postDraftingMode === 'drafting_delivery'
    ? 'Skip to Governance'
    : 'Run Refinement'; // Or "Run Reengineering" for intelligent_reengineering

<StageHeader 
  stageName={headerMessage}
  isApproveDisabled={isRefinementRunning || postDraftingMode === 'drafting_delivery'}
  approveLabel={actionLabel}
/>
```

---

## PART 3: TERMINOLOGY CHECKLIST

**Before Sprint 3 closes:**

- [ ] Database schema documented and verified (schema already supports; no changes needed)
- [ ] Persistence service behavior verified (service already correct; no changes needed)
- [ ] Governance router flow control updated with mode-specific messages
- [ ] Refinement prompt layer updated to pass mode and load mode-specific instructions
- [ ] PostDraftingDecisionGate component updated with all three modes + risk levels
- [ ] RefinementView component updated with mode-specific summary + info box
- [ ] StageHeader updated with mode-aware labels and action buttons
- [ ] All UI terminal messages reviewed for consistency
- [ ] Governance error messages distinguish between modes
- [ ] Refinement prompts include mode-specific guidance for Agent-F
- [ ] Test suite updated to verify mode-specific UI behavior
- [ ] Documentation regenerated with final vocabulary

---

## PART 4: TERMINOLOGY TRANSITION GUIDE

**What Changes:**
1. UI text now explicitly shows which mode user selected
2. Governance messages explain why refinement is blocked (if drafting_delivery)
3. Refinement prompts guide Agent-F based on selected mode
4. Error messages are specific to the chosen path

**What Stays the Same:**
- Database schema (already correct)
- Service layer API (already correct)
- Backend routing logic (already correct)
- Test framework (can add new tests, but core logic unchanged)

**User Impact:**
- **Positive:** UI is now clearer about consequences of each choice
- **Positive:** Refinement behavior aligns with user expectation (bounded vs. unbounded)
- **Positive:** Handover artifacts document which mode was applied
- **Neutral:** No functional change to core pipeline; all three modes already work

---

## PART 5: SPRINT 3 IMPLEMENTATION ORDER

### Phase A: Backend Clarification (1-2 hours)
1. Update governance router to include mode-specific error messages
2. Update refinement prompt layer to pass mode and load mode-specific instructions
3. Verify persistence service already handles all three modes correctly
4. Update backend tests to verify mode-specific governance behavior

### Phase B: Frontend Localization (2-3 hours)
1. Update PostDraftingDecisionGate to show all three modes with risk levels + details
2. Update RefinementView to show mode-specific summary + info box
3. Update StageHeader to use mode-aware labels and action buttons
4. Verify all UI transitions work for each mode
5. Add frontend tests for mode-specific UI behavior

### Phase C: Documentation & Handover (1 hour)
1. Update RELEASE_NOTES.md with vocabulary clarification
2. Add vocabulary explainer to user docs
3. Generate updated system architecture diagram showing mode flows
4. Close Sprint 3 checklist

**Estimated Total:** 4-6 hours

---

## APPENDIX: Mode Decision Matrix

| Criterion | Drafting Delivery | Structured Refinement | Intelligent Reengineering |
|-----------|-------------------|-----------------------|---------------------------|
| **Refinement Applied** | No | Yes (Bounded) | Yes (Unbounded) |
| **Risk Level** | Low | Low | Medium |
| **Agent-F Involvement** | No | Yes | Yes |
| **Expected Output Type** | Direct Translation | Optimized Translation | Reengineered Architecture |
| **Medallion Layers** | Not applied | Bronze → Silver → Gold | Suggested changes to layers |
| **Schema Redesign** | No | No (Consistency focus) | Yes (Optimization focus) |
| **Best For** | Simple, straightforward migrations | Most enterprise migrations | Complex systems needing redesign |
| **Handover Timeline** | Immediate | 1-2 stages | 1-2 stages + review |
| **Governance Audit** | Yes (Standard) | Yes (Standard) | Yes (Higher scrutiny) |

---

**End of Sprint 3 Vocabulary Specification**
