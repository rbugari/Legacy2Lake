# Documentation Index - Legacy2Lake v3.5

> Last Updated: 2026-02-01  
> Architecture Version: 3.5 (Cloud-Native, Multi-Tenant)

## Quick Start

- **[Installation Guide](INSTALL.md)** - Setup instructions for backend, frontend, and cloud services
- **[Introduction](INTRODUCTION.md)** - Platform overview, architecture, and key concepts
- **[User Guide](usr/GUIA_DEL_USUARIO.md)** - Spanish language user manual

## Core Documentation

### Platform Overview
- **[Introduction](INTRODUCTION.md)** - Vision, architecture, agent workforce
- **[Installation](INSTALL.md)** - Environment setup, R2 config, provider setup
- **[Release Notes](RELEASE_NOTES.md)** - Version history and changes
- **[Roadmap](ROADMAP.md)** - Future plans and features

### Migration Workflow (6 Stages)

1. **[Stage 1: Discovery](stages/STAGE_1_DISCOVERY.md)** - File upload, R2 storage, inventory
2. **[Stage 2: Triage](stages/STAGE_2_TRIAGE.md)** - Tech detection (Agent S), forensics
3. **[Stage 3: Drafting](stages/STAGE_3_DRAFTING.md)** - IR normalization, knowledge injection
4. **[Stage 4: Refinement](stages/STAGE_4_REFINEMENT.md)** - Code generation, cartridges
5. **[Stage 5: Certification](stages/STAGE_5_CERTIFICATION.md)** - Compliance, scoring, COP
6. **[Stage 6: Handover](stages/STAGE_6_HANDOVER.md)** - Deployment package, signed URLs

## Technical Documentation

### Architecture & Design
- **[Architecture Overview](technical/architecture.md)** - System design and components
- **[AI Infrastructure](technical/ai_infrastructure.md)** - Agent mesh and LLM integration
- **[System Prompts & Agents](technical/system_prompts_and_agents.md)** - Prompt Lab, Agent S, knowledge injection
- **[Data Model](technical/data_model.md)** - Database schema and relationships
- **[Database Structure](technical/database_structure.md)** - Supabase tables and RLS

### Development Guides
- **[Cartridge Manual](technical/cartridge_manual.md)** - Build custom code generators (6 cartridges)
- **[Universal IR](technical/universal_ir.md)** - Intermediate representation format
- **[Function Registry](technical/function_registry.md)** - Cross-platform function mapping
- **[Transpilation Examples](technical/transpilation_examples.md)** - Code generation samples
- **[API Contract](technical/api_contract.md)** - REST API endpoints and schemas

### Quality Assurance
- **[Test Scenarios](technical/test_scenarios.md)** - Testing strategies and examples

## Business & Planning
- **[Business Review](BUSINESS_REVIEW.md)** - Market analysis and value proposition
- **[Comprehensive Review](COMPREHENSIVE_REVIEW.md)** - Detailed system analysis
- **[Specification](SPECIFICATION.md)** - Functional and technical requirements

## v3.5 Key Features

### Cloud-Native Storage
- **Cloudflare R2**: S3-compatible object storage
- **Signed URLs**: Time-limited secure downloads (4h expiry)
- **Tenant Isolation**: Prefix-based data segregation
- **File Inventory**: `utm_file_inventory` for fast listing

### Multi-Tenancy
- **Row-Level Security (RLS)**: Supabase policies enforce tenant isolation
- **Provider Vault**: Encrypted API key storage per tenant
- **Agent Matrix**: Custom LLM assignments per tenant

### AI Agent System
- **Agent S (Scout)**: Technology detection (TSQL, PL/SQL, SSIS, etc.)
- **Agent A (Analyst)**: Dependency and risk analysis
- **Agent B (Interpreter)**: IR generation from legacy code
- **Agent C (Coder)**: Modern code synthesis with cartridges
- **Agent F (Critic)**: Code review and optimization
- **Agent G (Governor)**: Compliance auditing and COP generation

### Prompt Laboratory
- **22 Knowledge Modules**: 7 core + 9 origins + 6 destinations
- **Knowledge Injection**: Dynamic prompt enhancement with tech-specific rules
- **Contract Enforcement**: Schema validation for agent outputs
- **Versioning**: `origins/tsql/grammar_v1.json`, etc.

### Cartridge System
- **6 Production Cartridges**: Databricks, Snowflake, Fabric, BigQuery, Redshift, Salesforce
- **Jinja2 Templates**: Human-readable code generation
- **Type/Function Mapping**: Canonical IR → Target platform
- **Medallion Architecture**: Bronze, Silver, Gold layers

### Certified Output Package (COP)
- **Compliance Scoring**: 0-100 with SEC/PERF/BP/DOC checks
- **Modernization Runbook**: Auto-generated deployment guide
- **Variable Injection**: CI/CD-ready placeholders
- **Deployment Options**: Manual, CI/CD, or Direct cloud

## Obsolete Documentation (Pre-v3.5)

The following files may contain outdated information and should be reviewed:
- Files referencing local file storage (pre-R2 migration)
- Single-tenant architecture documentation
- Hardcoded provider configurations

## Contributing

When updating documentation:
1. Mark version changes clearly (`v3.5 Update:`)
2. Use GitHub alerts for important notes (NOTE, TIP, WARNING, IMPORTANT)
3. Include code examples and diagrams (Mermaid)
4. Link files using `[text](file:///absolute/path)` format
5. Update this index when adding new docs

## Support

- **GitHub**: [https://github.com/rbugari/Legacy2Lake](https://github.com/rbugari/Legacy2Lake)
- **Documentation Issues**: Create GitHub issues with `docs` label
