# GitHub Copilot Configuration

This directory contains GitHub Copilot instructions, schemas, and patterns for the Legacy2Lake UTM project.

## 📂 Structure

```
.github/
├── copilot-instructions.md          # Main instructions file (auto-loaded by Copilot)
└── copilot/
    ├── agents/
    │   └── data-architect-pm.md      # ⭐ PM/Architect agent for feature evaluation
    ├── schemas/
    │   ├── api-contracts.md          # Pydantic models & API contracts
    │   └── database-tables.md        # Database schema reference
    ├── patterns/
    │   ├── fastapi-crud.md           # FastAPI CRUD router template
    │   ├── agent-service.md          # AI agent service template
    │   └── react-stage-view.md       # React stage view template
    └── HOW_TO_USE_PM_AGENT.md        # Guide for consulting the PM Agent
```

## 🎯 Purpose

These files provide **context and patterns** to GitHub Copilot so it can:

1. **Understand the project architecture** (multi-tenant, agent-based, cartridge system)
2. **Suggest correct code patterns** (RLS queries, multi-tenancy, imports)
3. **Generate type-safe code** (matching Pydantic models with TypeScript interfaces)
4. **Avoid common mistakes** (missing tenant_id, hardcoded prompts, sync/async mixing)

## 📖 How It Works

### Automatic Loading

GitHub Copilot **automatically reads** `.github/copilot-instructions.md` and uses it as context for all suggestions in this workspace.

### On-Demand Reference

You can explicitly reference schemas and patterns in your prompts:

```
# Example: Ask Copilot to create a new endpoint
"Create a new FastAPI router for 'workflows' resource following the fastapi-crud.md pattern"

# Example: Ask Copilot about database structure
"What columns are available in utm_projects table?"

# Example: Ask Copilot to create a React component
"Create a new stage view component for Certification stage following react-stage-view.md"
```

## 🔄 Files Overview

### 0. agents/data-architect-pm.md ⭐ PRIMARY AGENT

**Product Manager / Data Architect Persona** - Contains:
- Senior Data Architect role definition (15+ years ETL migration experience)
- Understanding of 3-column system (Analysis, Generation, Governance)
- Feature evaluation framework (User Problem, ROI, Complexity, Strategic Fit)
- Evaluation output format (APPROVE / DEFER / REJECT)
- Example evaluations (approved, deferred, rejected features)
- Critical decision principles (validate with users, prioritize evenly, bias toward simplicity)

**Use Case:** Consult BEFORE implementing any feature to ensure it delivers real value to Data Engineers migrating ETL systems.

**How to Use:** See [HOW_TO_USE_PM_AGENT.md](HOW_TO_USE_PM_AGENT.md) for complete guide.

**Example:**
```
@workspace Using the Data Architect/PM Agent role in .github/copilot/agents/data-architect-pm.md,
evaluate this feature:

Feature: Export generated code to GitHub directly from UI
Effort: 2 weeks
```

### 2. copilot-instructions.md (Main File)

**Auto-loaded by Copilot** - Contains:
- Project overview and architecture
- Multi-tenancy enforcement rules
- AI agent patterns
- Import resolution patterns
- Database query patterns
- FastAPI router patterns
- React component patterns
- Real-time validation patterns
- Cartridge system overview
- Common anti-patterns to avoid

### 3. schemas/api-contracts.md

**API Contract Reference** - Contains:
- All Pydantic request/response models
- FastAPI endpoint signatures
- TypeScript type equivalents
- Validation rules
- Error response formats
- Usage examples for both backend and frontend

**Use Case:** Ensures frontend and backend use matching data structures.

### 4. schemas/database-tables.md

**Database Schema Reference** - Contains:
- Complete table definitions with SQL DDL
- Column descriptions and constraints
- Foreign key relationships
- RLS policies
- JSONB field structures
- Common query patterns
- Index recommendations

**Use Case:** Generates correct database queries with proper RLS filtering.

### 5. patterns/fastapi-crud.md

**FastAPI Router Template** - Contains:
- Complete CRUD endpoint implementation
- Multi-tenancy enforcement
- UUID validation
- Pagination support
- Error handling
- Logging patterns
- Test examples

**Use Case:** Rapidly create new API endpoints with consistent patterns.

### 6. patterns/agent-service.md

**AI Agent Service Template** - Contains:
- LLM client resolution from database
- Dynamic prompt loading
- Knowledge enrichment integration
- Response parsing
- Error handling
- Test fixtures

**Use Case:** Create new AI agents or extend existing ones.

### 7. patterns/react-stage-view.md

**React Component Template** - Contains:
- Complete stage view component
- fetchWithAuth usage
- Loading/error/empty states
- Tab-based navigation
- Status badges
- TypeScript types

**Use Case:** Create new stage views or other complex React components.

## 🚀 Getting Started

### Before Implementing ANY Feature ⭐

**ALWAYS consult the Data Architect/PM Agent first:**

```
@workspace Using the Data Architect/PM Agent role in .github/copilot/agents/data-architect-pm.md,
evaluate this feature:

Feature: [Your feature description]
Effort: [X weeks]
Problem solved: [User pain point]
Phase: [Which of the 6 phases does this impact?]
```

**The agent will respond with:** ✅ APPROVE / ⚠️ DEFER / ❌ REJECT + detailed rationale

This ensures you're building features that deliver real value to Data Engineers migrating ETL systems.

### For New Features

1. **Check patterns** directory for relevant templates
2. **Reference schemas** for data structures
3. **Follow conventions** from copilot-instructions.md
4. **Let Copilot suggest** based on context

### For Bug Fixes

1. **Check anti-patterns** section in copilot-instructions.md
2. **Verify multi-tenancy** enforcement
3. **Review database queries** against database-tables.md
4. **Check API contracts** for type mismatches

### For Code Reviews

1. **Verify patterns** match templates
2. **Check database queries** include tenant_id
3. **Validate imports** use try/except pattern
4. **Ensure type safety** matches api-contracts.md

## ✅ Verification

To verify GitHub Copilot is using this context:

1. **Open any Python file** in the project
2. **Type a comment:** `# Create a new endpoint for listing assets`
3. **Wait for suggestion** - It should include:
   - tenant_id filtering
   - Proper imports with try/except
   - Dependency injection with get_db
   - UUID validation

If suggestions don't follow patterns, Copilot may not be loading the instructions file. Try:
- Reloading VS Code window
- Checking file is at `.github/copilot-instructions.md` (exact path)
- Verifying GitHub Copilot extension is active

## 🔧 Maintenance

### When to Update

- **New patterns emerge** in the codebase → Add to patterns/
- **Database schema changes** → Update database-tables.md
- **API contracts change** → Update api-contracts.md
- **Anti-patterns identified** → Add to copilot-instructions.md

### How to Update

1. Edit the relevant file
2. Commit changes to git
3. GitHub Copilot will pick up changes automatically
4. No need to reload VS Code

## 📝 Best Practices

### Do's ✅

- Keep patterns up-to-date with actual code
- Include real examples from the codebase
- Add comments explaining "why" not just "what"
- Update when refactoring introduces new patterns
- Reference actual file paths for context

### Don'ts ❌

- Don't include sensitive data (API keys, passwords)
- Don't copy entire large files (use summaries)
- Don't include deprecated patterns
- Don't overcomplicate examples
- Don't forget to test suggested code

## 🎯 Impact Metrics

Track these to measure effectiveness:

- **Reduced multi-tenancy bugs** (missing tenant_id filters)
- **Faster feature development** (using patterns)
- **Fewer type mismatches** (frontend ↔ backend)
- **Consistent code style** across team
- **Reduced code review cycles**

## 🔗 Related Documentation

- [HOW_TO_USE_PM_AGENT.md](HOW_TO_USE_PM_AGENT.md) - **Complete guide** to consulting the Product Manager agent
- [SYSTEM_ARCHITECTURE.md](../../docs/SYSTEM_ARCHITECTURE.md) - Full system architecture
- [DATABASE_SCHEMA.md](../../docs/DATABASE_SCHEMA.md) - Complete database documentation
- [ROLES_AND_ONBOARDING.md](../../docs/ROLES_AND_ONBOARDING.md) - User roles and permissions
- [v4.0_FINAL_SCOPE.md](../../docs/planning/v4.0_FINAL_SCOPE.md) - Current development scope

---

**Questions?** 
1. **For feature evaluation:** Consult the PM Agent (see [HOW_TO_USE_PM_AGENT.md](HOW_TO_USE_PM_AGENT.md))
2. **For technical patterns:** Check the main project documentation in `/docs`
3. **For urgent help:** Ask in team chat
