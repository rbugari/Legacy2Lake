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

### `run_project_target_matrix.py`

Runs the same project against multiple target outputs using the live API and captures more than UI state:

- resets downstream stages while preserving Triage files
- updates both `target_tech` and registry `target_stack`
- starts Drafting and waits on execution logs + project status
- starts Refinement and waits on execution logs + project status
- downloads the generated file tree from storage via `/projects/{id}/files`
- downloads textual artifact contents via `/projects/{id}/files/content`
- supports `drafting_delivery`, `structured_refinement`, and `intelligent_reengineering`
- supports a boolean JSON matrix file to enable/disable target + mode combinations
- downloads delivery/governance ZIP bundles per combination and packages the full run into one ZIP
- writes per-target snapshots under `test_results/target_matrix/<timestamp>/`

Use when:

- comparing one project across many target cartridges
- validating real generated artifacts in storage, not only logs
- collecting evidence for Drafting + Refinement quality by target

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

Target matrix workflow:

1. ensure backend API is running
2. choose a project with Triage already prepared
3. run `run_project_target_matrix.py --project-id <project> --tenant-id <tenant_uuid> --targets snowflake_sql ms_fabric_sql bigquery pyspark`
4. inspect `matrix_summary.json` plus each target folder under `test_results/target_matrix/`

Matrix config workflow:

1. copy `scripts/target_matrix_config.example.json`
2. set `project_id`, activate `true/false` only for the canonical target ids from the catalog (`aws`, `databricks`, `dbt`, `gcp`, `ms_fabric`, `ms_fabric_sql`, `pyspark`, `salesforce`, `snowflake`, `snowflake_sql`), and toggle global post-drafting modes
3. run `run_project_target_matrix.py --config-file scripts/target_matrix_config.example.json`
4. download or inspect the final bundled ZIP stored under the run folder

Detailed reference:

1. see [docs/technical/target_matrix_tests.md](docs/technical/target_matrix_tests.md)

## Cleanup Policy

- one-off debug scripts were removed
- sprint migration helpers were removed
- legacy prompt migration utilities were removed
- this directory should stay small and operational
