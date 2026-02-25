# Sprint 14 Phase 2 - Day 5 TODO (February 20, 2026)

## 🎯 Quick Context

**Yesterday's Achievements (Day 4 - Feb 19):**
- ✅ Progress percentage reset fix
- ✅ 3 missing API endpoints created
- ✅ Database column errors fixed
- ✅ Components redesigned (compact dark theme)
- ✅ Sidebar status indicators implemented (green/yellow dots)
- ✅ Cartridge Settings loads default config

**Status:** All code working, services running, ready for testing

---

## 📋 Priority Tasks for Day 5

### 🧪 Testing & Validation (HIGH PRIORITY)

**1. Test Sidebar Status Indicators**
- [ ] Open project in Discovery stage → verify no dots on non-data sections
- [ ] Navigate to Triage stage
  - [ ] Before analysis: verify yellow dots on "Views" and "Analysis" sections
  - [ ] Run Triage execution
  - [ ] After analysis: verify green dots appear when `assetCount > 0`
- [ ] Navigate to Drafting stage
  - [ ] Before generation: verify yellow dots on "Execution" and "Output" sections
  - [ ] Run code generation pipeline
  - [ ] During execution: verify yellow dot continues (or stays yellow if in progress)
  - [ ] After completion: verify green dots when `filesGenerated > 0`
- [ ] Navigate to Refinement stage
  - [ ] Before refinement: verify yellow dot on "Review" section
  - [ ] After refinement starts: verify green dot appears

**2. Test Cartridge Settings**
- [ ] Open project that was created with destination="pyspark"
  - [ ] Navigate to Drafting → Cartridge Settings
  - [ ] Verify "PySpark Native" is pre-selected
- [ ] Open project created with destination="fabric"
  - [ ] Navigate to Drafting → Cartridge Settings
  - [ ] Verify "MS Fabric" is pre-selected
- [ ] Change cartridge selection (e.g., pyspark → snowflake)
  - [ ] Save and refresh page
  - [ ] Verify selection persists (reads from registry)

**3. Test Progress Reset**
- [ ] Navigate to Drafting stage
- [ ] Run code generation pipeline to completion (100%)
- [ ] Without refreshing page, run pipeline again
- [ ] Verify progress resets to 0% at start

**4. Verify API Endpoints**
- [ ] Open browser DevTools (F12) → Network tab
- [ ] Navigate through all stages (Discovery, Triage, Drafting, Refinement)
- [ ] Filter by status code "404"
- [ ] Verify zero 404 errors (especially `/registry`, `/generation/stats`, `/generation/summary`)

**5. Test Compact Dark Theme**
- [ ] Navigate to Drafting → Generated Output → Generation Stats
  - [ ] Verify dark background (gray-900)
  - [ ] Verify compact 2x2 grid layout
  - [ ] Verify text is readable (white on dark)
- [ ] Navigate to Drafting → Generated Output → Generation Summary
  - [ ] Verify compact design
  - [ ] Verify no "Drafting Philosophy" banner
  - [ ] Verify no "Project Structure" section

---

### 🔧 Bug Fixes (IF ISSUES FOUND)

**If Status Dots Don't Appear:**
```bash
# 1. Check browser console (F12)
# 2. Look for React errors
# 3. Check metrics API returns data:
curl http://localhost:8085/api/v1/projects/{PROJECT_ID}/sidebar-metrics?stage=2

# 4. If API works but dots don't show, check:
#    - Inspect element on sidebar header
#    - Verify w-2 h-2 rounded-full classes applied
#    - Check if statusColor variable is null (should be 'green' or 'yellow')
```

**If Status Dots Show Wrong Color:**
```typescript
// Add temporary debug logging to SidebarSection.tsx:
const statusColor = getSectionStatus(section, metrics);
console.log('[DEBUG] Section:', section.id, 'Metrics:', metrics, 'Status:', statusColor);
```

**If Dots Don't Update After Pipeline Run:**
```typescript
// Check useSidebarMetrics polling:
// 1. Verify polling interval is 10 seconds
// 2. Check executionStatus triggers continue polling
// 3. Verify backend /sidebar-metrics returns updated data
```

---

### 🐛 Known Issues to Investigate

1. **Collapsible Headers:** Status dots might only appear on non-collapsible headers
   - **Fix:** Add status dot JSX to collapsible button (line 69-82 in SidebarSection.tsx)
   - **Code to add:** Same dot rendering logic as non-collapsible headers

2. **Sidebar Stage Mismatch** (Carry over from Day 3)
   - **Symptom:** Sidebar shows wrong stage content
   - **Action:** Collect console logs if issue persists

3. **Execution Status Banner Persistence** (Carry over from Day 3)
   - **Symptom:** "Executing..." banner doesn't clear
   - **Action:** Monitor and document behavior

---

### 📝 Documentation (LOW PRIORITY)

- [ ] Add screenshots of status indicators to SPRINT_14_PHASE_2_SUMMARY.md
- [ ] Update user-facing documentation if needed
- [ ] Create animated GIF showing green/yellow dots in action

---

## 🔍 What to Report Back

### Success Criteria:
- ✅ Status dots appear on correct sections
- ✅ Dots show correct color based on data availability
- ✅ Dots update from yellow → green after pipeline execution
- ✅ Cartridge Settings loads project default
- ✅ Progress resets to 0% on each run
- ✅ Zero 404 errors in Network tab

### If Issues Found:
1. Take screenshot of the issue
2. Copy browser console errors
3. Copy relevant network request/response (if API error)
4. Note the exact steps to reproduce

---

## 📞 Quick Reference

### Key Files Modified (Day 4):
- `apps/web/app/components/stages/DraftingView.tsx` - Progress reset
- `apps/api/routers/projects.py` - 3 new endpoints, column fixes
- `apps/web/app/components/visualization/GenerationStats.tsx` - Dark theme
- `apps/web/app/components/visualization/CodeGenerationSummary.tsx` - Simplified
- `apps/web/app/components/navigation/SidebarSection.tsx` - Status indicators
- `apps/web/app/components/stages/TechnologyMixer.tsx` - Default config

### Key Endpoints:
- `GET /projects/{id}/registry` - Design Registry
- `POST /projects/{id}/registry` - Update Registry
- `GET /projects/{id}/generation/stats` - Generation metrics
- `GET /projects/{id}/generation/summary` - Code summary
- `GET /projects/{id}/sidebar-metrics?stage={n}` - Sidebar status data
- `GET /projects/{id}/settings` - Project settings (target_tech)

### Status Indicator Logic:
```typescript
// Green = Has data
- execution: filesGenerated > 0
- output: filesGenerated > 0
- views/analysis: assetCount > 0 || nodeCount > 0
- review: refinementStatus != 'NOT_STARTED'

// Yellow = No data yet
- execution: filesGenerated == 0
- output: filesGenerated == 0
- views/analysis: assetCount == 0 && nodeCount == 0
- review: refinementStatus == 'NOT_STARTED'

// No dot = Config sections
- config, target, actions: null
```

---

## 🚀 After Testing is Complete

### If All Tests Pass:
1. Mark all items as ✅ in this TODO
2. Update SPRINT_14_PHASE_2_SUMMARY.md → move Day 5 items to "Completed"
3. Consider Sprint 14 Phase 2 **COMPLETE**
4. Start planning Sprint 15 or v4.0 features

### If Issues Found:
1. Document issues in new section of SPRINT_14_PHASE_2_SUMMARY.md
2. Create bug tickets if needed
3. Prioritize fixes for Day 6
4. Continue testing after fixes

---

**Good luck! 🎯**  
*Remember: This is the polish phase. Small visual bugs are OK, major functionality should work.*
