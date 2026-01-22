# Project Roadmap 🗺️

## 🚀 Upcoming Features (Post-Rel 2.0)

### Phase 5: Deployment & CI/CD
- [ ] **Git Integration**: Direct push to GitHub/GitLab from the Governance view.
- [ ] **Terraform Generation**: Auto-generate IaC for the required cloud infrastructure (Storage Accounts, Databricks Workspaces).

### Advanced Refinement
- [ ] **Interactive SQL Editor**: A real-time Monaco editor for tweaking generated SQL before approval.
- [ ] **dbt Cartridge**: Full support for dbt project generation (models, YAMLs).
- [ ] **Unit Test Generation**: Auto-generate `pytest` or `dbt test` suites for the new pipelines.

### Enterprise Features
- [ ] **RBAC**: Role-based access control for large teams.
- [ ] **Multi-Tenancy**: Support for multiple organizations in a single deployment.
- [ ] **Audit Logs**: Comprehensive logging of who changed what rule and when.

## 🐛 Known Issues / Backlog
- **Validation**: The prompt editor validation currently fails with a 500 error (postponed fix).
- **Frontend**: `http-server` is used for serving; migrate to a robust Node.js server (planned).

## 📅 Release History

### v2.0 (The Style Master) - CURRENT
- **Contextual Config**: Embedded "Solution Config" tabs in Drafting and Refinement.
- **Technology Mixer**: UI toggles for PySpark, Pure SQL, or Mixed generation.
- **Design Registry**: Global policy engine for naming and paths.
- **Expanded Layout**: 80% width optimization for engineering workflows.

### v1.5: Governance & Lineage
- **Lineage Mapper**: Mapping legacy artifacts to OpenLineage-compliant targets.
- **Certification**: Automated compliance scores.

### v1.0 - v1.3: The Contextual Architect
- **Context Injection**: "Virtual Steps" for business logic.
- **Operational Intelligence**: Automated load strategy and PII detection.
- **Base Registry**: Initial implementation of naming conventions.
