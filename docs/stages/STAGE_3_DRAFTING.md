# Stage 3: Drafting (AI Planning)

## 📌 Overview
**Drafting** transforms the scoped requirements into a technical blueprint. It does not generate final code yet, but establishes the **Architectural Plan**.

## 🎯 Objectives
- Map legacy patterns to modern equivalents (e.g., `Cursor` -> `Window Function`).
- Define the target file structure.
- Apply `DesignRegistry` rules (naming conventions).

## 👨‍💻 User Guide
### 1. Configuration
- **Technology Mixer**: Verify your Target Stack (e.g., PySpark + Databricks).
- **Design Registry**: Check that naming rules (prefix/suffix) are correct.

### 2. Execution
- Click **"Run Pipeline"** (or "Generate Plan").
- **Agent C (Architect)** analyzes the `CORE` files and produces a `plan.json`.

### 3. Output Explorer
- Review the proposed file structure.
- Verify that complex procedures have been broken down effectively.

## ⚙️ Technical Details
- **Service**: `ArchitectService`
- **Output**: `solutions/{project}/drafting/plan.json`
- **Agents**: Agent C (Architect) - Mode: `Plan`
