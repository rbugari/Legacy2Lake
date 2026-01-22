# Phase 3: Refinement (The Builder)

The **Refinement Phase** is where the actual code generation happens. It takes the plan from Drafting and produces production-ready code.

## 🎯 Goal
Generate, Validate, and Refine high-fidelity code artifacts (PySpark, SQL).

## 🧠 Key Components

### 1. Orchestration Hub
- **Live Logs**: Watch the "Refinement Loop" in action.
- **Metrics**: See file counts for Bronze/Silver/Gold layers.

### 2. Workbench
- **Diff Viewer**: Compare generated code against previous versions.
- **Code Inspection**: Syntax-highlighted view of the generated artifacts.

### 3. Solution Config (NEW)
- **Technology Mixer**: Toggle between PySpark and SQL generation.
- **Design Registry**: Adjust architectural rules (e.g., change a prefix) and re-run refinement to apply them instantly.

## 🔄 The Refinement Loop
1. **Generate**: The system produces the initial V1 code.
2. **Critique**: Agent F (Fixer) reviews the code against the **Design Registry** rules.
3. **Refine**: Issues are fixed automatically.
4. **Verify**: The loop continues until the quality gate is met or max retries reached.

## 💡 Technology Mixer
Select **"Mixed / Dual"** mode to generate both PySpark notebooks (for Data Engineering) and SQL Stored Procedures (for legacy compatibility) in the same run.
