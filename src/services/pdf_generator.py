"""PDF report generation using WeasyPrint."""

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from src.config import settings

logger = logging.getLogger(__name__)

# Base CSS for reports
BASE_CSS = """
@page {
    size: letter;
    margin: 1in;
    @top-center {
        content: "{{ company_name }}";
        font-size: 10pt;
        color: #666;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a1a;
}

.header {
    border-bottom: 3px solid {{ primary_color }};
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.logo {
    max-height: 50px;
    margin-bottom: 10px;
}

h1 {
    color: {{ primary_color }};
    font-size: 24pt;
    margin: 0;
}

h2 {
    color: {{ primary_color }};
    font-size: 16pt;
    border-bottom: 1px solid #e5e5e5;
    padding-bottom: 10px;
    margin-top: 30px;
}

h3 {
    font-size: 13pt;
    color: #333;
}

.meta {
    color: #666;
    font-size: 10pt;
    margin-top: 5px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 10pt;
}

th {
    background: {{ primary_color }};
    color: white;
    text-align: left;
    padding: 10px;
    font-weight: 600;
}

td {
    padding: 8px 10px;
    border-bottom: 1px solid #e5e5e5;
}

tr:nth-child(even) {
    background: #f9fafb;
}

.metric-card {
    display: inline-block;
    width: 22%;
    margin: 1%;
    padding: 15px;
    background: #f3f4f6;
    border-radius: 8px;
    text-align: center;
}

.metric-value {
    font-size: 24pt;
    font-weight: bold;
    color: {{ primary_color }};
}

.metric-label {
    font-size: 9pt;
    color: #666;
    text-transform: uppercase;
}

.chart-placeholder {
    background: #f3f4f6;
    padding: 40px;
    text-align: center;
    color: #666;
    border-radius: 8px;
    margin: 20px 0;
}

.positive { color: #22c55e; }
.negative { color: #ef4444; }
.neutral { color: #6b7280; }

.footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e5e5e5;
    font-size: 9pt;
    color: #666;
    text-align: center;
}
"""


class PDFGenerator:
    """Generates PDF reports from templates and data."""

    def __init__(self):
        templates_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

        # Register custom filters
        self.jinja_env.filters["currency"] = lambda x: f"${x:,.2f}" if x else "$0.00"
        self.jinja_env.filters["percent"] = lambda x: f"{x:+.1f}%" if x else "0.0%"
        self.jinja_env.filters["number"] = lambda x: f"{x:,.0f}" if x else "0"

    def generate(
        self,
        template_name: str,
        data: dict[str, Any],
        output_path: str | None = None,
    ) -> bytes:
        """Generate a PDF report from a template and data."""
        logger.info(f"Generating PDF from template: {template_name}")

        # Add branding to data
        data.update({
            "company_name": settings.company_name,
            "company_logo_url": settings.company_logo_url,
            "primary_color": settings.primary_color,
            "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        })

        # Render template
        try:
            template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = template.render(**data)
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            # Use fallback template
            html_content = self._fallback_template(data)

        # Generate CSS with branding
        css_content = CSS(string=BASE_CSS.replace(
            "{{ company_name }}", settings.company_name
        ).replace(
            "{{ primary_color }}", settings.primary_color
        ))

        # Generate PDF
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf(stylesheets=[css_content])

        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
            logger.info(f"PDF saved to: {output_path}")

        return pdf_bytes

    def _fallback_template(self, data: dict[str, Any]) -> str:
        """Generate a basic report when template is missing."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>{data.get('title', 'Report')}</title></head>
        <body>
            <div class="header">
                <h1>{data.get('title', 'Business Report')}</h1>
                <p class="meta">Generated: {data.get('generated_at')}</p>
            </div>

            <h2>Summary</h2>
            <p>Report data is available but template "{data.get('template', 'unknown')}" was not found.</p>

            <div class="footer">
                <p>Generated by ReportGen for {data.get('company_name', 'Your Company')}</p>
            </div>
        </body>
        </html>
        """


# Singleton instance
pdf_generator = PDFGenerator()
