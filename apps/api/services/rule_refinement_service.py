"""
Rule Refinement Service - Evaluates and ranks rule candidates for reusability
and validates their applicability across project scope.

Provides:
- Rule scoring by reusability, complexity, and confidence
- Local vs Global classification  
- Materialized rule recommendations
- Rule evidence tracking
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import hashlib

try:
    from apps.api.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RuleRefinementService:
    """Evaluates and ranks rule candidates for downstream reuse."""

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    def score_rule_candidates(
        self,
        rule_candidates: List[Dict[str, Any]],
        operational_context: Dict[str, Any],
        project_scope: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Score and rank rule candidates by reusability and applicability.

        Scoring factors:
        - Reusability (does this apply outside single asset?)
        - Complexity (simple > complex for adoption)
        - Confidence (how certain are we)
        - Evidence count (backing)
        - Specificity (general > specific for reuse)

        Args:
            rule_candidates: List of rule candidates from understanding
            operational_context: Operational maps and orchestration
            project_scope: Scope and constraints of project

        Returns:
            List of scored and ranked rule candidates
        """
        scored = []

        for candidate in rule_candidates or []:
            score_data = {
                **candidate,
                "reusability_score": self._calculate_reusability(
                    candidate, operational_context, project_scope
                ),
                "complexity_score": self._calculate_complexity(candidate),
                "confidence_score": candidate.get("confidence", 0.5),
                "evidence_count": len(candidate.get("evidence", [])),
                "applicability": self._classify_applicability(
                    candidate, project_scope
                ),
                "recommendation": self._materialize_recommendation(candidate),
            }

            # Composite score: reusability * (1 - complexity) * confidence
            score_data["composite_score"] = (
                score_data["reusability_score"]
                * (1 - score_data["complexity_score"])
                * score_data["confidence_score"]
            )

            scored.append(score_data)

        # Sort by composite score descending
        scored.sort(key=lambda r: r["composite_score"], reverse=True)

        return scored

    def _calculate_reusability(
        self,
        candidate: Dict[str, Any],
        operational_context: Dict[str, Any],
        project_scope: Dict[str, Any],
    ) -> float:
        """Score how reusable this rule is across assets/processes."""
        score = 0.3  # Base

        # Applies to multiple assets
        if len(candidate.get("assets_affected", [])) > 1:
            score += 0.3

        # General pattern vs specific value
        if candidate.get("pattern_type") in ["regex", "structural", "semantic"]:
            score += 0.2

        # Cross-process applicability
        if len(candidate.get("processes_affected", [])) > 1:
            score += 0.2

        # Precedent in project history
        if candidate.get("historical_precedent"):
            score += 0.1

        return min(score, 1.0)

    def _calculate_complexity(self, candidate: Dict[str, Any]) -> float:
        """Score complexity of implementing this rule (lower is better)."""
        score = 0.0

        # Implementation language
        impl_lang = candidate.get("preferred_impl", "").lower()
        if impl_lang in ["sql", "pyspark"]:
            score += 0.2
        elif impl_lang in ["python", "javascript"]:
            score += 0.15
        else:
            score += 0.3

        # Dependency count
        deps = len(candidate.get("dependencies", []))
        score += min(deps * 0.1, 0.3)

        # Rule type
        rule_type = candidate.get("type", "").lower()
        if rule_type == "simple":
            score += 0.0
        elif rule_type == "conditional":
            score += 0.15
        elif rule_type == "recursive":
            score += 0.35

        return min(score, 1.0)

    def _classify_applicability(
        self, candidate: Dict[str, Any], project_scope: Dict[str, Any]
    ) -> str:
        """Classify rule as LOCAL or GLOBAL."""
        # GLOBAL if applies across multiple scopes
        if len(candidate.get("assets_affected", [])) > 1:
            if len(candidate.get("processes_affected", [])) > 1:
                return "GLOBAL"

        return "LOCAL"

    def _materialize_recommendation(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Convert scored candidate into concrete recommendation."""
        impl_type = candidate.get("preferred_impl", "sql").lower()

        return {
            "action": f"Implement {candidate.get('type', 'rule')} in {impl_type}",
            "priority": self._priority_from_score(candidate.get("composite_score", 0.5)),
            "effort_estimate": self._effort_estimate(candidate),
            "blockers": candidate.get("blockers", []),
            "evidence_summary": self._summarize_evidence(candidate.get("evidence", [])),
        }

    def _priority_from_score(self, score: float) -> str:
        """Map score to priority level."""
        if score >= 0.8:
            return "CRITICAL"
        elif score >= 0.6:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def _effort_estimate(self, candidate: Dict[str, Any]) -> str:
        """Estimate effort in t-shirt sizing."""
        deps = len(candidate.get("dependencies", []))

        if candidate.get("type") == "simple" and deps <= 2:
            return "XS"
        elif candidate.get("type") == "conditional" and deps <= 3:
            return "S"
        elif candidate.get("type") == "recursive" or deps > 5:
            return "L"
        else:
            return "M"

    def _summarize_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """Extract key evidence statement."""
        if not evidence:
            return "No evidence"

        key = evidence[0]
        return f"{key.get('type', 'observation')}: {key.get('description', 'N/A')}"

    def create_knowledge_package_snapshot(
        self,
        project_id: str,
        understanding: Dict[str, Any],
        refined_rules: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a versionable, reusable knowledge package snapshot.

        Package includes:
        - All understanding artifacts
        - Refined rules
        - Project metadata and scope
        - Generated timestamp and version
        - Content hash for change detection

        Args:
            project_id: Project identifier
            understanding: Complete understanding output
            refined_rules: Scored and ranked rules
            metadata: Additional project metadata

        Returns:
            Knowledge package snapshot structure
        """
        # Safe metadata merge
        meta_dict = metadata or {}
        
        package = {
            "metadata": {
                "project_id": project_id,
                "package_version": "v1",
                "created_at": datetime.utcnow().isoformat(),
                "snapshot_id": self._generate_snapshot_id(project_id),
                **meta_dict,
            },
            "understanding": understanding,
            "refined_rules": refined_rules[:20],  # Top 20 rules
            "package_hash": self._compute_package_hash(understanding, refined_rules),
        }

        logger.info(
            f"Created knowledge package snapshot for {project_id}: "
            f"{package['metadata']['snapshot_id']}"
        )

        return package

    def _generate_snapshot_id(self, project_id: str) -> str:
        """Generate unique snapshot ID."""
        ts = datetime.utcnow().timestamp()
        base = f"{project_id}:{ts}"
        return hashlib.md5(base.encode()).hexdigest()[:12]

    def _compute_package_hash(
        self, understanding: Dict[str, Any], refined_rules: List[Dict[str, Any]]
    ) -> str:
        """Compute hash for package content."""
        # Include rule scores to detect actual content changes
        rules_summary = [
            {
                "id": r.get("id"),
                "composite_score": round(r.get("composite_score", 0), 3),
                "type": r.get("type"),
            }
            for r in refined_rules[:5]
        ]

        content = json.dumps(
            {
                "understanding_keys": sorted(understanding.keys()),
                "rules_count": len(refined_rules),
                "rules_summary": rules_summary,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]
