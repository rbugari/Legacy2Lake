"""
PDF Report Generation Service - ROBUST VERSION

Generates professional PDF reports for Legacy2Lake projects using Playwright (Headless Chromium).
Optimized for Windows threadpool execution with detailed logging and error recovery.
"""

from playwright.sync_api import sync_playwright
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure local logging for report generation
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReportService")

class ReportService:
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / 'templates' / 'reports'
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # Brand assets paths
        self.brand_dir = Path(__file__).parent.parent.parent.parent / 'web' / 'public' / 'brand'
        
    def generate_triage_report(self, project: Dict[str, Any], assets: List[Dict[str, Any]]) -> bytes:
        """Generate Post-Triage Discovery Report (Sync)"""
        try:
            # Defensive check for assets
            if assets is None: assets = []
            if not isinstance(assets, list): assets = []
            
            # Release 3.7: Map 'type' to 'category' for template compatibility
            # and ensure we have all properties needed by the template
            processed_assets = []
            for a in assets:
                asset_copy = a.copy()

                # ── Category (CORE/SUPPORT/IGNORED) ───────────────────────────────────
                # In utm_objects: 'type' = CORE/SUPPORT/IGNORED (triage class)
                #                 'category' = migrable/soporte/documentacion (file class)
                # The template filters on asset.category == 'CORE' so we normalise here.
                triage_class = (a.get('type') or '').upper()
                if triage_class in ('CORE', 'SUPPORT', 'IGNORED'):
                    asset_copy['category'] = triage_class
                elif (a.get('category') or '').upper() in ('CORE', 'SUPPORT', 'IGNORED'):
                    asset_copy['category'] = a['category'].upper()
                else:
                    asset_copy['category'] = 'SUPPORT'  # safe fallback

                # ── PII flag ──────────────────────────────────────────────────────────
                # DB stores 'is_pii'; template expects 'has_pii'
                asset_copy['has_pii'] = bool(a.get('is_pii') or a.get('has_pii'))
                if asset_copy['has_pii']:
                    asset_copy['pii_reason'] = (a.get('metadata') or {}).get('pii_reason', 'Flagged by forensic analyser')

                # ── Complexity ────────────────────────────────────────────────────────
                # Not stored directly; try metadata then derive from criticality.
                meta = a.get('metadata') or {}
                complexity = (
                    a.get('complexity') or
                    meta.get('complexity') or
                    meta.get('complexity_level')
                )
                if not complexity:
                    crit = (a.get('criticality') or 'P3').upper()
                    complexity = {'P1': 'HIGH', 'P2': 'MEDIUM'}.get(crit, 'LOW')
                asset_copy['complexity'] = complexity.upper()

                # ── Display type (file extension / detected tech) ─────────────────────
                # 'type' in DB = CORE/SUPPORT/IGNORED — not useful for the Type column.
                # Use the source path extension or metadata hint instead.
                src = a.get('source_path') or a.get('filename') or ''
                ext = src.rsplit('.', 1)[-1].upper() if '.' in src else ''
                asset_copy['asset_type'] = (
                    meta.get('asset_type') or
                    meta.get('detected_tech') or
                    meta.get('file_type') or
                    ext or
                    'Unknown'
                )

                processed_assets.append(asset_copy)

            # Calculate statistics using the corrected mapping
            stats = self._calculate_triage_stats(processed_assets)
            
            # Sprint 14: schema intelligence stats
            schema_stats = self._calculate_schema_stats(processed_assets)

            # Quality score distribution
            quality_dist = {}
            for a in processed_assets:
                qs = a.get('quality_score') or (a.get('metadata') or {}).get('quality_score')
                if qs is not None:
                    try:
                        bucket = f"{int(float(qs) // 10) * 10}-{int(float(qs) // 10) * 10 + 9}"
                        quality_dist[bucket] = quality_dist.get(bucket, 0) + 1
                    except (TypeError, ValueError):
                        pass

            # Prepare template context
            context = {
                'project': project,
                'assets': processed_assets[:1000],  # Increased to 1000 for visibility
                'stats': stats,
                'schema_stats': schema_stats,
                'quality_dist': quality_dist,
                'scout': self._resolve_scout(project),
                'support_intel': project.get('settings', {}).get('support_intelligence', []),
                'generated_date': datetime.now().strftime('%B %d, %Y'),
                'brand_logo': self._to_file_url(self.brand_dir / 'logo.png'),
                'cover_image': self._to_file_url(self.brand_dir / '2 HERO_PORTAL.png'),
                'watermark': self._to_file_url(self.brand_dir / 'Gemini_Generated_Image_dt1e1dt1e1dt1e1d.png')
            }
            
            # Render HTML template
            template = self.env.get_template('triage_report.html')
            html_content = template.render(**context)
            
            # Convert to PDF
            return self._html_to_pdf(html_content, watermark_url=context.get('watermark'))
        except Exception as e:
            logger.error(f"Error in generate_triage_report: {e}", exc_info=True)
            return b""
    
    def generate_final_report(self, project: Dict[str, Any], assets: List[Dict[str, Any]], 
                             outputs: List[Dict[str, Any]], timeline: Dict[str, Any]) -> bytes:
        """Generate Final Migration Delivery Report (Sync)"""
        try:
            # Defensive checks
            if assets is None: assets = []
            if outputs is None: outputs = []
            
            # Sprint 14: Medallion breakdown + governance score
            medallion_stats = self._calculate_medallion_stats(outputs)
            governance_score = (
                project.get('governance_score')
                or project.get('settings', {}).get('governance_score')
                or project.get('settings', {}).get('audit_result', {}).get('score')
            )
            certification_score = (
                project.get('certification_score')
                or project.get('settings', {}).get('certification_score')
            )

            # Prepare template context
            context = {
                'project': project,
                'assets': assets,
                'outputs': outputs,
                'timeline': timeline,
                'medallion_stats': medallion_stats,
                'governance_score': governance_score,
                'certification_score': certification_score,
                'scout': self._resolve_scout(project),
                'support_intel': project.get('settings', {}).get('support_intelligence', []),
                'generated_date': datetime.now().strftime('%B %d, %Y'),
                'total_outputs': len(outputs),
                'brand_logo': self._to_file_url(self.brand_dir / 'logo.png'),
                'cover_image': self._to_file_url(self.brand_dir / '1 Front.png'),
                'watermark': self._to_file_url(self.brand_dir / 'Gemini_Generated_Image_dt1e1dt1e1dt1e1d.png')
            }
            
            # Render HTML template
            template = self.env.get_template('final_report.html')
            html_content = template.render(**context)
            
            # Convert to PDF
            return self._html_to_pdf(html_content, watermark_url=context.get('watermark'))
        except Exception as e:
            logger.error(f"Error in generate_final_report: {e}", exc_info=True)
            return b""
    
    def _calculate_schema_stats(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract PK/FK detection stats and column profiles from asset metadata (Sprint 14)"""
        if not assets:
            return {'pk_count': 0, 'fk_count': 0, 'detection_rate': 0,
                    'total_columns': 0, 'assets_with_schema': 0, 'column_profiles': []}

        pk_count = 0
        fk_count = 0
        total_columns = 0
        assets_with_schema = 0
        column_profiles = []

        for a in assets:
            meta = a.get('metadata') or {}
            schema = meta.get('schema_analysis') or meta.get('schema') or {}
            cols = schema.get('columns') or meta.get('columns') or []
            pks = schema.get('primary_keys') or meta.get('primary_keys') or []
            fks = schema.get('foreign_keys') or meta.get('foreign_keys') or []

            if cols or pks or fks:
                assets_with_schema += 1
                pk_count += len(pks)
                fk_count += len(fks)
                total_columns += len(cols)

                column_profiles.append({
                    'asset': a.get('name', '?'),
                    'column_count': len(cols),
                    'pk_count': len(pks),
                    'fk_count': len(fks),
                    'pii_columns': sum(1 for c in cols if c.get('is_pii') or c.get('pii')),
                    'quality_score': meta.get('quality_score') or a.get('quality_score') or '-',
                    'data_types': ', '.join(sorted(set(
                        c.get('type') or c.get('data_type', '') for c in cols if c.get('type') or c.get('data_type')
                    ))[:5]) or '-',
                })

        detection_rate = (assets_with_schema / len(assets) * 100) if assets else 0

        return {
            'pk_count': pk_count,
            'fk_count': fk_count,
            'detection_rate': round(detection_rate, 1),
            'total_columns': total_columns,
            'assets_with_schema': assets_with_schema,
            'column_profiles': column_profiles[:50],  # limit for report
        }

    def _calculate_medallion_stats(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Medallion Architecture breakdown from output artifacts (Sprint 14)"""
        if not outputs:
            return {'bronze': 0, 'silver': 0, 'gold': 0, 'other': 0,
                    'bronze_files': [], 'silver_files': [], 'gold_files': []}

        bronze, silver, gold, other = [], [], [], []
        for f in outputs:
            name = (f.get('name') or '').lower()
            layer = (f.get('layer') or f.get('medallion_layer') or '').lower()
            # Detect layer from metadata or filename
            if 'bronze' in layer or 'bronze' in name:
                bronze.append(f.get('name', ''))
            elif 'silver' in layer or 'silver' in name:
                silver.append(f.get('name', ''))
            elif 'gold' in layer or 'gold' in name:
                gold.append(f.get('name', ''))
            else:
                other.append(f.get('name', ''))

        return {
            'bronze': len(bronze),
            'silver': len(silver),
            'gold': len(gold),
            'other': len(other),
            'bronze_files': bronze[:10],
            'silver_files': silver[:10],
            'gold_files': gold[:10],
        }

    def _resolve_scout(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a scout dict that the triage_report template understands.
        Priority:
          1. project.settings.scout_assessment  (older projects, Agent S era)
          2. project.quick_assessment           (Sprint-14+, Quick Assessment)
          3. {}                                 (no scan yet — show warning block)
        """
        settings = project.get('settings') or {}

        # Legacy path
        sa = settings.get('scout_assessment') or {}
        if sa and (sa.get('completeness_score') or sa.get('assessment_summary') or sa.get('detected_gaps')):
            return sa

        # Sprint-14+ path: quick_assessment is a direct column on utm_projects
        qa = project.get('quick_assessment') or {}
        if not qa:
            return {}

        # Map QuickAssessmentResult fields → template fields
        blockers = qa.get('blockers') or []
        detected_gaps = [
            {
                'category': 'Blocker',
                'gap_description': b,
                'impact': 'HIGH',
                'suggested_file': None
            }
            for b in blockers
            if isinstance(b, str) and b.strip()
        ]

        techs = qa.get('detected_techs') or []
        detected_tech = ', '.join(techs) if techs else None

        return {
            'completeness_score': qa.get('score', 0),
            'detected_technology': detected_tech,
            'assessment_summary': (
                qa.get('llm_opinion') or
                f"Quick Assessment completed. Viability score: {qa.get('score', 0)}/100 "
                f"({qa.get('semaforo', 'yellow')}). "
                f"{len(qa.get('file_details') or [])} files analysed — "
                f"{(qa.get('file_breakdown') or {}).get('MIGRABLE', 0)} migratable."
            ),
            'detected_gaps': detected_gaps,
        }

    def _calculate_triage_stats(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from assets for triage report - Defensively"""
        if not assets or not isinstance(assets, list):
            return {
                'total': 0, 'core': 0, 'support': 0, 'ignored': 0,
                'complexity_high': 0, 'complexity_medium': 0, 'complexity_low': 0,
                'pii_count': 0, 'pii_assets': []
            }
            
        total = len(assets)
        
        # Safe asset access helper
        def get_val(a, key, default=None):
            # Try key first, then try 'type' if key is 'category'
            v = a.get(key)
            if v is None and key == 'category':
                v = a.get('type')
            return v if v is not None else default

        return {
            'total': total,
            'core': sum(1 for a in assets if get_val(a, 'category') == 'CORE'),
            'support': sum(1 for a in assets if get_val(a, 'category') == 'SUPPORT'),
            'ignored': sum(1 for a in assets if get_val(a, 'category') == 'IGNORED'),
            'complexity_high': sum(1 for a in assets if get_val(a, 'complexity') == 'HIGH'),
            'complexity_medium': sum(1 for a in assets if get_val(a, 'complexity') == 'MEDIUM'),
            'complexity_low': sum(1 for a in assets if get_val(a, 'complexity') == 'LOW'),
            'pii_count': sum(1 for a in assets if get_val(a, 'has_pii', False)),
            'pii_assets': [a for a in assets if a.get('has_pii', False)]
        }
    
    def _to_file_url(self, path: Path) -> str:
        """Convert local path to file:// URL for browser safely"""
        return path.absolute().as_uri()
    
    def _html_to_pdf(self, html_content: str, watermark_url: str = None) -> bytes:
        """Convert HTML to PDF using Playwright (Sync) with high resilience"""
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                # Create a context with higher execution timeouts
                context = browser.new_context()
                page = context.new_page()
                
                # CSS Injection setup
                injected_css = self._get_print_styles()
                if watermark_url:
                    injected_css += f'\n<style>body::before {{ background-image: url("{watermark_url}"); }}</style>'
                
                # Robustly inject CSS before </head>
                full_html = html_content
                if '</head>' in html_content:
                    full_html = html_content.replace('</head>', f'{injected_css}\n</head>')
                
                # Set content and wait for network activity to settle
                # domcontentloaded is faster, but networkidle ensures images are there
                # We use a 30s timeout
                page.set_content(full_html, wait_until="networkidle", timeout=30000)
                
                # Generate PDF (A4, high quality)
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
                    display_header_footer=True,
                    footer_template='''
                        <div style="font-size: 8px; color: #666; width: 100%; text-align: center; margin-bottom: 5px;">
                            Legacy2Lake Report | Project Documentation | Page <span class="pageNumber"></span> of <span class="totalPages"></span>
                        </div>
                    ''',
                    header_template='<div></div>'
                )
                
                browser.close()
                
                if not pdf_bytes or len(pdf_bytes) < 1000:
                    logger.warning(f"PDF generated but seems suspiciously small: {len(pdf_bytes)} bytes")
                
                return pdf_bytes
        except Exception as e:
            logger.error(f"Critical error in _html_to_pdf: {e}", exc_info=True)
            return b""

    def _get_print_styles(self) -> str:
        """Returns standard CSS for reports"""
        return '''
        <style>
            @page { size: A4; margin: 20mm 15mm; }
            body { font-family: 'Segoe UI', system-ui, sans-serif; color: #333; line-height: 1.6; position: relative; width: 100%; margin: 0; padding: 0; }
            body::before {
                content: ''; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                width: 60%; height: 60%; background-size: contain; background-repeat: no-repeat;
                background-position: center; opacity: 0.08; z-index: -1;
            }
            .page { page-break-after: always; padding: 10px; }
            .page:last-child { page-break-after: auto; }
            h1 { font-size: 32px; color: #0ea5e9; font-weight: 900; margin-bottom: 20px; }
            h2 { font-size: 24px; color: #0284c7; border-bottom: 2px solid #0ea5e9; padding-bottom: 5px; margin: 30px 0 15px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 11px; }
            th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #e5e7eb; word-break: break-all; }
            th { background-color: #f8fafc; color: #0369a1; font-weight: 700; text-transform: uppercase; font-size: 9px; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 9px; font-weight: 700; }
            .badge-high { background: #fee2e2; color: #991b1b; }
            .badge-medium { background: #fef3c7; color: #92400e; }
            .badge-low { background: #dcfce7; color: #166534; }
            .badge-core { background: #dbeafe; color: #1e40af; }
            .badge-support { background: #fef3c7; color: #92400e; }
            .badge-ignored { background: #f3f4f6; color: #6b7280; }
            .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }
            .stat-card { padding: 15px; background: #0ea5e9; color: white; border-radius: 8px; text-align: center; }
            .cover { text-align: center; padding-top: 100px; height: 100%; }
        </style>
        '''

# Singleton instance
report_service = ReportService()
