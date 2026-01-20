# Legacy2Lake: Future Releases & Strategic Roadmap 🚀

This document consolidates all identified improvements, advanced features, and technical debt items deferred for future releases to maintain the focus on the current stable MVP.

## 1. Intelligence & Multi-Model Orchestration
- [ ] **Multi-LLM Provider & Agent Mapping**: Dynamic routing where light models (e.g., GPT-4o-mini/Llama 3 8B) handle structural tasks and reasoning models (e.g., o1/Claude 3.5 Sonnet) handle global architecture.
- [ ] **Context Injection Layer**: Dedicated UI for users to provide project-specific "Executive Context" (business goals, undocumented logic) that is saved in the solution and injected into Agent A's prompt for high-precision Triage.

## 2. Operational Metadata & Data Treatment
- [ ] **Asset-Level Enrichment**: Feedback loop where users can add comments per asset (table/process) describing:
    - **Update Frequency**: Daily, Monthly, Near Real-Time.
    - **Business Criticality**: High/Medium/Low priority for lineage.
    - **Treatment Rules**: How to handle tables in Bronze (e.g., Hourly partitions vs Daily snapshots).
- [ ] **Modernization Manual (Human-in-the-Loop)**: Capture operational "tribal knowledge" that isn't in legacy XML/SQL and translate it into target-system configurations (Schedules, Partitioning logic).

## 3. Cartridge Design Principles (Best Practices Store)
- [ ] **Technology-Specific Design Tokens**: A central registry for best practices per target-cartridge:
    - **Naming Conventions**: Systematic renaming from legacy to cloud.
    - **Bronze/Silver/Gold Standards**: Specific folder structures (e.g., `bronze/YYYY/MM/DD/HH`) and naming patterns.
- [ ] **Principle Injection**: Agents will read these "Design Principles" before synthesis to ensure generated code follows company-wide standards by default.

## 4. Security & Enterprise Readiness
- [ ] **Advanced Graph Layouts**: Support for circular, organic, and hierarchical grouping layouts.
- [ ] **Persona-Based Perspectives**: Toggle between "Architect" (High-level) and "Engineer" (Code-deep) views.
- [ ] **Impact Analysis Mode**: Visual highlighting of downstream dependencies when a source object changes.

---
*Legacy2Lake Strategic Backlog - Prepared for Future Iterations.*
