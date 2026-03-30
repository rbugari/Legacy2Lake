@echo off
cd /d "C:\proyectos_dev\UTM.worktrees\copilot-worktree-2026-03-30T14-10-26"
echo === Step 1: git add -A in worktree ===
git add -A

echo.
echo === Step 2: Check if there are changes to commit ===
git status --porcelain > temp_status.txt
for /f %%A in ('find /c /v "" ^< temp_status.txt') do set lines=%%A
if %lines% gtr 0 (
  echo Changes detected. Running git commit...
  git commit -m "feat: Sprint 1-2-3 - Readiness model, Executive Summary, Gap Workspace^n^nSprint 1: Readiness + Confidence Model^n- readiness_service.py with signal aggregation^n- GET/POST readiness endpoints^n- ReadinessBadge.tsx (badge+card variants)^n- readiness_summary JSONB migration on utm_projects^n- Integrated in Discovery, Triage, Drafting views^n^nSprint 2: Executive Summary + Visible Gaps^n- executive_summary_service.py (on-demand)^n- executive-summary and gaps-summary endpoints^n- ExecutiveSummaryPanel.tsx (full+compact)^n- Integrated in Governance and Handover views^n^nSprint 3: Gap ^& Decision Workspace^n- gap_service.py with CRUD + auto-import from signals^n- gaps.py router with full REST API^n- utm_project_gaps table migration with RLS^n- GapWorkspace.tsx with filters, create form, resolve/reopen^n- Gap Workspace section in GovernanceView^n^nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
) else (
  echo No changes to commit.
)
del /q temp_status.txt

echo.
echo === Step 3: Checkout main in main repo ===
cd /d "C:\proyectos_dev\UTM"
git checkout main

echo.
echo === Step 4: Merge worktree branch into main ===
git merge --no-ff copilot/worktree-2026-03-30T14-10-26 -m "merge: Sprint 1-2-3 Readiness, Executive Summary, Gap Workspace^n^nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

echo.
echo ✅ All steps completed successfully!
