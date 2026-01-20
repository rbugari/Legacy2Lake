# Legacy2Lake: Strategic Roadmap & Versioning 🚀

This document defines the architectural evolution of the **Legacy2Lake** engine. The goal is to evolve from a technical "code converter" into an "Autonomous Data Solution Architect."

## 🚀 Release v1.1: The "Conscious Architect" (Human Context)

**Theme**: Bridging the gap between code logic and business intent ("Tribal Knowledge").

### Core Problems Solved
- Legacy code is often a "black box" where business logic is undocumented.
- AI agents may misinterpret operational "hacks" as structural logic.

### Technical Implementation
- [ ] **Context Injection Layer**: Mandatory pre-triage manual input.
- [ ] **Entity `UTM_Asset_Context`**: Relational storage linking `ObjectID` to user descriptions/rules.
    - *Example*: "Ignore duplicates in Table X, filter by `LastUpdateDate`."
- [ ] **Context-Aware Triage**: Injecting user notes into Agent A's system prompt.
- [ ] **"Virtual Steps"**: Generating IR placeholders for manual logic described by users but missing in source code.

---

## 📈 Release v1.2: Operational Intelligence (Behavioral Metadata)

**Theme**: Moving from static "snapshots" to dynamic "workloads".

### Core Problems Solved
- Missing knowledge of frequency, volume, and criticality leads to inefficient code (e.g., using Full Load for hourly data).

### Technical Implementation
- [ ] **Dynamic Behavior Attributes**:
    - `frequency`: {Hourly, Daily, Monthly, Near-RT}
    - `load_strategy`: {Incremental_Watermark, Full_Overwrite, SCD_Type_2}
    - `criticality`: {P1, P2, P3}
- [ ] **Adaptive Code Injection**:
    - **Hourly**: Auto-inject `checkpointLocation` and `Trigger.AvailableNow`.
    - **Incremental**: Auto-detect watermark columns (e.g., `ModifiedDate`) and inject `WHERE` clauses.
- [ ] **Pre-Flight Cost Estimation (FinOps)**:
    - distinct "Dry Run" agent that scans lines of code/complexity and estimates token usage/cost *before* the user commits to the migration.

---

## 🎨 Release v2.0: The "Style Master" (Design Policies)

**Theme**: Ensuring mass-generated code looks uniformed and "Senior Architect" quality.

### Core Problems Solved
- Inconsistency in naming and patterns across thousands of generated scripts.
- Users need to tweak cartridge behavior for specific solutions without writing code.

### Technical Implementation
- [ ] **`UTM_Design_Registry`**: Centralized store for design tokens.
- [ ] **Naming Conventions**: Enforced rules (e.g., `dbo.Table` -> `stg_table_snake_case`).
- [ ] **Layer Standards**: Standard physical paths (e.g., `/mnt/{layer}/{source}/{table}/`).
- [ ] **Principle Injection**: Agents consult the strict "Style Guide" before synthesis.
- [ ] **Solution-Level Cartridge Configuration**:
    - A dedicated inputs UI (similar to Context Injection) where users define specific parameters for the active cartridge (e.g., "For *this* project, use `abfss://` paths instead of mount points").

---

## 🏗️ Release v3.0: Multi-Paradigm Support (SQL & dbt)

**Theme**: Supporting modern stacks beyond Spark/Python.

### Core Problems Solved
- Serving clients who prefer ELT in Snowflake/Redshift or use dbt for lifecycle management.

### Technical Implementation
- [ ] **Pure SQL Cartridge**: Generating sequential scripts (`001_setup.sql`) or Stored Procedures.
- [ ] **dbt Architect Cartridge**:
    - `models/`: Jinja-SQL generation with `{{ config(...) }}`.
    - `snapshots/`: Auto-generation of SCD logic.
    - `schema.yml`: Auto-injection of tests (Unique, Not Null).
- [ ] **Graph Resolution**: Converting physical SSIS references to dynamic dbt `{{ ref('...') }}` DAGs.

---

## 🧠 Release v4.0: Multi-Model Orchestrator (AI Efficiency)

**Theme**: Optimizing cost and speed by using the "Right Brain" for the task.

### Core Problems Solved
- Using expensive reasoning models (o1/GPT-4o) for simple structural tasks is inefficient.
- Lack of visibility into Agent performance over time.

### Technical Implementation
- [ ] **Intelligent Agent Mapping**:
    - **Kernel (Analysis)**: Deep Reasoning Models (o1, Claude 3.5 Sonnet).
    - **Generator (Synthesis)**: High-speed Coding Models (Llama 3 70B via Groq).
- [ ] **Failover & Recovery**: Automatic provider switching upon latency/quota errors.
- [ ] **Engine Observability (Metacognition)**:
    - Dashboard tracking agent performance: "Hallucination Rate", "Correction Loops triggered by Critic", and "Successful Transpilations vs Retries".

---
*Reference Strategy Document v1.2 - Legacy2Lake Engineering*
