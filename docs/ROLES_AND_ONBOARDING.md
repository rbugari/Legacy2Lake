# Roles And Onboarding

> Last Updated: 2026-03-21
> Status: current

Legacy2Lake uses a role model focused on platform governance, tenant management, and project execution.

## Roles

### ADMIN

- platform-wide scope
- manages platform-level configuration and support operations
- can inspect and support tenant environments

### MANAGER

- tenant-wide scope
- manages tenant-level provider, model, user, and project configuration
- responsible for how the tenant uses platform resources

### COLLABORATOR

- project execution scope
- can work on assigned projects and use project capabilities according to the product flow

### VIEWER

- read-only project scope
- can inspect assigned projects without modifying them

## Onboarding Flow

1. create or identify the tenant
2. configure tenant-level runtime settings as needed
3. create or assign users
4. create the project
5. upload source assets
6. move through Discovery, Triage, Drafting, Refinement, Certification, and Handover

## Product Governance Split

This is especially important for the prompt model:

- Level 1 agent prompts are app-governed
- Level 2 cartridge prompts are app-governed
- Level 3 project custom instructions are optional project-level context

Tenant users do not edit the core agent or cartridge prompts directly.

## Notes

Use this document as the simple role reference. Older role and onboarding material was removed to keep the model easy to understand and aligned with the current product state.
