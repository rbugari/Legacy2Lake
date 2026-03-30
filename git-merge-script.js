const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const worktreeDir = 'C:\\proyectos_dev\\UTM.worktrees\\copilot-worktree-2026-03-30T14-10-26';
const mainRepoDir = 'C:\\proyectos_dev\\UTM';

try {
  console.log('=== Step 1: git add -A in worktree ===');
  execSync('git add -A', { cwd: worktreeDir, stdio: 'inherit' });
  
  console.log('\n=== Step 2: Check if there are changes to commit ===');
  const statusOutput = execSync('git status --porcelain', { cwd: worktreeDir, encoding: 'utf8' });
  
  if (statusOutput.trim()) {
    console.log('Changes detected. Running git commit...\n');
    execSync(`git commit -m "feat: Sprint 1-2-3 - Readiness model, Executive Summary, Gap Workspace\\n\\nSprint 1: Readiness + Confidence Model\\n- readiness_service.py with signal aggregation\\n- GET/POST readiness endpoints\\n- ReadinessBadge.tsx (badge+card variants)\\n- readiness_summary JSONB migration on utm_projects\\n- Integrated in Discovery, Triage, Drafting views\\n\\nSprint 2: Executive Summary + Visible Gaps\\n- executive_summary_service.py (on-demand)\\n- executive-summary and gaps-summary endpoints\\n- ExecutiveSummaryPanel.tsx (full+compact)\\n- Integrated in Governance and Handover views\\n\\nSprint 3: Gap & Decision Workspace\\n- gap_service.py with CRUD + auto-import from signals\\n- gaps.py router with full REST API\\n- utm_project_gaps table migration with RLS\\n- GapWorkspace.tsx with filters, create form, resolve/reopen\\n- Gap Workspace section in GovernanceView\\n\\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"`, { cwd: worktreeDir, stdio: 'inherit' });
  } else {
    console.log('No changes to commit.\n');
  }
  
  console.log('=== Step 3: Checkout main in main repo ===');
  execSync('git checkout main', { cwd: mainRepoDir, stdio: 'inherit' });
  
  console.log('\n=== Step 4: Merge worktree branch into main ===');
  execSync(`git merge --no-ff copilot/worktree-2026-03-30T14-10-26 -m "merge: Sprint 1-2-3 Readiness, Executive Summary, Gap Workspace\\n\\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"`, { cwd: mainRepoDir, stdio: 'inherit' });
  
  console.log('\n✅ All steps completed successfully!');
} catch (error) {
  console.error('\n❌ Error:', error.message);
  process.exit(1);
}
