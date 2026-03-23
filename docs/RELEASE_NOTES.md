# Release Notes

## Version 4.0.3 - Phase Landing Consistency And Help Refresh - 2026-03-23

### Workspace Navigation

- added a consistent `overview` landing for each stage in the workspace
- stopped carrying arbitrary subsections across phase changes
- preserved the last useful subsection only inside the same phase
- prevented transient `run-*` actions from becoming sticky landing targets
- aligned phase entry behavior with ready, running, and completed states

### Help And Guidance

- refreshed the stage help guides to reflect the current workflow
- aligned the help content with the real stage actions and views
- switched the stage help modal to consume Markdown as the editable source of truth

### Product UX

- the phase home now acts as the operational entry point for each stage
- users can leave a phase to configure or inspect something and return to a coherent landing point
- sidebar fallback behavior now prefers meaningful sections instead of `quick-info`

## Version 4.0.2 - Prompt Consolidation And SSIS E2E Validation - 2026-03-21

### Prompt Architecture

- consolidated the platform on `disk canonical + DB runtime mirror`
- normalized the active prompt taxonomy
- incorporated `agent_qa_assessment` into the canonical prompt set
- synchronized the active canonical inventory to `48` prompts
- deprecated active legacy `cartridge_*` runtime prompts

### Agent Prompt Alignment

- aligned `Agent A` prompt with the real runtime payload
- aligned `Agent S` prompt with its actual assessment contract
- made `Agent C`, `Agent F`, and `Agent G` less PySpark-centric in the core prompt layer
- clarified `direct` mode behavior to prevent invented enhancements

### Cartridge And Generator Alignment

- strengthened `direct` cartridges for:
  - trace headers
  - parameterization
  - no hardcoded placeholders
  - explicit mapping preference when metadata exists
- improved Fabric SQL generator behavior to better match cartridge guidance

### Runtime Fixes

- improved prompt resolution and override handling
- hardened placeholder validation for valid Python interpolation cases
- improved `Agent G` JSON parsing for fenced responses containing markdown and nested code blocks
- kept `Agent QA` in the same canonical prompt circuit as the rest of the LLM agents

### Validation

Executed real end-to-end validation on `2026-03-21` using:

- fixture: [`tests/fixtures/ssis_test_repo`](C:\proyectos_dev\UTM\tests\fixtures\ssis_test_repo)
- provider: Azure
- model: `gpt-4.1`

Validated chain:

- `Agent A`
- `Agent C`
- `Agent F`
- `Agent G`

Validated outputs:

- `snowflake_sql:direct`
- `pyspark:direct`

Generated reports:

- [`test_results/ssis_fixture_evaluation.json`](C:\proyectos_dev\UTM\test_results\ssis_fixture_evaluation.json)
- [`test_results/ssis_generation_pipeline.json`](C:\proyectos_dev\UTM\test_results\ssis_generation_pipeline.json)

### Current Interpretation

The platform is stable at the orchestration and prompt-assembly level. Remaining findings in governance are mostly semantic modernization decisions for the tested artifact, such as:

- PII masking
- SCD2 logic
- partitioning strategy
- ingestion metadata

Those are not infrastructure failures of the prompt/runtime chain.

## Previous Notes

Earlier v4.0 release and stabilization notes remain available in git history and older planning documents. This file now prioritizes the current stabilized state over the intermediate sprint narrative.
