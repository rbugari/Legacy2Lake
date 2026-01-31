# Stage 5: Certification (Governance & Audit)

## 📌 Overview
**Certification** ensures the generated code meets enterprise standards before it leaves the factory. It acts as the "Quality Gate".

## 🎯 Objectives
- Security auditing (PII, SQL Injection).
- Performance review (Join strategies, Partitioning).
- Code Standards compliance.

## 👨‍💻 User Guide
### 1. Run AI Audit
- Click **"Run AI Audit"** to activate **Agent G (Governor)**.
- It scans the files in `Refinement` and generates a report.

### 2. Review Metrics
- **Compliance Score**: 0-100 score based on passing checks.
- **Badges**: 
    - 🟢 **Certified**: Ready for Handover.
    - 🔴 **Action Required**: Needs remediation.

### 3. Approving
- If the score is sufficient (typically >80), the **"Proceed to Handover"** button becomes active.

## ⚙️ Technical Details
- **Service**: `GovernanceService` (Apps/API/Services/Refinement)
- **Primary Data Source**: Cloudflare R2 (`{tenant_id}/{project_id}/Refinement/`)
- **Agents**: Agent G (Guardian) - Mode: `Certification`
- **Output Artifacts**: 
    - `Modernization_Runbook.md` (Self-documenting deployment guide)
    - `compliance_audit.json` (Structured scorecard)
    - `certified_bundle.zip` (Memory-buffered export)

### Cloud-Native Performance (v3.5)
The certification process is now parallelized. `GovernanceService` reads file inventory from Supabase and fetches file contents from R2 in parallel batches, ensuring fast packaging even for large migration projects.
