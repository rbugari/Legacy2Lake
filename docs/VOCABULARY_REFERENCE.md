# Vocabulary Reference: Post-Drafting Execution Modes

**Version:** v4.3 (Sprint 3)  
**Last Updated:** 2026-04-10  
**Audience:** Users, Developers, QA

---

## Quick Reference Table

| Mode | Internal Name | User Path | Refinement | Risk | Best For | Next Stage |
|------|---------------|-----------|-----------|------|----------|------------|
| **Drafting Delivery** | `drafting_delivery` | Terminal | ❌ No | Low | Standard migrations | Governance → Certification |
| **Structured Refinement** | `structured_refinement` | Bounded | ✅ Yes (Medallion) | Low | Most enterprises | Run Refinement → Governance |
| **Intelligent Reengineering** | `intelligent_reengineering` | Advanced | ✅ Yes (Unrestricted) | Medium | Complex redesigns | Run Reengineering → Governance |

---

## Detailed Definitions

### 1. Drafting Delivery (`drafting_delivery`)

**What:** Assets are finished after Drafting; no further optimization or refinement applied.

**When to Choose:** 
- Direct SQL translations meet your needs
- Speed to delivery is the primary goal
- You want to skip intermediate optimization stages

**Expected Outcome:** 
- Functionally correct Snowflake/PySpark/dbt code in-hand immediately
- No architectural improvements applied

**User Workflow:**
```
Drafting Complete → Select "Drafting Delivery" 
→ Refinement Stage SKIPPED 
→ Governance Stage AVAILABLE 
→ Proceed to Certification
```

**UI Messaging:**
- Decision Gate: "Assets are ready for certification as-is. Skip Refinement and proceed directly to Governance."
- RefinementView: "Refinement Disabled (Drafting Delivery selected)"
- StageHeader: "Refinement Skipped — Drafting Delivery Selected"

**Backend:**
- `POST /refine/start` returns 400: "Refinement is not available for projects in Drafting Delivery mode."
- Status: "Blocked" in RefinementView
- Allows direct progression to Governance

---

### 2. Structured Refinement (`structured_refinement`)

**What:** Apply multi-layer medallion optimization (Bronze → Silver → Gold) with quality rules and governance compliance.

**When to Choose:**
- You want best practices and governance compliance within known patterns
- Medallion architecture (layered data modeling) aligns with your strategy
- You need consistency and performance optimization

**Expected Outcome:**
- Modernized, well-structured code with:
  - Medallion layer separation (Bronze/Silver/Gold)
  - Naming conventions and standards compliance
  - Performance optimizations (indexes, partitions)
  - Governance and audit patterns

**User Workflow:**
```
Drafting Complete → Select "Structured Refinement" 
→ Refinement Stage AVAILABLE 
→ Run Refinement (applies medallion patterns) 
  or Skip to Governance
→ Proceed to Certification
```

**UI Messaging:**
- Decision Gate: "Apply multi-layer medallion optimization with quality rules. Refinement stage will enhance consistency, governance, and best practices compliance."
- RefinementView: "Structured Refinement Ready — Multi-layer medallion optimization available"
- StageHeader: "Structured Refinement — Medallion Optimization"

**Backend:**
- `POST /refine/start` returns 200: Refinement allowed
- Refinement prompt includes: *"Apply multi-layer medallion patterns (Bronze → Silver → Gold) with focus on consistency and quality rules."*
- Status: "Ready" in RefinementView
- User can review refinement suggestions or proceed to Governance

---

### 3. Intelligent Reengineering (`intelligent_reengineering`)

**What:** Apply advanced optimizations including data model redesign, query pattern optimization, and architectural improvements.

**When to Choose:**
- Legacy architecture benefits from reimagining
- You want platform suggestions for architectural improvements
- Higher risk acceptable for potential gains

**Expected Outcome:**
- Intelligently transformed code with:
  - Schema redesigns (if beneficial)
  - Query optimization patterns
  - Architectural improvements and suggestions
  - Performance enhancements beyond standard patterns
  - Potential higher-order transformations

**User Workflow:**
```
Drafting Complete → Select "Intelligent Reengineering" 
→ Refinement Stage AVAILABLE 
→ Run Reengineering (applies advanced optimizations)
  or Skip to Governance (revert to direct path)
→ Review suggestions carefully (higher risk)
→ Proceed to Certification
```

**UI Messaging:**
- Decision Gate: "Apply advanced optimizations and architectural improvements. Reengineering may suggest schema redesigns, query improvements, and structural changes."
- RefinementView: "Intelligent Reengineering Ready — Advanced architectural optimization available"
- StageHeader: "Intelligent Reengineering — Advanced Optimization"

**Backend:**
- `POST /refine/start` returns 200: Refinement allowed
- Refinement prompt includes: *"Apply intelligent reengineering: redesign data models, optimize query patterns, suggest architectural changes. Accept higher-order transformations."*
- Status: "Ready" in RefinementView
- User can review reengineered output or revert to Drafting for conservative mode

---

## Implementation Details

### Database Schema

```sql
ALTER TABLE utm_projects
ADD COLUMN post_drafting_mode VARCHAR(50) 
  CHECK (post_drafting_mode IN (
    'drafting_delivery',
    'structured_refinement',
    'intelligent_reengineering'
  ));

ALTER TABLE utm_projects
ADD COLUMN post_drafting_mode_set_at TIMESTAMPTZ;
```

**No ongoing schema changes.** Existing schema supports all three modes.

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/projects/{project_id}/set-post-drafting-mode` | POST | Set the execution mode after Drafting |
| `/projects/{project_id}/get-post-drafting-mode` | GET | Retrieve the selected mode |
| `/refine/start` | POST | Start refinement; validates mode before proceeding |

### Governance Logic

**Flow Control in `governance.py`:**
- **If mode = `drafting_delivery`**: Block refinement, explain terminal path, allow skip to Governance
- **If mode = `structured_refinement`**: Allow refinement with medallion strategy
- **If mode = `intelligent_reengineering`**: Allow refinement with advanced strategy
- **If mode = `None`**: Require mode selection, show all options

---

## Code Examples

### Backend: Retrieving and Using Mode

```python
# Get the selected mode
mode = await db.get_post_drafting_mode(project_id)

# Check for drafting_delivery (terminal)
if mode == 'drafting_delivery':
    raise HTTPException(400, detail={
        "reason": "You selected the Drafting Delivery path. Assets proceed directly to Governance...",
        "next_action": "Proceed to Governance stage"
    })

# Proceed with mode-specific strategy
elif mode == 'structured_refinement':
    # Apply medallion patterns
    strategy = "Bronze → Silver → Gold with quality rules"
    
elif mode == 'intelligent_reengineering':
    # Apply advanced optimization
    strategy = "Architectural improvements and redesigns acceptable"
```

### Frontend: Selecting Mode

```tsx
const modes = [
  {
    id: "drafting_delivery",
    title: "Drafting Delivery",
    riskLevel: "low",
    description: "Assets are ready for certification as-is.",
  },
  {
    id: "structured_refinement",
    title: "Structured Refinement",
    riskLevel: "low",
    description: "Apply multi-layer medallion optimization with quality rules.",
  },
  {
    id: "intelligent_reengineering",
    title: "Intelligent Reengineering",
    riskLevel: "medium",
    description: "Apply advanced optimizations and architectural improvements.",
  },
];

// User clicks button to set mode
const response = await fetchWithAuth(
  `projects/${projectId}/set-post-drafting-mode`,
  { method: "POST", body: JSON.stringify({ mode: selectedMode }) }
);
```

### Frontend: Displaying Mode Status

```tsx
const modeConfig = {
  'drafting_delivery': {
    summary: 'Stage Skipped (Drafting Delivery)',
    allowRefinement: false,
    explanation: 'Project proceeds directly to Governance.',
  },
  'structured_refinement': {
    summary: 'Structured Refinement Ready',
    allowRefinement: true,
    explanation: 'Multi-layer medallion optimization available.',
  },
  'intelligent_reengineering': {
    summary: 'Intelligent Reengineering Ready',
    allowRefinement: true,
    explanation: 'Advanced architectural optimization available.',
  },
};

// Render based on selected mode
const config = modeConfig[postDraftingMode];
return <ModePanel summary={config.summary} />;
```

---

## Risk Levels Explained

### Low Risk
- **drafting_delivery**: Direct translation; no additional processing
- **structured_refinement**: Known patterns (medallion); bounded optimization

### Medium Risk
- **intelligent_reengineering**: Advanced transformations may alter structure; requires review

---

## User Decision Tree

```
After Drafting Completes:

1. Do you want refinement? 
   ├─ NO → Select "Drafting Delivery"
   │       └─ Assets proceed to Governance immediately
   │
   └─ YES → Do you want bounded optimization?
            ├─ YES → Select "Structured Refinement"
            │        └─ Apply medallion patterns, quality rules
            │
            └─ NO (Advanced optimization wanted) → Select "Intelligent Reengineering"
                                                    └─ Apply advanced optimizations, schema redesigns
```

---

## Common Questions

### Q: Can I change my mind after selecting a mode?
**A:** Yes. Re-run Drafting to reset your choice and re-select a different mode.

### Q: What if I choose Drafting Delivery by mistake?
**A:** Re-run Drafting (which clears the mode selection) and choose "Structured Refinement" or "Intelligent Reengineering" instead.

### Q: Which mode should I choose?
**A:** 
- **Drafting Delivery** if speed to delivery is critical
- **Structured Refinement** for most enterprise migrations
- **Intelligent Reengineering** for complex systems needing architectural reimagining

### Q: Will my assets change between modes?
**A:** 
- **Drafting Delivery**: No changes; direct translation only
- **Structured Refinement**: Enhanced with medallion patterns and quality rules
- **Intelligent Reengineering**: Potentially significant improvements (requires review)

---

## Related Documentation

- [Sprint 3 Vocabulary Specification](./planning/V4_3_SPRINT_3_VOCABULARY_SPECIFICATION.md) — Detailed semantic definitions
- [System Architecture](./SYSTEM_ARCHITECTURE.md) — Decision gate and refinement orchestration
- [RELEASE_NOTES.md](./RELEASE_NOTES.md) — Version history and changes

---

**End of Vocabulary Reference**
