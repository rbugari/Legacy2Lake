# Cleanup Workspace - Preparación para V4.0
# Fecha: 2026-02-13
# Propósito: Mover archivos obsoletos a /archive/ para revisión

$ErrorActionPreference = "Stop"

# Colores
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) { Write-Output $args }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Yellow "==============================================="
Write-ColorOutput Yellow "  UTM Workspace Cleanup - V4.0 Preparation"
Write-ColorOutput Yellow "==============================================="
Write-Host ""

# Crear carpeta de archivo con timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$archiveDir = ".\archive\$timestamp"

Write-ColorOutput Cyan "[+] Creando directorio de archivo: $archiveDir"
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
Write-Host ""

# Contador
$movedCount = 0

# Función para mover archivos
function Move-ToArchive {
    param(
        [string[]]$Patterns,
        [string]$Category
    )
    
    Write-ColorOutput Green ">> Procesando: $Category"
    
    $categoryDir = Join-Path $archiveDir $Category
    New-Item -ItemType Directory -Path $categoryDir -Force | Out-Null
    
    foreach ($pattern in $Patterns) {
        $files = Get-ChildItem -Path . -Filter $pattern -File -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            try {
                Move-Item $file.FullName -Destination $categoryDir -Force
                Write-Host "  [OK] $($file.Name)" -ForegroundColor Gray
                $script:movedCount++
            }
            catch {
                Write-Host "  [ERR] Error moviendo $($file.Name): $_" -ForegroundColor Red
            }
        }
    }
}

# 1. Scripts de Migración Antigua
Move-ToArchive -Patterns @(
    "apply_admin_role_migration.py",
    "apply_agent_migration.py",
    "apply_audit_log_migration.py",
    "apply_migrations_019_021.py",
    "apply_migration_019_dev.py",
    "apply_migration_021.py",
    "apply_missing_agents.py",
    "apply_phases_migration.py",
    "apply_retroactive_schema.py",
    "apply_rls_policies.py",
    "apply_role_fix.py",
    "apply_sprint13_migration.py",
    "apply_sprint7_migration.py",
    "apply_sprint8.5_migration.py",
    "apply_sprint8_migration.py",
    "execute_migration_dev.py"
) -Category "01_migrations"

# 2. Scripts de Debug/Check/Verify
Move-ToArchive -Patterns @(
    "check_*.py",
    "debug_*.py",
    "verify_*.py"
) -Category "02_debug_scripts"

# 3. Tests Antiguos de Agentes
Move-ToArchive -Patterns @(
    "execute_agent_c_*.py",
    "execute_e2e_smoke_test.py",
    "execute_sprint2_integration_tests.py"
) -Category "03_old_agent_tests"

# 4. Reportes de Sprint
Move-ToArchive -Patterns @(
    "SPRINT_*.md",
    "TESTING_SPRINT_*.md"
) -Category "04_sprint_reports"

# 5. Archivos de Resultados/Logs
Move-ToArchive -Patterns @(
    "activate_payload.json",
    "batch_test_results.json",
    "cleanup_audit.log",
    "debug_projects_list.txt",
    "prod_configs_export.json",
    "prod_legacy_export.json",
    "prod_model_catalog.json",
    "SMOKE_TEST_RESULTS.json",
    "SPRINT_2_INTEGRATION_TEST_RESULTS.json",
    "TEST_EXECUTION_FINAL_REPORT.json",
    "TEST_EXECUTION_FINAL_REPORT.md"
) -Category "05_test_results"

# 6. Documentación Obsoleta
Move-ToArchive -Patterns @(
    "CRITICAL_BUG_CARTRIDGE_SELECTION.md",
    "ENHANCEMENT_PROGRESS.md",
    "ESTRUCTURA_CORRECTA_TRIAGE_DRAFTING.txt",
    "MOCKUP_UI_UBICACION.txt",
    "PRODUCT_FEATURES_V4.md",
    "PROPUESTA_DASHBOARD_DISCOVERY_TRIAGE.md",
    "RELEASE_PLAN_ANALYSIS.md",
    "ROADMAP_NEXT_FEATURES.md",
    "TEST_DEMO33_DEMO34.md",
    "V3.9_GAP_ANALYSIS_AND_V4.0_ROADMAP.md",
    "V3.9_PHASE_INTEGRATION_STATUS.md",
    "V3.9_SPRINT_COMPLETED.md",
    "V4_FEATURE_PRIORITIZATION.md"
) -Category "06_old_docs"

# 7. Scripts de Producción Temporales
Move-ToArchive -Patterns @(
    "add_customer3_models.py",
    "analyze_public_models_impact.py",
    "clean_invalid_models.py",
    "compare_env_data.py",
    "complete_customer3_and_cleanup.py",
    "connect_supabase_dev.py",
    "create_demo_tenants.py",
    "create_platform_admin.py",
    "create_viewer_user.py",
    "cross_env_check.py",
    "delete_duplicate_prompts.py",
    "direct_discovery.py",
    "explore_*.py",
    "export_*.py",
    "extract_*.py",
    "final_*.py",
    "find_*.py",
    "fix_*.py",
    "force_*.py",
    "get_tenant_id.py",
    "import_*.py",
    "inspect_*.py",
    "list_*.py",
    "map_*.py",
    "migrate_*.py",
    "parse_*.py",
    "populate_*.py",
    "quick_*.py",
    "release_lock.py",
    "rename_*.py",
    "reparse_*.py",
    "rerun_*.py",
    "reset_*.py",
    "retroactive_*.py",
    "seed_*.py",
    "setup_*.py",
    "show_*.py",
    "sync_config.py",
    "update_*.py",
    "validate_*.py",
    "wipe_*.py"
) -Category "07_temp_scripts"

# 8. Tests en Raíz
Move-ToArchive -Patterns @(
    "batch_test_runner.py",
    "run_all_tests.py",
    "run_batch_tests.py",
    "run_manual_triage_test.py",
    "run_triage_extraction.py",
    "SPRINT_1_TEST_*.py",
    "test_*.py"
) -Category "08_root_tests"

Write-Host ""
Write-ColorOutput Yellow "==============================================="
Write-ColorOutput Green "[OK] Limpieza Completada"
Write-ColorOutput Yellow "==============================================="
Write-Host ""
Write-ColorOutput Cyan "[i] Resumen:"
Write-Host "  - Archivos movidos: $movedCount"
Write-Host "  - Ubicacion: $archiveDir"
Write-Host ""
Write-ColorOutput Yellow "[!] Siguiente paso:"
Write-Host "  1. Revisar archivos en /archive/$timestamp/"
Write-Host "  2. Si todo esta OK, eliminar carpeta /archive/"
Write-Host "  3. Hacer commit de workspace limpio"
Write-Host ""
Write-ColorOutput Green "[OK] Workspace listo para V4.0 development!"
Write-Host ""
