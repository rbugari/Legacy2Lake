# Sprint 3 Implementation Plan: Vocabulary & Semantics

**Prepared For:** Engineering  
**Scope:** Backend + Frontend vocabulary clarification  
**Effort Estimate:** 4-6 hours  
**Risk Level:** Low (no schema/API changes; pure messaging/logic clarification)

---

## CHANGE LOG & FILE MAPPING

### **SECTION A: BACKEND CHANGES (Governance & Prompts)**

---

#### **CHANGE A-1: Update governance.py — Mode-Specific Error Messages**

**File:** `apps/api/routers/governance.py`  
**Lines:** 188-213  
**Current State:**
```python
if mode == 'drafting_delivery':
    raise HTTPException(400, detail={"message": "...terminal path. Refinement is not available."})
elif mode is None:
    raise HTTPException(400, detail={"message": "Please choose: structured_refinement or intelligent_reengineering"})
```

**Required Change:**
```python
if mode == 'drafting_delivery':
    raise HTTPException(400, detail={
        "message": "Refinement is not available for projects in Drafting Delivery mode.",
        "reason": "You selected the Drafting Delivery path. Assets proceed directly to Governance for audit and certification.",
        "mode": "drafting_delivery",
        "next_action": "Proceed to Governance stage"
    })
elif mode == 'structured_refinement':
    return {
        "allowed": True,
        "mode": "structured_refinement",
        "strategy": "Multi-layer medallion optimization with quality rules and governance compliance"
    }
elif mode == 'intelligent_reengineering':
    return {
        "allowed": True,
        "mode": "intelligent_reengineering",
        "strategy": "Advanced optimizations and architectural improvements. Schema redesigns may be suggested."
    }
elif mode is None:
    raise HTTPException(400, detail={
        "message": "Please select a post-Drafting execution mode.",
        "options": {
            "drafting_delivery": "Terminal path: proceed directly to Governance",
            "structured_refinement": "Bounded refinement with medallion optimization",
            "intelligent_reengineering": "Advanced reengineering with architectural optimization"
        }
    })
```

**Impact:** Governance now explains mode differences and next actions clearly.

---

#### **CHANGE A-2: Update prompt_assembler.py — Pass Mode to Refinement Prompt**

**File:** `apps/api/services/prompt_assembler.py` (locate where refinement prompts are assembled)  

**Search for:**
```python
# Search for where Level 2 (cartridge) refinement prompt is loaded
refinement_level_2_prompt = await load_cartridge_prompt(...)
```

**Required Change:**
Include mode parameter and conditionally insert strategy guidance.

**Example implementation:**
```python
async def assemble_refinement_prompt(
    self,
    tenant_id: str,
    project_id: str,
    cartridge_name: str = "refinement",
    post_drafting_mode: Optional[str] = None  # ← NEW
) -> str:
    """Assemble refinement prompt with mode-specific guidance."""
    
    # Load base Level 2 cartridge prompt
    level_2_prompt = await self.load_cartridge_prompt(
        cartridge_name=cartridge_name,
        tenant_id=tenant_id,
        project_id=project_id
    )
    
    # Add mode-specific strategy guidance
    mode_strategy = self._get_refinement_strategy(post_drafting_mode)
    
    # Inject strategy into prompt template
    refined_prompt = level_2_prompt.replace(
        "{{REFINEMENT_STRATEGY}}",
        mode_strategy or "Apply quality rules and consistency optimization."
    )
    
    return refined_prompt

def _get_refinement_strategy(self, mode: Optional[str]) -> str:
    """Return strategy guidance based on post-drafting mode."""
    strategies = {
        "structured_refinement": (
            "REFINEMENT_STRATEGY: Apply multi-layer medallion patterns (Bronze → Silver → Gold) "
            "with focus on consistency, governance compliance, and quality rules. "
            "Maintain schema structure; optimize naming conventions, indexing, and partitioning."
        ),
        "intelligent_reengineering": (
            "REFINEMENT_STRATEGY: Apply advanced optimizations including data model redesign, "
            "query pattern optimization, and architectural improvements. "
            "Higher-order transformations and schema redesigns are acceptable and encouraged."
        ),
    }
    return strategies.get(mode, "Apply quality rules and consistency patterns.")
```

**Caller Update:** In transpile.py or wherever refinement is triggered:
```python
# OLD
refinement_prompt = await prompt_assembler.assemble_refinement_prompt(
    tenant_id=tenant_id,
    project_id=project_id
)

# NEW
refinement_prompt = await prompt_assembler.assemble_refinement_prompt(
    tenant_id=tenant_id,
    project_id=project_id,
    post_drafting_mode=post_drafting_mode  # ← pass mode
)
```

**Impact:** Agent-F now receives clear guidance based on user's mode choice.

---

### **SECTION B: FRONTEND CHANGES (UI Components)**

---

#### **CHANGE B-1: Update PostDraftingDecisionGate.tsx — Show All Three Modes with Details**

**File:** `apps/web/app/components/stages/PostDraftingDecisionGate.tsx`  

**Current State (Partial):**
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
  // ← intelligent_reengineering usually missing or stubbed
];
```

**Required Change:**
```tsx
const modes = [
  {
    id: "drafting_delivery",
    title: "Drafting Delivery",
    icon: "rocket", // or appropriate icon
    riskLevel: "low",
    description: "Assets are ready for certification as-is.",
    details: "Skip Refinement and proceed directly to Governance for audit and certification. No further optimization applied.",
    recommendation: "Best for: Standard SQL → Snowflake migrations with straightforward logic.",
  },
  {
    id: "structured_refinement",
    title: "Structured Refinement",
    icon: "layers", // medallion layers
    riskLevel: "low",
    description: "Apply multi-layer medallion optimization with quality rules.",
    details: "Refinement stage enhances consistency, performance, and governance compliance within bounded medallion patterns (Bronze → Silver → Gold).",
    recommendation: "Best for: Most enterprise migrations seeking modern data architecture.",
  },
  {
    id: "intelligent_reengineering",
    title: "Intelligent Reengineering",
    icon: "sparkles", // or appropriate icon
    riskLevel: "medium",
    description: "Apply advanced optimizations and architectural improvements.",
    details: "Refinement stage may propose schema redesigns, query optimizations, and structural improvements for better modernization.",
    recommendation: "Best for: Complex legacy systems where architectural redesign is strategic.",
  },
];

// Render each mode
return (
  <div className="decision-gate-container">
    {modes.map(mode => (
      <ModeCard
        key={mode.id}
        mode={mode}
        selected={selectedMode === mode.id}
        onSelect={() => handleSelect(mode.id)}
      />
    ))}
  </div>
);

// ModeCard component
function ModeCard({ mode, selected, onSelect }) {
  return (
    <div className={`mode-card ${selected ? 'selected' : ''}`}>
      <div className="card-header">
        <h3>{mode.title}</h3>
        <span className={`risk-badge risk-${mode.riskLevel}`}>{mode.riskLevel}</span>
      </div>
      <p className="description">{mode.description}</p>
      <p className="details">{mode.details}</p>
      <p className="recommendation">{mode.recommendation}</p>
      <button 
        onClick={onSelect}
        className="select-btn"
      >
        {selected ? '✓ Selected' : 'Select'}
      </button>
    </div>
  );
}
```

**Impact:** Users now see all three modes clearly labeled, with risk levels and recommendations.

---

#### **CHANGE B-2: Update RefinementView.tsx — Mode-Aware Status & Info Box**

**File:** `apps/web/app/components/stages/RefinementView.tsx`

**Current State (around line 521-537, 579, 603):**
```tsx
const refinementSummary = 
  postDraftingMode === 'drafting_delivery' 
    ? 'Refinement not applicable (Drafting Delivery selected)'
    : 'Ready to optimize and refine';

// Status label (line 579)
<span>{isRefinementRunning ? 'Running' : isComplete ? 'Complete' : postDraftingMode === 'drafting_delivery' ? 'Blocked' : 'Ready'}</span>

// Button disabled (line 603)
disabled={isRefinementRunning || postDraftingMode === 'drafting_delivery'}
```

**Required Change:**
```tsx
// Comprehensive mode-to-info mapping
const modeInfoMap = {
  'drafting_delivery': {
    summary: 'Stage Skipped (Drafting Delivery)',
    strategy: 'Terminal Path',
    explanation: 'Project proceeds directly to Governance. No refinement will be applied.',
    nextStage: 'Governance (audit & certification)',
    actionLabel: 'Skip to Governance',
    allowRefinement: false,
  },
  'structured_refinement': {
    summary: 'Structured Refinement Ready',
    strategy: 'Bounded Medallion Optimization',
    explanation: 'Multi-layer optimization with quality rules and governance compliance.',
    nextStage: 'Run Refinement or Skip to Governance',
    details: 'Refinement will apply medallion patterns (Bronze → Silver → Gold) with focus on consistency and best practices.',
    actionLabel: 'Run Refinement',
    allowRefinement: true,
  },
  'intelligent_reengineering': {
    summary: 'Intelligent Reengineering Ready',
    strategy: 'Advanced Architectural Optimization',
    explanation: 'Advanced optimizations including potential schema redesigns and architectural improvements.',
    nextStage: 'Run Reengineering or Skip to Governance',
    details: 'Reengineering may propose higher-order transformations and design improvements.',
    actionLabel: 'Run Reengineering',
    allowRefinement: true,
  },
};

const modeInfo = modeInfoMap[postDraftingMode];

// Status label update
<span className={`status-label status-${postDraftingMode}`}>
  {isRefinementRunning 
    ? 'Running...' 
    : isComplete 
    ? 'Complete' 
    : modeInfo?.summary || 'Waiting for mode selection'}
</span>

// Info box to display before refinement action
{modeInfo && (
  <div className={`mode-info-box mode-${postDraftingMode}`}>
    <div className="info-header">
      <h4>{modeInfo.strategy}</h4>
      <span className="info-badge">{modeInfo.summary}</span>
    </div>
    <p className="info-explanation">{modeInfo.explanation}</p>
    {modeInfo.details && (
      <details>
        <summary>Details</summary>
        <p>{modeInfo.details}</p>
      </details>
    )}
    <p className="info-next-stage">
      <strong>Next:</strong> {modeInfo.nextStage}
    </p>
  </div>
)}

// Button disabled and label update
<button 
  onClick={handleRunRefinement}
  disabled={isRefinementRunning || !modeInfo?.allowRefinement}
  className="run-refinement-btn"
>
  {modeInfo?.actionLabel || 'Run Refinement'}
</button>
```

**Impact:** RefinementView now shows mode-specific guidance and appropriate actions.

---

#### **CHANGE B-3: Update RefinementView.tsx — Stage Header with Mode-Aware Labels**

**File:** `apps/web/app/components/stages/RefinementView.tsx`  
**Location:** StageHeader section (around line 639-642)

**Current State:**
```tsx
<StageHeader
  stageName={postDraftingMode === 'drafting_delivery' ? 'Refinement Disabled' : 'Ready to Refine'}
  message="..."
  isApproveDisabled={isRefinementRunning}
/>
```

**Required Change:**
```tsx
// Compute stage header text based on mode
const stageHeaderConfig = {
  'drafting_delivery': {
    stageName: 'Refinement Skipped',
    subtitle: 'Drafting Delivery Selected',
    message: 'Project proceeds directly to Governance for audit and certification.',
    actionLabel: 'Skip to Governance',
  },
  'structured_refinement': {
    stageName: 'Structured Refinement',
    subtitle: 'Medallion Optimization',
    message: 'Apply multi-layer optimization with quality rules and consistency patterns.',
    actionLabel: 'Run Refinement',
  },
  'intelligent_reengineering': {
    stageName: 'Intelligent Reengineering',
    subtitle: 'Advanced Optimization',
    message: 'Apply advanced optimizations and potential architectural improvements.',
    actionLabel: 'Run Reengineering',
  },
};

const headerConfig = stageHeaderConfig[postDraftingMode] || {
  stageName: 'Refinement',
  message: 'Waiting for mode selection...',
  actionLabel: 'Proceed',
};

// Render stage header
<StageHeader
  stageName={headerConfig.stageName}
  subtitle={headerConfig.subtitle}
  message={headerConfig.message}
  isApproveDisabled={isRefinementRunning || postDraftingMode === 'drafting_delivery'}
  approveLabel={headerConfig.actionLabel}
/>
```

**Impact:** Stage header now clearly reflects which mode was selected and what action is available.

---

### **SECTION C: TESTING CHANGES**

---

#### **CHANGE C-1: Add Test Case for Mode-Specific Governance Messages**

**File:** `tests/test_sprint2_post_drafting_mode.py`  
**Add new test:**

```python
def test_governance_error_messages_mode_specific(client, mock_db):
    """Verify governance returns mode-specific error messages when refinement is blocked."""
    project_id = "test-project-123"
    
    # Case 1: drafting_delivery mode
    mock_db.get_post_drafting_mode = AsyncMock(return_value='drafting_delivery')
    response = client.post(f"/refine/start", json={"project_id": project_id})
    
    assert response.status_code == 400
    assert response.json()["detail"]["mode"] == "drafting_delivery"
    assert "Governance" in response.json()["detail"]["reason"]
    
    # Case 2: structured_refinement mode
    mock_db.get_post_drafting_mode = AsyncMock(return_value='structured_refinement')
    response = client.post(f"/refine/start", json={"project_id": project_id})
    
    assert response.status_code == 200  # allowed
    assert response.json()["mode"] == "structured_refinement"
    
    # Case 3: intelligent_reengineering mode
    mock_db.get_post_drafting_mode = AsyncMock(return_value='intelligent_reengineering')
    response = client.post(f"/refine/start", json={"project_id": project_id})
    
    assert response.status_code == 200  # allowed
    assert response.json()["mode"] == "intelligent_reengineering"
```

**Impact:** Tests verify mode-specific error messaging works.

---

#### **CHANGE C-2: Add Frontend Test for Mode-Specific UI Display**

**File:** `tests/frontend/stages/RefinementView.test.tsx`  
**Add new test:**

```typescript
describe('RefinementView Mode-Aware Rendering', () => {
  it('should display mode-specific summary for drafting_delivery', async () => {
    const { getByText, getByTestId } = render(
      <RefinementView postDraftingMode="drafting_delivery" />
    );
    
    expect(getByText('Refinement Skipped (Drafting Delivery)')).toBeInTheDocument();
    expect(getByText('Skip to Governance')).toBeInTheDocument();
  });

  it('should display mode-specific summary for structured_refinement', async () => {
    const { getByText, getByTestId } = render(
      <RefinementView postDraftingMode="structured_refinement" />
    );
    
    expect(getByText('Structured Refinement Ready')).toBeInTheDocument();
    expect(getByText('Multi-layer medallion optimization')).toBeInTheDocument();
    expect(getByText('Run Refinement')).toBeInTheDocument();
  });

  it('should display mode-specific summary for intelligent_reengineering', async () => {
    const { getByText } = render(
      <RefinementView postDraftingMode="intelligent_reengineering" />
    );
    
    expect(getByText('Intelligent Reengineering Ready')).toBeInTheDocument();
    expect(getByText('Advanced Architectural Optimization')).toBeInTheDocument();
    expect(getByText('Run Reengineering')).toBeInTheDocument();
  });
});
```

**Impact:** Frontend UI correctly renders mode-specific labels.

---

### **SECTION D: DOCUMENTATION UPDATES**

---

#### **CHANGE D-1: Update RELEASE_NOTES.md**

**File:** `docs/RELEASE_NOTES.md`  
**Add section under "Sprint 3":**

```markdown
## Sprint 3: Post-Drafting Execution Modes — Vocabulary & Semantics Clarification

### What Changed
- **Refined Mode Terminology:** Clarified semantic differences between three post-Drafting execution paths:
  - **Drafting Delivery (Terminal):** No refinement; direct to Governance
  - **Structured Refinement (Bounded):** Multi-layer medallion optimization with quality rules
  - **Intelligent Reengineering (Advanced):** Architectural improvements and schema redesigns
  
- **Backend Updates:**
  - Governance router now returns mode-specific error messages
  - Refinement prompts now receive mode parameter and load mode-specific strategies
  - Agent-F gets clear guidance on which optimization strategy to apply

- **Frontend Updates:**
  - PostDraftingDecisionGate now shows all three modes with risk levels and recommendations
  - RefinementView displays mode-specific summaries, strategy explanations, and action labels
  - StageHeader reflects mode choice and available actions

### User Impact
- **Clarity:** UI now explicitly shows consequences of each mode choice
- **Control:** Users understand which path they selected and what happens next
- **Guidance:** Refinement prompts align with user's mode choice, improving output quality

### Data Schema
No schema changes. Existing `post_drafting_mode` column supports all three modes.

### Backward Compatibility
✅ Fully compatible. Mode selection persists; existing projects retain their mode choice.
```

**Impact:** Release notes document vocabulary clarification for users and stakeholders.

---

#### **CHANGE D-2: Create Vocabulary Reference Guide**

**File:** `docs/VOCABULARY_REFERENCE.md`  
**Create new file:**

```markdown
# Vocabulary Reference: Post-Drafting Execution Modes

## Quick Reference

| Mode | Internal Name | User Path | Refinement | Risk | Best For |
|------|---------------|-----------|-----------|------|----------|
| Drafting Delivery | `drafting_delivery` | Terminal | ❌ No | Low | Standard migrations |
| Structured Refinement | `structured_refinement` | Bounded | ✅ Yes (Medallion) | Low | Most enterprises |
| Intelligent Reengineering | `intelligent_reengineering` | Advanced | ✅ Yes (Unrestricted) | Medium | Complex redesigns |

## Detailed Definitions

### Drafting Delivery
- **What:** Assets are finished after Drafting; no further optimization.
- **When to Choose:** When direct SQL translation meets your needs.
- **Expected Outcome:** Functionally correct Snowflake/PySpark/dbt code in-hand immediately.
- **Next Stage:** Governance (audit & certification).
- **User Effort:** Minimal review; ready for handover.

### Structured Refinement
- **What:** Apply medallion-layer optimization (Bronze → Silver → Gold) with quality rules.
- **When to Choose:** When you want best practices and governance compliance within known patterns.
- **Expected Outcome:** Modernized, well-structured code with consistency, performance, and governance patterns.
- **Next Stage:** Run Refinement or skip to Governance.
- **User Effort:** Review refinement suggestions; curate as needed.

### Intelligent Reengineering
- **What:** Apply advanced optimizations including data model redesign and architectural improvements.
- **When to Choose:** When legacy architecture benefits from reimagining; higher risk, higher reward.
- **Expected Outcome:** Reengineered architecture with suggested improvements, optimizations, and potential schema changes.
- **Next Stage:** Run Reengineering or revert to Drafting.
- **User Effort:** Careful review; may require technical re-evaluation.

## Code Examples

### Backend: Mode-Specific Refinement Prompt

```python
# In prompt_assembler.py
if mode == 'structured_refinement':
    strategy = "Apply medallion patterns with consistency focus..."
elif mode == 'intelligent_reengineering':
    strategy = "Accept architectural improvements and schema redesigns..."
```

### Frontend: Mode Selection Display

```tsx
// In PostDraftingDecisionGate.tsx
const modes = [
  { id: 'drafting_delivery', title: '...', riskLevel: 'low' },
  { id: 'structured_refinement', title: '...', riskLevel: 'low' },
  { id: 'intelligent_reengineering', title: '...', riskLevel: 'medium' },
];
```

---

**End of Reference**
```

**Impact:** New documentation serves as reference for users and developers.

---

## IMPLEMENTATION CHECKLIST

Before closing Sprint 3:

### Backend (2-3 hours)
- [ ] Update `apps/api/routers/governance.py` with mode-specific error messages (Change A-1)
- [ ] Update `apps/api/services/prompt_assembler.py` to pass mode and load mode-specific strategies (Change A-2)
- [ ] Add backend test for mode-specific governance messages (Change C-1)
- [ ] Verify persistence service is already correct (no changes needed)
- [ ] Run backend test suite: `pytest tests/ -k "post_drafting_mode"` → all passing
- [ ] Verify no new errors in tests/

### Frontend (2-3 hours)
- [ ] Update `PostDraftingDecisionGate.tsx` to show all three modes with details (Change B-1)
- [ ] Update `RefinementView.tsx` to show mode-aware summary & info box (Change B-2)
- [ ] Update `StageHeader` in `RefinementView.tsx` with mode-aware labels (Change B-3)
- [ ] Add frontend test for mode-specific UI display (Change C-2)
- [ ] Run frontend test suite: `npm test` → all passing
- [ ] Verify no TypeScript errors in components/
- [ ] Manual test: Navigate through decision gate for all three modes

### Documentation (1 hour)
- [ ] Update `RELEASE_NOTES.md` with Sprint 3 summary (Change D-1)
- [ ] Create `VOCABULARY_REFERENCE.md` (Change D-2)
- [ ] Update `SYSTEM_ARCHITECTURE.md` diagram if needed
- [ ] Review all new documentation for clarity

### Validation (0.5 hours)
- [ ] E2E test: Create project, run Drafting, select each mode, verify UI
- [ ] E2E test: Verify Governance blocks drafting_delivery mode
- [ ] E2E test: Verify both non-terminal modes allow refinement
- [ ] E2E test: Verify error messages are mode-specific
- [ ] Verify no console errors or warnings

---

## ROLLBACK PLAN

If Sprint 3 implementation causes issues:

1. **Backend Rollback:** Revert changes to `governance.py` and `prompt_assembler.py`; existing mode logic still works unchanged
2. **Frontend Rollback:** Revert UI component changes; existing decision gate and refinement view still functional
3. **Estimated Rollback Time:** 30 minutes (changes are isolated; no dependencies)

---

## SIGN-OFF CRITERIA

Sprint 3 is complete when:
- ✅ All three modes selectable and visually distinct
- ✅ Governance messages explain mode differences
- ✅ Refinement prompts receive mode-specific guidance
- ✅ RefinementView shows mode-specific summary and next actions
- ✅ Backend tests pass: `pytest tests/ -k "post_drafting_mode"` → all passing
- ✅ Frontend tests pass: `npm test` → all passing
- ✅ No TypeScript or console errors
- ✅ E2E test: all three modes route correctly through Governance/Refinement
- ✅ Documentation complete and accurate

---

**End of Sprint 3 Implementation Plan**
