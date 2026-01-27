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
- **Service**: `AgentGService` (Governance)
- **Output**: `solutions/{project}/governance/audit_report.json`
- **Agents**: Agent G (Governor) - Mode: `Audit`
