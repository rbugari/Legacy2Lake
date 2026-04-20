"""
Quick Assessment Service
Provides fast, hybrid (deterministic + LLM) evaluation of project viability
before running full Triage pipeline.

Phase A - Sprint 14
"""
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
    from apps.api.services.discovery_service import DiscoveryService
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence, PersistenceService
        from services.discovery_service import DiscoveryService
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence, PersistenceService
        from .discovery_service import DiscoveryService


# ============================================
# Pydantic Models
# ============================================

class FileClassification(BaseModel):
    """Classification details for a single file."""
    filename: str
    category: str  # MIGRATABLE, SUPPORT, DOCUMENTATION, UNRECOGNIZED
    detected_tech: Optional[str] = None  # SSIS, DataStage, Pentaho, SQL, etc.
    complexity_hint: str  # LOW, MEDIUM, HIGH
    size_bytes: int
    line_count: int


class QuickAssessmentResult(BaseModel):
    """Result of quick assessment evaluation."""
    score: int = Field(..., ge=0, le=100, description="Viability score 0-100")
    semaforo: str = Field(..., description="Traffic light: green, yellow, red")
    file_breakdown: Dict[str, int] = Field(..., description="Count by category")
    detected_techs: List[str] = Field(default_factory=list, description="Technologies detected")
    blockers: List[str] = Field(default_factory=list, description="Blocking issues if red")
    file_details: List[FileClassification] = Field(default_factory=list)
    total_files: int
    total_lines: int
    llm_opinion: Optional[str] = Field(None, description="Optional LLM-generated opinion")
    assessed_at: str


# ============================================
# Service
# ============================================

class QuickAssessmentService:
    """
    Quick Assessment Service - Phase A
    
    Hybrid evaluation:
    - Deterministic: file classification, scoring, blocker detection (3-5 sec)
    - LLM opinion: optional professional assessment via agent-qa (2-3 sec)
    
    Replaces expensive Agent S call in Discovery stage.
    """
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    
    async def assess(self, project_id: str) -> QuickAssessmentResult:
        """
        Performs hybrid quick assessment on project.
        
        Steps:
        1. Reuse DiscoveryService.generate_manifest() for file inventory
        2. Classify each file into 4 categories
        3. Calculate viability score and semaphore
        4. Detect technologies present
        5. Identify blockers if score < 30
        6. Generate compact summary for LLM
        7. Get optional LLM opinion via agent-qa
        8. Return comprehensive result
        
        Args:
            project_id: Project UUID
            
        Returns:
            QuickAssessmentResult with score, semaphore, breakdown, and opinion
        """
        logger.info(
            f"[QuickAssessment] Starting assessment: project_id={project_id}, tenant_id={self.tenant_id}",
            "QuickAssessment"
        )
        
        # 1. Resolve project UUID to name (R2 folders use project names, not UUIDs)
        project_name = project_id
        project_meta: Dict[str, Any] = {}
        if "-" in project_id:  # UUID format
            project_meta = await self.db.get_project_metadata(project_id) or {}
            if project_meta:
                project_name = project_meta["name"]
                logger.info(
                    f"[QuickAssessment] Resolved UUID to project name: {project_name}",
                    "QuickAssessment"
                )

        project_settings = await self.db.get_project_settings(project_id) or {}
        source_hint = (
            project_settings.get("source_tech")
            or project_meta.get("source_tech")
            or project_meta.get("settings", {}).get("source_tech")
            or project_meta.get("config", {}).get("source_tech")
            or ""
        )
        
        # 2. Reuse generate_manifest() for deterministic file analysis
        manifest = DiscoveryService.generate_manifest(
            project_name,  # Use resolved name, not UUID
            tenant_id=self.tenant_id,
            source_folder=PersistenceService.STAGE_SOURCE,
            project_settings=project_settings
        )
        
        file_inventory = manifest.get("file_inventory", [])
        if not file_inventory:
            raise ValueError("No files found in project (Source or Triage folder)")
        
        # 2. Classify each file into 4 categories
        breakdown = {
            "migratable": 0,
            "support": 0,
            "documentation": 0,
            "unrecognized": 0
        }
        file_details = []
        detected_techs = set()
        detected_tech_counts: Dict[str, int] = {}
        total_lines = 0
        
        for item in file_inventory:
            category, tech = self._classify_file(item, source_hint=source_hint)
            breakdown[category] += 1
            if tech:
                detected_techs.add(tech)
                detected_tech_counts[tech] = detected_tech_counts.get(tech, 0) + 1
            
            file_details.append(FileClassification(
                filename=item["name"],
                category=category.upper(),
                detected_tech=tech,
                complexity_hint=self._estimate_complexity(item),
                size_bytes=item.get("size", 0),
                line_count=item.get("lines", 0)
            ))
            total_lines += item.get("lines", 0)
        
        # 3. Calculate score and semaphore
        total_files = len(file_inventory)
        score = self._calculate_score(breakdown, total_files)
        semaforo = self._get_semaforo(score)
        
        # 4. Identify blockers if score < 30
        blockers = self._identify_blockers(breakdown, total_files) if score < 30 else []
        
        # 5. Generate compact summary for LLM
        summary = self._build_summary(breakdown, detected_techs, total_files, total_lines)
        
        # 6. Get optional LLM opinion (if agent-qa is configured)
        llm_opinion = None
        try:
            llm_opinion = await self._get_llm_opinion(summary, project_id)
        except Exception as e:
            logger.warning(
                f"[QuickAssessment] Could not obtain LLM opinion: {e}",
                "QuickAssessment"
            )
        
        # Order detected technologies by frequency first (desc), then name.
        # This prevents support techs (e.g., SQL) from outranking dominant ETL techs (e.g., SSIS)
        # just because of alphabetical sorting.
        ordered_detected_techs = sorted(
            list(detected_techs),
            key=lambda tech_name: (-detected_tech_counts.get(tech_name, 0), tech_name)
        )

        result = QuickAssessmentResult(
            score=score,
            semaforo=semaforo,
            file_breakdown=breakdown,
            detected_techs=ordered_detected_techs,
            blockers=blockers,
            file_details=file_details,
            total_files=total_files,
            total_lines=total_lines,
            llm_opinion=llm_opinion,
            assessed_at=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"[QuickAssessment] Completed: score={score}, semaforo={semaforo}, files={total_files}",
            "QuickAssessment"
        )
        
        return result
    
    def _classify_file(self, item: Dict[str, Any], source_hint: str = "") -> Tuple[str, Optional[str]]:
        """
        Classifies a file into one of 4 categories.
        
        Categories:
        - migratable: ETL packages (SSIS, DataStage, Pentaho, Informatica)
        - support: Support files (SQL, CSV, schemas)
        - documentation: Documentation (MD, TXT, PDF)
        - unrecognized: Unrecognized files
        
        Returns:
            Tuple of (category, detected_tech)
        """
        filename = item["name"].lower()
        ext = filename.split('.')[-1] if '.' in filename else ''

        # SSIS project scaffolding is valuable migration context even if it is not
        # directly executable ETL logic.
        if (
            filename.endswith(".dtproj.user")
            or ext in ["dtproj", "params", "conmgr", "sln", "database"]
        ):
            return ("support", "SSIS")
        
        # MIGRATABLE - ETL packages
        if ext in ['dtsx', 'dsx', 'kjb', 'ktr', 'pmx']:
            tech = None
            if ext == 'dtsx':
                tech = 'SSIS'
            elif ext == 'dsx':
                tech = 'DataStage'
            elif ext in ['kjb', 'ktr']:
                tech = 'Pentaho'
            elif ext == 'pmx':
                tech = 'Informatica'
            return ("migratable", tech)
        
        # Informatica XML (requires signature detection)
        if ext == 'xml' and 'informatica' in item.get('signatures', []):
            return ("migratable", "Informatica")
        
        # SUPPORT - Support files
        if ext in ['sql', 'csv', 'xlsx', 'xls', 'json', 'yaml', 'yml']:
            tech = None
            if ext == 'sql':
                tech = self._resolve_sql_tech_from_source_hint(source_hint)
            elif ext in ['xlsx', 'xls']:
                tech = 'Excel'
            return ("support", tech)
        
        # DOCUMENTATION - Documentation
        if ext in ['md', 'txt', 'pdf', 'docx', 'doc', 'rtf']:
            return ("documentation", None)
        
        # UNRECOGNIZED - Unrecognized
        return ("unrecognized", None)

    def _resolve_sql_tech_from_source_hint(self, source_hint: str) -> str:
        """Return a concrete SQL tech label when project settings already define the SQL family."""
        hint = (source_hint or "").upper()
        if "MYSQL" in hint or "MARIADB" in hint:
            return "MySQL"
        if "ORACLE" in hint:
            return "Oracle"
        if "SQLSERVER" in hint or "SQL SERVER" in hint or "TSQL" in hint or "T-SQL" in hint:
            return "SQL Server"
        return "SQL"
    
    def _estimate_complexity(self, item: Dict[str, Any]) -> str:
        """
        Estimates complexity based on lines or file size.
        
        Returns:
            "LOW" | "MEDIUM" | "HIGH"
        """
        filename = item.get("name", "").lower()
        if filename.endswith((".xls", ".xlsx")):
            return "LOW"

        lines = item.get("lines", 0)
        if lines == 0:
            return "LOW"
        elif lines < 200:
            return "LOW"
        elif lines < 500:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_score(self, breakdown: Dict[str, int], total: int) -> int:
        """
        Calculates viability score based on weighted file categories.
        
        Formula: (migratable*4 + support*2 + documentation*1 + unrecognized*0) / (total*4) * 100
        
        Returns:
            Score from 0 to 100
        """
        if total == 0:
            return 0
        
        weighted_sum = (
            breakdown["migratable"] * 4 +
            breakdown["support"] * 2 +
            breakdown["documentation"] * 1 +
            breakdown["unrecognized"] * 0
        )
        
        max_possible = total * 4
        score = int((weighted_sum / max_possible) * 100)
        return min(max(score, 0), 100)
    
    def _get_semaforo(self, score: int) -> str:
        """
        Maps score to traffic light semaphore.
        
        Returns:
            "green" (≥60) | "yellow" (30-59) | "red" (<30)
        """
        if score >= 60:
            return "green"
        elif score >= 30:
            return "yellow"
        else:
            return "red"
    
    def _identify_blockers(self, breakdown: Dict[str, int], total: int) -> List[str]:
        """
        Identifies blocking issues when score is red (<30).
        
        Returns:
            List of blocker descriptions
        """
        blockers = []
        
        # No migratable files detected
        if breakdown["migratable"] == 0:
            blockers.append("No migratable files detected (SSIS, DataStage, Pentaho, Informatica)")
        
        # Too many unrecognized files
        no_rec_pct = (breakdown["unrecognized"] / total * 100) if total > 0 else 0
        if no_rec_pct > 70:
            blockers.append(f"{no_rec_pct:.0f}% of files are unrecognized")
        
        # Missing support files
        if breakdown["support"] == 0 and breakdown["migratable"] > 0:
            blockers.append("Missing support files (DDL, schemas, reference data)")
        
        return blockers
    
    def _build_summary(
        self,
        breakdown: Dict,
        techs: set,
        total: int,
        lines: int
    ) -> str:
        """
        Builds compact summary for LLM consumption.
        
        Returns:
            Formatted summary string
        """
        tech_list = ", ".join(techs) if techs else "None detected"
        return f"""Migration project analysis. Files uploaded: {total} ({lines:,} lines)
- {breakdown['migratable']} migratable packages
- {breakdown['support']} support files
- {breakdown['documentation']} documentation
- {breakdown['unrecognized']} unrecognized
Technologies detected: {tech_list}
Is this migration viable? What are the main risks? Respond in 3-4 lines."""
    
    async def _get_llm_opinion(self, summary: str, project_id: str) -> Optional[str]:
        """
        Gets LLM opinion via Agent Matrix (agent-qa or fallback to agent-helper).
        
        Args:
            summary: Compact project summary
            project_id: Project UUID for context
            
        Returns:
            LLM-generated professional opinion (3-4 lines) or None if unavailable
        """
        try:
            # Resolve model from Agent Matrix (agent-qa or fallback)
            config = await self.db.resolve_agent_model("agent-qa")
            
            # Validate config exists
            if not config or not isinstance(config, dict):
                return None
            
            if config["provider"] == "azure":
                from langchain_openai import AzureChatOpenAI
                llm = AzureChatOpenAI(
                    azure_deployment=config["deployment"],  # key is 'deployment', not 'deployment_name'
                    api_key=config["api_key"],
                    azure_endpoint=config["endpoint"],
                    openai_api_version=config.get("api_version", "2024-05-01-preview"),
                    temperature=0.3
                )
            else:  # openrouter, openai, groq, etc.
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=config["deployment"],  # key is 'deployment', not 'model'
                    api_key=config["api_key"],
                    base_url=config.get("endpoint"),
                    temperature=0.3
                )
            
            from langchain_core.messages import SystemMessage, HumanMessage
            
            prompt_content = await self.db.get_prompt("agent_qa_assessment")
            if not prompt_content:
                prompt_content = "You are an expert in ETL migration viability analysis."
                
            messages = [
                SystemMessage(content=prompt_content),
                HumanMessage(content=summary)
            ]
            
            response = await llm.ainvoke(messages)
            return response.content.strip()
        
        except Exception as e:
            logger.warning(
                f"[QuickAssessment] Error obtaining LLM opinion: {e}",
                "QuickAssessment"
            )
            return None
