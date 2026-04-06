"""
Reports Catalog Service - Centralized Report Registry and Generation

Provides unified interface to all available reports/exports across the platform.
Enables discovery, filtering, and on-demand generation of:
- PDF reports (Triage, Final)
- Documentation exports (Markdown/HTML/JSON)
- Governance artifacts (audit, metrics)
- Analysis outputs (rules, recommendations)

Multi-tenant safe with role-based filtering.
"""

from typing import Dict, List, Any, Optional
import logging
from enum import Enum

logger = logging.getLogger("ReportsCatalogService")


class ReportCategory(str, Enum):
    """Report category for UI grouping and filtering."""
    TECHNICAL = "technical"  # For architects, engineers
    EXECUTIVE = "executive"  # For stakeholders, management
    GOVERNANCE = "governance"  # For audit, compliance
    HANDOVER = "handover"  # For deployment, ops
    ANALYSIS = "analysis"  # For exploration, insights


class ReportType(str, Enum):
    """Output format."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


class AudienceProfile(str, Enum):
    """User role/profile for discoverability."""
    DATA_ENGINEER = "data_engineer"
    ARCHITECT = "architect"
    EXECUTIVE = "executive"
    GOVERNANCE_OFFICER = "governance_officer"
    OPERATIONS = "operations"


class ProductLine(str, Enum):
    """Explicit product lens for reports catalog."""
    SOURCE_INTELLIGENCE = "source_intelligence"
    MIGRATION_FACTORY = "migration_factory"


class ReportMetadata:
    """Metadata describing a single report in the catalog."""
    
    def __init__(
        self,
        report_id: str,
        name: str,
        description: str,
        report_type: ReportType,           # Default/primary format
        available_formats: List[ReportType], # All formats this report supports
        category: ReportCategory,
        product_line: ProductLine,
        minimum_stage: int,
        audience: List[AudienceProfile],
        generator_service: str,
        api_endpoint: str,                 # Template: use {format} for format-driven endpoints
        icon: str = "📄",
        color: str = "cyan",
        estimated_generation_seconds: int = 5,
        available_filters: Optional[List[str]] = None,
        related_reports: Optional[List[str]] = None,
        metadata_extra: Optional[Dict[str, Any]] = None,
    ):
        self.report_id = report_id
        self.name = name
        self.description = description
        self.report_type = report_type
        self.available_formats = available_formats
        self.category = category
        self.product_line = product_line
        self.minimum_stage = minimum_stage
        self.audience = audience
        self.generator_service = generator_service
        self.api_endpoint = api_endpoint
        self.icon = icon
        self.color = color
        self.estimated_generation_seconds = estimated_generation_seconds
        self.available_filters = available_filters or []
        self.related_reports = related_reports or []
        self.metadata_extra = metadata_extra or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API response."""
        return {
            "report_id": self.report_id,
            "name": self.name,
            "description": self.description,
            "type": self.report_type.value,
            "available_formats": [f.value for f in self.available_formats],
            "category": self.category.value,
            "product_line": self.product_line.value,
            "minimum_stage": self.minimum_stage,
            "audience": [a.value for a in self.audience],
            "generator_service": self.generator_service,
            "api_endpoint": self.api_endpoint,
            "icon": self.icon,
            "color": self.color,
            "estimated_generation_seconds": self.estimated_generation_seconds,
            "available_filters": self.available_filters,
            "related_reports": self.related_reports,
            "metadata": self.metadata_extra,
        }


class ReportsCatalogService:
    """Centralized registry and discovery service for all available reports."""
    
    # Singleton instance with all registered reports
    _catalog: Dict[str, ReportMetadata] = {}
    
    @classmethod
    def _initialize_catalog(cls):
        """Register all available reports (called on first use)."""
        if cls._catalog:
            return  # Already initialized
        
        # 1. DISCOVERY PHASE REPORTS (Stage 2 - Triage)
        cls._catalog["discovery-analysis"] = ReportMetadata(
            report_id="discovery-analysis",
            name="Discovery Analysis Report",
            description="Post-triage asset analysis: complexity, PII detection, technology stack, schema profiling and migration blockers.",
            report_type=ReportType.PDF,
            available_formats=[ReportType.PDF],
            category=ReportCategory.ANALYSIS,
            product_line=ProductLine.SOURCE_INTELLIGENCE,
            minimum_stage=2,
            audience=[AudienceProfile.ARCHITECT, AudienceProfile.DATA_ENGINEER, AudienceProfile.EXECUTIVE],
            generator_service="ReportService.generate_triage_report",
            api_endpoint="projects/{project_id}/reports/triage",
            icon="🔍",
            color="cyan",
            estimated_generation_seconds=8,
            available_filters=["show_pii_only", "complexity_filter", "category_filter"],
            related_reports=["schema-intelligence", "forensic-assessment"],
            metadata_extra={
                "highlights": ["Asset inventory", "Complexity breakdown", "PII detection", "Schema profiling"],
                "data_freshness": "Post-triage",
                "product_story": "Source system understanding and origin documentation",
            }
        )

        # 2. DRAFTING PHASE REPORTS (Stage 3+)
        cls._catalog["migration-delivery"] = ReportMetadata(
            report_id="migration-delivery",
            name="Migration Delivery Report",
            description="Complete migration documentation: generated artifacts catalog, medallion breakdown, governance scores and deployment instructions.",
            report_type=ReportType.PDF,
            available_formats=[ReportType.PDF],
            category=ReportCategory.HANDOVER,
            product_line=ProductLine.MIGRATION_FACTORY,
            minimum_stage=3,
            audience=[AudienceProfile.OPERATIONS, AudienceProfile.EXECUTIVE, AudienceProfile.DATA_ENGINEER],
            generator_service="ReportService.generate_final_report",
            api_endpoint="projects/{project_id}/reports/final",
            icon="📦",
            color="purple",
            estimated_generation_seconds=10,
            available_filters=["show_medallion_breakdown", "show_artifacts_only"],
            related_reports=["rule-candidates", "knowledge-export"],
            metadata_extra={
                "highlights": ["Artifacts catalog", "Medallion layers", "Deployment guide", "Quality metrics"],
                "data_freshness": "Post-drafting",
                "product_story": "Target solution delivery and generated artifact handover",
            }
        )

        # 3. KNOWLEDGE EXPORT — unified entry with format selector
        cls._catalog["knowledge-export"] = ReportMetadata(
            report_id="knowledge-export",
            name="Knowledge Export",
            description="Handover-ready documentation from understanding artifacts: data lineage, process flows, transformation rules, and governance findings. Available as Markdown, HTML or JSON.",
            report_type=ReportType.MARKDOWN,         # default
            available_formats=[ReportType.MARKDOWN, ReportType.HTML, ReportType.JSON],
            category=ReportCategory.TECHNICAL,
            product_line=ProductLine.SOURCE_INTELLIGENCE,
            minimum_stage=3,
            audience=[AudienceProfile.ARCHITECT, AudienceProfile.DATA_ENGINEER, AudienceProfile.EXECUTIVE],
            generator_service="DocumentationExportService.export_documentation",
            api_endpoint="projects/{project_id}/export/documentation?format={format}",
            icon="📝",
            color="indigo",
            estimated_generation_seconds=5,
            available_filters=["include_evidence", "include_recommendations"],
            related_reports=["recommendations", "rule-candidates"],
            metadata_extra={
                "highlights": ["TOC", "Lineage", "Rules", "Dependencies"],
                "data_freshness": "Post-understanding",
                "product_story": "Structured understanding of the source estate, ready for handover",
            }
        )

        # 4. RULE CANDIDATES LIBRARY (Stage 3+)
        cls._catalog["rule-candidates"] = ReportMetadata(
            report_id="rule-candidates",
            name="Rule Candidates Library",
            description="Extracted and scored transformation rules with reusability metrics, LOCAL/GLOBAL classification, effort estimates and consolidation opportunities.",
            report_type=ReportType.JSON,
            available_formats=[ReportType.JSON, ReportType.MARKDOWN],
            category=ReportCategory.TECHNICAL,
            product_line=ProductLine.MIGRATION_FACTORY,
            minimum_stage=3,
            audience=[AudienceProfile.DATA_ENGINEER, AudienceProfile.ARCHITECT],
            generator_service="DocumentationExportService.export_rule_candidates",
            api_endpoint="projects/{project_id}/export/rule-candidates",
            icon="⚙️",
            color="amber",
            estimated_generation_seconds=3,
            available_filters=["reusability_level", "applicability", "priority"],
            related_reports=["knowledge-export", "recommendations"],
            metadata_extra={
                "highlights": ["Top 20 rules", "Reusability scoring", "Consolidation detection"],
                "data_freshness": "Post-refinement",
                "product_story": "Transformation logic library for delivery acceleration",
            }
        )

        # 5. RECOMMENDATIONS (Stage 3+)
        cls._catalog["recommendations"] = ReportMetadata(
            report_id="recommendations",
            name="Recommendation Actions",
            description="Prioritized recommendations with implementation paths, effort estimates (XS–L) and stakeholder guidance.",
            report_type=ReportType.JSON,
            available_formats=[ReportType.JSON, ReportType.MARKDOWN],
            category=ReportCategory.ANALYSIS,
            product_line=ProductLine.SOURCE_INTELLIGENCE,
            minimum_stage=3,
            audience=[AudienceProfile.ARCHITECT, AudienceProfile.EXECUTIVE],
            generator_service="DocumentationExportService.export_recommendation_actions",
            api_endpoint="projects/{project_id}/export/recommendation-actions",
            icon="💡",
            color="blue",
            estimated_generation_seconds=3,
            available_filters=["priority_level", "effort_range"],
            related_reports=["rule-candidates", "knowledge-export"],
            metadata_extra={
                "highlights": ["Priority ranking", "Effort sizing", "Implementation paths"],
                "data_freshness": "Post-understanding",
                "product_story": "Decision support derived from source understanding",
            }
        )

        # 6. SCHEMA INTELLIGENCE (Stage 2+)
        cls._catalog["schema-intelligence"] = ReportMetadata(
            report_id="schema-intelligence",
            name="Schema Intelligence Report",
            description="Column-level analysis: PK/FK detection, data type profiling, PII classification and quality metrics per asset.",
            report_type=ReportType.JSON,
            available_formats=[ReportType.JSON, ReportType.MARKDOWN],
            category=ReportCategory.TECHNICAL,
            product_line=ProductLine.SOURCE_INTELLIGENCE,
            minimum_stage=2,
            audience=[AudienceProfile.DATA_ENGINEER, AudienceProfile.ARCHITECT],
            generator_service="ReportService._calculate_schema_stats",
            api_endpoint="projects/{project_id}/reports/schema-intelligence",
            icon="📊",
            color="sky",
            estimated_generation_seconds=4,
            available_filters=["show_pii_only", "show_pk_fk_only"],
            related_reports=["discovery-analysis", "forensic-assessment"],
            metadata_extra={
                "highlights": ["PK detection rate", "FK relationships", "Column profiling", "PII columns"],
                "data_freshness": "Post-triage",
                "product_story": "Data model intelligence extracted from the legacy estate",
            }
        )

        # 7. FORENSIC ASSESSMENT (Stage 1+)
        cls._catalog["forensic-assessment"] = ReportMetadata(
            report_id="forensic-assessment",
            name="Forensic Assessment Report",
            description="Agent S scan results: completeness score, gap detection, blockers and tribal knowledge warnings.",
            report_type=ReportType.JSON,
            available_formats=[ReportType.JSON, ReportType.MARKDOWN],
            category=ReportCategory.ANALYSIS,
            product_line=ProductLine.SOURCE_INTELLIGENCE,
            minimum_stage=1,
            audience=[AudienceProfile.ARCHITECT, AudienceProfile.GOVERNANCE_OFFICER],
            generator_service="QuickAssessmentService",
            api_endpoint="projects/{project_id}/reports/forensic-assessment",
            icon="🔎",
            color="orange",
            estimated_generation_seconds=4,
            available_filters=["show_blockers_only"],
            related_reports=["discovery-analysis", "schema-intelligence"],
            metadata_extra={
                "highlights": ["Completeness score", "Blockers", "Gap analysis"],
                "data_freshness": "Post-discovery",
                "product_story": "Discovery-risk assessment of the source repository",
            }
        )
    
    @classmethod
    def get_all_reports(
        cls,
        stage: Optional[int] = None,
        category: Optional[str] = None,
        product_line: Optional[str] = None,
        audience: Optional[str] = None,
        report_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all available reports with optional filtering.
        
        Args:
            stage: Current project stage (filters to available reports)
            category: Filter by report category
            audience: Filter by audience profile
            report_type: Filter by output type (pdf, json, etc.)
        
        Returns:
            List of report metadata dictionaries
        """
        cls._initialize_catalog()
        
        results = []
        for report in cls._catalog.values():
            # Stage filter
            if stage is not None and report.minimum_stage > stage:
                continue
            
            # Category filter
            if category and report.category.value != category:
                continue
            
            # Product line filter
            if product_line and report.product_line.value != product_line:
                continue

            # Type filter
            if report_type and report.report_type.value != report_type:
                continue
            
            # Audience filter (match if any of user's roles match)
            if audience:
                user_profiles = [p.strip() for p in audience.split(",")]
                if not any(p in [a.value for a in report.audience] for p in user_profiles):
                    continue
            
            results.append(report.to_dict())
        
        return sorted(results, key=lambda r: (r["name"]))
    
    @classmethod
    def get_report(cls, report_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific report."""
        cls._initialize_catalog()
        report = cls._catalog.get(report_id)
        return report.to_dict() if report else None
    
    @classmethod
    def get_reports_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get all reports in a specific category."""
        return cls.get_all_reports(category=category)
    
    @classmethod
    def get_reports_for_stage(cls, stage: int) -> List[Dict[str, Any]]:
        """Get all reports available at a specific stage."""
        return cls.get_all_reports(stage=stage)
    
    @classmethod
    def get_reports_for_audience(cls, audience_profile: str) -> List[Dict[str, Any]]:
        """Get all reports relevant to a specific audience."""
        return cls.get_all_reports(audience=audience_profile)
    
    @classmethod
    def get_catalog_summary(cls) -> Dict[str, Any]:
        """Get overall catalog statistics."""
        cls._initialize_catalog()
        
        by_category = {}
        by_type = {}
        by_stage = {}
        by_product_line = {}
        
        for report in cls._catalog.values():
            cat = report.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            typ = report.report_type.value
            by_type[typ] = by_type.get(typ, 0) + 1
            
            stg = report.minimum_stage
            by_stage[stg] = by_stage.get(stg, 0) + 1

            product = report.product_line.value
            by_product_line[product] = by_product_line.get(product, 0) + 1
        
        return {
            "total_reports": len(cls._catalog),
            "by_category": by_category,
            "by_type": by_type,
            "by_stage": by_stage,
            "by_product_line": by_product_line,
            "available_categories": [c.value for c in ReportCategory],
            "available_types": [t.value for t in ReportType],
            "available_audience_profiles": [a.value for a in AudienceProfile],
            "available_product_lines": [p.value for p in ProductLine],
            "product_line_descriptions": {
                ProductLine.SOURCE_INTELLIGENCE.value: "Analysis and documentation of the source/origin system",
                ProductLine.MIGRATION_FACTORY.value: "Generation, certification, and handover of new target artifacts",
            },
        }
