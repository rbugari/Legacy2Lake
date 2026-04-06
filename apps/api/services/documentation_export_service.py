"""
Documentation Export Service - Block 4 Downstreams

Generates markdown/HTML documentation artifacts from understanding snapshots.
Produces handover-ready exports including:
- Data lineage narrative
- Process flows with decision points
- Rule extraction and reusability assessment
- Governance and quality findings

Multi-format support (markdown, html, json).
"""

import json
import inspect
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.understanding_service import UnderstandingService


class ExportFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class DocumentationExportService:
    """Generates documentation exports from understanding artifacts."""

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        self.understanding = None

    def _derive_report_context(self, project: Dict[str, Any], understanding: Dict[str, Any]) -> Dict[str, Any]:
        functional_map = understanding.get("functional_map", {}) or {}
        operational_map = understanding.get("operational_map", {}) or {}
        recommendation_set = understanding.get("recommendation_set", {}) or {}
        rule_summary = understanding.get("rule_candidate_summary", {}) or {}

        domains = functional_map.get("domains", []) or []
        legacy_data_assets = functional_map.get("data_assets", []) or []
        components = functional_map.get("components", []) or []
        processes = operational_map.get("processes", []) or []

        capability_assets: List[Dict[str, Any]] = []
        dependencies: List[Dict[str, Any]] = []
        dataset_names = set()
        component_names = set()
        asset_ref_to_name: Dict[str, str] = {}

        for domain in domains:
            capabilities = domain.get("capabilities", []) or []
            for capability in capabilities:
                raw_name = capability.get("name") or "unnamed"
                asset_type = self._infer_asset_type(
                    raw_name,
                    capability.get("source_tech") or capability.get("type"),
                    capability.get("datasets", []),
                    capability.get("reads_from", []),
                )
                normalized_capability = {
                    "name": raw_name,
                    "type": asset_type,
                    "description": capability.get("description") or self._build_capability_description(capability),
                    "columns": capability.get("columns", []),
                    "datasets": capability.get("datasets", []),
                    "reads_from": capability.get("reads_from", []),
                    "domain": domain.get("name", "general"),
                    "confidence": capability.get("confidence"),
                    "uncertainty": capability.get("uncertainty", []),
                    "asset_ref": capability.get("asset_ref"),
                }
                if self._is_documentable_asset(normalized_capability):
                    capability_assets.append(normalized_capability)
                    if normalized_capability.get("asset_ref"):
                        asset_ref_to_name[str(normalized_capability.get("asset_ref"))] = raw_name
                component_names.add(raw_name)
                for dataset in capability.get("datasets", []) or []:
                    dataset_names.add(dataset)
                    dependencies.append({
                        "source": raw_name,
                        "target": dataset,
                        "type": "writes_to",
                    })
                for source_table in capability.get("reads_from", []) or []:
                    dataset_names.add(source_table)
                    dependencies.append({
                        "source": source_table,
                        "target": raw_name,
                        "type": "reads_from",
                    })

        filtered_processes: List[Dict[str, Any]] = []
        for proc in processes:
            proc_name = proc.get("name") or "unnamed"
            proc_asset = {
                "name": proc_name,
                "type": self._infer_asset_type(
                    proc_name,
                    proc.get("source_tech"),
                    proc.get("outputs", []) or [],
                    proc.get("inputs", []) or [],
                ),
                "datasets": proc.get("outputs", []) or [],
                "reads_from": proc.get("inputs", []) or [],
            }
            if self._is_documentable_asset(proc_asset):
                filtered_processes.append(proc)
                component_names.add(proc_name)

        recommendations = recommendation_set.get("recommendations")
        if recommendations is None:
            recommendations = recommendation_set.get("items", []) or []

        rules = rule_summary.get("rules")
        if rules is None:
            rules = rule_summary.get("candidates", []) or []
        filtered_rules = [rule for rule in rules if self._is_meaningful_rule(rule)]

        total_assets = (
            len({asset.get("name") for asset in capability_assets if asset.get("name")})
            or functional_map.get("total_assets")
            or project.get("asset_count")
            or len(legacy_data_assets)
            or len(processes)
            or 0
        )

        documentable_component_names = {
            asset.get("name") for asset in capability_assets if asset.get("name")
        }
        total_components = (
            len(components)
            or len(documentable_component_names)
            or operational_map.get("total_processes")
            or 0
        )

        total_data_assets = len(legacy_data_assets) or len(dataset_names)

        return {
            "status": project.get("status") or project.get("stage") or "UNKNOWN",
            "asset_count": total_assets,
            "domains": domains,
            "components": components,
            "data_assets": legacy_data_assets,
            "capability_assets": capability_assets,
            "dataset_names": sorted(dataset_names),
            "dependencies": functional_map.get("dependencies", []) or dependencies,
            "processes": filtered_processes,
            "recommendations": recommendations,
            "rules": filtered_rules,
            "suppressed_rule_count": max(len(rules) - len(filtered_rules), 0),
            "total_domains": functional_map.get("total_domains") or len(domains),
            "total_components": total_components,
            "total_data_assets": total_data_assets,
            "asset_ref_to_name": asset_ref_to_name,
        }

    def _infer_asset_type(
        self,
        asset_name: str,
        source_tech: Optional[str],
        datasets: List[str],
        reads_from: List[str],
    ) -> str:
        name = (asset_name or "").lower()
        tech = (source_tech or "").lower()
        if name.endswith(".dtsx") or tech == "ssis":
            return "SSIS package"
        if name.endswith(".sql"):
            return "SQL script"
        if name.endswith(".json") and "layout" in name:
            return "Layout artifact"
        if name.endswith(".md") or "readme" in name:
            return "Documentation artifact"
        if datasets and reads_from:
            return "Data pipeline"
        if datasets:
            return "Target dataset loader"
        if reads_from:
            return "Source dataset reader"
        if source_tech:
            return str(source_tech)
        return "Asset"

    def _is_documentable_asset(self, asset: Dict[str, Any]) -> bool:
        name = (asset.get("name") or "").lower()
        asset_type = (asset.get("type") or "").lower()
        return not (
            name == "layout.json"
            or name.endswith(".layout.json")
            or "layout artifact" == asset_type
            or (name.endswith(".json") and not asset.get("datasets") and not asset.get("reads_from"))
        )

    def _is_meaningful_rule(self, rule: Dict[str, Any]) -> bool:
        expression = (
            rule.get("sample_expression")
            or rule.get("extraction_logic")
            or rule.get("description")
            or ""
        ).strip()
        normalized = expression.upper()
        if not expression:
            return False
        # Exclude low-signal tokens and placeholders that do not describe transform logic.
        if normalized in {
            "OUTPUT", "DERIVED", "DIRECT", "NONE", "NULL",
            "SOURCE_DB", "DESTINATION_DB", "UNKNOWN", "N/A",
        }:
            return False
        if (
            rule.get("pattern") == "custom_expression"
            and "(" not in expression
            and ")" not in expression
            and all(ch.isalnum() or ch == "_" for ch in expression)
        ):
            return False
        if len(expression) < 6 and not rule.get("pattern"):
            return False
        return True

    def _build_capability_description(self, capability: Dict[str, Any]) -> str:
        reads = capability.get("reads_from", []) or []
        writes = capability.get("datasets", []) or []
        fragments = []
        if reads:
            fragments.append(f"reads {len(reads)} source table(s)")
        if writes:
            fragments.append(f"writes {len(writes)} target dataset(s)")
        confidence = capability.get("confidence")
        if confidence is not None:
            fragments.append(f"confidence {confidence:.2f}")
        return ", ".join(fragments)

    def _normalize_recommendation_priority(self, recommendation: Dict[str, Any]) -> str:
        severity = recommendation.get("severity")
        if severity:
            return str(severity).upper()

        impact = str(recommendation.get("impact") or "").lower()
        mapping = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
        }
        return mapping.get(impact, "MEDIUM")

    def _normalize_rule_name(self, rule: Dict[str, Any]) -> str:
        if rule.get("pattern"):
            return str(rule.get("pattern")).replace("_", " ").title()
        return (
            rule.get("name")
            or rule.get("id")
            or rule.get("pattern")
            or "unnamed"
        )

    def _normalize_rule_description(self, rule: Dict[str, Any]) -> str:
        if rule.get("pattern") and rule.get("sample_expression"):
            return (
                f"Observed {rule.get('pattern', 'rule').replace('_', ' ')} pattern. "
                f"Sample expression: {rule.get('sample_expression')}"
            )
        return (
            rule.get("description")
            or rule.get("sample_expression")
            or rule.get("extraction_logic")
            or "No rule description available"
        )

    def _normalize_rule_reusability(self, rule: Dict[str, Any]) -> str:
        if rule.get("reusability_score"):
            return str(rule.get("reusability_score"))
        reuse_scope = str(rule.get("reuse_scope") or "").lower()
        if reuse_scope == "project":
            return "HIGH"
        if reuse_scope == "asset":
            return "MEDIUM"
        return "UNKNOWN"

    def _summarize_rule_scope(self, rule: Dict[str, Any]) -> Optional[str]:
        observed = rule.get("observed_in_assets") or []
        count = rule.get("occurrence_count")
        reuse_scope = rule.get("reuse_scope")
        parts = []
        if reuse_scope:
            parts.append(f"scope={reuse_scope}")
        if count:
            parts.append(f"occurrences={count}")
        if observed:
            parts.append(f"assets={len(observed)}")
        return ", ".join(parts) if parts else None

    def _normalize_recommendation_title(self, recommendation: Dict[str, Any]) -> str:
        return (
            recommendation.get("title")
            or recommendation.get("statement")
            or recommendation.get("id")
            or "Untitled"
        )

    def _normalize_recommendation_body(self, recommendation: Dict[str, Any]) -> str:
        return (
            recommendation.get("description")
            or recommendation.get("rationale")
            or "No description"
        )

    def _format_process_summary(self, proc: Dict[str, Any]) -> List[str]:
        lines: List[str] = []
        inputs = proc.get("inputs", []) or []
        outputs = proc.get("outputs", []) or []
        dependencies = proc.get("depends_on_names", []) or []
        fragility = proc.get("fragility_signals", []) or []

        if inputs:
            lines.append(f"Inputs: {', '.join(inputs[:5])}")
        if outputs:
            lines.append(f"Outputs: {', '.join(outputs[:5])}")
        if dependencies:
            lines.append(f"Depends On: {', '.join(dependencies[:5])}")
        if proc.get("trigger") and proc.get("trigger") != "unknown":
            lines.append(f"Trigger: {proc.get('trigger')}")
        if proc.get("schedule_hint") and proc.get("schedule_hint") != "not_configured":
            lines.append(f"Schedule: {proc.get('schedule_hint')}")
        if fragility:
            lines.append(f"Fragility Signals: {', '.join(fragility[:5])}")
        return lines

    def _format_recommendation_details(self, recommendation: Dict[str, Any]) -> List[str]:
        return self._format_recommendation_details_with_context(recommendation, {})

    def _format_recommendation_details_with_context(
        self,
        recommendation: Dict[str, Any],
        report: Dict[str, Any],
    ) -> List[str]:
        details: List[str] = []
        category = recommendation.get("category")
        impact = recommendation.get("impact")
        effort = recommendation.get("effort")
        confidence = recommendation.get("confidence")
        based_on = recommendation.get("based_on") or recommendation.get("dependencies") or []
        uncertainty = recommendation.get("uncertainty") or []

        if category:
            details.append(f"Category: {category}")
        if impact:
            details.append(f"Impact: {impact}")
        if effort:
            details.append(f"Effort: {effort}")
        if confidence is not None:
            details.append(f"Confidence: {float(confidence):.2f}")
        if based_on:
            details.append(
                f"Based On: {', '.join(self._humanize_reference(str(item), report) for item in based_on[:5])}"
            )
        if uncertainty:
            details.append(f"Uncertainty: {', '.join(str(item) for item in uncertainty[:5])}")
        return details

    def _humanize_reference(self, reference: str, report: Dict[str, Any]) -> str:
        if reference.startswith("asset:"):
            name = report.get("asset_ref_to_name", {}).get(reference)
            if name:
                return name
            return reference
        if reference.startswith("impact:"):
            return reference.replace("impact:", "table ", 1)
        return reference

    async def _get_understanding_snapshot(self, project_id: str) -> Dict[str, Any]:
        """
        Resolve understanding snapshot with backward-compatible behavior.

        - Uses injected/mocked self.understanding when present.
        - Falls back to project-scoped UnderstandingService otherwise.
        - Supports both get_snapshot(project_id) and get_snapshot() signatures.
        """
        svc = self.understanding or UnderstandingService(
            project_id=project_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
        )

        getter = getattr(svc, "get_snapshot", None)
        if not callable(getter):
            return {}

        try:
            return await getter(project_id)
        except TypeError:
            return await getter()

    async def _get_project_metadata(self, project_id: str) -> Dict[str, Any]:
        """Resolve project context in a backward-compatible way."""
        getter = getattr(self.db, "get_project_metadata", None)
        if callable(getter):
            maybe = getter(project_id)
            result = await maybe if inspect.isawaitable(maybe) else maybe
            if isinstance(result, dict):
                return result

        legacy_query = getattr(self.db, "execute_query", None)
        if callable(legacy_query):
            maybe = legacy_query(
                """
                SELECT id, name, status, created_at, discovery_findings,
                       triage_findings, governance_findings, asset_count
                FROM utm_projects
                WHERE id = %s AND tenant_id = %s
                """,
                [project_id, self.tenant_id],
            )
            rows = await maybe if inspect.isawaitable(maybe) else maybe
            if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                return rows[0]

        return {}

    async def export_full_documentation(
        self,
        project_id: str,
        format: ExportFormat = ExportFormat.MARKDOWN,
    ) -> Dict[str, Any]:
        """
        Generate complete documentation export from understanding snapshot.

        Returns:
        {
            "format": "markdown|html|json",
            "generated_at": ISO timestamp,
            "project_id": str,
            "content": markdown/html/json string,
            "metadata": {
                "sections": count,
                "lines": count,
                "images": count,
                "tables": count,
                "code_blocks": count,
            },
            "toc": table of contents for markdown
        }
        """
        try:
            # Get understanding snapshot
            understanding = await self._get_understanding_snapshot(project_id)
            if not understanding:
                return {
                    "error": "understanding_not_found",
                    "project_id": project_id,
                    "message": f"No understanding found for project {project_id}",
                }

            # Get project metadata for context
            project = await self._get_project_metadata(project_id)

            # Generate format-specific content
            if format == ExportFormat.MARKDOWN:
                content = self._generate_markdown(project, understanding)
            elif format == ExportFormat.HTML:
                content = self._generate_html(project, understanding)
            else:  # JSON
                content = json.dumps(self._generate_json(project, understanding), indent=2)

            # Build metadata about the export
            metadata = self._calculate_metadata(content, format)

            # Build table of contents for markdown
            toc = self._build_toc(content) if format == ExportFormat.MARKDOWN else None

            return {
                "format": format,
                "generated_at": datetime.utcnow().isoformat(),
                "project_id": project_id,
                "project_name": project.get("name", "Unknown"),
                "project_status": project.get("status", "UNKNOWN"),
                "content": content,
                "metadata": metadata,
                "toc": toc,
            }

        except Exception as e:
            return {
                "error": "export_failed",
                "project_id": project_id,
                "message": str(e),
            }

    def _generate_markdown(self, project: Dict, understanding: Dict) -> str:
        """Generate markdown documentation."""
        lines = []
        report = self._derive_report_context(project, understanding)

        # Title and metadata
        lines.append(f"# Data Warehouse Documentation")
        lines.append(f"**Project:** {project.get('name', 'Unknown')}")
        lines.append(f"**Status:** {report['status']}")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Asset Count:** {report['asset_count']}")
        lines.append("")

        # Table of contents placeholder
        lines.append("## Table of Contents")
        lines.append("1. [Executive Summary](#executive-summary)")
        lines.append("2. [Data Assets](#data-assets)")
        lines.append("3. [Data Flows](#data-flows)")
        lines.append("4. [Process Orchestration](#process-orchestration)")
        lines.append("5. [Extraction Rules](#extraction-rules)")
        lines.append("6. [Recommendations](#recommendations)")
        lines.append("7. [Governance Findings](#governance-findings)")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append(f"Total Domains: {report['total_domains']}")
        lines.append(f"Total Components: {report['total_components']}")
        lines.append(f"Total Data Assets: {report['total_data_assets']}")
        if report["capability_assets"]:
            lines.append(
                f"Documented Assets: {len(report['capability_assets'])} relevant pipeline asset(s) after excluding layout/support noise."
            )
        lines.append("")

        # Data Assets
        lines.append("## Data Assets")
        lines.append("### Sources")
        for asset in report["data_assets"]:
            asset_type = asset.get("type", "unknown")
            asset_name = asset.get("name", "unnamed")
            lines.append(f"- **{asset_name}** ({asset_type})")
            if asset.get("description"):
                lines.append(f"  - {asset.get('description')}")
            if asset.get("columns"):
                col_sample = asset.get("columns", [])[:3]
                col_names = ", ".join([c.get("name", "?") for c in col_sample])
                lines.append(f"  - Columns: {col_names}" + (
                    "..." if len(asset.get("columns", [])) > 3 else ""
                ))
        if not report["data_assets"] and report["capability_assets"]:
            for asset in report["capability_assets"]:
                lines.append(f"- **{asset.get('name', 'unnamed')}** ({asset.get('type', 'asset')})")
                if asset.get("description"):
                    lines.append(f"  - {asset.get('description')}")
                if asset.get("datasets"):
                    lines.append(f"  - Targets: {', '.join(asset.get('datasets', [])[:5])}")
                if asset.get("reads_from"):
                    lines.append(f"  - Sources: {', '.join(asset.get('reads_from', [])[:5])}")
                if asset.get("domain"):
                    lines.append(f"  - Domain: {asset.get('domain')}")
                if asset.get("uncertainty"):
                    lines.append(f"  - Uncertainty: {', '.join(asset.get('uncertainty', [])[:3])}")
        if not report["data_assets"] and not report["capability_assets"]:
            lines.append("No data assets documented yet.")
        lines.append("")

        # Data Flows (Lineage)
        lines.append("## Data Flows")
        functional_deps = report["dependencies"]
        if functional_deps:
            for dep in functional_deps[:10]:
                source = dep.get("source", "?")
                target = dep.get("target", "?")
                lineage_type = dep.get("type", "unknown")
                lines.append(f"- {source} → {target} ({lineage_type})")
            if len(functional_deps) > 10:
                lines.append(f"- ... and {len(functional_deps) - 10} more dependencies")
        else:
            lines.append("No dependencies documented yet.")
        lines.append("")

        # Process Orchestration
        lines.append("## Process Orchestration")
        processes = report["processes"]
        for proc in processes:
            proc_name = proc.get("name", "unnamed")
            lines.append(f"### {proc_name}")
            if proc.get("description"):
                lines.append(f"{proc.get('description')}")
            for summary_line in self._format_process_summary(proc):
                lines.append(summary_line)
            if proc.get("steps"):
                for i, step in enumerate(proc.get("steps", [])[:5], 1):
                    lines.append(f"{i}. {step.get('description', 'Step ' + str(i))}")
            if len(proc.get("steps", [])) > 5:
                lines.append(f"... and {len(proc.get('steps', [])) - 5} more steps")
            lines.append("")
        if not processes:
            lines.append("No process orchestration documented yet.")
            lines.append("")

        # Rules
        lines.append("## Extraction Rules")
        rules = report["rules"]
        for rule in rules[:10]:
            rule_name = self._normalize_rule_name(rule)
            lines.append(f"### {rule_name}")
            lines.append(f"{self._normalize_rule_description(rule)}")
            lines.append(f"**Reusability:** {self._normalize_rule_reusability(rule)}")
            if rule.get("observed_in_assets"):
                lines.append(f"**Observed In:** {', '.join(rule.get('observed_in_assets', [])[:5])}")
            scope_summary = self._summarize_rule_scope(rule)
            if scope_summary:
                lines.append(f"**Coverage:** {scope_summary}")
            lines.append("")
        if not rules:
            lines.append("No extraction rules documented yet.")
        elif report.get("suppressed_rule_count"):
            lines.append(f"Suppressed {report['suppressed_rule_count']} low-signal rule candidate(s) with non-informative expressions.")
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            recs = [
                r for r in report["recommendations"]
                if self._normalize_recommendation_priority(r) == severity
            ]
            if recs:
                lines.append(f"### {severity} Priority")
                for rec in recs[:5]:
                    lines.append(
                        f"- **{self._normalize_recommendation_title(rec)}**: "
                        f"{self._normalize_recommendation_body(rec)}"
                    )
                    for detail in self._format_recommendation_details_with_context(rec, report):
                        lines.append(f"  - {detail}")
                if len(recs) > 5:
                    lines.append(f"... and {len(recs) - 5} more {severity} recommendations")
                lines.append("")
        if not report["recommendations"]:
            lines.append("No recommendations documented yet.")
            lines.append("")

        # Governance
        lines.append("## Governance Findings")
        governance = project.get("governance_findings") or {}
        if isinstance(governance, dict) and governance:
            for key, value in governance.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("Governance checks have not been evaluated yet, or no findings were recorded.")
        lines.append("")

        return "\n".join(lines)

    def _generate_html(self, project: Dict, understanding: Dict) -> str:
        """Generate HTML documentation."""
        markdown_content = self._generate_markdown(project, understanding)
        
        # Simple markdown to HTML conversion (lightweight)
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            f"<title>{project.get('name', 'Documentation')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }",
            "h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }",
            "h2 { color: #34495e; margin-top: 30px; }",
            "h3 { color: #7f8c8d; }",
            "code { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #3498db; color: white; }",
            "ul { margin: 10px 0; }",
            "li { margin: 5px 0; }",
            ".metadata { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Simple conversion
        for line in markdown_content.split("\n"):
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("**"):
                html_lines.append(f"<strong>{line[2:-2]}</strong>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")

        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)

    def _generate_json(self, project: Dict, understanding: Dict) -> Dict:
        """Generate JSON documentation structure."""
        report = self._derive_report_context(project, understanding)
        return {
            "project": {
                "id": project.get("id"),
                "name": project.get("name"),
                "status": report["status"],
                "created_at": project.get("created_at"),
                "asset_count": report["asset_count"],
            },
            "exported_at": datetime.utcnow().isoformat(),
            "understanding": understanding,
            "structure": {
                "functional_map_sections": report["total_domains"],
                "operational_map_sections": len(report["processes"]),
                "recommendations_count": len(report["recommendations"]),
                "rules_count": len(report["rules"]),
                "components_count": report["total_components"],
                "data_assets_count": report["total_data_assets"],
            },
        }

    def _calculate_metadata(self, content: str, format: ExportFormat) -> Dict[str, int]:
        """Calculate metadata about the generated content."""
        lines = content.split("\n")
        
        if format == ExportFormat.MARKDOWN:
            headers = len([l for l in lines if l.startswith("#")])
            tables = len([l for l in lines if "|" in l])
            code_blocks = len([l for l in lines if l.startswith("```")])
        elif format == ExportFormat.HTML:
            headers = content.count("<h1>") + content.count("<h2>") + content.count("<h3>")
            tables = content.count("<table>")
            code_blocks = content.count("<code>")
        else:  # JSON
            headers = tables = code_blocks = 0

        return {
            "sections": len([l for l in lines if l.strip() and len(l) > 50]),
            "lines": len(lines),
            "headers": headers,
            "tables": tables,
            "code_blocks": code_blocks,
            "size_bytes": len(content.encode("utf-8")),
        }

    def _build_toc(self, content: str) -> list:
        """Build table of contents from markdown headers."""
        toc = []
        for line in content.split("\n"):
            if line.startswith("##") and not line.startswith("###"):
                title = line.replace("## ", "").strip()
                anchor = title.lower().replace(" ", "-")
                toc.append({"level": 2, "title": title, "anchor": anchor})
            elif line.startswith("###"):
                title = line.replace("### ", "").strip()
                anchor = title.lower().replace(" ", "-")
                toc.append({"level": 3, "title": title, "anchor": anchor})
        return toc

    async def export_rule_candidates_with_tracking(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Export rule candidates with implementation tracking.

        Returns:
        {
            "rule_candidates": [
                {
                    "id": str,
                    "name": str,
                    "description": str,
                    "source_asset": str,
                    "extraction_logic": str,
                    "reusability_score": "HIGH|MEDIUM|LOW",
                    "implementation_status": "DRAFT|VALIDATED|IMPLEMENTED",
                    "subset_extraction": { columns, filters, transformations },
                    "reusability_markers": [tags],
                    "confidence": 0.0-1.0,
                }
            ],
            "consolidation_opportunities": [
                { "from": str, "to": str, "reason": str }
            ]
        }
        """
        try:
            # Get understanding snapshot
            understanding = await self._get_understanding_snapshot(project_id)
            if not understanding:
                return {"error": "understanding_not_found"}

            rule_summary = understanding.get("rule_candidate_summary", {})
            rules = rule_summary.get("rules", [])

            # Enhance rules with tracking
            tracked_rules = []
            for rule in rules:
                tracked_rule = {
                    **rule,
                    "implementation_status": "DRAFT",  # default
                    "subset_extraction": self._build_subset_extraction(rule),
                    "reusability_markers": self._extract_reusability_markers(rule),
                }
                tracked_rules.append(tracked_rule)

            # Identify consolidation opportunities
            consolidations = self._identify_consolidation_opportunities(tracked_rules)

            return {
                "project_id": project_id,
                "generated_at": datetime.utcnow().isoformat(),
                "rule_candidates": tracked_rules,
                "consolidation_opportunities": consolidations,
                "summary": {
                    "total_rules": len(tracked_rules),
                    "high_reusability": len([r for r in tracked_rules 
                                            if r.get("reusability_score") == "HIGH"]),
                    "consolidation_candidates": len(consolidations),
                },
            }

        except Exception as e:
            return {"error": str(e), "project_id": project_id}

    def _build_subset_extraction(self, rule: Dict) -> Dict:
        """Build subset extraction specification from rule."""
        return {
            "columns": rule.get("source_columns", []),
            "filters": rule.get("suggested_filters", []),
            "transformations": rule.get("transformations", []),
            "output_format": rule.get("output_format", "table"),
        }

    def _extract_reusability_markers(self, rule: Dict) -> list:
        """Extract reusability markers from rule context."""
        markers = []
        if rule.get("reusability_score") == "HIGH":
            markers.append("highly-reusable")
        if rule.get("applicable_to"):
            markers.extend(rule.get("applicable_to", []))
        if rule.get("prerequisite_assets"):
            markers.append("dependent")
        return markers

    def _identify_consolidation_opportunities(self, rules: list) -> list:
        """Identify rules that could be consolidated."""
        consolidations = []
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1 :]:
                if self._rules_are_consolidatable(rule1, rule2):
                    consolidations.append({
                        "from": rule1.get("name"),
                        "to": rule2.get("name"),
                        "reason": "Similar extraction logic and output",
                        "opportunity": "Merge into single parameterized rule",
                    })
        return consolidations

    def _rules_are_consolidatable(self, rule1: Dict, rule2: Dict) -> bool:
        """Check if two rules can be consolidated."""
        # Simple heuristic: same source columns and similar transformations
        same_columns = set(rule1.get("source_columns", [])) == set(
            rule2.get("source_columns", [])
        )
        same_logic = (
            rule1.get("extraction_logic", "").split()[0:3]
            == rule2.get("extraction_logic", "").split()[0:3]
        )
        return same_columns and same_logic

    async def export_recommendation_actions(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Map recommendations to concrete implementation actions.

        Returns:
        {
            "recommendation_actions": [
                {
                    "recommendation_id": str,
                    "title": str,
                    "severity": str,
                    "actions": [
                        {"action_type": str, "artifact_type": str, "details": str}
                    ],
                    "implementation_path": str,
                    "dependencies": [str],
                    "estimated_effort": "LOW|MEDIUM|HIGH",
                }
            ]
        }
        """
        try:
            understanding = await self._get_understanding_snapshot(project_id)
            if not understanding:
                return {"error": "understanding_not_found"}

            recommendations = understanding.get("recommendation_set", {}).get("recommendations", [])
            actions = []

            for rec in recommendations:
                recommendation_actions = {
                    "recommendation_id": rec.get("id"),
                    "title": rec.get("title"),
                    "severity": rec.get("severity"),
                    "actions": self._map_recommendation_to_actions(rec),
                    "implementation_path": self._determine_implementation_path(rec),
                    "dependencies": rec.get("dependencies", []),
                    "estimated_effort": self._estimate_effort(rec),
                }
                actions.append(recommendation_actions)

            return {
                "project_id": project_id,
                "generated_at": datetime.utcnow().isoformat(),
                "recommendation_actions": actions,
                "action_summary": {
                    "total_recommendations": len(recommendations),
                    "document_generation": len([a for a in actions 
                                               if any(ac.get("artifact_type") == "documentation" 
                                                     for ac in a.get("actions", []))]),
                    "code_generation": len([a for a in actions 
                                           if any(ac.get("artifact_type") == "code" 
                                                 for ac in a.get("actions", []))]),
                    "process_updates": len([a for a in actions 
                                           if any(ac.get("artifact_type") == "process" 
                                                 for ac in a.get("actions", []))]),
                },
            }

        except Exception as e:
            return {"error": str(e), "project_id": project_id}

    def _map_recommendation_to_actions(self, recommendation: Dict) -> list:
        """Map a recommendation to concrete implementation actions."""
        actions = []
        rec_type = recommendation.get("category", "general")

        if rec_type == "documentation":
            actions.append({
                "action_type": "create",
                "artifact_type": "documentation",
                "details": f"Generate {recommendation.get('title')} documentation",
            })
        elif rec_type == "data_quality":
            actions.extend([
                {
                    "action_type": "validate",
                    "artifact_type": "validation_rule",
                    "details": f"Implement data quality check: {recommendation.get('title')}",
                },
                {
                    "action_type": "monitor",
                    "artifact_type": "monitoring",
                    "details": "Set up continuous monitoring",
                },
            ])
        elif rec_type == "governance":
            actions.append({
                "action_type": "establish",
                "artifact_type": "governance",
                "details": f"Establish {recommendation.get('title')}",
            })
        elif rec_type == "optimization":
            actions.append({
                "action_type": "refactor",
                "artifact_type": "code",
                "details": f"Optimize: {recommendation.get('title')}",
            })

        return actions

    def _determine_implementation_path(self, recommendation: Dict) -> str:
        """Determine the recommended implementation path."""
        severity = recommendation.get("severity", "MEDIUM")
        if severity == "CRITICAL":
            return "immediate_action"
        elif severity == "HIGH":
            return "next_sprint"
        elif severity == "MEDIUM":
            return "planned_development"
        else:
            return "backlog"

    def _estimate_effort(self, recommendation: Dict) -> str:
        """Estimate effort to implement recommendation."""
        complexity_signals = len(recommendation.get("dependencies", []))
        if complexity_signals > 5:
            return "HIGH"
        elif complexity_signals > 2:
            return "MEDIUM"
        else:
            return "LOW"
