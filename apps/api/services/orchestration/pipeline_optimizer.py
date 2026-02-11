"""
Pipeline Optimizer - Sprint 2 Enhancement
Optimizes Agent C → F pipeline with intelligent validation and flow control
"""
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

try:
    from apps.api.services.agent_c_service import AgentCService
    from apps.api.services.agent_f_service import AgentFService
    from apps.api.services.orchestration.retry_manager import retry_manager
    from apps.api.services.orchestration.context_manager import SharedContext
    from apps.api.utils.logger import logger
except ImportError:
    from services.agent_c_service import AgentCService
    from services.agent_f_service import AgentFService
    from services.orchestration.retry_manager import retry_manager
    from services.orchestration.context_manager import SharedContext
    from utils.logger import logger


class ValidationResult:
    """Result of code validation"""
    
    def __init__(self, valid: bool, issues: List[str] = None, warnings: List[str] = None):
        self.valid = valid
        self.issues = issues or []
        self.warnings = warnings or []
    
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues"""
        return len(self.issues) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "valid": self.valid,
            "issues": self.issues,
            "warnings": self.warnings
        }


class PipelineOptimizer:
    """
    Optimizes the Agent C → F pipeline with:
    - Pre-validation before Agent F
    - Intelligent retry logic
    - Context enrichment
    - Performance monitoring
    """
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        context_manager: Optional[SharedContext] = None
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.context_manager = context_manager
        
        # Initialize agents
        self.agent_c = AgentCService(tenant_id=tenant_id, client_id=client_id)
        self.agent_f = AgentFService(tenant_id=tenant_id, client_id=client_id)
        
        # Metrics
        self.metrics = {
            "total_packages": 0,
            "agent_c_success": 0,
            "agent_c_failures": 0,
            "agent_f_success": 0,
            "agent_f_failures": 0,
            "validation_skips": 0,
            "total_time": 0.0,
            "avg_c_time": 0.0,
            "avg_f_time": 0.0
        }
    
    async def execute_pipeline(
        self,
        package_name: str,
        task_definition: Dict[str, Any],
        project_uuid: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute full C → F pipeline for a package.
        
        Returns:
            (success: bool, result: Dict)
        """
        start_time = datetime.utcnow()
        self.metrics["total_packages"] += 1
        
        result = {
            "package_name": package_name,
            "success": False,
            "agent_c_result": None,
            "agent_f_result": None,
            "generated_code": None,
            "final_code": None,
            "status": None,
            "score": 0,
            "validation": None,
            "timing": {}
        }
        
        try:
            # Phase 1: Agent C - Code Generation with retry
            logger.info(f"🔧 Agent C: Generating code for {package_name}", "Pipeline")
            c_start = datetime.utcnow()
            
            # Enrich context if context manager available
            if self.context_manager:
                enriched_context = self.context_manager.build_agent_context(package_name)
                task_definition.update(enriched_context.get("package", {}))
            
            # Execute with retry logic
            c_success, c_result, c_error = await retry_manager.execute_with_retry(
                self.agent_c.transpile_task,
                task_definition,
                context_name=f"Agent C - {package_name}"
            )
            
            c_time = (datetime.utcnow() - c_start).total_seconds()
            result["timing"]["agent_c"] = c_time
            
            if not c_success:
                logger.error(f"❌ Agent C failed for {package_name}: {c_error}", "Pipeline")
                self.metrics["agent_c_failures"] += 1
                result["error"] = c_error
                result["phase_failed"] = "agent_c"
                return (False, result)
            
            self.metrics["agent_c_success"] += 1
            result["agent_c_result"] = c_result
            
            # Extract generated code
            generated_code = self._extract_code(c_result)
            if not generated_code:
                logger.error(f"❌ Agent C returned no code for {package_name}", "Pipeline")
                result["error"] = "No code generated"
                result["phase_failed"] = "agent_c"
                return (False, result)
            
            result["generated_code"] = generated_code
            logger.info(
                f"✅ Agent C: Generated {len(generated_code)} chars in {c_time:.2f}s",
                "Pipeline"
            )
            
            # Phase 1.5: Pre-validation (quick checks before Agent F)
            validation = self._pre_validate_code(generated_code, task_definition)
            result["validation"] = validation.to_dict()
            
            if validation.has_critical_issues():
                logger.warning(
                    f"⚠️  Pre-validation found issues in {package_name}: {validation.issues}",
                    "Pipeline"
                )
                self.metrics["validation_skips"] += 1
                # Could retry Agent C here or skip to Agent F for detailed feedback
            
            # Phase 2: Agent F - Code Review with retry
            logger.info(f"🔍 Agent F: Auditing code for {package_name}", "Pipeline")
            f_start = datetime.utcnow()
            
            f_success, f_result, f_error = await retry_manager.execute_with_retry(
                self.agent_f.review_code,
                task_definition,
                generated_code,
                project_id=project_uuid,
                context_name=f"Agent F - {package_name}"
            )
            
            f_time = (datetime.utcnow() - f_start).total_seconds()
            result["timing"]["agent_f"] = f_time
            
            if not f_success:
                logger.error(f"❌ Agent F failed for {package_name}: {f_error}", "Pipeline")
                self.metrics["agent_f_failures"] += 1
                result["error"] = f_error
                result["phase_failed"] = "agent_f"
                # Still consider a partial success since we have generated code
                result["final_code"] = generated_code
                result["status"] = "GENERATED_UNAUDITED"
                return (True, result)  # Partial success
            
            self.metrics["agent_f_success"] += 1
            result["agent_f_result"] = f_result
            
            # Determine final code (optimized or original)
            status = f_result.get("status", "UNKNOWN")
            score = f_result.get("score", 0)
            final_code = generated_code
            
            if status == "IMPROVED" and f_result.get("optimized_code"):
                final_code = f_result["optimized_code"]
                logger.info(
                    f"✨ Agent F: Optimized code for {package_name} (Score: {score})",
                    "Pipeline"
                )
            elif status == "APPROVED":
                logger.info(
                    f"✅ Agent F: Approved code for {package_name} (Score: {score})",
                    "Pipeline"
                )
            else:
                logger.warning(
                    f"⚠️  Agent F: Status {status} for {package_name} (Score: {score})",
                    "Pipeline"
                )
            
            result["final_code"] = final_code
            result["status"] = status
            result["score"] = score
            result["success"] = status in ["APPROVED", "IMPROVED"]
            
            # Total timing
            total_time = (datetime.utcnow() - start_time).total_seconds()
            result["timing"]["total"] = total_time
            self.metrics["total_time"] += total_time
            
            logger.info(
                f"🎉 Pipeline completed for {package_name}: {status} in {total_time:.2f}s",
                "Pipeline"
            )
            
            return (result["success"], result)
        
        except Exception as e:
            logger.error(f"💥 Pipeline exception for {package_name}: {str(e)}", "Pipeline")
            result["error"] = str(e)
            result["phase_failed"] = "exception"
            return (False, result)
    
    def _extract_code(self, agent_c_result: Dict[str, Any]) -> Optional[str]:
        """Extract generated code from Agent C result"""
        possible_keys = [
            "code",
            "pyspark_code",
            "sql_code",
            "dbt_code",
            "snowflake_code",
            "final_code",
            "generated_code"
        ]
        
        for key in possible_keys:
            if key in agent_c_result and agent_c_result[key]:
                return agent_c_result[key]
        
        return None
    
    def _pre_validate_code(
        self,
        code: str,
        task_definition: Dict[str, Any]
    ) -> ValidationResult:
        """
        Pre-validate generated code before sending to Agent F.
        Quick syntactic checks to catch obvious issues.
        """
        issues = []
        warnings = []
        
        # Check 1: Code not empty
        if not code or len(code.strip()) < 10:
            issues.append("Generated code is too short or empty")
        
        # Check 2: Has basic structure (functions, imports, etc.)
        code_lower = code.lower()
        
        tech_id = task_definition.get("tech_id", "pyspark")
        
        if tech_id == "pyspark":
            if "import" not in code_lower and "from" not in code_lower:
                warnings.append("No import statements found")
            
            if "def " not in code_lower and "class " not in code_lower:
                warnings.append("No function or class definitions found")
        
        elif tech_id in ["snowflake", "dbt", "bigquery"]:
            # SQL-based checks
            if not any(kw in code_lower for kw in ["select", "create", "insert"]):
                issues.append("No SQL statements found")
        
        # Check 3: Has L2L trace comments
        if "L2L" not in code and "Legacy2Lake" not in code:
            warnings.append("Missing L2L modernization trace comments")
        
        # Check 4: Reasonable length (not too short, not suspiciously long)
        line_count = len(code.splitlines())
        if line_count < 5:
            issues.append(f"Code too short: only {line_count} lines")
        elif line_count > 1000:
            warnings.append(f"Code very long: {line_count} lines")
        
        # Check 5: No obvious error messages in code
        error_keywords = ["error:", "exception:", "failed:", "could not"]
        for keyword in error_keywords:
            if keyword in code_lower[:200]:  # Check first 200 chars
                issues.append(f"Potential error message in generated code: contains '{keyword}'")
        
        valid = len(issues) == 0
        return ValidationResult(valid=valid, issues=issues, warnings=warnings)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pipeline metrics"""
        total = self.metrics["total_packages"]
        
        if total > 0:
            self.metrics["agent_c_success_rate"] = self.metrics["agent_c_success"] / total
            self.metrics["agent_f_success_rate"] = self.metrics["agent_f_success"] / total
            self.metrics["avg_time_per_package"] = self.metrics["total_time"] / total
        
        return self.metrics.copy()
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        metrics = self.get_metrics()
        return (
            f"Pipeline: {metrics['total_packages']} packages, "
            f"C: {metrics['agent_c_success']}/{metrics['total_packages']}, "
            f"F: {metrics['agent_f_success']}/{metrics['total_packages']}, "
            f"Avg: {metrics.get('avg_time_per_package', 0):.2f}s/pkg"
        )
