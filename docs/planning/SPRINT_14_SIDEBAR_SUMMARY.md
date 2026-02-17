# Sprint 14 - Stage-Adaptive Sidebar Implementation (Phase 1 Complete)

**Date:** February 13, 2026  
**Feature:** Stage-Adaptive Sidebar Navigation  
**Status:** Phase 1 Complete ✅ (Config + Components + Backend)

---

## 🎯 Executive Summary

Implemented a **config-driven, stage-adaptive sidebar navigation system** that replaces the horizontal tab navigation in all project phases. The sidebar dynamically shows relevant sections based on project stage (0-4), reducing UI clutter and improving user experience.

**Problem Solved:** TriageView had 13+ horizontal tabs that were difficult to navigate and didn't scale well.

**Solution:** Vertical sidebar with collapsible groups, auto-updating badges, and stage-specific content that adapts as the project progresses through its lifecycle.

---

## ✅ What Was Completed

### Frontend Components (7 files)

1. **Configuration File**
   - File: `apps/web/app/config/sidebar-sections.ts` (265 lines)
   - Defines all sections for 5 stages (0-4)
   - Stage 0: 4 sections (Discovery)
   - Stage 1: 13+ sections (Triage - most complex)
   - Stage 2: 7 sections (Drafting)
   - Stage 3: 8 sections (Refinement)
   - Stage 4: 5 sections (Governance)
   - Helper functions: `getSectionsForStage()`, `getAllSectionIds()`, `findSectionById()`

2. **Custom Hook**
   - File: `apps/web/app/hooks/useSidebarMetrics.ts` (120 lines)
   - Fetches stage-specific metrics from backend
   - Auto-refreshes every 3s when process is running
   - Handles 20+ different metric types
   - Formats badge values (counts, percentages, deltas)

3. **Main Component**
   - File: `apps/web/app/components/navigation/StageSidebar.tsx` (130 lines)
   - Renders stage-appropriate sidebar
   - Keyboard shortcut: `Cmd+B` / `Ctrl+B` to toggle collapse
   - Persists collapsed state in localStorage
   - Shows mini-sidebar when collapsed (icons only)

4. **Child Components**
   - File: `apps/web/app/components/navigation/SidebarHeader.tsx` (100 lines)
     - Stage-specific header with quick metrics
     - Shows score card for Triage
     - Progress bar for Drafting
     - Quality delta for Refinement
   
   - File: `apps/web/app/components/navigation/SidebarSection.tsx` (110 lines)
     - Collapsible group wrapper
     - Auto-expands when child is active
     - Badge display from metrics
   
   - File: `apps/web/app/components/navigation/SidebarItem.tsx` (50 lines)
     - Individual nav item with icon + label + badge
     - Active state styling
     - Loading spinner when process running

5. **Example Component**
   - File: `apps/web/app/components/navigation/TriageViewExample.tsx` (200 lines)
   - Complete example showing integration pattern
   - Maps all 13 sections to content components
   - Includes migration notes and testing checklist

### Backend Implementation

6. **API Endpoint**
   - File: `apps/api/routers/projects.py` (modified)
   - Added: `GET /api/v1/projects/{id}/sidebar-metrics?stage={stage}`
   - Returns stage-specific metrics JSON
   - Auto-detects stage from project status if not provided
   - Helper functions:
     - `_detect_stage_from_status()` - Maps status to stage number
     - `_calculate_progress_from_logs()` - Estimates progress percentage
     - `_extract_current_agent()` - Detects active agent

7. **Database Helpers**
   - File: `apps/api/services/persistence_service.py` (modified)
   - Added 4 new methods:
     - `get_quality_metrics_summary()` - Aggregates quality scores, PII counts
     - `get_project_tech_stats()` - Source/target tech detection
     - `get_code_validations()` - Validation results from Sprint 8
     - `get_governance_files()` - Documentation readiness check

### Documentation

8. **Integration Guide**
   - File: `docs/planning/SIDEBAR_INTEGRATION_GUIDE.md` (300 lines)
   - Quick start examples
   - Section-by-section breakdown
   - API contract documentation
   - Migration steps for Phase 2
   - Testing checklist

9. **Design Specification**
   - File: `docs/planning/SIDEBAR_NAVIGATION_DESIGN.md` (existing, 1258 lines)
   - Complete design spec with ASCII mockups
   - Component architecture
   - Implementation roadmap

---

## 🎨 Key Features

### 1. Stage-Adaptive Content
- **Stage 0 (Discovery):** Simple upload/file management
- **Stage 1 (Triage):** Full analysis with 13+ sections in collapsible groups
- **Stage 2 (Drafting):** Generation progress + output layers
- **Stage 3 (Refinement):** Code review + optimization tools
- **Stage 4 (Governance):** Documentation + handover bundle

### 2. Live Metrics & Badges
- Auto-updating badges show:
  - Asset counts: "42 Assets"
  - Table counts: "18 Tables"
  - Issue counts: "3 Issues"
  - Progress percentages: "75%"
  - Quality deltas: "+5%"
- Fetched from backend every 3 seconds during active processes

### 3. Collapsible Groups
- Sections with children can collapse/expand
- Groups: "Views", "Analysis", "Config", "Output", "Review", "Optimization", "Documentation", "Handover"
- Auto-expands when child section is active
- State persisted in localStorage

### 4. Keyboard Shortcuts
- `Cmd+B` (Mac) or `Ctrl+B` (Windows): Toggle sidebar
- Shows hint in footer: "Cmd+B to toggle"

### 5. Responsive States
- **Expanded:** 256px wide with full labels
- **Collapsed:** 48px mini-sidebar with icon-only buttons
- **Mobile:** Overlay mode (future enhancement)

---

## 📊 Stage Breakdown

### Stage 0: Discovery (4 sections)
```
Overview
Upload Assets
Files
Settings
```

### Stage 1: Triage (13+ sections, 3 groups)
```
Quick Info
├─ Views ▼
│  ├─ Graph
│  ├─ Files
│  ├─ Assets
│  └─ Tables
├─ Analysis ▼
│  ├─ Transformations
│  ├─ Queries
│  ├─ Lineage
│  ├─ Dependencies
│  ├─ Quality
│  └─ PII
Tables
└─ Config ▼
   ├─ Settings
   ├─ Prompts
   └─ Models
```

### Stage 2: Drafting (7 sections, 2 groups)
```
Progress
├─ Output ▼
│  ├─ Bronze Layer
│  ├─ Silver Layer
│  ├─ Gold Layer
│  ├─ All Files
│  └─ Validation
└─ Config ▼
   ├─ Generation Settings
   ├─ Cartridge Config
   ├─ Agent Matrix
   └─ Files
```

### Stage 3: Refinement (8 sections, 3 groups)
```
Status
├─ Review ▼
│  ├─ Code Issues
│  ├─ Validation Results
│  ├─ Quality Report
│  └─ Changes Log
├─ Optimization ▼
│  ├─ Performance Tuning
│  ├─ Best Practices
│  ├─ Agent Feedback
│  └─ Diff Viewer
└─ Actions ▼
   ├─ Re-run Refinement
   ├─ Apply Fixes
   └─ Deploy Preview
```

### Stage 4: Governance (5 sections, 2 groups)
```
Completion Status
├─ Documentation ▼
│  ├─ README
│  ├─ Architecture Docs
│  ├─ API Reference
│  └─ Migration Guide
└─ Handover ▼
   ├─ COP Bundle
   ├─ Deployment Guide
   └─ Support Assets
```

---

## 🔌 API Contract

### GET /api/v1/projects/{projectId}/sidebar-metrics?stage={stage}

**Query Parameters:**
- `stage` (optional): 0-4 (auto-detected if not provided)

**Response (Stage 1 example):**
```json
{
  "executionStatus": "TRIAGED",
  "lastUpdate": "2026-02-13T15:30:00Z",
  "quickAssessment": {
    "score": 85,
    "readability": 90,
    "complexity": 75,
    "risk": "LOW"
  },
  "assetCount": 42,
  "tableCount": 18,
  "sourceTech": "SSIS",
  "targetTech": "Databricks",
  "qualityScore": 87.5,
  "columnsWithPii": 8,
  "partitionedTables": 5
}
```

---

## 🧪 Testing Status

### ✅ Completed
- All TypeScript files compile without errors
- Components properly typed (no `any` types)
- Import paths resolved correctly
- Backend endpoint implemented
- Database helper methods created

### ⏳ Pending (Phase 2)
- [ ] Manual testing of sidebar in browser
- [ ] Integration into existing views (TriageView, DraftingView, RefinementView)
- [ ] End-to-end testing with real project data
- [ ] Load testing (3s polling doesn't cause issues)
- [ ] Accessibility testing (keyboard navigation)

---

## 📁 File Inventory

### New Files Created (9)
1. `apps/web/app/config/sidebar-sections.ts` (265 lines)
2. `apps/web/app/hooks/useSidebarMetrics.ts` (120 lines)
3. `apps/web/app/components/navigation/StageSidebar.tsx` (130 lines)
4. `apps/web/app/components/navigation/SidebarHeader.tsx` (100 lines)
5. `apps/web/app/components/navigation/SidebarSection.tsx` (110 lines)
6. `apps/web/app/components/navigation/SidebarItem.tsx` (50 lines)
7. `apps/web/app/components/navigation/TriageViewExample.tsx` (200 lines)
8. `docs/planning/SIDEBAR_INTEGRATION_GUIDE.md` (300 lines)
9. `docs/planning/SPRINT_14_SIDEBAR_SUMMARY.md` (this file)

### Modified Files (2)
1. `apps/api/routers/projects.py` (+130 lines)
2. `apps/api/services/persistence_service.py` (+120 lines)

**Total:** 1525 new lines of code + documentation

---

## 🚀 Next Steps (Phase 2-4)

### Phase 2: Integration & Testing (2 days)
1. **Integrate into TriageView**
   - Replace horizontal tabs with StageSidebar
   - Map section IDs to content components
   - Remove old TABS array
   - Test all 13 sections

2. **Integrate into DraftingView**
   - Add sidebar with `stage={2}`
   - Connect generation progress
   - Test layer filters

3. **Integrate into RefinementView**
   - Add sidebar with `stage={3}`
   - Connect validation results
   - Test quality metrics

4. **Test End-to-End**
   - Navigate between stages
   - Verify metrics auto-refresh
   - Check badge counts accuracy
   - Test keyboard shortcuts

### Phase 3: Polish (1 day)
1. Add smooth animations (slide, fade, collapse)
2. Implement mobile responsive (overlay sidebar)
3. Accessibility improvements (ARIA labels, focus management)
4. Performance optimization (memoization, lazy loading)

### Phase 4: Deployment (0.5 days)
1. Final testing in staging
2. Update user documentation
3. Deploy to production
4. Monitor for issues

**Estimated Timeline:** 3.5 days remaining (6 days total)

---

## 📝 Migration Guide for Developers

### Before (Old Tab System)
```tsx
const TABS = ['overview', 'graph', 'files', ...];
const [activeTab, setActiveTab] = useState('overview');

<div className="tabs">
  {TABS.map(tab => (
    <button onClick={() => setActiveTab(tab)}>{tab}</button>
  ))}
</div>

{activeTab === 'overview' && <OverviewContent />}
```

### After (Sidebar System)
```tsx
import StageSidebar from '@/app/components/navigation/StageSidebar';

const [activeSection, setActiveSection] = useState('quick-info');

<div className="flex h-screen">
  <StageSidebar
    stage={1}
    projectId={projectId}
    activeSection={activeSection}
    onSectionChange={setActiveSection}
  />
  
  <div className="flex-1 overflow-auto p-6">
    {activeSection === 'quick-info' && <QuickAssessmentPanel />}
    {activeSection === 'graph' && <GraphView />}
    ...
  </div>
</div>
```

**Benefits:**
- ✅ Cleaner code (no massive arrays of tab definitions)
- ✅ Auto-updating badges (no manual state management)
- ✅ Collapsible groups (better organization)
- ✅ Keyboard shortcuts (better UX)
- ✅ Stage-adaptive (right tools at right time)

---

## 🔧 Configuration Example

### Adding a New Section

**1. Edit Config File** (`sidebar-sections.ts`):
```typescript
1: [  // Stage 1 (Triage)
  {
    id: 'my-new-section',
    label: 'Custom Analysis',
    icon: Star,  // from lucide-react
    badge: { type: 'customMetric' },
  },
  // ... other sections
]
```

**2. Update Backend Endpoint** (`projects.py`):
```python
if current_stage == 1:
    # ... existing metrics
    metrics["customMetric"] = await calculate_custom_metric(project_id)
```

**3. Render Content** (in view component):
```tsx
{activeSection === 'my-new-section' && (
  <CustomAnalysisPanel projectId={projectId} />
)}
```

---

## 🎯 Success Metrics

Phase 1 achieved:
- ✅ **Zero compilation errors** in all TypeScript files
- ✅ **Fully typed** components (no `any` types)
- ✅ **Backend endpoint** implemented and ready to test
- ✅ **Complete documentation** for integration
- ✅ **Example component** showing best practices

Phase 2 success criteria:
- [ ] All 3 views migrated (Triage, Drafting, Refinement)
- [ ] No infinite loops or excessive API calls
- [ ] Metrics update in < 1 second
- [ ] Badge counts match actual data
- [ ] Keyboard shortcut works in all browsers

---

## 📞 Support & Resources

### Documentation
- **Design Spec:** [SIDEBAR_NAVIGATION_DESIGN.md](./SIDEBAR_NAVIGATION_DESIGN.md)
- **Integration Guide:** [SIDEBAR_INTEGRATION_GUIDE.md](./SIDEBAR_INTEGRATION_GUIDE.md)
- **Example Component:** [TriageViewExample.tsx](../../apps/web/app/components/navigation/TriageViewExample.tsx)

### Key Files
- **Config:** [sidebar-sections.ts](../../apps/web/app/config/sidebar-sections.ts)
- **Hook:** [useSidebarMetrics.ts](../../apps/web/app/hooks/useSidebarMetrics.ts)
- **Main Component:** [StageSidebar.tsx](../../apps/web/app/components/navigation/StageSidebar.tsx)
- **Backend:** [projects.py](../../apps/api/routers/projects.py) (line 980+)

### Testing Commands
```bash
# Frontend type checking
cd apps/web
npm run type-check

# Backend testing
cd apps/api
pytest tests/test_sidebar_metrics.py

# Start dev server
npm run dev  # Frontend
python run.py  # Backend
```

---

## 🎉 Summary

**Phase 1 Complete!** 

The stage-adaptive sidebar system is fully implemented at the component level. All TypeScript files compile without errors, the backend endpoint is ready, and comprehensive documentation is in place.

**Next:** Integrate into existing views (TriageView, DraftingView, RefinementView) and test with real project data.

**Timeline:** 1/6 days complete (Phase 1), 5 days remaining (Phase 2-4)

---

**Status:** ✅ Ready for Phase 2 (Integration & Testing)
