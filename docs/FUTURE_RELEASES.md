# Legacy2Lake: Strategic Roadmap & Versioning 🚀

This document defines the architectural evolution of the Legacy2Lake engine. The goal is to evolve from a technical "code converter" into an "Autonomous Data Solution Architect."

---

## ✅ Release v1.1 - v1.3: The "Contextual Architect" (SHIPPED)

**Theme**: Bridging logic with business intent and operational behavioral intelligence.

### 🧠 Core Features Implemented
- **Release v1.1: Context Injection Layer**: 
    - Dedicated UI for manual pre-triage input.
    - **"Virtual Steps"**: Agent-generated logic placeholders for business requirements not found in source code.
- **Release v1.2: Operational & Security Intelligence**:
    - **Inertial Mapping**: Automated detection of `frequency`, `load_strategy`, and `criticality`.
    - **PII Awareness**: Automated detection of sensitive data (Names, Emails, SSN) with suggested masking policies.
- **Release v1.3: Design Registry & Policies**:
    - Centralized **Knowledge Base** where users define naming conventions and cloud paths.
    - Policies are injected into Agent A/C to ensure "Senior Architect" quality code from flight one.

---

## 🏗️ Release v1.5: Executable Governance (In Development)

**Theme**: Ensuring mass-generated code looks uniformed and "Senior Architect" quality.

### Core Problems Solved
- Inconsistency in naming and patterns across thousands of generated scripts.
- Users need to tweak cartridge behavior without touching the core engine.

### Technical Implementation
- [ ] **`UTM_Design_Registry`**: Centralized store for design tokens and architectural rules.
- [ ] **Naming Conventions**: Enforced rules (e.g., `dbo.Table` -> `stg_table_snake_case`).
- [ ] **Layer Standards**: Standard physical paths (e.g., `/mnt/{layer}/{source}/{table}/`).
- [ ] **Security & Privacy Masking**: Auto-detection of PII (Personally Identifiable Information) to suggest `F.sha2()` or masking logic in the Silver layer.
- [ ] **Solution-Level Cartridge Configuration**:
    - UI where users define parameters like "Use `abfss://` paths instead of mount points" or "Force liquid clustering on Date keys."

---

## 🏗️ Release v3.0: Multi-Paradigm & Governance (SQL & dbt)

**Theme**: Supporting modern stacks and ensuring data trust.

### Core Problems Solved
- Serving clients who prefer ELT in Snowflake/Redshift or use dbt for lifecycle management.
- Lack of built-in validation for the migrated data.

### Technical Implementation
- [ ] **Pure SQL Cartridge**: Generating sequential scripts (`001_setup.sql`) or modern Stored Procedures (BEGIN/END).
- [ ] **dbt Architect Cartridge**:
    - `models/`: Jinja-SQL generation with `{{ ref() }}` and `{{ source() }}`.
    - `snapshots/`: Auto-generation of SCD files.
    - `schema.yml`: Auto-injection of column documentation and tests (Unique, Not Null).
- [ ] **Graph Resolution**: Converting physical SSIS references into a dynamic Directed Acyclic Graph (DAG).
- [ ] **Automated Data Quality (Unit Testing)**: Generation of validation scripts (e.g., Row Count comparison or Null Checks) to run post-migration.

---

## 🤖 Release v4.0: Multi-Model Orchestrator (AI Efficiency)

**Theme**: Optimizing cost and reliability by using the "Right Brain" for the task.

### Core Problems Solved
- Using expensive reasoning models (o1/GPT-4o) for simple structural tasks is inefficient.
- Lack of visibility into Agent performance and reliability.

### Technical Implementation
- [ ] **Intelligent Agent Mapping**:
    - **Kernel (Logical Analysis)**: Deep Reasoning Models (o1, Claude 3.5 Sonnet).
    - **Generator (Code Synthesis)**: High-speed Coding Models (Llama 3.1 70B via Groq).
- [ ] **Failover & Recovery**: Automatic provider switching (e.g., Azure to OpenRouter) upon latency or quota errors.
- [ ] **Engine Observability (Metacognition Dashboard)**:
    - Tracking "Hallucination Rate", "Correction Loops" (how many times the Critic Agent intervened), and "Success vs Retry" metrics.

---
*Reference Strategy Document v1.3 - Legacy2Lake Engineering - Approved for Implementation.*
