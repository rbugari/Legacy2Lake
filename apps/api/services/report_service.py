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
                # If category is missing, try to get it from 'type'
                if not asset_copy.get('category'):
                    asset_copy['category'] = a.get('type', 'SUPPORT')
                processed_assets.append(asset_copy)

            # Calculate statistics using the corrected mapping
            stats = self._calculate_triage_stats(processed_assets)
            
            # Prepare template context
            context = {
                'project': project,
                'assets': processed_assets[:1000],  # Increased to 1000 for visibility
                'stats': stats,
                'scout': project.get('settings', {}).get('scout_assessment', {}),
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
            
            # Prepare template context
            context = {
                'project': project,
                'assets': assets,
                'outputs': outputs,
                'timeline': timeline,
                'scout': project.get('settings', {}).get('scout_assessment', {}),
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
