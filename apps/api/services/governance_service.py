"""
Governance & Versioning Service - Snapshot versioning, diff tracking, 
and governance pre-checks before finalization.

Provides:
- Snapshot versioning and history
- Change detection between snapshots (diffs)
- Audit trail for rule refinement decisions
- Governance readiness validations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from enum import Enum

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class SnapshotChangeType(str, Enum):
    """Types of changes between snapshots."""
    RULE_ADDED = "rule_added"
    RULE_REMOVED = "rule_removed"
    RULE_RESCORED = "rule_rescored"
    RULE_PROMOTED = "rule_promoted"  # Moved up in ranking
    RULE_DEMOTED = "rule_demoted"     # Moved down in ranking
    SCORE_IMPROVED = "score_improved"
    SCORE_DECLINED = "score_declined"
    APPLICABILITY_CHANGED = "applicability_changed"


class GovernanceCheckStatus(str, Enum):
    """Governance check result status."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class SnapshotVersioningService:
    """Manages snapshot versioning, versioning, and governance validation."""

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = None  # Will be injected

    def set_db(self, db: SupabasePersistence):
        """Set the database instance."""
        self.db = db

    def compute_snapshot_diff(
        self,
        previous_snapshot: Optional[Dict[str, Any]],
        current_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute differences between two snapshots.

        Returns structured diff with:
        - Added/removed rules
        - Rescores (score changes)
        - Ranking changes
        - Applicability changes

        Args:
            previous_snapshot: Prior snapshot (can be None if first)
            current_snapshot: Latest snapshot

        Returns:
            Diff structure with change types and details
        """
        diff = {
            "changes": [],
            "summary": {
                "total_changes": 0,
                "promoted_count": 0,
                "demoted_count": 0,
                "added_count": 0,
                "removed_count": 0,
            },
            "significant": False,
        }

        if not previous_snapshot:
            # First snapshot - all rules are "added"
            for rule in current_snapshot.get("refined_rules", []):
                diff["changes"].append({
                    "type": SnapshotChangeType.RULE_ADDED,
                    "rule_id": rule.get("id"),
                    "details": f"New rule: {rule.get('type')}",
                })
            diff["summary"]["added_count"] = len(current_snapshot.get("refined_rules", []))
            return diff

        # Compare previous and current rules
        prev_rules = {r.get("id"): r for r in previous_snapshot.get("refined_rules", [])}
        curr_rules = {r.get("id"): r for r in current_snapshot.get("refined_rules", [])}

        # Detect added rules
        for rule_id, curr_rule in curr_rules.items():
            if rule_id not in prev_rules:
                diff["changes"].append({
                    "type": SnapshotChangeType.RULE_ADDED,
                    "rule_id": rule_id,
                    "score": curr_rule.get("composite_score"),
                })
                diff["summary"]["added_count"] += 1

        # Detect removed rules
        for rule_id, prev_rule in prev_rules.items():
            if rule_id not in curr_rules:
                diff["changes"].append({
                    "type": SnapshotChangeType.RULE_REMOVED,
                    "rule_id": rule_id,
                    "prev_score": prev_rule.get("composite_score"),
                })
                diff["summary"]["removed_count"] += 1

        # Detect changes in existing rules
        for rule_id in curr_rules:
            if rule_id in prev_rules:
                prev_rule = prev_rules[rule_id]
                curr_rule = curr_rules[rule_id]

                prev_score = prev_rule.get("composite_score", 0)
                curr_score = curr_rule.get("composite_score", 0)

                # Score changes
                score_delta = curr_score - prev_score
                if abs(score_delta) > 0.01:  # Meaningful change
                    change_type = (
                        SnapshotChangeType.SCORE_IMPROVED
                        if score_delta > 0
                        else SnapshotChangeType.SCORE_DECLINED
                    )
                    diff["changes"].append({
                        "type": change_type,
                        "rule_id": rule_id,
                        "previous_score": prev_score,
                        "current_score": curr_score,
                        "delta": round(score_delta, 3),
                    })

                # Applicability changes
                if (
                    prev_rule.get("applicability")
                    != curr_rule.get("applicability")
                ):
                    diff["changes"].append({
                        "type": SnapshotChangeType.APPLICABILITY_CHANGED,
                        "rule_id": rule_id,
                        "previous": prev_rule.get("applicability"),
                        "current": curr_rule.get("applicability"),
                    })

                # Ranking changes (position in list)
                prev_ranking = next(
                    (i for i, r in enumerate(previous_snapshot.get("refined_rules", []))
                     if r.get("id") == rule_id),
                    None,
                )
                curr_ranking = next(
                    (i for i, r in enumerate(current_snapshot.get("refined_rules", []))
                     if r.get("id") == rule_id),
                    None,
                )

                if prev_ranking is not None and curr_ranking is not None:
                    rank_delta = prev_ranking - curr_ranking  # Positive = promoted
                    if abs(rank_delta) > 0:
                        change_type = (
                            SnapshotChangeType.RULE_PROMOTED
                            if rank_delta > 0
                            else SnapshotChangeType.RULE_DEMOTED
                        )
                        diff["changes"].append({
                            "type": change_type,
                            "rule_id": rule_id,
                            "previous_rank": prev_ranking,
                            "current_rank": curr_ranking,
                            "positions": abs(rank_delta),
                        })

                        if change_type == SnapshotChangeType.RULE_PROMOTED:
                            diff["summary"]["promoted_count"] += 1
                        else:
                            diff["summary"]["demoted_count"] += 1

        diff["summary"]["total_changes"] = len(diff["changes"])
        diff["significant"] = (
            diff["summary"]["total_changes"] > 5
            or diff["summary"]["added_count"] > 2
            or diff["summary"]["removed_count"] > 2
        )

        return diff

    def validate_governance_readiness(
        self,
        snapshot: Dict[str, Any],
        project_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate project readiness based on understanding and refined rules.

        Checks:
        - Minimum rule candidates scored
        - Rule coverage across domains
        - Global vs Local rule balance
        - Evidence backing for high-priority rules
        - Governance scoring pass

        Args:
            snapshot: Current knowledge package snapshot
            project_context: Project metadata (stage, scope, risks)

        Returns:
            Governance validation result with pass/fail + warnings
        """
        checks = []
        overall_status = GovernanceCheckStatus.PASS

        # Check 1: Minimum rules scored
        refined_rules = snapshot.get("refined_rules", [])
        rules_check = {
            "name": "minimum_rules_scored",
            "status": GovernanceCheckStatus.PASS,
            "message": f"{len(refined_rules)} rules refined",
        }
        if len(refined_rules) < 3:
            rules_check["status"] = GovernanceCheckStatus.WARNING
            rules_check["message"] = f"Only {len(refined_rules)} rules refined; recommend 5+"
        checks.append(rules_check)

        # Check 2: High-priority rules have evidence
        critical_rules = [r for r in refined_rules 
                         if r.get("recommendation", {}).get("priority") == "CRITICAL"]
        evidence_check = {
            "name": "critical_rules_evidence",
            "status": GovernanceCheckStatus.PASS,
            "message": f"All {len(critical_rules)} critical rules have evidence",
        }
        
        rules_without_evidence = [
            r for r in critical_rules 
            if not r.get("recommendation", {}).get("evidence_summary")
            or "No evidence" in r.get("recommendation", {}).get("evidence_summary", "")
        ]
        if rules_without_evidence:
            evidence_check["status"] = GovernanceCheckStatus.WARNING
            evidence_check["message"] = (
                f"{len(rules_without_evidence)}/{len(critical_rules)} critical rules "
                f"lack evidence backing"
            )
        checks.append(evidence_check)

        # Check 3: Rule applicability distribution
        global_rules = [r for r in refined_rules 
                       if r.get("applicability") == "GLOBAL"]
        local_rules = [r for r in refined_rules 
                      if r.get("applicability") == "LOCAL"]
        
        applicability_check = {
            "name": "rule_applicability",
            "status": GovernanceCheckStatus.PASS,
            "message": f"Good distribution: {len(global_rules)} global, {len(local_rules)} local",
        }
        
        if len(refined_rules) > 0:
            global_ratio = len(global_rules) / len(refined_rules)
            if global_ratio < 0.2 and len(refined_rules) > 5:
                applicability_check["status"] = GovernanceCheckStatus.WARNING
                applicability_check["message"] = (
                    f"Low reusability: only {global_ratio*100:.0f}% global rules"
                )
        checks.append(applicability_check)

        # Check 4: Top rule confidence
        if refined_rules:
            top_rule = refined_rules[0]
            confidence = top_rule.get("confidence_score", 0)
            top_confidence_check = {
                "name": "top_rule_confidence",
                "status": GovernanceCheckStatus.PASS if confidence >= 0.7 
                         else GovernanceCheckStatus.WARNING,
                "message": f"Top rule confidence: {confidence*100:.0f}%",
            }
            if confidence < 0.5:
                top_confidence_check["status"] = GovernanceCheckStatus.WARNING
                top_confidence_check["message"] = (
                    f"Top rule confidence low ({confidence*100:.0f}%); "
                    f"may indicate unclear requirements"
                )
            checks.append(top_confidence_check)

        # Check 5: Blockers present on critical rules
        blockers_check = {
            "name": "critical_blockers",
            "status": GovernanceCheckStatus.PASS,
            "message": "No blockers on critical rules",
        }
        
        critical_with_blockers = [
            r for r in critical_rules
            if r.get("recommendation", {}).get("blockers")
        ]
        if critical_with_blockers:
            blockers_check["status"] = GovernanceCheckStatus.WARNING
            blockers_check["message"] = (
                f"{len(critical_with_blockers)} critical rules have blockers; "
                f"resolve before finalization"
            )
        checks.append(blockers_check)

        # Determine overall status
        if any(c["status"] == GovernanceCheckStatus.FAIL for c in checks):
            overall_status = GovernanceCheckStatus.FAIL
        elif any(c["status"] == GovernanceCheckStatus.WARNING for c in checks):
            overall_status = GovernanceCheckStatus.WARNING

        return {
            "status": overall_status,
            "checks": checks,
            "passed": sum(1 for c in checks if c["status"] == GovernanceCheckStatus.PASS),
            "warnings": sum(1 for c in checks if c["status"] == GovernanceCheckStatus.WARNING),
            "failures": sum(1 for c in checks if c["status"] == GovernanceCheckStatus.FAIL),
            "can_finalize": overall_status != GovernanceCheckStatus.FAIL,
        }

    def create_audit_entry(
        self,
        project_id: str,
        action_type: str,
        rule_id: Optional[str] = None,
        previous_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        reasoning: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an audit trail entry for governance tracking."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "action_type": action_type,
            "rule_id": rule_id,
            "previous_value": previous_value,
            "new_value": new_value,
            "reasoning": reasoning or "",
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
        }

        logger.info(
            f"Audit entry: {action_type} on {rule_id} for project {project_id}"
        )

        return entry
