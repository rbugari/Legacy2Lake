# Installation

> Last Updated: 2026-03-21
> Status: current

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project
- access to the project `.env`

## Backend

From the repo root:

```powershell
pip install -r requirements.txt
python run.py
```

Use the project launch scripts if that is how your environment is already managed:

- [`start_backend.ps1`](C:\proyectos_dev\UTM\start_backend.ps1)
- [`_start_backend.bat`](C:\proyectos_dev\UTM\_start_backend.bat)

## Frontend

The repo includes Node assets for the web app. From the appropriate frontend workspace, install dependencies and run the web layer according to the project setup already in use.

At minimum, the root Node packages are managed through:

```powershell
npm install
```

## Environment

The `.env` file should contain infrastructure-level configuration such as:

- Supabase connection values
- storage configuration
- deployment/runtime variables

LLM provider and model selection are tenant-scoped runtime concerns and should be managed through the database-backed configuration model, not by treating `.env` as the primary operating surface for tenant behavior.

## Prompt Workflow

The current prompt workflow is:

1. edit canonical prompts on disk
2. run [`sync_prompts_v4.py`](C:\proyectos_dev\UTM\scripts\sync_prompts_v4.py)
3. run [`validate_prompts.py`](C:\proyectos_dev\UTM\scripts\validate_prompts.py)

## Validation Workflow

For the current SSIS validation path:

1. run [`evaluate_ssis_fixture.py`](C:\proyectos_dev\UTM\scripts\evaluate_ssis_fixture.py)
2. run [`evaluate_ssis_generation_pipeline.py`](C:\proyectos_dev\UTM\scripts\evaluate_ssis_generation_pipeline.py)

For a full end-to-end run across mesh nodes with a single command:

```powershell
python scripts/run_ssis_full_pipeline.py --tenant-id f98edb5e-4165-4c49-9fce-18894e8a818c
```

Optional smoke run (first 1 node):

```powershell
python scripts/run_ssis_full_pipeline.py --tenant-id f98edb5e-4165-4c49-9fce-18894e8a818c --max-nodes 1
```

The summary report is generated at `test_results/ssis_full_pipeline_summary.json`.

## Notes

- prefer the documentation in [`docs/INDEX.md`](C:\proyectos_dev\UTM\docs\INDEX.md) as the current source of truth
- old setup guides and sprint documents were intentionally removed to keep installation and runtime guidance current
