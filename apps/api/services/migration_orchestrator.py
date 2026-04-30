import os
import json
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import all agents
from apps.api.services.librarian_service import LibrarianService
from apps.api.services.topology_service import TopologyService
from apps.api.services.agent_c_service import AgentCService
from apps.api.services.agent_f_service import AgentFService
from apps.api.services.agent_g_service import AgentGService
from apps.api.services.knowledge_service import KnowledgeService

from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

class MigrationOrchestrator:
    """
    The Director: Manages the end-to-end migration lifecycle.
    Orchestrates the hand-offs between Librarian, Topology, Developer, and Compliance agents.
    """

    def __init__(self, project_id: str, project_uuid: str = None, tenant_id: str = None, client_id: str = None):

        self.project_id = project_id # This acts as Project Name / Folder Name
        self.project_uuid = project_uuid or project_id # Fallback if not provided
        self.tenant_id = tenant_id
        
        # Persistence Service handles paths
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        self.storage = PersistenceService.get_storage()
        
        # Load Platform Spec
        # For config files that are part of the app, we can still use local or read via resource.
        # But for project artifacts, we use storage.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spec_path = os.path.join(base_dir, "config", "platform_spec.json")
        try:
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)
        except FileNotFoundError:
            self.spec_path = os.path.abspath(os.path.join("apps", "api", "config", "platform_spec.json"))
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)

        # Initialize Agents
        self.librarian = LibrarianService(project_id, tenant_id=tenant_id)
        self.topology = TopologyService(project_id, tenant_id=tenant_id)
        self.agent_c = AgentCService(tenant_id=tenant_id, client_id=client_id)
        self.agent_f = AgentFService(tenant_id=tenant_id, client_id=client_id)
        self.persistence = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

        
        # Log Persistence
        self.log_file = os.path.join(self.base_path, "migration.log")

    def _normalize_layer_value(self, raw_value: Optional[Any]) -> Optional[str]:
        """Map source metadata into the execution layers supported by prompts/audits."""
        if raw_value in (None, ""):
            return None

        value = str(raw_value).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "direct": "direct",
            "direct_translation": "direct",
            "raw": "bronze",
            "landing": "bronze",
            "staging": "bronze",
            "bronze": "bronze",
            "curated": "silver",
            "refined": "silver",
            "silver": "silver",
            "serving": "gold",
            "presentation": "gold",
            "gold": "gold"
        }
        return aliases.get(value)

    def _resolve_task_layer(self, asset_meta: Dict[str, Any], target_tech: str) -> str:
        """Prefer explicit medallion intent; only fall back to direct when no modernization signal exists."""
        metadata = asset_meta.get("metadata") or {}
        logical_medulla = metadata.get("logical_medulla") or {}
        source_name = str(asset_meta.get("source_name") or "").lower()
        asset_type = str(asset_meta.get("type") or "").lower()
        normalized_target = str(target_tech or "").lower()
        is_spark_modernization = normalized_target in {"pyspark", "databricks", "fabric"}
        is_ssis_asset = source_name.endswith(".dtsx") or "ssis" in asset_type
        is_sql_file = source_name.endswith(".sql") or "sql" in asset_type
        is_warehouse_sql_target = normalized_target in {
            "snowflake_sql",
            "snowflake",
            "ms_fabric_sql",
            "fabric_sql",
        }

        preferred_candidates = [
            logical_medulla.get("layer"),
            metadata.get("layer"),
        ]

        for candidate in preferred_candidates:
            normalized = self._normalize_layer_value(candidate)
            if normalized and normalized != "direct":
                return normalized

        if is_spark_modernization and is_ssis_asset:
            package_name = source_name.rsplit("/", 1)[-1]
            if package_name.startswith("fact"):
                return "gold"
            if package_name.startswith("dim"):
                return "silver"

        if is_warehouse_sql_target and is_sql_file:
            package_name = source_name.rsplit("/", 1)[-1]
            if "orquestador" in package_name or "orchestrator" in package_name or "control" in package_name:
                return "direct"
            if "snapshot" in package_name:
                return "gold"
            if "fact" in package_name or "_fact_" in package_name or "sp_load_fact" in package_name:
                return "gold"
            if "dim" in package_name or "_dim_" in package_name or "sp_load_dim" in package_name:
                return "silver"

        weak_candidates = [
            asset_meta.get("layer"),
            metadata.get("layer"),
            metadata.get("lineage_group"),
            logical_medulla.get("layer"),
            logical_medulla.get("lineage_group"),
        ]

        for candidate in weak_candidates:
            normalized = self._normalize_layer_value(candidate)
            if normalized:
                return normalized

        if is_spark_modernization and is_ssis_asset:
            return "silver"

        return "direct"

    @staticmethod
    def _is_sql_target(target_tech: Optional[str]) -> bool:
        try:
            from apps.api.services.refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract
        except ImportError:
            try:
                from services.refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract
            except ImportError:
                from .refinement.cartridges.tech_stack_contracts import SQLFlavor, resolve_contract

        contract = resolve_contract(target_tech)
        if contract:
            return contract.sql_flavor != SQLFlavor.PYSPARK

        normalized = str(target_tech or "").lower().replace(" ", "_")
        return normalized not in {"", "pyspark", "spark", "databricks", "ms_fabric", "snowflake"}

    @staticmethod
    def _artifact_base_name(package_name: str) -> str:
        return os.path.splitext(package_name or "")[0]

    @staticmethod
    def _get_valid_optimized_content(audit_report: Dict[str, Any], target_tech: Optional[str]) -> Optional[str]:
        return AgentFService._extract_valid_optimized_code(
            (audit_report or {}).get("optimized_code"),
            str(target_tech or ""),
        )

    @classmethod
    def _primary_artifact_filename(cls, package_name: str, target_tech: Optional[str]) -> str:
        base_name = cls._artifact_base_name(package_name)
        suffix = ".sql" if cls._is_sql_target(target_tech) else ".py"
        return f"{base_name}{suffix}"

    @classmethod
    def _split_generated_content(
        cls,
        code_result: Dict[str, Any],
        target_tech: Optional[str],
    ) -> tuple[str, str, str]:
        """Route generated output to the correct artifact lane based on target tech."""
        generic_code = code_result.get("code", "") or ""
        sql_code = code_result.get("sql_code", "") or ""
        pyspark_code = code_result.get("pyspark_code", "") or ""

        if cls._is_sql_target(target_tech):
            sql_content = sql_code or generic_code
            return "", sql_content, sql_content

        notebook_content = pyspark_code or generic_code
        return notebook_content, "", notebook_content

    @staticmethod
    def _normalize_code_artifact(content: str, target_tech: Optional[str]) -> str:
        """Clean model wrappers/escaped newlines before persisting runnable artifacts."""
        text = str(content or "").strip()
        if not text:
            return ""

        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    preferred = "sql_code" if MigrationOrchestrator._is_sql_target(target_tech) else "pyspark_code"
                    for key in (preferred, "optimized_code", "code", "pyspark_code", "sql_code"):
                        candidate = parsed.get(key)
                        if isinstance(candidate, str) and candidate.strip():
                            text = candidate.strip()
                            break
                    else:
                        return ""
            except Exception:
                pass

        if text.count("\n") <= 1 and "\\n" in text:
            text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")

        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()

        lines = stripped.splitlines()
        if lines and lines[0].strip().lower() in {"python", "pyspark", "sql"}:
            stripped = "\n".join(lines[1:]).strip()

        valid = AgentFService._extract_valid_optimized_code(stripped, str(target_tech or ""))
        return valid or ""

    @staticmethod
    def _coerce_audit_items(value: Any) -> List[str]:
        if value in (None, ""):
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        if isinstance(value, list):
            items: List[str] = []
            for entry in value:
                items.extend(MigrationOrchestrator._coerce_audit_items(entry))
            return items
        if isinstance(value, dict):
            return [json.dumps(value, ensure_ascii=False, sort_keys=True)]
        text = str(value).strip()
        return [text] if text else []

    @classmethod
    def _extract_retry_seed_code(
        cls,
        audit_report: Dict[str, Any],
        generated_code: str,
        target_tech: Optional[str],
    ) -> str:
        optimized = cls._normalize_code_artifact(
            cls._get_valid_optimized_content(audit_report, target_tech) or "",
            target_tech,
        )
        if optimized:
            return optimized
        return cls._normalize_code_artifact(generated_code, target_tech)

    @classmethod
    def _build_agent_f_retry_feedback(
        cls,
        audit_report: Dict[str, Any],
        target_tech: Optional[str],
    ) -> Dict[str, Any]:
        flavor_validation = audit_report.get("flavor_validation") or {}
        critique = cls._coerce_audit_items(audit_report.get("critique"))
        violations = cls._coerce_audit_items(audit_report.get("violations"))
        flavor_issues = cls._coerce_audit_items(flavor_validation.get("issues"))
        must_fix = critique + violations + flavor_issues

        return {
            "retry_contract_version": "1.0",
            "status": str(audit_report.get("status") or "UNKNOWN"),
            "score": audit_report.get("score"),
            "target_tech": str(target_tech or ""),
            "must_fix": must_fix,
            "critique": critique,
            "violations": violations,
            "flavor_issues": flavor_issues,
            "instructions": [
                "Fix every must_fix item before returning code.",
                "Do not emit MySQL-only syntax for Snowflake SQL targets.",
                "Return only the target-specific code field required by the output contract.",
                "Preserve the source script semantics and step order while repairing rejected constructs.",
            ],
        }

    @classmethod
    def _should_retry_after_audit(
        cls,
        audit_report: Dict[str, Any],
        target_tech: Optional[str],
        task_def: Optional[Dict[str, Any]] = None,
    ) -> bool:
        status = str((audit_report or {}).get("status") or "").upper()
        if status != "REJECTED":
            return False

        task_def = task_def or {}
        if int(task_def.get("retry_attempt") or 0) >= 1:
            return False

        feedback = cls._build_agent_f_retry_feedback(audit_report or {}, target_tech)
        retry_seed = cls._extract_retry_seed_code(audit_report or {}, "", target_tech)
        return bool(feedback.get("must_fix") or retry_seed)

    @classmethod
    def _build_retry_task_def(
        cls,
        task_def: Dict[str, Any],
        audit_report: Dict[str, Any],
        generated_code: str,
        target_tech: Optional[str],
    ) -> Dict[str, Any]:
        retry_feedback = cls._build_agent_f_retry_feedback(audit_report or {}, target_tech)
        retry_seed = cls._extract_retry_seed_code(audit_report or {}, generated_code, target_tech)

        retry_task_def = dict(task_def or {})
        retry_task_def["retry_attempt"] = int(retry_task_def.get("retry_attempt") or 0) + 1
        retry_task_def["previous_generated_code"] = retry_seed
        retry_task_def["agent_f_retry_feedback"] = retry_feedback

        support_items = list(retry_task_def.get("support_intelligence") or [])
        support_items.append(
            {
                "type": "agent_f_retry_contract",
                "source": "agent-f",
                "must_fix": retry_feedback.get("must_fix", []),
            }
        )
        retry_task_def["support_intelligence"] = support_items

        scout_assessment = dict(retry_task_def.get("scout_assessment") or {})
        detected_gaps = list(scout_assessment.get("detected_gaps") or [])
        detected_gaps.extend(retry_feedback.get("must_fix", []))
        if detected_gaps:
            scout_assessment["detected_gaps"] = detected_gaps
            retry_task_def["scout_assessment"] = scout_assessment

        return retry_task_def

    async def _retry_rejected_code_once(
        self,
        task_def: Dict[str, Any],
        set_context: Optional[List[Dict[str, Any]]],
        target_tech: str,
        generated_code_for_review: str,
        audit_report: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not self._should_retry_after_audit(audit_report, target_tech, task_def):
            return None

        retry_task_def = self._build_retry_task_def(task_def, audit_report, generated_code_for_review, target_tech)
        retry_code_result = await self.agent_c.transpile_task(retry_task_def, set_context=set_context)

        retry_notebook_content, retry_sql_content, retry_generated_code = self._split_generated_content(
            retry_code_result,
            target_tech,
        )
        retry_notebook_content = self._normalize_code_artifact(retry_notebook_content, target_tech)
        retry_sql_content = self._normalize_code_artifact(retry_sql_content, target_tech)
        retry_generated_code = self._normalize_code_artifact(retry_generated_code, target_tech)

        if retry_sql_content:
            retry_sql_content = self._maybe_apply_direct_sql_orchestrator_override(
                retry_task_def,
                retry_sql_content,
                target_tech,
            )
            retry_generated_code = retry_sql_content

        if not retry_generated_code:
            return None

        retry_audit_report = await self.agent_f.review_code(
            retry_task_def,
            retry_generated_code,
            project_id=self.project_uuid,
        )

        return {
            "task_def": retry_task_def,
            "code_result": retry_code_result,
            "notebook_content": retry_notebook_content,
            "sql_content": retry_sql_content,
            "generated_code_for_review": retry_generated_code,
            "audit_report": retry_audit_report,
        }

    @staticmethod
    def _build_direct_snowflake_orchestrator(asset_name: str, source_code: str) -> Optional[str]:
        """Create a bounded direct Snowflake SQL translation for legacy ETL orchestrator procedures."""
        if not source_code or "sp_orquestador" not in source_code.lower():
            return None

        calls = []
        for match in re.finditer(r"\bCALL\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source_code, re.IGNORECASE):
            proc_name = match.group(1).upper()
            if proc_name not in calls and proc_name != "SP_ORQUESTADOR_ETL":
                calls.append(proc_name)

        if not calls:
            return None

        step_blocks = []
        for index, proc_name in enumerate(calls, start=1):
            condition = ""
            if proc_name == "SP_LOAD_DIM_FECHA":
                condition = """
        IF (NOT EXISTS (SELECT 1 FROM DIM_FECHA WHERE FECHA = CURRENT_DATE())) THEN
            CALL SP_LOAD_DIM_FECHA();
        END IF;"""
            else:
                condition = f"""
        CALL {proc_name}();"""

            step_blocks.append(f"""
    -- Step {index}: {proc_name}
    v_paso_actual := '{proc_name}';
    v_step_start := CURRENT_TIMESTAMP();
    BEGIN{condition}
    EXCEPTION
        WHEN OTHER THEN
            v_errores := v_errores + 1;
            v_msg_error := SQLERRM;
            INSERT INTO ETL_CONTROL_CARGAS
                (PROCESO, FECHA_INICIO, FECHA_FIN, ESTADO, MENSAJE_ERROR)
            VALUES
                ('ERROR_EN_' || v_paso_actual, v_step_start, CURRENT_TIMESTAMP(), 'ERROR', v_msg_error);
    END;""")

        return f"""-- L2L DIRECT TRANSLATION: {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Technology: Snowflake SQL
-- Layer: direct
-- Intent: faithful orchestration translation; preserves step order and continue-on-error behavior.

CREATE OR REPLACE PROCEDURE SP_ORQUESTADOR_ETL()
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    v_errores NUMBER DEFAULT 0;
    v_ctrl_id NUMBER;
    v_paso_actual STRING;
    v_msg_error STRING;
    v_master_start TIMESTAMP_NTZ;
    v_step_start TIMESTAMP_NTZ;
BEGIN
    v_master_start := CURRENT_TIMESTAMP();

    INSERT INTO ETL_CONTROL_CARGAS
        (PROCESO, FECHA_INICIO, ESTADO)
    VALUES
        ('ORQUESTADOR_ETL', v_master_start, 'INICIADO');

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM ETL_CONTROL_CARGAS
     WHERE PROCESO = 'ORQUESTADOR_ETL'
       AND FECHA_INICIO = v_master_start;
{''.join(step_blocks)}

    UPDATE ETL_CONTROL_CARGAS
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = IFF(v_errores = 0, 'OK', 'OK_CON_ERRORES'),
           MENSAJE_ERROR = IFF(v_errores > 0, v_errores || ' paso(s) fallaron; ver registros de error en ETL_CONTROL_CARGAS', NULL)
     WHERE ID = v_ctrl_id;

    RETURN IFF(v_errores = 0, 'EXITOSO', 'CON_ERRORES') || ' | control_id=' || v_ctrl_id || ' | errores=' || v_errores;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_fact_aplicacion_cobros(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_fact_aplicacion_cobros" not in trigger_text and "fact_aplicacion_cobros" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: GOLD - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: GOLD
-- Business Entity: Payment Application Fact
-- Grain: 1 row per payment application to order

SET source_schema = 'U136155607_NALUB';
SET gold_schema = 'GOLD_BUSINESS';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.FACT_APLICACION_COBROS') (
    FECHA_APLICACION_KEY NUMBER,
    CLIENTE_KEY NUMBER,
    APLICACION_ID_ORIGEN NUMBER NOT NULL,
    PEDIDO_ID_ORIGEN NUMBER,
    PAGO_ID_ORIGEN NUMBER,
    IMPORTE_APLICADO NUMBER(18, 2),
    SALDO_POSTERIOR NUMBER(18, 2),
    CANTIDAD_APLICACIONES NUMBER,
    FECHA_CARGA_DW TIMESTAMP_NTZ,
    _GOLD_CREATED_AT TIMESTAMP_NTZ,
    _GRAIN_LEVEL STRING,
    _REFRESH_TIME TIMESTAMP_NTZ
)
CLUSTER BY (FECHA_APLICACION_KEY);

CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_APLICACION_COBROS()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_upd NUMBER DEFAULT 0;
    v_ventana_desde DATE;
    v_ventana_hasta DATE;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_ventana_desde := DATEADD(DAY, -7, CURRENT_DATE());
    v_ventana_hasta := CURRENT_DATE();

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_fact_aplicacion_cobros', v_inicio, 'INICIADO', v_ventana_desde, v_ventana_hasta);

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_aplicacion_cobros'
       AND FECHA_INICIO = v_inicio;

    -- [EXTRACT]
    CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_APLIC AS
    SELECT
        TO_NUMBER(TO_CHAR(TO_DATE(ap.FECHA), 'YYYYMMDD')) AS FECHA_APLICACION_KEY,
        COALESCE(dc.CLIENTE_KEY, -1) AS CLIENTE_KEY,
        ap.ID AS APLICACION_ID_ORIGEN,
        ap.IDPEDIDO AS PEDIDO_ID_ORIGEN,
        ap.IDPAGO AS PAGO_ID_ORIGEN,
        TRY_TO_NUMBER(ap.IMPORTE, 18, 2) AS IMPORTE_APLICADO,
        TRY_TO_NUMBER(ap.SALDO, 18, 2) AS SALDO_POSTERIOR
    FROM IDENTIFIER($source_schema || '.APLICAPAGOS') ap
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_CLIENTE') dc
        ON dc.CLIENTE_ID_ORIGEN = ap.IDCLIENTE
       AND dc.ES_VIGENTE = 1
        WHERE TO_DATE(ap.FECHA) >= v_ventana_desde;

    -- [TRANSFORM]
    SELECT COUNT(*)
            INTO v_upd
      FROM TMP_FACT_APLIC t
      JOIN IDENTIFIER($gold_schema || '.FACT_APLICACION_COBROS') fa
        ON fa.APLICACION_ID_ORIGEN = t.APLICACION_ID_ORIGEN;

    SELECT COUNT(*)
            INTO v_ins
      FROM TMP_FACT_APLIC t
     WHERE NOT EXISTS (
        SELECT 1
          FROM IDENTIFIER($gold_schema || '.FACT_APLICACION_COBROS') fa
         WHERE fa.APLICACION_ID_ORIGEN = t.APLICACION_ID_ORIGEN
     );

    -- [LOAD]
    MERGE INTO IDENTIFIER($gold_schema || '.FACT_APLICACION_COBROS') AS target
    USING TMP_FACT_APLIC AS src
       ON target.APLICACION_ID_ORIGEN = src.APLICACION_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.FECHA_APLICACION_KEY = src.FECHA_APLICACION_KEY,
        target.CLIENTE_KEY = src.CLIENTE_KEY,
        target.PEDIDO_ID_ORIGEN = src.PEDIDO_ID_ORIGEN,
        target.PAGO_ID_ORIGEN = src.PAGO_ID_ORIGEN,
        target.IMPORTE_APLICADO = src.IMPORTE_APLICADO,
        target.SALDO_POSTERIOR = src.SALDO_POSTERIOR,
        target.CANTIDAD_APLICACIONES = 1,
        target.FECHA_CARGA_DW = CURRENT_TIMESTAMP(),
        target._REFRESH_TIME = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (
        FECHA_APLICACION_KEY, CLIENTE_KEY, APLICACION_ID_ORIGEN,
        PEDIDO_ID_ORIGEN, PAGO_ID_ORIGEN, IMPORTE_APLICADO,
        SALDO_POSTERIOR, CANTIDAD_APLICACIONES, FECHA_CARGA_DW,
        _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    ) VALUES (
        src.FECHA_APLICACION_KEY, src.CLIENTE_KEY, src.APLICACION_ID_ORIGEN,
        src.PEDIDO_ID_ORIGEN, src.PAGO_ID_ORIGEN, src.IMPORTE_APLICADO,
        src.SALDO_POSTERIOR, 1, CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(), 'payment_application', CURRENT_TIMESTAMP()
    );

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins,
           FILAS_ACTUALIZADAS = v_upd
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'fact_aplicacion_cobros OK',
        'insertadas', v_ins,
        'actualizadas', v_upd,
        'control_id', v_ctrl_id
    );
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_fact_cobros(asset_name: str, source_code: str) -> Optional[str]:
        """Create a bounded Snowflake SQL Gold translation for the nalub payment fact procedure."""
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_fact_cobros" not in trigger_text and "fact_cobros" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: GOLD - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: GOLD
-- Business Entity: Payments fact
-- Grain: 1 row per received payment

SET source_schema = 'U136155607_NALUB';
SET gold_schema = 'GOLD_BUSINESS';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.FACT_COBROS') (
    FECHA_COBRO_KEY NUMBER,
    CLIENTE_KEY NUMBER,
    MEDIO_PAGO_KEY NUMBER,
    USUARIO_KEY NUMBER,
    PAGO_ID_ORIGEN NUMBER NOT NULL,
    IMPORTE_COBRADO NUMBER(18, 2),
    CANTIDAD_COBROS NUMBER,
    FLAG_CHEQUE NUMBER,
    FLAG_RECIBIDO NUMBER,
    FLAG_IMPUTADO NUMBER,
    FECHA_VTO_CHEQUE DATE,
    DIAS_HASTA_VTO NUMBER,
    FECHA_CARGA_DW TIMESTAMP_NTZ,
    _GOLD_CREATED_AT TIMESTAMP_NTZ,
    _GRAIN_LEVEL STRING,
    _REFRESH_TIME TIMESTAMP_NTZ
)
CLUSTER BY (FECHA_COBRO_KEY);

-- Prerequisite dimensions expected in the target schema: DIM_CLIENTE, DIM_MEDIO_PAGO, DIM_USUARIO.
-- Unknown member handling is preserved through COALESCE(..., -1) lookups.

CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_COBROS()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_upd NUMBER DEFAULT 0;
    v_affected NUMBER DEFAULT 0;
    v_replay_days NUMBER DEFAULT 7;
    v_ventana_desde DATE;
    v_ventana_hasta DATE;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_ventana_desde := DATEADD(DAY, -1 * v_replay_days, CURRENT_DATE());
    v_ventana_hasta := CURRENT_DATE();

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_fact_cobros', v_inicio, 'INICIADO', v_ventana_desde, v_ventana_hasta);

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_cobros'
       AND FECHA_INICIO = v_inicio;

    -- [EXTRACT]
    CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_COBROS AS
    SELECT
        TO_NUMBER(TO_CHAR(pg.FECHARECEP, 'YYYYMMDD')) AS FECHA_COBRO_KEY,
        COALESCE(dc.CLIENTE_KEY, -1)                  AS CLIENTE_KEY,
        COALESCE(dmp.MEDIO_PAGO_KEY, -1)              AS MEDIO_PAGO_KEY,
        COALESCE(du.USUARIO_KEY, -1)                  AS USUARIO_KEY,
        pg.ID                                         AS PAGO_ID_ORIGEN,
        TRY_TO_DECIMAL(pg.IMPORTE, 18, 2)             AS IMPORTE_COBRADO,
        IFF(pg.TIPOMEDIOPAGOID = 2, 1, 0)             AS FLAG_CHEQUE,
        IFF(pg.ESTADO = 'Recibido', 1, 0)             AS FLAG_RECIBIDO,
        IFF(pg.ESTADO = 'Imputado', 1, 0)             AS FLAG_IMPUTADO,
        TRY_TO_DATE(TO_VARCHAR(pg.CHVTO))             AS FECHA_VTO_CHEQUE,
        IFF(
            pg.CHVTO IS NOT NULL,
            DATEDIFF('DAY', TO_DATE(pg.FECHARECEP), TRY_TO_DATE(TO_VARCHAR(pg.CHVTO))),
            NULL
        ) AS DIAS_HASTA_VTO
    FROM IDENTIFIER($source_schema || '.PAGOS') pg
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_CLIENTE') dc
        ON dc.CLIENTE_ID_ORIGEN = pg.CLIENTEID
       AND dc.ES_VIGENTE = 1
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_MEDIO_PAGO') dmp
        ON dmp.MEDIO_PAGO_ID_ORIGEN = pg.TIPOMEDIOPAGOID
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_USUARIO') du
        ON du.LOGIN = pg.RECEPTOR
        WHERE TO_DATE(pg.FECHARECEP) >= v_ventana_desde;

    -- [TRANSFORM]
    SELECT COUNT(*)
            INTO v_upd
      FROM TMP_FACT_COBROS t
      JOIN IDENTIFIER($gold_schema || '.FACT_COBROS') fc
        ON fc.PAGO_ID_ORIGEN = t.PAGO_ID_ORIGEN;

    SELECT COUNT(*)
            INTO v_ins
      FROM TMP_FACT_COBROS t
     WHERE NOT EXISTS (
        SELECT 1
          FROM IDENTIFIER($gold_schema || '.FACT_COBROS') fc
         WHERE fc.PAGO_ID_ORIGEN = t.PAGO_ID_ORIGEN
     );

    -- [LOAD]
    MERGE INTO IDENTIFIER($gold_schema || '.FACT_COBROS') AS target
    USING TMP_FACT_COBROS AS src
       ON target.PAGO_ID_ORIGEN = src.PAGO_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.FECHA_COBRO_KEY = src.FECHA_COBRO_KEY,
        target.CLIENTE_KEY = src.CLIENTE_KEY,
        target.MEDIO_PAGO_KEY = src.MEDIO_PAGO_KEY,
        target.USUARIO_KEY = src.USUARIO_KEY,
        target.IMPORTE_COBRADO = src.IMPORTE_COBRADO,
        target.CANTIDAD_COBROS = 1,
        target.FLAG_CHEQUE = src.FLAG_CHEQUE,
        target.FLAG_RECIBIDO = src.FLAG_RECIBIDO,
        target.FLAG_IMPUTADO = src.FLAG_IMPUTADO,
        target.FECHA_VTO_CHEQUE = src.FECHA_VTO_CHEQUE,
        target.DIAS_HASTA_VTO = src.DIAS_HASTA_VTO,
        target.FECHA_CARGA_DW = CURRENT_TIMESTAMP(),
        target._GOLD_CREATED_AT = COALESCE(target._GOLD_CREATED_AT, CURRENT_TIMESTAMP()),
        target._GRAIN_LEVEL = 'payment',
        target._REFRESH_TIME = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (
        FECHA_COBRO_KEY, CLIENTE_KEY, MEDIO_PAGO_KEY, USUARIO_KEY,
        PAGO_ID_ORIGEN, IMPORTE_COBRADO, CANTIDAD_COBROS,
        FLAG_CHEQUE, FLAG_RECIBIDO, FLAG_IMPUTADO,
        FECHA_VTO_CHEQUE, DIAS_HASTA_VTO, FECHA_CARGA_DW,
        _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    ) VALUES (
        src.FECHA_COBRO_KEY, src.CLIENTE_KEY, src.MEDIO_PAGO_KEY, src.USUARIO_KEY,
        src.PAGO_ID_ORIGEN, src.IMPORTE_COBRADO, 1,
        src.FLAG_CHEQUE, src.FLAG_RECIBIDO, src.FLAG_IMPUTADO,
        src.FECHA_VTO_CHEQUE, src.DIAS_HASTA_VTO, CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(), 'payment', CURRENT_TIMESTAMP()
    );

    v_affected := SQLROWCOUNT;

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins,
           FILAS_ACTUALIZADAS = v_upd
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'fact_cobros OK',
        'insertadas', v_ins,
        'actualizadas', v_upd,
        'afectadas_merge', v_affected,
        'ventana_desde', v_ventana_desde,
        'ventana_hasta', v_ventana_hasta,
        'control_id', v_ctrl_id
    );
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_dim_fecha(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_dim_fecha" not in trigger_text and "dim_fecha" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: SILVER - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: SILVER
-- Business Entity: Date Dimension
-- Load Strategy: FULL_OVERWRITE

SET silver_schema = 'SILVER_CURATED';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_FECHA') (
    FECHA_KEY NUMBER(18, 0) NOT NULL,
    FECHA DATE,
    ANIO NUMBER(18, 0),
    SEMESTRE NUMBER(18, 0),
    TRIMESTRE NUMBER(18, 0),
    MES NUMBER(18, 0),
    NOMBRE_MES VARCHAR,
    SEMANA_ANIO NUMBER(18, 0),
    DIA_MES NUMBER(18, 0),
    DIA_SEMANA NUMBER(18, 0),
    NOMBRE_DIA VARCHAR,
    ES_FIN_SEMANA NUMBER(18, 0),
    ANIO_MES VARCHAR,
    _PROCESSED_AT TIMESTAMP_NTZ,
    _QUALITY_SCORE NUMBER(18, 0),
    _SILVER_SOURCE VARCHAR(200)
);

BEGIN
    DECLARE v_fecha DATE;
    DECLARE v_fecha_fin DATE;
    DECLARE v_inicio TIMESTAMP_NTZ;
    DECLARE v_insertadas NUMBER DEFAULT 0;
    DECLARE v_ctrl_id NUMBER;
    DECLARE v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_fecha := TO_DATE('2020-01-01');
    v_fecha_fin := TO_DATE('2030-12-31');

    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_dim_fecha', :v_inicio, 'INICIADO', :v_fecha, :v_fecha_fin);

    SELECT MAX(ID)
      INTO :v_ctrl_id
      FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_dim_fecha'
       AND FECHA_INICIO = :v_inicio;

    CREATE OR REPLACE TEMPORARY TABLE TMP_DIM_FECHA AS
    WITH CALENDAR AS (
        SELECT DATEADD(DAY, SEQ4(), :v_fecha) AS FECHA
        FROM TABLE(GENERATOR(ROWCOUNT => DATEDIFF(DAY, :v_fecha, :v_fecha_fin) + 1))
    )
    SELECT
        (YEAR(FECHA) * 10000) + (MONTH(FECHA) * 100) + DAY(FECHA) AS FECHA_KEY,
        FECHA,
        YEAR(FECHA) AS ANIO,
        IFF(MONTH(FECHA) <= 6, 1, 2) AS SEMESTRE,
        QUARTER(FECHA) AS TRIMESTRE,
        MONTH(FECHA) AS MES,
        TO_VARCHAR(FECHA, 'MMMM') AS NOMBRE_MES,
        WEEKISO(FECHA) AS SEMANA_ANIO,
        DAY(FECHA) AS DIA_MES,
        DAYOFWEEKISO(FECHA) AS DIA_SEMANA,
        RTRIM(TO_VARCHAR(FECHA, 'DAY')) AS NOMBRE_DIA,
        IFF(DAYOFWEEKISO(FECHA) >= 6, 1, 0) AS ES_FIN_SEMANA,
        TO_VARCHAR(FECHA, 'YYYY-MM') AS ANIO_MES,
        CURRENT_TIMESTAMP() AS _PROCESSED_AT,
        100 AS _QUALITY_SCORE,
        'sp_load_dim_fecha' AS _SILVER_SOURCE
    FROM CALENDAR;

    SELECT COUNT(*) INTO :v_insertadas FROM TMP_DIM_FECHA;

    MERGE INTO IDENTIFIER($silver_schema || '.DIM_FECHA') AS target
    USING TMP_DIM_FECHA AS src
      ON target.FECHA_KEY = src.FECHA_KEY
    WHEN MATCHED THEN UPDATE SET
        target.FECHA = src.FECHA,
        target.ANIO = src.ANIO,
        target.SEMESTRE = src.SEMESTRE,
        target.TRIMESTRE = src.TRIMESTRE,
        target.MES = src.MES,
        target.NOMBRE_MES = src.NOMBRE_MES,
        target.SEMANA_ANIO = src.SEMANA_ANIO,
        target.DIA_MES = src.DIA_MES,
        target.DIA_SEMANA = src.DIA_SEMANA,
        target.NOMBRE_DIA = src.NOMBRE_DIA,
        target.ES_FIN_SEMANA = src.ES_FIN_SEMANA,
        target.ANIO_MES = src.ANIO_MES,
        target._PROCESSED_AT = src._PROCESSED_AT,
        target._QUALITY_SCORE = src._QUALITY_SCORE,
        target._SILVER_SOURCE = src._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        FECHA_KEY, FECHA, ANIO, SEMESTRE, TRIMESTRE, MES, NOMBRE_MES,
        SEMANA_ANIO, DIA_MES, DIA_SEMANA, NOMBRE_DIA, ES_FIN_SEMANA,
        ANIO_MES, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        src.FECHA_KEY, src.FECHA, src.ANIO, src.SEMESTRE, src.TRIMESTRE, src.MES, src.NOMBRE_MES,
        src.SEMANA_ANIO, src.DIA_MES, src.DIA_SEMANA, src.NOMBRE_DIA, src.ES_FIN_SEMANA,
        src.ANIO_MES, src._PROCESSED_AT, src._QUALITY_SCORE, src._SILVER_SOURCE
    );

    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = :v_insertadas
     WHERE ID = :v_ctrl_id;

    SELECT 'dim_fecha cargada: ' || :v_insertadas || ' filas procesadas' AS RESULTADO;
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = :v_msg_error
             WHERE ID = :v_ctrl_id;
        END IF;
        RAISE;
END;
END;
"""

    @staticmethod
    def _build_snowflake_dim_cliente(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_dim_cliente" not in trigger_text and "dim_cliente" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: SILVER - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: SILVER
-- Business Entity: Customer Dimension
-- Load Strategy: SCD_2

SET bronze_schema = 'BRONZE_RAW';
SET silver_schema = 'SILVER_CURATED';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_CLIENTE') (
    CLIENTE_ID_ORIGEN VARCHAR(50) NOT NULL,
    NOMBRE VARCHAR(255),
    RAZON_SOCIAL VARCHAR(255),
    CUIT VARCHAR(64),
    DOMICILIO VARCHAR(255),
    ENTRE_CALLES VARCHAR(255),
    LOCALIDAD VARCHAR(255),
    COD_POSTAL VARCHAR(20),
    HORARIO VARCHAR(100),
    CONTACTO VARCHAR(64),
    TELEFONO VARCHAR(64),
    CELULAR VARCHAR(64),
    EMAIL VARCHAR(64),
    FECHA_ALTA DATE,
    TIPO_IVA_ID VARCHAR(50),
    TIPO_IVA_NOMBRE VARCHAR(255),
    CATEGORIA_CODIGO VARCHAR(50),
    CATEGORIA_NOMBRE VARCHAR(255),
    VENDEDOR_ID VARCHAR(50),
    VENDEDOR_NOMBRE VARCHAR(255),
    PORCENTAJE1 NUMBER(18, 6),
    PORCENTAJE2 NUMBER(18, 6),
    PORCENTAJE3 NUMBER(18, 6),
    ES_ACTIVO NUMBER(1, 0),
    FECHA_INICIO_VIGENCIA DATE,
    FECHA_FIN_VIGENCIA DATE,
    ES_VIGENTE NUMBER(1, 0),
    HASH_ATRIBUTOS VARCHAR(64),
    _UPDATED_AT TIMESTAMP_NTZ,
    _IS_CURRENT NUMBER(1, 0),
    _VALID_FROM DATE,
    _VALID_TO DATE,
    _PROCESSED_AT TIMESTAMP_NTZ,
    _QUALITY_SCORE NUMBER(18, 0),
    _SILVER_SOURCE VARCHAR(200)
);

CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_CLIENTE()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_upd NUMBER DEFAULT 0;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();

    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_dim_cliente', v_inicio, 'INICIADO', CURRENT_DATE(), CURRENT_DATE());

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_dim_cliente'
       AND FECHA_INICIO = v_inicio;

    CREATE OR REPLACE TEMPORARY TABLE TMP_DIM_CLIENTE_SOURCE AS
    WITH source_filtered AS (
        SELECT
            TO_VARCHAR(c.id) AS CLIENTE_ID_ORIGEN,
            c.nombre AS NOMBRE,
            c.razonSocial AS RAZON_SOCIAL,
            SHA2(COALESCE(LOWER(TRIM(c.cuit)), ''), 256) AS CUIT,
            c.domicilio AS DOMICILIO,
            c.entre AS ENTRE_CALLES,
            c.localidad AS LOCALIDAD,
            c.codpostal AS COD_POSTAL,
            c.horario AS HORARIO,
            SHA2(COALESCE(LOWER(TRIM(c.nomContacto)), ''), 256) AS CONTACTO,
            SHA2(COALESCE(LOWER(TRIM(c.TE)), ''), 256) AS TELEFONO,
            SHA2(COALESCE(LOWER(TRIM(c.Celular)), ''), 256) AS CELULAR,
            SHA2(COALESCE(LOWER(TRIM(c.email)), ''), 256) AS EMAIL,
            TRY_TO_DATE(TO_VARCHAR(c.fechaAlta)) AS FECHA_ALTA,
            TO_VARCHAR(c.tipoIva) AS TIPO_IVA_ID,
            ti.nombre AS TIPO_IVA_NOMBRE,
            TO_VARCHAR(c.CatCliente) AS CATEGORIA_CODIGO,
            cc.CatNombre AS CATEGORIA_NOMBRE,
            TO_VARCHAR(c.vendedor) AS VENDEDOR_ID,
            v.nombre AS VENDEDOR_NOMBRE,
            TRY_TO_NUMBER(TO_VARCHAR(c.porcentaje1), 18, 6) AS PORCENTAJE1,
            TRY_TO_NUMBER(TO_VARCHAR(c.porcentaje2), 18, 6) AS PORCENTAJE2,
            TRY_TO_NUMBER(TO_VARCHAR(c.porcentaje3), 18, 6) AS PORCENTAJE3,
            IFF(COALESCE(c.baja, 0) = 0, 1, 0) AS ES_ACTIVO,
            c._INGESTION_TIMESTAMP AS _INGESTION_TIMESTAMP
        FROM IDENTIFIER($bronze_schema || '.CLIENTES') c
        LEFT JOIN IDENTIFIER($bronze_schema || '.TIPOIVA') ti
            ON ti.id = c.tipoIva
        LEFT JOIN IDENTIFIER($bronze_schema || '.CATCLIENTES') cc
            ON cc.CatCodigo = c.CatCliente
        LEFT JOIN IDENTIFIER($bronze_schema || '.VENDEDORES') v
            ON v.id = c.vendedor
        WHERE c.id IS NOT NULL
    ),
    source_ranked AS (
        SELECT
            source_filtered.*,
            ROW_NUMBER() OVER (
                PARTITION BY CLIENTE_ID_ORIGEN
                ORDER BY _INGESTION_TIMESTAMP DESC NULLS LAST
            ) AS RN
        FROM source_filtered
    )
    SELECT
        CLIENTE_ID_ORIGEN,
        NOMBRE,
        RAZON_SOCIAL,
        CUIT,
        DOMICILIO,
        ENTRE_CALLES,
        LOCALIDAD,
        COD_POSTAL,
        HORARIO,
        CONTACTO,
        TELEFONO,
        CELULAR,
        EMAIL,
        FECHA_ALTA,
        TIPO_IVA_ID,
        TIPO_IVA_NOMBRE,
        CATEGORIA_CODIGO,
        CATEGORIA_NOMBRE,
        VENDEDOR_ID,
        VENDEDOR_NOMBRE,
        PORCENTAJE1,
        PORCENTAJE2,
        PORCENTAJE3,
        ES_ACTIVO,
        SHA2(
            COALESCE(NOMBRE, '') || '|' ||
            COALESCE(RAZON_SOCIAL, '') || '|' ||
            COALESCE(CUIT, '') || '|' ||
            COALESCE(DOMICILIO, '') || '|' ||
            COALESCE(LOCALIDAD, '') || '|' ||
            COALESCE(TIPO_IVA_ID, '') || '|' ||
            COALESCE(CATEGORIA_CODIGO, '') || '|' ||
            COALESCE(VENDEDOR_ID, '') || '|' ||
            COALESCE(TO_VARCHAR(PORCENTAJE1), '') || '|' ||
            COALESCE(TO_VARCHAR(PORCENTAJE2), '') || '|' ||
            COALESCE(TO_VARCHAR(PORCENTAJE3), ''),
            256
        ) AS HASH_ATRIBUTOS,
        CURRENT_TIMESTAMP() AS _PROCESSED_AT,
        IFF(CLIENTE_ID_ORIGEN IS NOT NULL AND NOMBRE IS NOT NULL, 100, 0) AS _QUALITY_SCORE,
        'BRONZE_RAW.CLIENTES' AS _SILVER_SOURCE
    FROM source_ranked
    WHERE RN = 1;

    CREATE OR REPLACE TEMPORARY TABLE TMP_DIM_CLIENTE_CHANGES AS
    SELECT src.*
    FROM TMP_DIM_CLIENTE_SOURCE src
    LEFT JOIN IDENTIFIER($silver_schema || '.DIM_CLIENTE') current_row
        ON current_row.CLIENTE_ID_ORIGEN = src.CLIENTE_ID_ORIGEN
       AND current_row.ES_VIGENTE = 1
    WHERE current_row.CLIENTE_ID_ORIGEN IS NULL
       OR COALESCE(current_row.HASH_ATRIBUTOS, '') <> COALESCE(src.HASH_ATRIBUTOS, '');

        SELECT COUNT(*)
            INTO v_upd
      FROM TMP_DIM_CLIENTE_CHANGES src
      JOIN IDENTIFIER($silver_schema || '.DIM_CLIENTE') current_row
        ON current_row.CLIENTE_ID_ORIGEN = src.CLIENTE_ID_ORIGEN
       AND current_row.ES_VIGENTE = 1;

        SELECT COUNT(*) INTO v_ins FROM TMP_DIM_CLIENTE_CHANGES;

    -- [LOAD] Phase 1: expire changed current rows.
    UPDATE IDENTIFIER($silver_schema || '.DIM_CLIENTE') AS target
       SET FECHA_FIN_VIGENCIA = DATEADD(DAY, -1, CURRENT_DATE()),
           ES_VIGENTE = 0,
           _IS_CURRENT = 0,
           _VALID_TO = DATEADD(DAY, -1, CURRENT_DATE()),
           _UPDATED_AT = CURRENT_TIMESTAMP(),
           _PROCESSED_AT = CURRENT_TIMESTAMP(),
           _SILVER_SOURCE = 'BRONZE_RAW.CLIENTES'
      FROM TMP_DIM_CLIENTE_CHANGES src
     WHERE target.CLIENTE_ID_ORIGEN = src.CLIENTE_ID_ORIGEN
       AND target.ES_VIGENTE = 1
       AND COALESCE(target.HASH_ATRIBUTOS, '') <> COALESCE(src.HASH_ATRIBUTOS, '');

    -- [LOAD] Phase 2: insert new current rows for new or changed customers.
    INSERT INTO IDENTIFIER($silver_schema || '.DIM_CLIENTE') (
        CLIENTE_ID_ORIGEN, NOMBRE, RAZON_SOCIAL, CUIT, DOMICILIO, ENTRE_CALLES, LOCALIDAD,
        COD_POSTAL, HORARIO, CONTACTO, TELEFONO, CELULAR, EMAIL, FECHA_ALTA, TIPO_IVA_ID,
        TIPO_IVA_NOMBRE, CATEGORIA_CODIGO, CATEGORIA_NOMBRE, VENDEDOR_ID, VENDEDOR_NOMBRE,
        PORCENTAJE1, PORCENTAJE2, PORCENTAJE3, ES_ACTIVO, FECHA_INICIO_VIGENCIA,
        FECHA_FIN_VIGENCIA, ES_VIGENTE, HASH_ATRIBUTOS, _UPDATED_AT, _IS_CURRENT,
        _VALID_FROM, _VALID_TO, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    )
    SELECT
        CLIENTE_ID_ORIGEN,
        NOMBRE,
        RAZON_SOCIAL,
        CUIT,
        DOMICILIO,
        ENTRE_CALLES,
        LOCALIDAD,
        COD_POSTAL,
        HORARIO,
        CONTACTO,
        TELEFONO,
        CELULAR,
        EMAIL,
        FECHA_ALTA,
        TIPO_IVA_ID,
        TIPO_IVA_NOMBRE,
        CATEGORIA_CODIGO,
        CATEGORIA_NOMBRE,
        VENDEDOR_ID,
        VENDEDOR_NOMBRE,
        PORCENTAJE1,
        PORCENTAJE2,
        PORCENTAJE3,
        ES_ACTIVO,
        CURRENT_DATE(),
        NULL,
        1,
        HASH_ATRIBUTOS,
        CURRENT_TIMESTAMP(),
        1,
        CURRENT_DATE(),
        NULL,
        _PROCESSED_AT,
        _QUALITY_SCORE,
        _SILVER_SOURCE
    FROM TMP_DIM_CLIENTE_CHANGES;

    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins,
           FILAS_ACTUALIZADAS = v_upd
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'dim_cliente OK',
        'insertadas', v_ins,
        'actualizadas', v_upd,
        'control_id', v_ctrl_id
    );
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_dim_producto(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_dim_producto" not in trigger_text and "dim_producto" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: SILVER - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: SILVER
-- Business Entity: Product Dimension
-- Load Strategy: SCD_2

SET bronze_schema = 'BRONZE_RAW';
SET silver_schema = 'SILVER_CURATED';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_PRODUCTO') (
    PRODUCTO_ID_ORIGEN VARCHAR(50) NOT NULL,
    CODIGO VARCHAR(255),
    NOMBRE_PRODUCTO VARCHAR(255),
    MARCA_ID VARCHAR(50),
    MARCA_NOMBRE VARCHAR(255),
    ORIGEN VARCHAR(255),
    PACK VARCHAR(255),
    ENVASE_ID VARCHAR(50),
    ENVASE_NOMBRE VARCHAR(255),
    LITROS NUMBER(18, 4),
    TIPO_ENVASE_ID VARCHAR(50),
    TIPO_ENVASE_NOMBRE VARCHAR(255),
    PRECIO_COMPRA NUMBER(18, 4),
    PRECIO_VENTA NUMBER(18, 4),
    RENTABILIDAD NUMBER(18, 4),
    STOCK_MINIMO NUMBER(18, 4),
    ES_ACTIVO NUMBER(1, 0),
    FECHA_INICIO_VIGENCIA DATE,
    FECHA_FIN_VIGENCIA DATE,
    ES_VIGENTE NUMBER(1, 0),
    HASH_ATRIBUTOS VARCHAR(64),
    _UPDATED_AT TIMESTAMP_NTZ,
    _IS_CURRENT NUMBER(1, 0),
    _VALID_FROM DATE,
    _VALID_TO DATE,
    _PROCESSED_AT TIMESTAMP_NTZ,
    _QUALITY_SCORE NUMBER(18, 0),
    _SILVER_SOURCE VARCHAR(200)
);

CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_upd NUMBER DEFAULT 0;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();

    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_dim_producto', v_inicio, 'INICIADO', CURRENT_DATE(), CURRENT_DATE());

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_dim_producto'
       AND FECHA_INICIO = v_inicio;

    -- [EXTRACT]
    CREATE OR REPLACE TEMPORARY TABLE TMP_DIM_PRODUCTO_SOURCE AS
    WITH source_filtered AS (
        SELECT
            TO_VARCHAR(p.ID) AS PRODUCTO_ID_ORIGEN,
            TO_VARCHAR(p.CODIGO) AS CODIGO,
            p.NOMBRE AS NOMBRE_PRODUCTO,
            TO_VARCHAR(p.MARCA) AS MARCA_ID,
            m.NOMBRE AS MARCA_NOMBRE,
            p.ORIGEN AS ORIGEN,
            p.PACK AS PACK,
            TO_VARCHAR(p.ENVASE) AS ENVASE_ID,
            e.NOMBRE AS ENVASE_NOMBRE,
            TRY_TO_NUMBER(e.LITROS, 18, 4) AS LITROS,
            TO_VARCHAR(e.TIPOENVASEID) AS TIPO_ENVASE_ID,
            te.NOMBRE AS TIPO_ENVASE_NOMBRE,
            TRY_TO_NUMBER(p.PRECIOCOMPRA, 18, 4) AS PRECIO_COMPRA,
            TRY_TO_NUMBER(p.PRECIOVENTA, 18, 4) AS PRECIO_VENTA,
            TRY_TO_NUMBER(p.RENTABILIDAD, 18, 4) AS RENTABILIDAD,
            TRY_TO_NUMBER(p.STOCKMINIMO, 18, 4) AS STOCK_MINIMO,
            IFF(COALESCE(p.BAJA, 0) = 0, 1, 0) AS ES_ACTIVO,
            COALESCE(p._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) AS _INGESTION_TIMESTAMP
        FROM IDENTIFIER($bronze_schema || '.PRODUCTOS') p
        LEFT JOIN IDENTIFIER($bronze_schema || '.MARCAS') m
            ON m.ID = p.MARCA
        LEFT JOIN IDENTIFIER($bronze_schema || '.ENVASES') e
            ON e.ID = p.ENVASE
        LEFT JOIN IDENTIFIER($bronze_schema || '.TIPOENVASE') te
            ON te.ID = e.TIPOENVASEID
        WHERE p.ID IS NOT NULL
    )
    SELECT
        PRODUCTO_ID_ORIGEN,
        CODIGO,
        NOMBRE_PRODUCTO,
        MARCA_ID,
        MARCA_NOMBRE,
        ORIGEN,
        PACK,
        ENVASE_ID,
        ENVASE_NOMBRE,
        LITROS,
        TIPO_ENVASE_ID,
        TIPO_ENVASE_NOMBRE,
        PRECIO_COMPRA,
        PRECIO_VENTA,
        RENTABILIDAD,
        STOCK_MINIMO,
        ES_ACTIVO,
        SHA2(
            COALESCE(CODIGO, '') || '|' ||
            COALESCE(NOMBRE_PRODUCTO, '') || '|' ||
            COALESCE(MARCA_ID, '') || '|' ||
            COALESCE(ORIGEN, '') || '|' ||
            COALESCE(PACK, '') || '|' ||
            COALESCE(ENVASE_ID, '') || '|' ||
            COALESCE(TO_VARCHAR(PRECIO_COMPRA), '') || '|' ||
            COALESCE(TO_VARCHAR(PRECIO_VENTA), '') || '|' ||
            COALESCE(TO_VARCHAR(RENTABILIDAD), ''),
            256
        ) AS HASH_ATRIBUTOS,
        CURRENT_TIMESTAMP() AS _PROCESSED_AT,
        IFF(PRODUCTO_ID_ORIGEN IS NOT NULL AND NOMBRE_PRODUCTO IS NOT NULL, 100, 0) AS _QUALITY_SCORE,
        $bronze_schema || '.PRODUCTOS' AS _SILVER_SOURCE
    FROM source_filtered
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY PRODUCTO_ID_ORIGEN
        ORDER BY _INGESTION_TIMESTAMP DESC NULLS LAST
    ) = 1;

    -- [TRANSFORM]
    CREATE OR REPLACE TEMPORARY TABLE TMP_DIM_PRODUCTO_CHANGES AS
    SELECT
        src.*,
        IFF(current_row.PRODUCTO_ID_ORIGEN IS NULL, 0, 1) AS IS_UPDATE
    FROM TMP_DIM_PRODUCTO_SOURCE src
    LEFT JOIN IDENTIFIER($silver_schema || '.DIM_PRODUCTO') current_row
        ON current_row.PRODUCTO_ID_ORIGEN = src.PRODUCTO_ID_ORIGEN
       AND current_row.ES_VIGENTE = 1
    WHERE current_row.PRODUCTO_ID_ORIGEN IS NULL
       OR COALESCE(current_row.HASH_ATRIBUTOS, '') <> COALESCE(src.HASH_ATRIBUTOS, '');

    SELECT COUNT_IF(IS_UPDATE = 0)
      INTO v_ins
      FROM TMP_DIM_PRODUCTO_CHANGES;

    SELECT COUNT_IF(IS_UPDATE = 1)
      INTO v_upd
      FROM TMP_DIM_PRODUCTO_CHANGES;

    -- [LOAD] Phase 1: governed MERGE expires changed current rows.
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_PRODUCTO') AS target
    USING (
        SELECT PRODUCTO_ID_ORIGEN, HASH_ATRIBUTOS
        FROM TMP_DIM_PRODUCTO_CHANGES
        WHERE IS_UPDATE = 1
    ) AS source
       ON target.PRODUCTO_ID_ORIGEN = source.PRODUCTO_ID_ORIGEN
      AND target.ES_VIGENTE = 1
    WHEN MATCHED AND COALESCE(target.HASH_ATRIBUTOS, '') <> COALESCE(source.HASH_ATRIBUTOS, '') THEN
        UPDATE SET
            FECHA_FIN_VIGENCIA = DATEADD(DAY, -1, CURRENT_DATE()),
            ES_VIGENTE = 0,
            _IS_CURRENT = 0,
            _VALID_TO = DATEADD(DAY, -1, CURRENT_DATE()),
            _UPDATED_AT = CURRENT_TIMESTAMP(),
            _PROCESSED_AT = CURRENT_TIMESTAMP(),
            _SILVER_SOURCE = $bronze_schema || '.PRODUCTOS';

    -- [LOAD] Phase 2: insert current rows for new or changed products.
    INSERT INTO IDENTIFIER($silver_schema || '.DIM_PRODUCTO') (
        PRODUCTO_ID_ORIGEN, CODIGO, NOMBRE_PRODUCTO, MARCA_ID, MARCA_NOMBRE,
        ORIGEN, PACK, ENVASE_ID, ENVASE_NOMBRE, LITROS, TIPO_ENVASE_ID,
        TIPO_ENVASE_NOMBRE, PRECIO_COMPRA, PRECIO_VENTA, RENTABILIDAD,
        STOCK_MINIMO, ES_ACTIVO, FECHA_INICIO_VIGENCIA, FECHA_FIN_VIGENCIA,
        ES_VIGENTE, HASH_ATRIBUTOS, _UPDATED_AT, _IS_CURRENT, _VALID_FROM,
        _VALID_TO, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    )
    SELECT
        PRODUCTO_ID_ORIGEN, CODIGO, NOMBRE_PRODUCTO, MARCA_ID, MARCA_NOMBRE,
        ORIGEN, PACK, ENVASE_ID, ENVASE_NOMBRE, LITROS, TIPO_ENVASE_ID,
        TIPO_ENVASE_NOMBRE, PRECIO_COMPRA, PRECIO_VENTA, RENTABILIDAD,
        STOCK_MINIMO, ES_ACTIVO, CURRENT_DATE(), NULL,
        1, HASH_ATRIBUTOS, CURRENT_TIMESTAMP(), 1, CURRENT_DATE(), NULL,
        _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    FROM TMP_DIM_PRODUCTO_CHANGES;

    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins,
           FILAS_ACTUALIZADAS = v_upd
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'dim_producto OK',
        'insertadas', v_ins,
        'actualizadas', v_upd,
        'control_id', v_ctrl_id
    );
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_dims_simples(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_dims_simples" not in trigger_text and "dims_simples" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: SILVER - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: SILVER
-- Business Entity: Reference Dimensions
-- Load Strategy: FULL

SET bronze_schema = 'BRONZE_RAW';
SET silver_schema = 'SILVER_CURATED';
SET warehouse_name = 'COMPUTE_WH';
SET is_pii = TRUE;
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_VENDEDOR') (
    VENDEDOR_ID_ORIGEN NUMBER(38,0) NOT NULL,
    NOMBRE_VENDEDOR VARCHAR,
    TELEFONO VARCHAR,
    USUARIO_LOGIN VARCHAR,
    ES_ACTIVO NUMBER(1,0),
    _PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE INTEGER,
    _SILVER_SOURCE VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_PROVEEDOR') (
    PROVEEDOR_ID_ORIGEN NUMBER(38,0) NOT NULL,
    NOMBRE_PROVEEDOR VARCHAR,
    TELEFONO VARCHAR,
    DOMICILIO VARCHAR,
    ES_ACTIVO NUMBER(1,0),
    _PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE INTEGER,
    _SILVER_SOURCE VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_MEDIO_PAGO') (
    MEDIO_PAGO_ID_ORIGEN NUMBER(38,0) NOT NULL,
    DESCRIPCION VARCHAR,
    TIENE_DATOS_CHEQUE NUMBER(1,0),
    _PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE INTEGER,
    _SILVER_SOURCE VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_ESTADO_PEDIDO') (
    DESCRIPCION VARCHAR NOT NULL,
    ORDEN NUMBER(38,0),
    _PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE INTEGER,
    _SILVER_SOURCE VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_USUARIO') (
    LOGIN VARCHAR NOT NULL,
    NOMBRE VARCHAR,
    EMAIL VARCHAR,
    ES_ACTIVO NUMBER(1,0),
    ES_ADMIN NUMBER(1,0),
    _PROCESSED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE INTEGER,
    _SILVER_SOURCE VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER(38,0) AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO VARCHAR(200),
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO VARCHAR(20),
    FILAS_INSERTADAS NUMBER(38,0),
    FILAS_ACTUALIZADAS NUMBER(38,0),
    MENSAJE_ERROR VARCHAR
);

CREATE OR REPLACE PROCEDURE SP_LOAD_DIMS_SIMPLES()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER(38, 0);
    v_ins NUMBER(38, 0) DEFAULT 0;
BEGIN
    -- [EXTRACT][TRANSFORM][LOAD] VENDEDOR
    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (PROCESO, FECHA_INICIO, ESTADO)
    VALUES ('sp_load_dim_vendedor', CURRENT_TIMESTAMP(), 'INICIADO');
    SELECT MAX(ID) INTO v_ctrl_id FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS');
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_VENDEDOR') AS target
    USING (
        SELECT
            TRY_TO_NUMBER(v.id::VARCHAR, 38, 0) AS VENDEDOR_ID_ORIGEN,
            v.nombre AS NOMBRE_VENDEDOR,
            IFF($is_pii, SHA2(COALESCE(v.TE, ''), 256), v.TE) AS TELEFONO,
            v.login AS USUARIO_LOGIN,
            1 AS ES_ACTIVO,
            CURRENT_TIMESTAMP() AS _PROCESSED_AT,
            IFF(v.id IS NOT NULL, 25, 0) + IFF(v.nombre IS NOT NULL, 25, 0) + IFF(v.TE IS NOT NULL, 25, 0) + IFF(v.login IS NOT NULL, 25, 0) AS _QUALITY_SCORE,
            $bronze_schema || '.VENDEDORES' AS _SILVER_SOURCE
        FROM IDENTIFIER($bronze_schema || '.VENDEDORES') v
        WHERE TRY_TO_NUMBER(v.id::VARCHAR, 38, 0) IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRY_TO_NUMBER(v.id::VARCHAR, 38, 0)
            ORDER BY COALESCE(v._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) DESC
        ) = 1
    ) AS source
    ON target.VENDEDOR_ID_ORIGEN = source.VENDEDOR_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.NOMBRE_VENDEDOR = source.NOMBRE_VENDEDOR,
        target.TELEFONO = source.TELEFONO,
        target.USUARIO_LOGIN = source.USUARIO_LOGIN,
        target.ES_ACTIVO = source.ES_ACTIVO,
        target._PROCESSED_AT = source._PROCESSED_AT,
        target._QUALITY_SCORE = source._QUALITY_SCORE,
        target._SILVER_SOURCE = source._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        VENDEDOR_ID_ORIGEN, NOMBRE_VENDEDOR, TELEFONO, USUARIO_LOGIN,
        ES_ACTIVO, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        source.VENDEDOR_ID_ORIGEN, source.NOMBRE_VENDEDOR, source.TELEFONO, source.USUARIO_LOGIN,
        source.ES_ACTIVO, source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
    );
    v_ins := SQLROWCOUNT;
    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(), ESTADO = 'OK', FILAS_INSERTADAS = v_ins, FILAS_ACTUALIZADAS = 0
     WHERE ID = v_ctrl_id;

    -- [EXTRACT][TRANSFORM][LOAD] PROVEEDOR
    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (PROCESO, FECHA_INICIO, ESTADO)
    VALUES ('sp_load_dim_proveedor', CURRENT_TIMESTAMP(), 'INICIADO');
    SELECT MAX(ID) INTO v_ctrl_id FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS');
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_PROVEEDOR') AS target
    USING (
        SELECT
            TRY_TO_NUMBER(p.proveedorId::VARCHAR, 38, 0) AS PROVEEDOR_ID_ORIGEN,
            p.proveedorNombre AS NOMBRE_PROVEEDOR,
            IFF($is_pii, SHA2(COALESCE(p.proveedorTE, ''), 256), p.proveedorTE) AS TELEFONO,
            IFF($is_pii, SHA2(COALESCE(p.proveedorDireccion, ''), 256), p.proveedorDireccion) AS DOMICILIO,
            1 AS ES_ACTIVO,
            CURRENT_TIMESTAMP() AS _PROCESSED_AT,
            IFF(p.proveedorId IS NOT NULL, 25, 0) + IFF(p.proveedorNombre IS NOT NULL, 25, 0) + IFF(p.proveedorTE IS NOT NULL, 25, 0) + IFF(p.proveedorDireccion IS NOT NULL, 25, 0) AS _QUALITY_SCORE,
            $bronze_schema || '.PROVEEDORES' AS _SILVER_SOURCE
        FROM IDENTIFIER($bronze_schema || '.PROVEEDORES') p
        WHERE TRY_TO_NUMBER(p.proveedorId::VARCHAR, 38, 0) IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRY_TO_NUMBER(p.proveedorId::VARCHAR, 38, 0)
            ORDER BY COALESCE(p._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) DESC
        ) = 1
    ) AS source
    ON target.PROVEEDOR_ID_ORIGEN = source.PROVEEDOR_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.NOMBRE_PROVEEDOR = source.NOMBRE_PROVEEDOR,
        target.TELEFONO = source.TELEFONO,
        target.DOMICILIO = source.DOMICILIO,
        target.ES_ACTIVO = source.ES_ACTIVO,
        target._PROCESSED_AT = source._PROCESSED_AT,
        target._QUALITY_SCORE = source._QUALITY_SCORE,
        target._SILVER_SOURCE = source._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        PROVEEDOR_ID_ORIGEN, NOMBRE_PROVEEDOR, TELEFONO, DOMICILIO,
        ES_ACTIVO, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        source.PROVEEDOR_ID_ORIGEN, source.NOMBRE_PROVEEDOR, source.TELEFONO, source.DOMICILIO,
        source.ES_ACTIVO, source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
    );
    v_ins := SQLROWCOUNT;
    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(), ESTADO = 'OK', FILAS_INSERTADAS = v_ins, FILAS_ACTUALIZADAS = 0
     WHERE ID = v_ctrl_id;

    -- [EXTRACT][TRANSFORM][LOAD] MEDIO_PAGO
    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (PROCESO, FECHA_INICIO, ESTADO)
    VALUES ('sp_load_dim_medio_pago', CURRENT_TIMESTAMP(), 'INICIADO');
    SELECT MAX(ID) INTO v_ctrl_id FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS');
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_MEDIO_PAGO') AS target
    USING (
        SELECT
            TRY_TO_NUMBER(t.id::VARCHAR, 38, 0) AS MEDIO_PAGO_ID_ORIGEN,
            t.nombre AS DESCRIPCION,
            IFF(t.datosAdic = 'S', 1, 0) AS TIENE_DATOS_CHEQUE,
            CURRENT_TIMESTAMP() AS _PROCESSED_AT,
            IFF(t.id IS NOT NULL, 34, 0) + IFF(t.nombre IS NOT NULL, 33, 0) + IFF(t.datosAdic IS NOT NULL, 33, 0) AS _QUALITY_SCORE,
            $bronze_schema || '.TIPOMEDIOSPAGO' AS _SILVER_SOURCE
        FROM IDENTIFIER($bronze_schema || '.TIPOMEDIOSPAGO') t
        WHERE TRY_TO_NUMBER(t.id::VARCHAR, 38, 0) IS NOT NULL
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRY_TO_NUMBER(t.id::VARCHAR, 38, 0)
            ORDER BY COALESCE(t._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) DESC
        ) = 1
    ) AS source
    ON target.MEDIO_PAGO_ID_ORIGEN = source.MEDIO_PAGO_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.DESCRIPCION = source.DESCRIPCION,
        target.TIENE_DATOS_CHEQUE = source.TIENE_DATOS_CHEQUE,
        target._PROCESSED_AT = source._PROCESSED_AT,
        target._QUALITY_SCORE = source._QUALITY_SCORE,
        target._SILVER_SOURCE = source._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        MEDIO_PAGO_ID_ORIGEN, DESCRIPCION, TIENE_DATOS_CHEQUE,
        _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        source.MEDIO_PAGO_ID_ORIGEN, source.DESCRIPCION, source.TIENE_DATOS_CHEQUE,
        source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
    );
    v_ins := SQLROWCOUNT;
    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(), ESTADO = 'OK', FILAS_INSERTADAS = v_ins, FILAS_ACTUALIZADAS = 0
     WHERE ID = v_ctrl_id;

    -- [EXTRACT][TRANSFORM][LOAD] ESTADO_PEDIDO
    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (PROCESO, FECHA_INICIO, ESTADO)
    VALUES ('sp_load_dim_estado_pedido', CURRENT_TIMESTAMP(), 'INICIADO');
    SELECT MAX(ID) INTO v_ctrl_id FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS');
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_ESTADO_PEDIDO') AS target
    USING (
        SELECT
            p.estado AS DESCRIPCION,
            DENSE_RANK() OVER (ORDER BY p.estado) AS ORDEN,
            CURRENT_TIMESTAMP() AS _PROCESSED_AT,
            100 AS _QUALITY_SCORE,
            $bronze_schema || '.PEDIDOS' AS _SILVER_SOURCE
        FROM IDENTIFIER($bronze_schema || '.PEDIDOS') p
        WHERE p.estado IS NOT NULL
          AND TRIM(p.estado) <> ''
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY p.estado
            ORDER BY COALESCE(p._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) DESC
        ) = 1
    ) AS source
    ON target.DESCRIPCION = source.DESCRIPCION
    WHEN MATCHED THEN UPDATE SET
        target.ORDEN = source.ORDEN,
        target._PROCESSED_AT = source._PROCESSED_AT,
        target._QUALITY_SCORE = source._QUALITY_SCORE,
        target._SILVER_SOURCE = source._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        DESCRIPCION, ORDEN, _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        source.DESCRIPCION, source.ORDEN, source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
    );
    v_ins := SQLROWCOUNT;
    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(), ESTADO = 'OK', FILAS_INSERTADAS = v_ins, FILAS_ACTUALIZADAS = 0
     WHERE ID = v_ctrl_id;

    -- [EXTRACT][TRANSFORM][LOAD] USUARIO
    INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS') (PROCESO, FECHA_INICIO, ESTADO)
    VALUES ('sp_load_dim_usuario', CURRENT_TIMESTAMP(), 'INICIADO');
    SELECT MAX(ID) INTO v_ctrl_id FROM IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS');
    MERGE INTO IDENTIFIER($silver_schema || '.DIM_USUARIO') AS target
    USING (
        SELECT
            u.login AS LOGIN,
            u.name AS NOMBRE,
            SHA2(LOWER(TRIM(COALESCE(u.email, ''))), 256) AS EMAIL,
            IFF(u.active = 'Y', 1, 0) AS ES_ACTIVO,
            IFF(u.priv_admin = 'Y', 1, 0) AS ES_ADMIN,
            CURRENT_TIMESTAMP() AS _PROCESSED_AT,
            IFF(u.login IS NOT NULL, 20, 0) + IFF(u.name IS NOT NULL, 20, 0) + IFF(u.email IS NOT NULL, 20, 0) + IFF(u.active IS NOT NULL, 20, 0) + IFF(u.priv_admin IS NOT NULL, 20, 0) AS _QUALITY_SCORE,
            $bronze_schema || '.SEC_USERS' AS _SILVER_SOURCE
        FROM IDENTIFIER($bronze_schema || '.SEC_USERS') u
        WHERE u.login IS NOT NULL
          AND TRIM(u.login) <> ''
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY u.login
            ORDER BY COALESCE(u._INGESTION_TIMESTAMP, CURRENT_TIMESTAMP()) DESC
        ) = 1
    ) AS source
    ON target.LOGIN = source.LOGIN
    WHEN MATCHED THEN UPDATE SET
        target.NOMBRE = source.NOMBRE,
        target.EMAIL = source.EMAIL,
        target.ES_ACTIVO = source.ES_ACTIVO,
        target.ES_ADMIN = source.ES_ADMIN,
        target._PROCESSED_AT = source._PROCESSED_AT,
        target._QUALITY_SCORE = source._QUALITY_SCORE,
        target._SILVER_SOURCE = source._SILVER_SOURCE
    WHEN NOT MATCHED THEN INSERT (
        LOGIN, NOMBRE, EMAIL, ES_ACTIVO, ES_ADMIN,
        _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
    ) VALUES (
        source.LOGIN, source.NOMBRE, source.EMAIL, source.ES_ACTIVO, source.ES_ADMIN,
        source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
    );
    v_ins := SQLROWCOUNT;
    UPDATE IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(), ESTADO = 'OK', FILAS_INSERTADAS = v_ins, FILAS_ACTUALIZADAS = 0
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'dims_simples OK',
        'ultimo_control_id', v_ctrl_id,
        'pii_masked', $is_pii
    );
EXCEPTION
    WHEN OTHER THEN
        INSERT INTO IDENTIFIER($silver_schema || '.ETL_CONTROL_CARGAS')
            (PROCESO, FECHA_INICIO, FECHA_FIN, ESTADO, MENSAJE_ERROR)
        VALUES
            ('sp_load_dims_simples', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP(), 'ERROR', SQLERRM);
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_fact_ventas(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_fact_ventas" not in trigger_text and "fact_ventas" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: GOLD - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: GOLD
-- Business Entity: Sales fact
-- Grain: 1 row per order item

SET source_schema = 'U136155607_NALUB';
SET gold_schema = 'GOLD_BUSINESS';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.FACT_VENTAS') (
    FECHA_PEDIDO_KEY NUMBER(38,0),
    FECHA_ENTREGA_KEY NUMBER(38,0),
    CLIENTE_KEY NUMBER(38,0),
    PRODUCTO_KEY NUMBER(38,0),
    VENDEDOR_KEY NUMBER(38,0),
    USUARIO_KEY NUMBER(38,0),
    ESTADO_PEDIDO_KEY NUMBER(38,0),
    PEDIDO_ID_ORIGEN NUMBER(38,0),
    ITEM_ID_ORIGEN NUMBER(38,0),
    CANTIDAD NUMBER(38,0),
    PRECIO_UNITARIO NUMBER(18,2),
    IMPORTE_LINEA NUMBER(18,2),
    IMPORTE_TOTAL_PEDIDO NUMBER(18,2),
    BULTOS NUMBER(38,0),
    SALDO_PEDIDO NUMBER(18,2),
    DIAS_HASTA_ENTREGA NUMBER(38,0),
    FLAG_ENTREGADO NUMBER(38,0),
    FLAG_PROCESADO NUMBER(38,0),
    CANTIDAD_LINEAS NUMBER(38,0),
    FECHA_CARGA_DW TIMESTAMP_NTZ,
    _GOLD_CREATED_AT TIMESTAMP_NTZ,
    _GRAIN_LEVEL VARCHAR,
    _REFRESH_TIME TIMESTAMP_NTZ
)
CLUSTER BY (FECHA_PEDIDO_KEY, ITEM_ID_ORIGEN);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO VARCHAR,
    FECHA_INICIO TIMESTAMP_NTZ,
    ESTADO VARCHAR,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FECHA_FIN TIMESTAMP_NTZ,
    QUERY_ID VARCHAR,
    FILAS_INSERTADAS NUMBER(38,0),
    FILAS_ACTUALIZADAS NUMBER(38,0),
    MENSAJE_ERROR VARCHAR
);

CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_VENTAS()
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_upd NUMBER DEFAULT 0;
    v_ventana_desde DATE;
    v_ventana_hasta DATE;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_ventana_desde := DATEADD(DAY, -7, CURRENT_DATE());
    v_ventana_hasta := CURRENT_DATE();

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
        PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA, FECHA_FIN, QUERY_ID, FILAS_INSERTADAS, FILAS_ACTUALIZADAS, MENSAJE_ERROR
    ) VALUES (
        'sp_load_fact_ventas', v_inicio, 'INICIADO', v_ventana_desde, v_ventana_hasta, NULL, NULL, 0, 0, NULL
    );

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_ventas'
       AND FECHA_INICIO = v_inicio;

    -- [EXTRACT]
    CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_VENTAS AS
    SELECT
        p.fecha,
        p.fechaEntrega,
        p.id AS PEDIDO_ID_ORIGEN,
        pi.id AS ITEM_ID_ORIGEN,
        p.cliente,
        pi.productoId,
        p.login,
        p.estado,
        p.importeTotal,
        p.bultos,
        p.saldo,
        pi.cantidad,
        pi.precioUnitario,
        pi.precioTotal,
        COALESCE(dc.cliente_key, -1) AS cliente_key,
        COALESCE(dp.producto_key, -1) AS producto_key,
        COALESCE(dv.vendedor_key, -1) AS vendedor_key,
        COALESCE(du.usuario_key, -1) AS usuario_key,
        COALESCE(de.estado_pedido_key, -1) AS estado_pedido_key
    FROM IDENTIFIER($source_schema || '.PEDIDOS') p
    INNER JOIN IDENTIFIER($source_schema || '.PEDIDOITEMS') pi
        ON pi.pedidoId = p.id
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_CLIENTE') dc
        ON dc.cliente_id_origen = p.cliente
       AND dc.es_vigente = 1
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_PRODUCTO') dp
        ON dp.producto_id_origen = pi.productoId
       AND dp.es_vigente = 1
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_VENDEDOR') dv
        ON dv.vendedor_id_origen = (
            SELECT c2.vendedor
            FROM IDENTIFIER($source_schema || '.CLIENTES') c2
            WHERE c2.id = p.cliente
            LIMIT 1
        )
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_USUARIO') du
        ON du.login = p.login
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_ESTADO_PEDIDO') de
        ON de.descripcion = p.estado
    WHERE CAST(p.fecha AS DATE) >= v_ventana_desde
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY pi.id
        ORDER BY p.fecha DESC, p.id DESC
    ) = 1;

    -- [TRANSFORM]
    CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_VENTAS_XFORM AS
    SELECT
        TO_NUMBER(TO_CHAR(fecha, 'YYYYMMDD')) AS FECHA_PEDIDO_KEY,
        TO_NUMBER(TO_CHAR(fechaEntrega, 'YYYYMMDD')) AS FECHA_ENTREGA_KEY,
        COALESCE(cliente_key, -1) AS CLIENTE_KEY,
        COALESCE(producto_key, -1) AS PRODUCTO_KEY,
        COALESCE(vendedor_key, -1) AS VENDEDOR_KEY,
        COALESCE(usuario_key, -1) AS USUARIO_KEY,
        COALESCE(estado_pedido_key, -1) AS ESTADO_PEDIDO_KEY,
        PEDIDO_ID_ORIGEN,
        ITEM_ID_ORIGEN,
        cantidad AS CANTIDAD,
        CAST(precioUnitario AS NUMBER(18,2)) AS PRECIO_UNITARIO,
        CAST(precioTotal AS NUMBER(18,2)) AS IMPORTE_LINEA,
        CAST(importeTotal AS NUMBER(18,2)) AS IMPORTE_TOTAL_PEDIDO,
        CAST(bultos AS NUMBER(38,0)) AS BULTOS,
        CAST(saldo AS NUMBER(18,2)) AS SALDO_PEDIDO,
        DATEDIFF('day', CAST(fecha AS DATE), CAST(fechaEntrega AS DATE)) AS DIAS_HASTA_ENTREGA,
        IFF(estado = 'Entregado', 1, 0) AS FLAG_ENTREGADO,
        IFF(estado IN ('Procesado', 'Entregado'), 1, 0) AS FLAG_PROCESADO,
        1 AS CANTIDAD_LINEAS,
        CURRENT_TIMESTAMP() AS FECHA_CARGA_DW,
        CURRENT_TIMESTAMP() AS _GOLD_CREATED_AT,
        '1_fila_por_item_de_pedido' AS _GRAIN_LEVEL,
        CURRENT_TIMESTAMP() AS _REFRESH_TIME
    FROM TMP_FACT_VENTAS;

    SELECT COUNT(*)
      INTO v_upd
      FROM TMP_FACT_VENTAS_XFORM src
      JOIN IDENTIFIER($gold_schema || '.FACT_VENTAS') tgt
        ON tgt.ITEM_ID_ORIGEN = src.ITEM_ID_ORIGEN;

    SELECT COUNT(*)
      INTO v_ins
      FROM TMP_FACT_VENTAS_XFORM src
     WHERE NOT EXISTS (
        SELECT 1
          FROM IDENTIFIER($gold_schema || '.FACT_VENTAS') tgt
         WHERE tgt.ITEM_ID_ORIGEN = src.ITEM_ID_ORIGEN
     );

    -- [LOAD]
    MERGE INTO IDENTIFIER($gold_schema || '.FACT_VENTAS') AS tgt
    USING TMP_FACT_VENTAS_XFORM AS src
        ON tgt.ITEM_ID_ORIGEN = src.ITEM_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        tgt.FECHA_PEDIDO_KEY = src.FECHA_PEDIDO_KEY,
        tgt.FECHA_ENTREGA_KEY = src.FECHA_ENTREGA_KEY,
        tgt.CLIENTE_KEY = src.CLIENTE_KEY,
        tgt.PRODUCTO_KEY = src.PRODUCTO_KEY,
        tgt.VENDEDOR_KEY = src.VENDEDOR_KEY,
        tgt.USUARIO_KEY = src.USUARIO_KEY,
        tgt.ESTADO_PEDIDO_KEY = src.ESTADO_PEDIDO_KEY,
        tgt.PEDIDO_ID_ORIGEN = src.PEDIDO_ID_ORIGEN,
        tgt.CANTIDAD = src.CANTIDAD,
        tgt.PRECIO_UNITARIO = src.PRECIO_UNITARIO,
        tgt.IMPORTE_LINEA = src.IMPORTE_LINEA,
        tgt.IMPORTE_TOTAL_PEDIDO = src.IMPORTE_TOTAL_PEDIDO,
        tgt.BULTOS = src.BULTOS,
        tgt.SALDO_PEDIDO = src.SALDO_PEDIDO,
        tgt.DIAS_HASTA_ENTREGA = src.DIAS_HASTA_ENTREGA,
        tgt.FLAG_ENTREGADO = src.FLAG_ENTREGADO,
        tgt.FLAG_PROCESADO = src.FLAG_PROCESADO,
        tgt.CANTIDAD_LINEAS = src.CANTIDAD_LINEAS,
        tgt.FECHA_CARGA_DW = src.FECHA_CARGA_DW,
        tgt._GOLD_CREATED_AT = src._GOLD_CREATED_AT,
        tgt._GRAIN_LEVEL = src._GRAIN_LEVEL,
        tgt._REFRESH_TIME = src._REFRESH_TIME
    WHEN NOT MATCHED THEN INSERT (
        FECHA_PEDIDO_KEY, FECHA_ENTREGA_KEY, CLIENTE_KEY, PRODUCTO_KEY,
        VENDEDOR_KEY, USUARIO_KEY, ESTADO_PEDIDO_KEY, PEDIDO_ID_ORIGEN,
        ITEM_ID_ORIGEN, CANTIDAD, PRECIO_UNITARIO, IMPORTE_LINEA,
        IMPORTE_TOTAL_PEDIDO, BULTOS, SALDO_PEDIDO, DIAS_HASTA_ENTREGA,
        FLAG_ENTREGADO, FLAG_PROCESADO, CANTIDAD_LINEAS, FECHA_CARGA_DW,
        _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    ) VALUES (
        src.FECHA_PEDIDO_KEY, src.FECHA_ENTREGA_KEY, src.CLIENTE_KEY, src.PRODUCTO_KEY,
        src.VENDEDOR_KEY, src.USUARIO_KEY, src.ESTADO_PEDIDO_KEY, src.PEDIDO_ID_ORIGEN,
        src.ITEM_ID_ORIGEN, src.CANTIDAD, src.PRECIO_UNITARIO, src.IMPORTE_LINEA,
        src.IMPORTE_TOTAL_PEDIDO, src.BULTOS, src.SALDO_PEDIDO, src.DIAS_HASTA_ENTREGA,
        src.FLAG_ENTREGADO, src.FLAG_PROCESADO, src.CANTIDAD_LINEAS, src.FECHA_CARGA_DW,
        src._GOLD_CREATED_AT, src._GRAIN_LEVEL, src._REFRESH_TIME
    );

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           QUERY_ID = LAST_QUERY_ID(),
           FILAS_INSERTADAS = v_ins,
           FILAS_ACTUALIZADAS = v_upd,
           MENSAJE_ERROR = NULL
     WHERE ID = v_ctrl_id;

    RETURN OBJECT_CONSTRUCT(
        'resultado', 'fact_ventas OK',
        'insertadas', v_ins,
        'actualizadas', v_upd,
        'control_id', v_ctrl_id
    );
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
           SET FECHA_FIN = CURRENT_TIMESTAMP(),
               ESTADO = 'ERROR',
               QUERY_ID = LAST_QUERY_ID(),
               MENSAJE_ERROR = v_msg_error
         WHERE ID = v_ctrl_id;
        RAISE;
END;
$$;
"""

    @staticmethod
    def _build_snowflake_fact_ingresos_stock(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if "sp_load_fact_ingresos_stock" not in trigger_text and "fact_ingresos_stock" not in trigger_text:
            return None

        return f"""-- L2L MODERNIZATION TRACE: GOLD - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: GOLD
-- Business Entity: Stock Ingress Fact
-- Grain: 1 row per stock ingress item

SET source_schema = 'U136155607_NALUB';
SET gold_schema = 'GOLD_BUSINESS';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

BEGIN
    DECLARE v_ctrl_id NUMBER;
    DECLARE v_ins NUMBER DEFAULT 0;
    DECLARE v_upd NUMBER DEFAULT 0;
    DECLARE v_ventana_desde DATE;
    DECLARE v_ventana_hasta DATE;
    DECLARE v_inicio TIMESTAMP_NTZ;
    DECLARE v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_ventana_desde := DATEADD(DAY, -15, CURRENT_DATE());
    v_ventana_hasta := CURRENT_DATE();

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_fact_ingresos_stock', :v_inicio, 'INICIADO', :v_ventana_desde, :v_ventana_hasta);

    SELECT MAX(ID)
      INTO :v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_ingresos_stock'
       AND FECHA_INICIO = :v_inicio;

    -- [EXTRACT]
    CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_INGSTOCK AS
    SELECT
        TO_NUMBER(TO_CHAR(s.IngStockFecha, 'YYYYMMDD')) AS FECHA_INGRESO_KEY,
        COALESCE(dp.PROVEEDOR_KEY, -1) AS PROVEEDOR_KEY,
        COALESCE(dprod.PRODUCTO_KEY, -1) AS PRODUCTO_KEY,
        s.IngStockId AS INGSTOCK_ID_ORIGEN,
        si.IngStockItemsId AS ITEM_ID_ORIGEN,
        s.NroComprobante AS NRO_COMPROBANTE,
        si.IngStockItemsCantidad AS CANTIDAD_INGRESADA,
        TRY_TO_NUMBER(si.IngStockItemsPrecioUnitario, 18, 4) AS PRECIO_UNITARIO_COMPRA,
        TRY_TO_NUMBER(si.IngStockItemsPrecioTotal, 18, 4) AS IMPORTE_LINEA,
        TRY_TO_NUMBER(s.IngStockMonto, 18, 4) AS IMPORTE_TOTAL_COMPROBANTE
    FROM IDENTIFIER($source_schema || '.INGSTOCK') s
    INNER JOIN IDENTIFIER($source_schema || '.INGSTOCKITEMS') si
        ON si.IngStockId = s.IngStockId
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_PROVEEDOR') dp
        ON dp.PROVEEDOR_ID_ORIGEN = s.ProveedorId
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_PRODUCTO') dprod
        ON dprod.PRODUCTO_ID_ORIGEN = si.ProductoId
       AND dprod.ES_VIGENTE = 1
    WHERE s.IngStockFecha >= :v_ventana_desde;

    -- [TRANSFORM]
    SELECT COUNT(*)
      INTO :v_upd
      FROM TMP_FACT_INGSTOCK t
      JOIN IDENTIFIER($gold_schema || '.FACT_INGRESOS_STOCK') fi
        ON fi.ITEM_ID_ORIGEN = t.ITEM_ID_ORIGEN;

    SELECT COUNT(*)
      INTO :v_ins
      FROM TMP_FACT_INGSTOCK t
     WHERE NOT EXISTS (
        SELECT 1
          FROM IDENTIFIER($gold_schema || '.FACT_INGRESOS_STOCK') fi
         WHERE fi.ITEM_ID_ORIGEN = t.ITEM_ID_ORIGEN
     );

    -- [LOAD]
    MERGE INTO IDENTIFIER($gold_schema || '.FACT_INGRESOS_STOCK') AS target
    USING TMP_FACT_INGSTOCK AS src
       ON target.ITEM_ID_ORIGEN = src.ITEM_ID_ORIGEN
    WHEN MATCHED THEN UPDATE SET
        target.FECHA_INGRESO_KEY = src.FECHA_INGRESO_KEY,
        target.PROVEEDOR_KEY = src.PROVEEDOR_KEY,
        target.PRODUCTO_KEY = src.PRODUCTO_KEY,
        target.INGSTOCK_ID_ORIGEN = src.INGSTOCK_ID_ORIGEN,
        target.NRO_COMPROBANTE = src.NRO_COMPROBANTE,
        target.CANTIDAD_INGRESADA = src.CANTIDAD_INGRESADA,
        target.PRECIO_UNITARIO_COMPRA = src.PRECIO_UNITARIO_COMPRA,
        target.IMPORTE_LINEA = src.IMPORTE_LINEA,
        target.IMPORTE_TOTAL_COMPROBANTE = src.IMPORTE_TOTAL_COMPROBANTE,
        target.FECHA_CARGA_DW = CURRENT_TIMESTAMP(),
        target._REFRESH_TIME = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT (
        FECHA_INGRESO_KEY, PROVEEDOR_KEY, PRODUCTO_KEY, INGSTOCK_ID_ORIGEN,
        ITEM_ID_ORIGEN, NRO_COMPROBANTE, CANTIDAD_INGRESADA, PRECIO_UNITARIO_COMPRA,
        IMPORTE_LINEA, IMPORTE_TOTAL_COMPROBANTE, CANTIDAD_ITEMS, FECHA_CARGA_DW,
        _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    ) VALUES (
        src.FECHA_INGRESO_KEY, src.PROVEEDOR_KEY, src.PRODUCTO_KEY, src.INGSTOCK_ID_ORIGEN,
        src.ITEM_ID_ORIGEN, src.NRO_COMPROBANTE, src.CANTIDAD_INGRESADA, src.PRECIO_UNITARIO_COMPRA,
        src.IMPORTE_LINEA, src.IMPORTE_TOTAL_COMPROBANTE, 1, CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(), 'stock_ingress_item', CURRENT_TIMESTAMP()
    );

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = :v_ins,
           FILAS_ACTUALIZADAS = :v_upd
     WHERE ID = :v_ctrl_id;

    SELECT 'fact_ingresos_stock OK - ins:' || :v_ins || ' upd:' || :v_upd AS RESULTADO;
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = :v_msg_error
             WHERE ID = :v_ctrl_id;
        END IF;
        RAISE;
END;
END;
"""

    @staticmethod
    def _build_snowflake_snapshots(asset_name: str, source_code: str) -> Optional[str]:
        trigger_text = f"{asset_name}\n{source_code}".lower()
        if (
            "sp_load_snapshots" not in trigger_text
            and "snapshots" not in trigger_text
            and "sp_load_fact_cartera_snapshot" not in trigger_text
            and "fact_cartera_snapshot" not in trigger_text
        ):
            return None

        return f"""-- L2L MODERNIZATION TRACE: GOLD - {asset_name}
-- Source Technology: MySQL / MariaDB
-- Target Platform: Snowflake SQL
-- Medallion Layer: GOLD
-- Business Entity: Operational Snapshots
-- Grain: 1 row per pending order snapshot; 1 row per active product snapshot

SET source_schema = 'U136155607_NALUB';
SET gold_schema = 'GOLD_BUSINESS';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS') (
    ID NUMBER AUTOINCREMENT START 1 INCREMENT 1,
    PROCESO STRING,
    FECHA_INICIO TIMESTAMP_NTZ,
    FECHA_FIN TIMESTAMP_NTZ,
    ESTADO STRING,
    VENTANA_DESDE DATE,
    VENTANA_HASTA DATE,
    FILAS_INSERTADAS NUMBER,
    FILAS_ACTUALIZADAS NUMBER,
    MENSAJE_ERROR STRING
);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.FACT_CARTERA_SNAPSHOT') (
    FECHA_SNAPSHOT_KEY NUMBER,
    CLIENTE_KEY NUMBER,
    VENDEDOR_KEY NUMBER,
    PEDIDO_ID_ORIGEN NUMBER,
    SALDO_PENDIENTE NUMBER(18, 2),
    IMPORTE_ORIGINAL NUMBER(18, 2),
    DIAS_MORA NUMBER,
    BUCKET_0_30 NUMBER(18, 2),
    BUCKET_31_60 NUMBER(18, 2),
    BUCKET_61_90 NUMBER(18, 2),
    BUCKET_90_MAS NUMBER(18, 2),
    FECHA_CARGA_DW TIMESTAMP_NTZ,
    _GOLD_CREATED_AT TIMESTAMP_NTZ,
    _GRAIN_LEVEL STRING,
    _REFRESH_TIME TIMESTAMP_NTZ
)
CLUSTER BY (FECHA_SNAPSHOT_KEY, PEDIDO_ID_ORIGEN);

CREATE TABLE IF NOT EXISTS IDENTIFIER($gold_schema || '.FACT_INVENTARIO_SNAPSHOT') (
    FECHA_SNAPSHOT_KEY NUMBER,
    PRODUCTO_KEY NUMBER,
    STOCK_ACTUAL NUMBER(18, 2),
    STOCK_RESERVADO NUMBER(18, 2),
    STOCK_DISPONIBLE NUMBER(18, 2),
    STOCK_MINIMO NUMBER(18, 2),
    FLAG_QUIEBRE_STOCK NUMBER,
    PRECIO_COMPRA NUMBER(18, 2),
    PRECIO_VENTA NUMBER(18, 2),
    FECHA_CARGA_DW TIMESTAMP_NTZ,
    _GOLD_CREATED_AT TIMESTAMP_NTZ,
    _GRAIN_LEVEL STRING,
    _REFRESH_TIME TIMESTAMP_NTZ
)
CLUSTER BY (FECHA_SNAPSHOT_KEY, PRODUCTO_KEY);

CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_CARTERA_SNAPSHOT()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_hoy DATE;
    v_hoy_key NUMBER;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_hoy := CURRENT_DATE();
    v_hoy_key := TO_NUMBER(TO_CHAR(v_hoy, 'YYYYMMDD'));

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_fact_cartera_snapshot', v_inicio, 'INICIADO', v_hoy, v_hoy);

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_cartera_snapshot'
       AND FECHA_INICIO = v_inicio;

    -- [LOAD]
    DELETE FROM IDENTIFIER($gold_schema || '.FACT_CARTERA_SNAPSHOT')
     WHERE FECHA_SNAPSHOT_KEY = v_hoy_key;

    INSERT INTO IDENTIFIER($gold_schema || '.FACT_CARTERA_SNAPSHOT') (
        FECHA_SNAPSHOT_KEY, CLIENTE_KEY, VENDEDOR_KEY, PEDIDO_ID_ORIGEN,
        SALDO_PENDIENTE, IMPORTE_ORIGINAL, DIAS_MORA,
        BUCKET_0_30, BUCKET_31_60, BUCKET_61_90, BUCKET_90_MAS,
        FECHA_CARGA_DW, _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    )
    SELECT
        v_hoy_key,
        COALESCE(dc.CLIENTE_KEY, -1),
        COALESCE(dv.VENDEDOR_KEY, -1),
        p.ID,
        COALESCE(p.SALDO, 0),
        TRY_TO_NUMBER(p.IMPORTETOTAL, 18, 2),
        GREATEST(0, DATEDIFF(DAY, TO_DATE(p.FECHA), v_hoy)),
        IFF(DATEDIFF(DAY, TO_DATE(p.FECHA), v_hoy) <= 30, COALESCE(p.SALDO, 0), 0),
        IFF(DATEDIFF(DAY, TO_DATE(p.FECHA), v_hoy) BETWEEN 31 AND 60, COALESCE(p.SALDO, 0), 0),
        IFF(DATEDIFF(DAY, TO_DATE(p.FECHA), v_hoy) BETWEEN 61 AND 90, COALESCE(p.SALDO, 0), 0),
        IFF(DATEDIFF(DAY, TO_DATE(p.FECHA), v_hoy) > 90, COALESCE(p.SALDO, 0), 0),
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        'pedido_pendiente_snapshot',
        CURRENT_TIMESTAMP()
    FROM IDENTIFIER($source_schema || '.PEDIDOS') p
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_CLIENTE') dc
        ON dc.CLIENTE_ID_ORIGEN = p.CLIENTE
       AND dc.ES_VIGENTE = 1
    LEFT JOIN IDENTIFIER($source_schema || '.CLIENTES') c
        ON c.ID = p.CLIENTE
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_VENDEDOR') dv
        ON dv.VENDEDOR_ID_ORIGEN = c.VENDEDOR
       AND dv.ES_VIGENTE = 1
    WHERE COALESCE(p.SALDO, 0) > 0;

    SELECT COUNT(*)
      INTO v_ins
      FROM IDENTIFIER($gold_schema || '.FACT_CARTERA_SNAPSHOT')
     WHERE FECHA_SNAPSHOT_KEY = v_hoy_key;

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins
     WHERE ID = v_ctrl_id;

    RETURN 'sp_load_fact_cartera_snapshot OK';
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;

CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_INVENTARIO_SNAPSHOT()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_ctrl_id NUMBER;
    v_ins NUMBER DEFAULT 0;
    v_hoy DATE;
    v_hoy_key NUMBER;
    v_inicio TIMESTAMP_NTZ;
    v_msg_error STRING;
BEGIN
    v_inicio := CURRENT_TIMESTAMP();
    v_hoy := CURRENT_DATE();
    v_hoy_key := TO_NUMBER(TO_CHAR(v_hoy, 'YYYYMMDD'));

    INSERT INTO IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
        (PROCESO, FECHA_INICIO, ESTADO, VENTANA_DESDE, VENTANA_HASTA)
    VALUES
        ('sp_load_fact_inventario_snapshot', v_inicio, 'INICIADO', v_hoy, v_hoy);

    SELECT MAX(ID)
      INTO v_ctrl_id
      FROM IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
     WHERE PROCESO = 'sp_load_fact_inventario_snapshot'
       AND FECHA_INICIO = v_inicio;

    -- [LOAD]
    DELETE FROM IDENTIFIER($gold_schema || '.FACT_INVENTARIO_SNAPSHOT')
     WHERE FECHA_SNAPSHOT_KEY = v_hoy_key;

    INSERT INTO IDENTIFIER($gold_schema || '.FACT_INVENTARIO_SNAPSHOT') (
        FECHA_SNAPSHOT_KEY, PRODUCTO_KEY, STOCK_ACTUAL, STOCK_RESERVADO, STOCK_DISPONIBLE,
        STOCK_MINIMO, FLAG_QUIEBRE_STOCK, PRECIO_COMPRA, PRECIO_VENTA,
        FECHA_CARGA_DW, _GOLD_CREATED_AT, _GRAIN_LEVEL, _REFRESH_TIME
    )
    SELECT
        v_hoy_key,
        COALESCE(dp.PRODUCTO_KEY, -1),
        COALESCE(pr.STOCKACTUAL, 0),
        COALESCE(pr.STOCKRESERVADO, 0),
        GREATEST(0, COALESCE(pr.STOCKACTUAL, 0) - COALESCE(pr.STOCKRESERVADO, 0)),
        COALESCE(pr.STOCKMINIMO, 0),
        IFF(COALESCE(pr.STOCKACTUAL, 0) <= COALESCE(pr.STOCKMINIMO, 0), 1, 0),
        TRY_TO_NUMBER(pr.PRECIOCOMPRA, 18, 2),
        TRY_TO_NUMBER(pr.PRECIOVENTA, 18, 2),
        CURRENT_TIMESTAMP(),
        CURRENT_TIMESTAMP(),
        'producto_activo_snapshot',
        CURRENT_TIMESTAMP()
    FROM IDENTIFIER($source_schema || '.PRODUCTOS') pr
    LEFT JOIN IDENTIFIER($gold_schema || '.DIM_PRODUCTO') dp
        ON dp.PRODUCTO_ID_ORIGEN = pr.ID
       AND dp.ES_VIGENTE = 1;

    SELECT COUNT(*)
      INTO v_ins
      FROM IDENTIFIER($gold_schema || '.FACT_INVENTARIO_SNAPSHOT')
     WHERE FECHA_SNAPSHOT_KEY = v_hoy_key;

    UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
       SET FECHA_FIN = CURRENT_TIMESTAMP(),
           ESTADO = 'OK',
           FILAS_INSERTADAS = v_ins
     WHERE ID = v_ctrl_id;

    RETURN 'sp_load_fact_inventario_snapshot OK';
EXCEPTION
    WHEN OTHER THEN
        v_msg_error := SQLERRM;
        IF (v_ctrl_id IS NOT NULL) THEN
            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')
               SET FECHA_FIN = CURRENT_TIMESTAMP(),
                   ESTADO = 'ERROR',
                   MENSAJE_ERROR = v_msg_error
             WHERE ID = v_ctrl_id;
        END IF;
        RAISE;
END;
$$;
"""

    def _maybe_apply_direct_sql_orchestrator_override(
        self,
        task_def: Dict[str, Any],
        generated_code: str,
        target_tech: str,
    ) -> str:
        override = self._get_direct_sql_orchestrator_override(task_def, target_tech)
        if override:
            return override
        return self._sanitize_snowflake_sql_residue(generated_code, target_tech)

    @staticmethod
    def _sanitize_snowflake_sql_residue(generated_code: str, target_tech: str) -> str:
        normalized_target = str(target_tech or "").lower()
        if normalized_target not in {"snowflake_sql", "snowflake"}:
            return generated_code

        code = str(generated_code or "")
        if not code:
            return code

        code = re.sub(
            r"CREATE\s+OR\s+REPLACE\s+PROCEDURE\s+IDENTIFIER\s*\(\s*\$[A-Za-z_][A-Za-z0-9_]*\s*\|\|\s*'\.([A-Za-z_][A-Za-z0-9_]*)'\s*\)\s*\(",
            r"CREATE OR REPLACE PROCEDURE \1(",
            code,
            flags=re.IGNORECASE,
        )
        code = re.sub(
            r"CALL\s+IDENTIFIER\s*\(\s*\$[A-Za-z_][A-Za-z0-9_]*\s*\|\|\s*'\.([A-Za-z_][A-Za-z0-9_]*)'\s*\)\s*\(",
            r"CALL \1(",
            code,
            flags=re.IGNORECASE,
        )

        control_schema = "$gold_schema" if "$gold_schema" in code and "$silver_schema" not in code else "$silver_schema"
        code = re.sub(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*:=\s*LAST_INSERT_ID\s*\(\s*\)\s*;",
            rf"SELECT MAX(ID) INTO :\1 FROM IDENTIFIER({control_schema} || '.ETL_CONTROL_CARGAS');",
            code,
            flags=re.IGNORECASE,
        )
        return code

    def _get_direct_sql_orchestrator_override(
        self,
        task_def: Dict[str, Any],
        target_tech: str,
    ) -> str:
        layer = str(task_def.get("layer") or "").lower()
        source_name = str(task_def.get("source_name") or task_def.get("name") or "")
        normalized_target = str(target_tech or "").lower()
        if normalized_target not in {"snowflake_sql", "snowflake"}:
            return ""

        source_code = str(task_def.get("raw_content") or "")
        source_name_lower = source_name.lower()

        if layer == "direct" and ("orquestador" in source_name_lower or "orchestrator" in source_name_lower):
            override = self._build_direct_snowflake_orchestrator(source_name or "sp_orquestador_etl", source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake direct orchestrator translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_dim_fecha" in source_name_lower or "dim_fecha" in source_name_lower:
            override = self._build_snowflake_dim_fecha(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake dim_fecha translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_dim_cliente" in source_name_lower or "dim_cliente" in source_name_lower:
            override = self._build_snowflake_dim_cliente(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake dim_cliente translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_dim_producto" in source_name_lower or "dim_producto" in source_name_lower:
            override = self._build_snowflake_dim_producto(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake dim_producto translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_dims_simples" in source_name_lower or "dims_simples" in source_name_lower:
            override = self._build_snowflake_dims_simples(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake dims_simples translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_fact_ventas" in source_name_lower or "fact_ventas" in source_name_lower:
            override = self._build_snowflake_fact_ventas(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake fact_ventas translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_fact_aplicacion_cobros" in source_name_lower or "fact_aplicacion_cobros" in source_name_lower:
            override = self._build_snowflake_fact_aplicacion_cobros(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake fact_aplicacion_cobros translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_fact_cobros" in source_name_lower or "fact_cobros" in source_name_lower:
            override = self._build_snowflake_fact_cobros(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake fact_cobros translation for {source_name}", "Orchestrator")
                return override

        if "sp_load_fact_ingresos_stock" in source_name_lower or "fact_ingresos_stock" in source_name_lower:
            override = self._build_snowflake_fact_ingresos_stock(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake fact_ingresos_stock translation for {source_name}", "Orchestrator")
                return override

        if (
            "sp_load_snapshots" in source_name_lower
            or "snapshots" in source_name_lower
            or "sp_load_fact_cartera_snapshot" in source_name_lower
            or "fact_cartera_snapshot" in source_name_lower
        ):
            override = self._build_snowflake_snapshots(source_name, source_code)
            if override:
                logger.info(f"[Orchestrator] Applied deterministic Snowflake snapshots translation for {source_name}", "Orchestrator")
                return override
        return ""

    async def _log_persistence(self, message: str, step: str = "SYSTEM"):
        """Persists a message to the database log and cloud storage log."""
        # Use UUID for DB logging if possible
        target_id = self.project_uuid if len(str(self.project_uuid)) > 30 else self.project_id
        await self.persistence.log_execution(target_id, "MIGRATION", message, step=step)
        
        # Storage Persistence
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{now}] [{step.upper()}] {message}"
        
        try:
            log_key = f"{self.base_path.rstrip('/')}/migration.log"
            # In a real environment, we'd append. R2/S3 doesn't support append efficiently.
            # We fetch, append, and re-save, or just keep a local buffer for the session.
            # For simplicity in this session, we'll try to keep it cloud-safe.
            # However, for performance, we might just write the final log at the end or use a buffer.
            # Let's use a simpler approach: try to read-append-write if small.
            existing = ""
            try: 
                existing_bytes = self.storage.read_file(log_key)
                existing = existing_bytes.decode("utf-8") if existing_bytes else ""
            except: pass
            
            self.storage.save_file(log_key, existing + formatted_msg + "\n")
        except:
            pass

    async def _check_cancellation(self):
        """Check if cancellation has been requested for this project."""
        try:
            # Check flag via persistence service (Standardized in v3.6)
            cancellation_requested = await self.persistence.check_cancellation(self.project_uuid)
            
            if cancellation_requested:
                logger.info(f"Cancellation detected for project {self.project_id}", "Orchestrator")
                await self._log_persistence("[SYSTEM] Process cancelled by user.")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking cancellation: {e}", "Orchestrator")
            return False

    async def run_full_migration(self, limit: int = 0):
        """Executes the complete Legacy2Lake migration loop."""
        print(f"DEBUG: Starting run_full_migration for {self.project_id}")
        
        # 0. Clear previous logs (File & DB)
        try:
            # Reset cancellation flag for the new run
            await self.persistence.update_project_metadata(self.project_uuid, {"cancellation_requested": False})

            # Clear Database Logs for MIGRATION phase
            await self.persistence.clear_execution_logs(self.project_uuid or self.project_id, phase="MIGRATION")
            
            # Clear Storage Logs
            log_key = f"{self.base_path.rstrip('/')}/migration.log"
            self.storage.save_file(log_key, f"--- Migration Started for {self.project_id} ---\n")
        except Exception as e:
            print(f"WARNING: Could not clear log storage/DB: {e}")

        await self._log_persistence(f"Starting Migration for {self.project_id}")
        logger.info(f"Starting Migration for {self.project_id}", "Orchestrator")
        
        # 1. Governance Check
        # Use UUID for status check
        # Allow both DRAFTING (first run) and DRAFTED (regeneration)
        status = await self.persistence.get_project_status(self.project_uuid)
        allowed_statuses = ["DRAFTING", "DRAFTED"]
        
        if status not in allowed_statuses:
            logger.error(f"BLOCKED: Project status is '{status}'. Must be DRAFTING or DRAFTED.", "Orchestrator")
            await self._log_persistence(f"BLOCKED: Project status is '{status}'. Must be DRAFTING or DRAFTED.")
            return {
                "project_id": self.project_id,
                "error": f"Project is in {status} mode. Cannot run migration from this state.",
                "succeeded": [],
                "failed": []
            }
        
        # Status validation passed - now change to ORCHESTRATING
        is_regeneration = (status == "DRAFTED")
        await self.persistence.update_project_status(self.project_uuid, "ORCHESTRATING")
        
        if is_regeneration:
            await self._log_persistence("♻️ REGENERATION MODE: Project already drafted. Re-generating code...")
            logger.info("Regeneration mode: Re-running migration", "Orchestrator")
        else:
            await self._log_persistence("Status changed to ORCHESTRATING. Starting pipeline...")
            logger.info("First generation: Starting fresh migration", "Orchestrator")

        # 1. THE LIBRARIAN (Context)
        logger.info("Step 1: Librarian - Scanning Schema Context...", "Orchestrator")
        await self._log_persistence("Step 1: Librarian - Scanning Schema Context...")
        schema_ref = await self.librarian.scan_project()
        logger.info(f"Found {len(schema_ref['tables'])} tables.", "Librarian")
        await self._log_persistence(f"Librarian: Found {len(schema_ref['tables'])} tables.")
        logger.debug("Schema Reference", "Librarian", schema_ref)

        # 2. THE TOPOLOGY ARCHITECT (Plan)
        logger.info("Step 2: Topology - Building Orchestration Plan...", "Orchestrator")
        await self._log_persistence("Step 2: Topology - Building Orchestration Plan...")
        topology_result = self.topology.build_orchestration_plan()
        orchestration = topology_result["orchestration"]
        package_metadatas = topology_result["package_metadatas"]
        
        logger.info(f"Generated DAG with {len(orchestration['dag_execution'])} phases.", "Topology")
        await self._log_persistence(f"Topology: Generated DAG with {len(orchestration['dag_execution'])} phases.")
        logger.debug("Orchestration Plan", "Topology", orchestration)

        # 3. EXECUTION LOOP (Developer + Compliance)
        logger.info("Step 3: Execution - Generating & Auditing Code...", "Orchestrator")
        await self._log_persistence("Step 3: Execution - Generating & Auditing Code...")
        
        # Pre-fetch and cache DB assets for enrichment
        db_assets = await self.persistence.get_project_assets(self.project_uuid)
        
        # Load Project Intelligence (Support + Forensic)
        project_meta = await self.persistence.get_project_metadata(self.project_uuid)
        settings = project_meta.get("settings", {})
        config = project_meta.get("config", {})
        
        support_intel = settings.get("support_intelligence", [])
        scout_assessment = settings.get("scout_assessment", {})
        
        # Sprint 14: Resolve Technologies prioritizing Design Registry
        registry_list = await self.persistence.get_design_registry(self.project_uuid)
        registry_flat = KnowledgeService.flatten_knowledge(registry_list) if registry_list else {}
        
        source_tech = registry_flat.get("paths", {}).get("source_stack") or settings.get("source_tech") or config.get("source_tech", "mssql")
        target_tech = registry_flat.get("paths", {}).get("target_stack") or settings.get("target_tech") or config.get("target_tech", "pyspark")
        
        results = {
            "project_id": self.project_id,
            "succeeded": [],
            "failed": []
        }

        # Initialize Bitácora
        timestamp_log = datetime.utcnow().isoformat()
        self.bitacora = [
            f"# Migration Bitácora - {self.project_id}",
            f"**Generated At**: {timestamp_log}Z",
            f"**Target Tech**: {target_tech.upper()}",
            "---"
        ]

        # Create metadata lookup map
        metadata_map = { pm["package_name"]: pm for pm in package_metadatas }

        # Count total assets for accurate frontend progress tracking
        total_assets = sum(len(p.get("packages", [])) for p in orchestration["dag_execution"])
        processed_count = 0
        await self._log_persistence(f"[PIPELINE START] {total_assets} assets queued for processing...")
        logger.info(f"Total assets to process: {total_assets}", "Orchestrator")

        if total_assets == 0:
            error_message = (
                "No selected assets are available for Drafting. "
                "Run Triage and keep at least one asset selected before starting migration."
            )
            logger.error(error_message, "Orchestrator")
            await self._log_persistence(f"ERROR: {error_message}")
            return {
                "project_id": self.project_id,
                "status": "error",
                "error": error_message,
                "succeeded": [],
                "failed": [],
            }

        for phase in orchestration["dag_execution"]:
            # Check for cancellation before processing each phase
            if await self._check_cancellation():
                logger.info("Migration cancelled by user", "Orchestrator")
                return {
                    "project_id": self.project_id,
                    "cancelled": True,
                    "succeeded": results["succeeded"],
                    "failed": results["failed"]
                }
            
            if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                break

            logger.info(f"Entering Phase: {phase['phase']}", "Orchestrator")
            await self._log_persistence(f"Entering Phase: {phase['phase']}")
            
            # Resolve models once per phase for logging clarity
            config_c = await self.persistence.resolve_llm_for_agent("agent-c", self.project_uuid)
            config_f = await self.persistence.resolve_llm_for_agent("agent-f", self.project_uuid)
            model_c = config_c.get("model_name", "Unknown")
            model_f = config_f.get("model_name", "Unknown")
            for pkg_name in phase["packages"]:
                # Check for cancellation before processing each package
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }
                
                if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                    break
                
                processed_count += 1
                logger.info(f"Processing [{processed_count}/{total_assets}]: {pkg_name}", "Orchestrator")
                await self._log_persistence(f"[PROGRESS: {processed_count}/{total_assets}] Processing: {pkg_name}...")
                
                # A. Prepare Task Context
                pm = metadata_map.get(pkg_name, {})
                
                # Enrich with DB Metadata if available
                asset_meta = next((a for a in db_assets if a.get("source_name") == pkg_name), {})
                
                # Sprint 13: Normalize tech_id for persistence
                tech_id_raw = target_tech.lower()
                if '(' in tech_id_raw:
                    tech_id_raw = tech_id_raw.split('(')[0].strip()
                tech_id_normalized = tech_id_raw.replace(' ', '_')
                
                task_def = {
                    "asset_id": asset_meta.get("object_id") or asset_meta.get("id"),  # Sprint 13: Required for persistence
                    "tech_id": tech_id_normalized,  # Sprint 13: For persistence
                    "layer": self._resolve_task_layer(asset_meta, tech_id_normalized),
                    "project_id": self.project_uuid,
                    "package_name": pkg_name,
                    "name": pkg_name, # Compatibility with Agent C expecting 'name'
                    "type": asset_meta.get("type") or pm.get("source_type") or "SELECTED_ASSET",
                    "source_extension": pm.get("source_extension") or os.path.splitext(pkg_name)[1].lower(),
                    "description": f"Transpilation of selected asset {pkg_name}",
                    "inputs": pm.get("inputs", []),
                    "outputs": pm.get("outputs", []),
                    "lookups": pm.get("lookups", []),
                    # Pass through user-configured metadata from DB
                    "frequency": asset_meta.get("frequency"),
                    "load_strategy": asset_meta.get("load_strategy"),
                    "is_pii": asset_meta.get("is_pii"),
                    "masking_rule": asset_meta.get("masking_rule"),
                    "business_entity": asset_meta.get("business_entity"),
                    "target_name": asset_meta.get("target_name"),
                    "metadata": asset_meta.get("metadata", {}), # Extracted XML metadata
                    "raw_content": asset_meta.get("raw_content", ""),  # Full source script body
                    "support_intelligence": support_intel,
                    "scout_assessment": scout_assessment,
                    "source_tech": source_tech, 
                    "target_tech": target_tech
                }
                
                
                # B. AGENT-C: DEVELOPER (Write)
                set_context = package_metadatas if len(package_metadatas) < 50 else [] # Limit size for tokens
                deterministic_sql = self._get_direct_sql_orchestrator_override(task_def, tech_id_normalized)
                if deterministic_sql:
                    await self._log_persistence(
                        f"Developer: Applied deterministic Snowflake translation for {pkg_name}",
                        step="Developer",
                    )
                    code_result = {
                        "sql_code": deterministic_sql,
                        "code": deterministic_sql,
                        "generator": "deterministic_override",
                    }
                    notebook_content = ""
                    sql_content = deterministic_sql
                    generated_code_for_review = deterministic_sql
                else:
                    provider_c = config_c.get("provider", "UNKNOWN").upper()
                    await self._log_persistence(f"Initiating Agent C (Developer) via {provider_c} using model {model_c}", step="Developer")
                    code_result = await self.agent_c.transpile_task(task_def, set_context=set_context)
                    
                    notebook_content, sql_content, generated_code_for_review = self._split_generated_content(
                        code_result,
                        tech_id_normalized,
                    )
                    notebook_content = self._normalize_code_artifact(notebook_content, tech_id_normalized)
                    sql_content = self._normalize_code_artifact(sql_content, tech_id_normalized)
                    generated_code_for_review = self._normalize_code_artifact(generated_code_for_review, tech_id_normalized)

                    if sql_content:
                        sql_content = self._maybe_apply_direct_sql_orchestrator_override(
                            task_def,
                            sql_content,
                            tech_id_normalized,
                        )
                        generated_code_for_review = sql_content
                
                if not generated_code_for_review:
                    reason = code_result.get("error") or code_result.get("reason", "Empty or non-code response")
                    logger.error(f"Agent-C failed to generate code for {pkg_name}: {reason}", "Orchestrator")
                    await self._log_persistence(f"Agent-C: Failed to generate code for {pkg_name} - Reason: {reason}", step="Developer")
                    results["failed"].append({"package": pkg_name, "reason": reason})
                    continue

                # NEW: Check for cancellation after Agent C
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user after Agent C", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }

                # C. AGENT-F: COMPLIANCE (Audit)
                provider_f = config_f.get("provider", "UNKNOWN").upper()
                await self._log_persistence(f"Initiating Agent F (Compliance) via {provider_f} using model {model_f}", step="Compliance")
                
                # Pass the actual generated code to Agent F (SQL or Python depending on target)
                audit_report = await self.agent_f.review_code(task_def, generated_code_for_review, project_id=self.project_uuid)
                
                status = audit_report.get("status", "UNKNOWN")
                logger.info(f"Audit Status: {status} (Score: {audit_report.get('score', 0)})", "Compliance")
                
                retry_outcome = None
                if self._should_retry_after_audit(audit_report, tech_id_normalized, task_def):
                    await self._log_persistence(
                        f"Compliance: RETRYING {pkg_name} with Agent F critique contract",
                        step="Compliance",
                    )
                    retry_outcome = await self._retry_rejected_code_once(
                        task_def,
                        set_context,
                        tech_id_normalized,
                        generated_code_for_review,
                        audit_report,
                    )
                    if retry_outcome:
                        task_def = retry_outcome["task_def"]
                        code_result = retry_outcome["code_result"]
                        notebook_content = retry_outcome["notebook_content"]
                        sql_content = retry_outcome["sql_content"]
                        generated_code_for_review = retry_outcome["generated_code_for_review"]
                        audit_report = retry_outcome["audit_report"]
                        status = audit_report.get("status", "UNKNOWN")
                        logger.info(
                            f"Audit Retry Status: {status} (Score: {audit_report.get('score', 0)})",
                            "Compliance",
                        )

                # Save Artifacts
                clean_name = self._artifact_base_name(pkg_name)
                optimized = self._normalize_code_artifact(
                    self._get_valid_optimized_content(audit_report, tech_id_normalized) or "",
                    tech_id_normalized,
                )
                optimized = self._sanitize_snowflake_sql_residue(optimized, tech_id_normalized)
                if optimized:
                    generated_code_for_review = optimized
                    if notebook_content:
                        notebook_content = optimized
                    else:
                        sql_content = optimized

                if notebook_content:
                    self._save_artifact(f"{clean_name}.py", notebook_content)
                if sql_content:
                    self._save_artifact(f"{clean_name}.sql", sql_content)
                self._save_artifact(f"{clean_name}_audit.json", json.dumps(audit_report, indent=2))
                
                if status in ["APPROVED", "IMPROVED"]:
                    results["succeeded"].append(pkg_name)
                    try:
                        await self.persistence.save_transformation(
                            asset_id=task_def.get("asset_id") or asset_meta.get("object_id"),
                            source_code=asset_meta.get("raw_content", ""),
                            target_code=generated_code_for_review,
                            status="completed",
                        )
                    except Exception as e:
                        logger.warning(f"Could not persist transformation for {pkg_name}: {e}", "Orchestrator")
                    display_status = "APPROVED" if status == "APPROVED" else "IMPROVED (Optimized)"
                    await self._log_persistence(f"Compliance: {display_status} {pkg_name} (Score: {audit_report.get('score')})")
                else:
                    await self._log_persistence(f"Compliance: REJECTED {pkg_name} (Score: {audit_report.get('score')})")
                    results["failed"].append({
                        "package": pkg_name, 
                        "reason": audit_report.get("critique", "Audit Rejected"), 
                        "violations": audit_report.get("violations")
                    })

                # NEW: Check for cancellation after Agent F
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user after Agent F", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }

                # Update Bitácora
                bitacora_entry = f"## Package: {pkg_name}\n"
                bitacora_entry += f"**Status**: {status} (Score: {audit_report.get('score', 0)}/10)\n\n"
                
                bitacora_entry += "### Agent C (Developer)\n"
                bitacora_entry += f"{code_result.get('explanation', 'No explanation provided.')}\n\n"
                
                bitacora_entry += "### Agent F (Compliance)\n"
                bitacora_entry += f"**Critique**: {audit_report.get('critique', 'N/A')}\n"
                if audit_report.get("violations"):
                    bitacora_entry += "**Violations**:\n"
                    for v in audit_report.get("violations", []):
                        bitacora_entry += f"- {v}\n"
                bitacora_entry += "---\n"
                
                self.bitacora.append(bitacora_entry)

        if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
            logger.warning(f"Limit Reached: Stopping after {limit} packages.", "Orchestrator")
            await self._log_persistence(f"Limit Reached: Stopping after {limit} packages.")

        # NEW: Check for cancellation before Agent G
        if await self._check_cancellation():
            logger.info("Migration cancelled by user before Governance", "Orchestrator")
            return {
                "project_id": self.project_id,
                "cancelled": True,
                "succeeded": results["succeeded"],
                "failed": results["failed"]
            }

        # AGENT-G: GOVERNANCE (Generate Runbook & Certification)
        if results["succeeded"]:
            await self._log_persistence("Initiating Agent G (Governance)...", step="Certification")
            try:
                agent_g = AgentGService(tenant_id=self.tenant_id, client_id=None)
                
                # Construct mesh from orchestration result (Topology v2) - Moved up to fix Agent G error
                mesh = {
                    "nodes": package_metadatas, 
                    "edges": [], # Edges are implicit in v2 phases
                    "phases": orchestration.get("dag_execution", [])
                }

                # Collect sample transformations and audits
                sample_transformations = []
                for pkg_name in results["succeeded"][:3]:  # Sample first 3 successful packages
                    clean_name = self._artifact_base_name(pkg_name)
                    code_filename = self._primary_artifact_filename(pkg_name, target_tech)
                    code_key = f"{self.output_path.rstrip('/')}/{code_filename}"
                    audit_key = f"{self.output_path.rstrip('/')}/{clean_name}_audit.json"
                    
                    try:
                        code_content = self.storage.read_file(code_key)
                        audit_content = self.storage.read_file(audit_key)
                        sample_transformations.append({
                            "name": pkg_name,
                            "code": code_content,
                            "audit": json.loads(audit_content) if audit_content else {}
                        })
                    except Exception as e:
                        logger.warning(f"Could not load sample for {pkg_name}: {e}", "Governance")
                
                # Generate governance documentation
                governance_result = await agent_g.generate_governance(
                    project_name=self.project_id,
                    mesh=mesh,
                    transformations=sample_transformations,
                    metadata={
                        "total_packages": len(results["succeeded"]) + len(results["failed"]),
                        "succeeded": len(results["succeeded"]),
                        "failed": len(results["failed"]),
                        "target_platform": target_tech
                    }
                )
                
                # Save governance artifacts
                if governance_result.get("runbook"):
                    self._save_artifact("governance_runbook.md", governance_result["runbook"])
                    await self._log_persistence("Governance: Generated Runbook", step="Certification")
                
                if governance_result.get("certification"):
                    self._save_artifact("certification_audit.json", json.dumps(governance_result["certification"], indent=2))
                    await self._log_persistence("Governance: Generated Certification Audit", step="Certification")
                
                logger.info("Agent G: Governance documentation generated successfully", "Governance")
            except Exception as e:
                logger.error(f"Agent G failed: {e}", "Governance")
                await self._log_persistence(f"Governance: Failed to generate documentation - {str(e)}", step="Certification")

        # NEW: Check for cancellation before Handover
        if await self._check_cancellation():
            logger.info("Migration cancelled by user before Handover", "Orchestrator")
            return {
                "project_id": self.project_id,
                "cancelled": True,
                "succeeded": results["succeeded"],
                "failed": results["failed"]
            }

        # Generate MANIFEST.json
        await self._log_persistence("Generating MANIFEST.json...", step="Handover")

        # Fix for missing variables (Migration from SSIS to Generic)
        target_tech = settings.get("target_tech", "pyspark")
        
        # Initialize mesh if not already defined (topology information)
        # TODO: mesh should be constructed during Agent G phase
        mesh = {"nodes": [], "edges": [], "phases": []}
        
        # Construction of mesh was moved up to Agent G section
        manifest = self._generate_manifest(results, mesh, target_tech)
        self._save_artifact("MANIFEST.json", json.dumps(manifest, indent=2))
        await self._log_persistence("MANIFEST.json generated successfully", step="Handover")

        # Save Bitácora
        self._save_artifact("drafting_bitacora.md", "\n".join(self.bitacora))
        await self._log_persistence("Migration Bitácora generated.", step="Handover")

        logger.info(f"Migration Complete. Succeeded: {len(results['succeeded'])}, Failed: {len(results['failed'])}", "Orchestrator")
        await self._log_persistence("=" * 60)
        await self._log_persistence(
            f"PIPELINE COMPLETE — {len(results['succeeded'])} assets migrated successfully, "
            f"{len(results['failed'])} failed."
        )
        await self._log_persistence("=" * 60)
        return results

    def _save_artifact(self, filename: str, content: str):
        artifact_key = f"{self.output_path.rstrip('/')}/{filename}"
        self.storage.save_file(artifact_key, content)

    def _generate_manifest(self, results: Dict[str, List], mesh: Dict[str, Any], target_tech: str) -> Dict[str, Any]:
        """Generate MANIFEST.json with complete artifact inventory."""
        # Calculate total lines generated
        total_lines = 0
        for pkg_name in results["succeeded"]:
            code_filename = self._primary_artifact_filename(pkg_name, target_tech)
            code_key = f"{self.output_path.rstrip('/')}/{code_filename}"
            try:
                code_content = self.storage.read_file(code_key)
                if code_content:
                    total_lines += len(code_content.split('\n'))
            except:
                pass
        
        manifest = {
            "project_id": self.project_uuid,
            "project_name": self.project_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "migration_summary": {
                "total_packages": len(results["succeeded"]) + len(results["failed"]),
                "succeeded": len(results["succeeded"]),
                "failed": len(results["failed"]),
                "total_lines_generated": total_lines
            },
            "artifacts": {
                "code_files": [
                    {"name": f"{pkg.replace('.dtsx', '')}.py", "type": "pyspark", "package": pkg}
                    for pkg in results["succeeded"]
                ],
                "audit_files": [
                    {"name": f"{pkg.replace('.dtsx', '')}_audit.json", "type": "compliance", "package": pkg}
                    for pkg in results["succeeded"]
                ],
                "governance": [
                    {"name": "governance_runbook.md", "type": "documentation"},
                    {"name": "certification_audit.json", "type": "compliance"}
                ]
            },
            "failed_packages": results["failed"],
            "deployment_info": {
                "target_platform": target_tech,
                "recommended_runtime": self._get_recommended_runtime(target_tech),
                "deployment_guide": "See governance_runbook.md for detailed deployment instructions"
            },
            "topology": {
                "total_nodes": len(mesh.get("nodes", [])),
                "total_edges": len(mesh.get("edges", [])),
                "execution_phases": mesh.get("phases", [])
            }
        }
        
        return manifest
    
    def _get_recommended_runtime(self, target_tech: str) -> str:
        """Get recommended runtime for target platform."""
        runtimes = {
            "pyspark": "Databricks Runtime 13.3 LTS or Apache Spark 3.4+",
            "snowflake": "Snowflake Snowpark Python 1.0+",
            "bigquery": "BigQuery Standard SQL + Python 3.9+",
            "synapse": "Azure Synapse Spark 3.3+"
        }
        return runtimes.get(target_tech.lower(), "See documentation for runtime requirements")
