# Stage Sidebar Integration Guide

## Overview

The Stage Sidebar is a dynamic navigation component that adapts its content based on the current project stage (0-4). It replaces the horizontal tab system with a vertical sidebar that provides cleaner organization and better scalability.

## Files Created (Phase 1 Complete)

### Configuration & Hooks
- ✅ `apps/web/app/config/sidebar-sections.ts` - Section definitions for all 5 stages
- ✅ `apps/web/app/hooks/useSidebarMetrics.ts` - Auto-refreshing metrics hook

### Components
- ✅ `apps/web/app/components/navigation/StageSidebar.tsx` - Main sidebar wrapper
- ✅ `apps/web/app/components/navigation/SidebarHeader.tsx` - Stage-specific header
- ✅ `apps/web/app/components/navigation/SidebarSection.tsx` - Collapsible groups
- ✅ `apps/web/app/components/navigation/SidebarItem.tsx` - Individual nav items

### Backend
- ✅ `apps/api/routers/projects.py` - Added `GET /projects/{id}/sidebar-metrics?stage={stage}`
- ✅ `apps/api/services/persistence_service.py` - Added helper methods:
  - `get_quality_metrics_summary()`
  - `get_project_tech_stats()`
  - `get_code_validations()`
  - `get_governance_files()`

---

## Quick Start Integration

### Example: Integrating into TriageView (Stage 1)

**Before (Horizontal Tabs):**
```tsx
<div className="tabs-horizontal">
  <button className={activeTab === 'overview' ? 'active' : ''}>Overview</button>
  <button className={activeTab === 'graph' ? 'active' : ''}>Graph</button>
  // ... 11+ more tabs
</div>

{activeTab === 'overview' && <OverviewContent />}
{activeTab === 'graph' && <GraphView />}
```

**After (Stage Sidebar):**
```tsx
import StageSidebar from '@/app/components/navigation/StageSidebar';

export default function TriageView({ projectId }: { projectId: string }) {
  const [activeSection, setActiveSection] = useState('quick-info');

  return (
    <div className="flex h-screen">
      {/* Sidebar (replaces horizontal tabs) */}
      <StageSidebar
        stage={1}  // 1 = Triage
        projectId={projectId}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto p-6">
        {activeSection === 'quick-info' && <QuickAssessmentPanel />}
        {activeSection === 'graph' && <GraphView />}
        {activeSection === 'files' && <FileExplorer />}
        {activeSection === 'assets' && <AssetInventory />}
        {activeSection === 'tables' && <TableImpacts />}
        {activeSection === 'transformations' && <TransformationsView />}
        {activeSection === 'queries' && <QueriesView />}
        {activeSection === 'lineage' && <DataLineage />}
        {activeSection === 'dependencies' && <DependencyDAG />}
        {activeSection === 'quality' && <QualityMetrics />}
        {activeSection === 'pii' && <PIIAnalysis />}
        {activeSection === 'settings' && <ProjectSettings />}
      </div>
    </div>
  );
}
```

---

## Stage-Specific Sections

### Stage 0: Discovery (4 sections)
- Overview
- Upload Assets
- Files
- Settings

### Stage 1: Triage (13+ sections)
- Quick Info
- **Views** (collapsible group)
  - Graph
  - Files
  - Assets
  - Tables
- **Analysis** (collapsible group)
  - Transformations
  - Queries
  - Lineage
  - Dependencies
  - Quality
  - PII
- Tables
- **Config** (collapsible group)
  - Settings
  - Prompts
  - Models

### Stage 2: Drafting (7 sections)
- Progress
- **Output** (collapsible group)
  - Bronze Layer
  - Silver Layer
  - Gold Layer
  - All Files
  - Validation
- **Config** (collapsible group)
  - Generation Settings
  - Cartridge Config
  - Agent Matrix
  - Files
- Files

### Stage 3: Refinement (8 sections)
- Status
- **Review** (collapsible group)
  - Code Issues
  - Validation Results
  - Quality Report
  - Changes Log
- **Optimization** (collapsible group)
  - Performance Tuning
  - Best Practices
  - Agent Feedback
  - Diff Viewer
- **Actions** (collapsible group)
  - Re-run Refinement
  - Apply Fixes
  - Deploy Preview

### Stage 4: Governance (5 sections)
- Completion Status
- **Documentation** (collapsible group)
  - README
  - Architecture Docs
  - API Reference
  - Migration Guide
- **Handover** (collapsible group)
  - COP Bundle
  - Deployment Guide
  - Support Assets

---

## Features

### Auto-Refresh Metrics
The sidebar automatically fetches and displays live metrics:
- Updates every 3 seconds when a process is running
- Shows progress bars for active operations
- Displays badge counts for sections (e.g., "12 Assets", "5 Issues")

### Keyboard Shortcuts
- `Cmd+B` (Mac) or `Ctrl+B` (Windows): Toggle sidebar collapse

### Responsive Behavior
- **Desktop**: 256px wide sidebar
- **Collapsed**: 48px mini-sidebar with icons only
- **Mobile**: Overlay sidebar (future enhancement)

### Collapsible Groups
Sections with children (e.g., "Views", "Analysis") can be collapsed/expanded:
- Auto-expands when child is active
- State persisted in localStorage

---

## Backend API

### Endpoint: `GET /api/v1/projects/{projectId}/sidebar-metrics?stage={stage}`

**Response Structure:**
```json
{
  "executionStatus": "TRIAGED",
  "lastUpdate": "2026-02-13T15:30:00Z",
  
  // Stage 0: Discovery
  "fileCount": 15,
  "uploadStatus": "DISCOVERY",
  
  // Stage 1: Triage
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
  "partitionedTables": 5,
  
  // Stage 2: Drafting
  "generationProgress": 75,
  "currentAgent": "Agent-C",
  "filesGenerated": 36,
  "bronzeNodes": 18,
  "silverNodes": 12,
  "goldNodes": 6,
  
  // Stage 3: Refinement
  "refinementStatus": "REFINING",
  "issueCount": 3,
  "validationCount": 36,
  "qualityDelta": 5,
  
  // Stage 4: Governance
  "docsGenerated": true,
  "bundleReady": false
}
```

---

## Migration Steps (Phase 2)

### Step 1: Integrate into TriageView
1. Import `StageSidebar` component
2. Replace horizontal tabs with sidebar
3. Map old tab IDs to new section IDs
4. Test all 13 sections

### Step 2: Integrate into DraftingView
1. Add sidebar with `stage={2}`
2. Remove old navigation
3. Connect section IDs to content components

### Step 3: Integrate into RefinementView
1. Add sidebar with `stage={3}`
2. Connect refinement-specific sections

### Step 4: Create DiscoveryView & GovernanceView
1. New view for Stage 0 (if doesn't exist)
2. New view for Stage 4 (if doesn't exist)

### Step 5: Test Stage Transitions
1. Verify sidebar updates when moving between stages
2. Test metrics auto-refresh
3. Verify localStorage persistence

---

## Customization

### Adding New Sections
Edit `apps/web/app/config/sidebar-sections.ts`:

```typescript
// Example: Add new section to Stage 1
1: [
  {
    id: 'quick-info',
    label: 'Quick Info',
    icon: Info,
    badge: { type: 'quickAssessmentScore' }
  },
  {
    id: 'my-new-section',  // ← New section
    label: 'Custom View',
    icon: Star,
    badge: { type: 'customMetric' }
  },
  // ... existing sections
]
```

### Adding New Metrics
1. Update `SidebarMetrics` interface in `useSidebarMetrics.ts`
2. Add logic to backend endpoint in `projects.py`
3. Update `formatBadgeValue()` for custom formatting

---

## Testing Checklist

- [ ] Sidebar renders correctly for all 5 stages
- [ ] Sections collapse/expand properly
- [ ] Active section highlights correctly
- [ ] Metrics auto-refresh when process running
- [ ] Badge counts display correctly
- [ ] Keyboard shortcut (Cmd+B) works
- [ ] Collapsed state persists in localStorage
- [ ] No infinite loops or excessive API calls
- [ ] Mobile responsive (future)

---

## Known Limitations (Phase 1)

1. **Mobile Responsive**: Not yet implemented (requires overlay/modal behavior)
2. **Stage 0/4 Views**: May need to create dedicated views if they don't exist
3. **Migration**: Old tab system still in place (needs removal)
4. **Animations**: Basic transitions, can be enhanced

---

## Next Steps (Phase 2-4)

**Phase 2: Backend Integration (1.5 days)**
- ✅ Endpoint created
- ⏳ Test all metrics for each stage
- ⏳ Verify auto-refresh logic

**Phase 3: View Integration (2 days)**
- ⏳ Integrate into TriageView (most complex)
- ⏳ Integrate into DraftingView
- ⏳ Integrate into RefinementView
- ⏳ Create Discovery/Governance views

**Phase 4: Polish (1 day)**
- ⏳ Add animations (slide, fade, collapse)
- ⏳ Implement mobile responsive
- ⏳ Add accessibility (keyboard nav)
- ⏳ Performance testing

---

## Support

For questions or issues, refer to:
- [SIDEBAR_NAVIGATION_DESIGN.md](./SIDEBAR_NAVIGATION_DESIGN.md) - Full design spec
- [sidebar-sections.ts](../apps/web/app/config/sidebar-sections.ts) - Section definitions
- [useSidebarMetrics.ts](../apps/web/app/hooks/useSidebarMetrics.ts) - Hook implementation

**Status:** Phase 1 Complete ✅ (Config + Components)
