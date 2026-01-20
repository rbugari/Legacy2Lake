# Legacy2Lake: Future Releases & Strategic Roadmap 🚀

This document consolidates all identified improvements, advanced features, and technical debt items deferred for future releases to maintain the focus on the current stable MVP.

## 1. Security & Enterprise Readiness
- [ ] **Data Anonymization Filter**: Pre-processing layer to detect and mask PII (IPs, server names, credentials) before LLM submission.
- [ ] **State Persistence (Heartbeat)**: Automatic saving of `MigrationState` every 30s to allow recovery in long-running processes.
- [ ] **Formal XSD Validation**: Implement formal schema validation for `.dtsx` files to catch structural errors early.

## 2. Advanced Data Engineering (The "Gold Standard")
- [ ] **Test-Driven Generation (TDG)**: Automatic generation of unit tests (`pytest`/`chispa`) alongside every synthesized notebook.
- [ ] **Data Quality Contracts**: Integration of `Great Expectations` or `Soda` checks directly into the generated code.
- [ ] **Standardized Observability**: Implementation of a unified logger for cloud-native metrics (`Azure Monitor`, `CloudWatch`).
- [ ] **CI/CD as Code**: Automated generation of deployment pipelines (YAML) for Azure DevOps and GitHub Actions.

## 3. Intelligent Discovery & Orchestration
- [ ] **Script Task Deep Dive**: Specialized agents to analyze and transpile custom C#/VB.NET logic within SSIS.
- [ ] **Bidirectional Mesh Editing**: Full synchronization between UI graph adjustments (React Flow) and the Metadata Store.
- [ ] **Technology Footprint Report**: Executive summary of supported vs. unsupported components in the source repository.

## 4. UI/UX Enhancements
- [ ] **Advanced Graph Layouts**: Support for circular, organic, and hierarchical grouping layouts.
- [ ] **Persona-Based Perspectives**: Toggle between "Architect" (High-level) and "Engineer" (Code-deep) views.
- [ ] **Impact Analysis Mode**: Visual highlighting of downstream dependencies when a source object changes.

---
*Legacy2Lake Strategic Backlog - Prepared for Future Iterations.*
