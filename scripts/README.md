# Scripts - Current Utilities

> Last Updated: 2026-03-21
> Status: active

This folder now keeps only the scripts that are still part of the current prompt and validation workflow.

## Active Scripts

### `sync_prompts_v4.py`

Synchronizes the canonical prompt catalog from disk to Supabase.

Use when:

- agent prompts changed
- cartridge prompts changed
- shared prompt content changed

### `validate_prompts.py`

Validates that active prompts in Supabase match the canonical prompt catalog on disk.

Use when:

- a sync was just executed
- you want to confirm runtime parity
- you are auditing prompt drift

### `deprecate_legacy_prompts.py`

Disables legacy prompt records that should no longer remain active in the runtime path.

Use when:

- migrating old prompt inventories
- cleaning runtime prompt state

### `evaluate_ssis_fixture.py`

Runs discovery, quick assessment, and Agent A evaluation against the SSIS fixture.

Use when:

- validating intake and triage behavior
- checking project viability and mesh generation

### `evaluate_ssis_generation_pipeline.py`

Runs the drafting/governance chain against the SSIS fixture:

- Agent C
- Agent F
- Agent G

### `run_ssis_full_pipeline.py`

Runs the complete fixture + drafting/governance flow end-to-end:

- executes `evaluate_ssis_fixture.py`
- reads mesh nodes from Agent A output
- executes `evaluate_ssis_generation_pipeline.py` per node
- writes consolidated summary to `test_results/ssis_full_pipeline_summary.json`

Use when:

- validating generation quality
- testing direct outputs
- checking end-to-end behavior against a real fixture

## Workflow

Typical prompt workflow:

1. edit prompts on disk
2. run `sync_prompts_v4.py`
3. run `validate_prompts.py`

Typical SSIS validation workflow:

1. run `evaluate_ssis_fixture.py`
2. run `evaluate_ssis_generation_pipeline.py`

Or run a single end-to-end command:

1. run `run_ssis_full_pipeline.py --tenant-id <tenant_uuid>`

## Cleanup Policy

- one-off debug scripts were removed
- sprint migration helpers were removed
- legacy prompt migration utilities were removed
- this directory should stay small and operational
