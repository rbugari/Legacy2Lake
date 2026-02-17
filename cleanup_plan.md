# Plan de Limpieza - Preparación para V4.0

**Fecha:** 13 de febrero, 2026  
**Objetivo:** Limpiar workspace dejando solo lo necesario para V4.0 y futuro  

---

## 📋 Resumen Ejecutivo

| Categoría | Archivos a Mover | Estado |
|-----------|------------------|--------|
| Scripts de migración antigua | 16 archivos | ⏳ Pendiente |
| Scripts de debug/check/verify | 80+ archivos | ⏳ Pendiente |
| Tests antiguos de agentes | 25+ archivos | ⏳ Pendiente |
| Reportes de Sprint obsoletos | 30+ archivos | ⏳ Pendiente |
| Archivos de resultados/logs | 10+ archivos | ⏳ Pendiente |
| Documentación obsoleta en raíz | 15+ archivos | ⏳ Pendiente |
| Scripts de producción temporales | 20+ archivos | ⏳ Pendiente |
| **TOTAL** | **~200 archivos** | ⏳ Pendiente |

---

## 🗑️ Archivos a Archivar

### 1. Scripts de Migración Antigua (16 archivos)

```
apply_admin_role_migration.py
apply_agent_migration.py
apply_audit_log_migration.py
apply_migrations_019_021.py
apply_migration_019_dev.py
apply_migration_021.py
apply_missing_agents.py
apply_phases_migration.py
apply_retroactive_schema.py
apply_rls_policies.py
apply_role_fix.py
apply_sprint13_migration.py
apply_sprint7_migration.py
apply_sprint8.5_migration.py
apply_sprint8_migration.py
execute_migration_dev.py
```

**Razón:** Migraciones ya aplicadas en producción, no necesarias para V4.0

---

### 2. Scripts de Debug/Check/Verify (80+ archivos)

**Patrón:** `check_*.py`, `debug_*.py`, `verify_*.py`

```
check_agent_catalog.py
check_agent_matrix.py
check_agent_names.py
check_all_locks.py
check_azure_config.py
check_catalogs_diag.py
check_db_state.py
check_demo3_azure.py
check_discovery_result.py
check_generated_code.py
check_medulla_exists.py
check_medulla_status.py
check_missing_agents.py
check_object_names.py
check_process_locks.py
check_project_members_table.py
check_project_roles.py
check_prompt_storage.py
check_providers_diag.py
check_quick_locks.py
check_sprint85_data.py
check_sprint8_data.py
check_ssis_file.py
check_tech_id.py
check_tenants_data.py
check_tenants_structure.py
check_users_diag.py
check_utm_catalog_dbt.py
check_utm_objects_columns.py
check_utm_projects_structure.py
check_vault_structure.py

debug_agents_mismatch.py
debug_dbt_direct.py
debug_demo3_impersonation.py
debug_lab.py
debug_login.py
debug_prompts.py
debug_sprint85_direct.py

verify_catalog_dev.py
verify_catalog_separation.py
verify_client_removal.py
verify_customer3_config.py
verify_demo34_password.py
verify_endpoints_diag.py
verify_env_config.py
verify_imported_configs.py
verify_migration_023.py
verify_no_public_models.py
verify_phases_data.py
verify_prod_state.py
verify_rls_status.py
verify_schema_now.py
verify_support_asset_fix.py
verify_task3_agents.py
verify_tenant_plans.py
verify_v3_9_tables.py
```

**Razón:** Scripts de diagnóstico temporal, no útiles para desarrollo V4.0

---

### 3. Tests Antiguos de Agentes (25+ archivos)

```
execute_agent_c_aws_bronze_test.py
execute_agent_c_aws_gold_test.py
execute_agent_c_aws_silver_test.py
execute_agent_c_dbt_bronze_test.py
execute_agent_c_fabric_bronze_test.py
execute_agent_c_fabric_gold_test.py
execute_agent_c_fabric_silver_test.py
execute_agent_c_gcp_bronze_test.py
execute_agent_c_generic_bronze_test.py
execute_agent_c_generic_gold_test.py
execute_agent_c_generic_silver_test.py
execute_agent_c_gold_test.py
execute_agent_c_salesforce_bronze_test.py
execute_agent_c_salesforce_gold_test.py
execute_agent_c_salesforce_silver_test.py
execute_agent_c_silver_test.py
execute_agent_c_snowflake_bronze_test.py
execute_agent_c_snowflake_gold_test.py
execute_agent_c_snowflake_silver_test.py
execute_agent_c_test.py
execute_e2e_smoke_test.py
execute_sprint2_integration_tests.py
```

**Razón:** Tests manuales obsoletos, reemplazados por suite en `/tests/`

---

### 4. Reportes de Sprint Obsoletos (30+ archivos)

```
SPRINT_0_DAY_4_FINAL_REPORT.md
SPRINT_0_DAY_5_6_PROMPT_REFINEMENT_REPORT.md
SPRINT_0_RETROSPECTIVE.md
SPRINT_10_QUICK_REFERENCE.md
SPRINT_10_SCHEMA_EVOLUTION_REPORT.md
SPRINT_11_DATA_QUALITY_REPORT.md
SPRINT_11_QUICK_REFERENCE.md
SPRINT_12_ARCHITECTURE.md
SPRINT_12_REPORT.md
SPRINT_13_ENHANCED_SCHEMA_VISUALIZATION_REPORT.md
SPRINT_1_COMPLETION_REPORT.md
SPRINT_2_COMPLETION_REPORT.md
SPRINT_2_SUMMARY.md
SPRINT_3_MULTI_TENANT_SECURITY_REPORT.md
SPRINT_4_SECURITY_HARDENING_FINAL_REPORT.md
SPRINT_5_BATCH_TESTING_FINAL_REPORT.md
SPRINT_6_RATE_LIMIT_AUDIT_FINAL_REPORT.md
SPRINT_7_DEEP_FORENSIC_TRIAGE_REPORT.md
SPRINT_7_QUICK_REFERENCE.md
SPRINT_8.5_AND_13_CLOSURE_SUMMARY.md
SPRINT_8.5_ORIGIN_ANALYSIS_REPORT.md
SPRINT_8_QUICK_REFERENCE.md
SPRINT_8_REAL_TIME_VALIDATION_REPORT.md
SPRINT_9_QUICK_REFERENCE.md
SPRINT_9_ZERO_HARDCODE_GENERATION_REPORT.md
TESTING_SPRINT_COMPLETION_REPORT.md
TESTING_SPRINT_EXECUTION_RESULTS.md
TESTING_SPRINT_FINAL_REPORT.md
```

**Razón:** Reportes históricos, información consolidada en `/docs/RELEASE_NOTES.md`

---

### 5. Archivos de Resultados/Logs (10+ archivos)

```
activate_payload.json
batch_test_results.json
cleanup_audit.log
debug_projects_list.txt
prod_configs_export.json
prod_legacy_export.json
prod_model_catalog.json
SMOKE_TEST_RESULTS.json
SPRINT_2_INTEGRATION_TEST_RESULTS.json
TEST_EXECUTION_FINAL_REPORT.json
TEST_EXECUTION_FINAL_REPORT.md
```

**Razón:** Resultados de ejecuciones pasadas, no necesarios para desarrollo

---

### 6. Documentación Obsoleta en Raíz (15+ archivos)

```
CRITICAL_BUG_CARTRIDGE_SELECTION.md
ENHANCEMENT_PROGRESS.md
ESTRUCTURA_CORRECTA_TRIAGE_DRAFTING.txt
MOCKUP_UI_UBICACION.txt
PRODUCT_FEATURES_V4.md
PROPUESTA_DASHBOARD_DISCOVERY_TRIAGE.md
RELEASE_PLAN_ANALYSIS.md
ROADMAP_NEXT_FEATURES.md
TEST_DEMO33_DEMO34.md
V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md
V3.9_PHASE_INTEGRATION_STATUS.md
V3.9_SPRINT_COMPLETED.md
V4_FEATURE_PRIORITIZATION.md
```

**Razón:** Documentación temporal o duplicada, información ya en `/docs/`

---

### 7. Scripts de Producción Temporales (20+ archivos)

```
add_customer3_models.py
analyze_public_models_impact.py
clean_invalid_models.py
compare_env_data.py
complete_customer3_and_cleanup.py
connect_supabase_dev.py
create_demo_tenants.py
create_platform_admin.py
create_viewer_user.py
cross_env_check.py
delete_duplicate_prompts.py
direct_discovery.py
explore_prod_structure.py
explore_prod_tenants.py
explore_supabase_schema.py
export_prod_configs.py
export_prod_configs_v2.py
extract_model_catalog_prod.py
extract_prod_legacy.py
final_fix_origin.py
final_import_summary.py
find_admin_users.py
find_projects_with_files.py
find_ssis_file.py
fix_azure_deployment.py
fix_deployment_ids.py
fix_origin_with_test_data.py
fix_permissions.py
fix_prompt_tenant_leakage.py
fix_public_flag.py
force_expire_locks.py
force_unlock_project.py
get_tenant_id.py
import_model_catalog_to_dev.py
import_prod_configs_to_dev.py
inspect_medulla_structure.py
inspect_utm_prompts_schema.py
list_all_tenants_dev.py
list_prompts.py
list_solutions_diag.py
list_storage_buckets.py
list_tables_diag.py
list_tables_supabase.py
list_tenants_diag.py
map_demo_tenants_prod.py
migrate_demo_users.py
parse_test_ssis_and_update.py
populate_agent_matrix.py
quick_migrate_sprint13.py
release_lock.py
rename_demo3_to_customer3.py
reparse_from_storage.py
reparse_ssis_connections.py
rerun_discovery_triage.py
reset_and_test_login.py
reset_demo33_password.py
retroactive_schema_update.py
seed_cartridge_prompts_to_db.py
setup_test_tenants.py
show_agent_matrix_schema.py
show_architecture_diagram.py
show_implementation_summary.py
show_medulla_content.py
show_migration_019_sql.py
show_reset_command.py
show_roles_diagram.py
show_users_summary.py
sync_config.py
update_deployment_names.py
validate_demo3_test1.py
wipe_projects_diag.py
wipe_r2_prod.py
```

**Razón:** Scripts oneshot para migraciones/fixes específicos ya ejecutados

---

### 8. Tests en Raíz (30+ archivos)

```
batch_test_runner.py
run_all_tests.py
run_batch_tests.py
run_manual_triage_test.py
run_triage_extraction.py
SPRINT_1_TEST_DB_PYSPARK_BRONZE.py
test_api_endpoints.py
test_cartridge_knowledge.py
test_cartridge_selection.py
test_code_api.py
test_collaborator_automated.py
test_collaborator_flow.py
test_complete_extraction.py
test_dbt_simple.py
test_gcp_sf_quick.py
test_history_analyzer.py
test_login_v3_9.py
test_manager_operations.py
test_multi_tenant_isolation.py
test_multi_tenant_security.py
test_origin_analysis.py
test_origin_extraction.py
test_pattern4_extraction.py
test_project_members.py
test_r2_diag.py
test_real_medulla.py
test_role_permissions_matrix.py
test_schema_api.py
test_schema_api_now.py
test_schema_extraction.py
test_sprint1_batch_db_prompts.py
test_sprint1_db_prompts.py
test_sprint4_live.py
test_sprint6_security.py
test_sprint7_column_profiling.py
test_sprint85_complete.py
test_sprint8_validation.py
test_transpile_task_sprint85.py
test_triage_apis.py
test_user_management.py
test_viewer_automated.py
```

**Razón:** Tests deberían estar en `/tests/`, no en raíz

---

## ✅ Archivos a MANTENER

### Estructura Principal
```
/apps/              # Código fuente (frontend + backend)
/database/          # Migraciones actuales
/docs/              # Documentación V3.9 GA (recién actualizada)
/migrations/        # Migraciones Supabase
/prompt_lab/        # Prompts activos del sistema
/scripts/           # Scripts de utilidad permanente
/tests/             # Suite de tests oficial
/utils/             # Utilidades compartidas
```

### Archivos de Configuración
```
.env
.env.example
.gitignore
package.json
package-lock.json
pytest.ini
README.md
requirements.txt
run.py
nixpacks.toml
Procfile
railway.json
server.js
start_backend.ps1
```

### SQL
```
check_table_grants.sql
sync_prompts.sql
```

---

## 🚀 Script de Limpieza

Archivo: `cleanup_workspace.ps1`

---

## 📊 Impacto Estimado

| Métrica | Antes | Después | Reducción |
|---------|-------|---------|-----------|
| **Archivos en raíz** | ~250 | ~20 | 92% |
| **Tamaño estimado** | ~50 MB | ~5 MB | 90% |
| **Claridad** | Confuso | Limpio | +100% |

---

## ⚠️ Precauciones

1. **No se elimina nada permanentemente** - Todo va a `/archive/`
2. **Revisar antes de borrar** - Carpeta `/archive/` debe revisarse manualmente
3. **Git tracked** - Archivos versionados permanecen en historial
4. **Backup recomendado** - Hacer commit antes de ejecutar limpieza

---

## 🎯 Beneficios para V4.0

1. **Workspace limpio** - Solo archivos relevantes
2. **Onboarding más rápido** - Nuevos desarrolladores entienden estructura
3. **CI/CD más rápido** - Menos archivos que procesar
4. **Claridad mental** - Foco en lo importante
5. **Mantenibilidad** - Código organizado = fácil mantener

---

## 📝 Siguiente Paso

Ejecutar: `.\cleanup_workspace.ps1`

Esto moverá todos los archivos obsoletos a `/archive/YYYY-MM-DD/` para revisión.
