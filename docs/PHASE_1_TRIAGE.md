# Phase 1: Triage & Discovery (Complete Guide)

## 📌 Introduction
The **Triage** phase is the first critical step in the Legacy2Lake modernization process. Its goal is to transform a "noisy" and complex source repository (like a set of old SSIS packages) into a clear functional architecture, prioritizing assets that generate business value.

---

## 👨‍💻 For the User: What happens here?
In this stage, the system performs an "intelligent scan" of your project to help you decide what to migrate and how everything is connected.

### Key Concepts
*   **CORE:** Vital processes that contain business logic and must be migrated to the target technology.
*   **SUPPORT:** Dependencies, configuration tables, or auxiliary processes.
*   **IGNORED:** Log files, local configs, or redundant code that should not clutter the new architecture.

### Tools at your disposal
1.  **Graph View:** An interactive visualization of your architecture. You can drag assets, delete nodes, and auto-order the mesh (Vertical/Horizontal).
2.  **Inventory (Grid):** A detailed list where you can batch-edit categories for every file.
3.  **Context Injection (User Input):** Add "Tribal Knowledge" (notes, business rules) to specific assets. Agent A will use this to generate **Virtual Steps**—logic that doesn't exist in the source but is required for the business.
4.  **Column Mapping Editor**: A granular view to map source columns to target Bronze/Silver/Gold fields, including PII tagging and business context injection. Accessible via the 'Database' icon in the Grid or the 'Column Mapping' tab.
5.  **Prompts Explorer**: Unified interface to manage agent instructions (A, C, F, G) with local persistence and real-time prompt refining.
6.  **Operational intelligence**: The agent automatically infers:
    - **Soberanía (Security):** PII detection and masking rules.
    - **Strategy:** Optimal load strategy (Full, Incremental, SCD 2).
    - **Criticality:** Business impact classification (P1/P2/P3).
7.  **Maximize Mode:** Hides the interface to focus exclusively on technical mesh design.

---

## ⚙️ For the Technical Team: Architecture and Logic
The Triage process is an orchestration between a deterministic scanning layer and an agentic reasoning model.

### 1. The Scanner (Discovery Engine)
Located in `DiscoveryService`, this component performs static analysis of the local or cloned repository.
*   **Signature Extraction:** It identifies component "signatures" (SQL tasks, Data Flow transforms) within XML/SQL content.
*   **Manifest Generation:** Creates a structured JSON summary of the technical inventory without sending massive source code to the LLM.

### 2. Detective Agent (Mesh Architect)
The "brain" of this phase. It receives the manifest and uses a specialized **System Prompt** to classify files and infer dependencies (`READS_FROM`, `WRITES_TO`, `SEQUENTIAL`).

### 3. Graph Orchestration & Layout
The visualization uses **React Flow**, while the layout intelligence resides in the **Dagre** algorithm, ensuring dependencies flow logically without overlaps.

### 4. Persistence & Reset
*   **Project Reset**: Selective purge via `POST /projects/{id}/reset` to return the project to the Discovery state.
*   **Layout Saving**: Node coordinates are saved in the Metadata Store.

---

## 🎨 Design and UX (v3.0 Premium)
Legacy2Lake v3.0 features an **Enterprise Glassmorphism** design system. 
- **Purple & Indigo Accents**: Deep tonal harmony for long engineering sessions.
- **Card-Glass Components**: Translucent panels with background blur for complex data visualization.
- **High-Contrast Typography**: Enhanced readability using font hierarchies optimized for technical documentation.

## ⏭️ Next Steps: Moving to Synthesis
Once your inventory is validated and your mesh is designed, you are ready to "Approve" the plan and transition to **Stage 2: Drafting**.
