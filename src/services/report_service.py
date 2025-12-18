"""Main report generation orchestration."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from enum import Enum

import pandas as pd

from src.config import settings
from src.services.data_sources import data_manager
from src.services.pdf_generator import pdf_generator

logger = logging.getLogger(__name__)


class ReportStatus(str, Enum):
    """Status of a report."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Report:
    """A generated report."""
    id: str
    title: str
    template: str
    status: ReportStatus
    created_at: datetime
    completed_at: datetime | None = None
    pdf_path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "template": self.template,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "pdf_path": self.pdf_path,
            "error": self.error,
            "metadata": self.metadata,
        }


class ReportService:
    """Service for generating and managing reports."""

    def __init__(self):
        self._reports: dict[str, Report] = {}
        self._report_counter = 0
        self._reports_dir = Path("reports")
        self._reports_dir.mkdir(exist_ok=True)

    @property
    def reports(self) -> list[dict[str, Any]]:
        """Get all reports as dictionaries."""
        return [r.to_dict() for r in sorted(
            self._reports.values(),
            key=lambda x: x.created_at,
            reverse=True,
        )]

    def get_report(self, report_id: str) -> Report | None:
        """Get a specific report by ID."""
        return self._reports.get(report_id)

    def generate_report(
        self,
        title: str,
        template: str = "weekly_summary",
        data_sources: list[str] | None = None,
    ) -> Report:
        """Generate a new report."""
        self._report_counter += 1
        report_id = f"RPT-{self._report_counter:04d}"

        report = Report(
            id=report_id,
            title=title,
            template=template,
            status=ReportStatus.GENERATING,
            created_at=datetime.now(),
        )
        self._reports[report_id] = report

        try:
            logger.info(f"Generating report: {title} ({report_id})")

            # Connect to data sources
            data_manager.connect_all()

            # Fetch data from specified sources (or all)
            sources = data_sources or list(data_manager.sources.keys())
            raw_data = {}
            for source in sources:
                try:
                    raw_data[source] = data_manager.fetch(source)
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source}: {e}")

            # Process data for report
            processed_data = self._process_data(raw_data)

            # Generate PDF
            pdf_filename = f"{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = self._reports_dir / pdf_filename

            pdf_generator.generate(
                template_name=template,
                data={
                    "title": title,
                    "template": template,
                    **processed_data,
                },
                output_path=str(pdf_path),
            )

            report.status = ReportStatus.COMPLETED
            report.completed_at = datetime.now()
            report.pdf_path = str(pdf_path)
            report.metadata = {
                "sources": sources,
                "rows_processed": sum(len(df) for df in raw_data.values()),
            }

            logger.info(f"Report completed: {report_id}")

        except Exception as e:
            logger.exception(f"Report generation failed: {e}")
            report.status = ReportStatus.FAILED
            report.error = str(e)

        return report

    def _process_data(self, raw_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """Process raw data into report-ready format."""
        result = {
            "sections": [],
            "metrics": [],
            "tables": [],
        }

        # Process sales data
        if "sales" in raw_data and not raw_data["sales"].empty:
            sales_df = raw_data["sales"]

            # Calculate metrics
            total_revenue = sales_df["revenue"].sum()
            avg_order = sales_df["revenue"].mean()
            total_orders = len(sales_df)

            result["metrics"].extend([
                {"label": "Total Revenue", "value": f"${total_revenue:,.2f}"},
                {"label": "Orders", "value": f"{total_orders:,}"},
                {"label": "Avg Order Value", "value": f"${avg_order:,.2f}"},
            ])

            # Region breakdown table
            region_summary = sales_df.groupby("region").agg({
                "revenue": "sum",
                "quantity": "sum",
            }).reset_index()
            region_summary.columns = ["Region", "Revenue", "Units Sold"]

            result["tables"].append({
                "title": "Sales by Region",
                "headers": list(region_summary.columns),
                "rows": region_summary.values.tolist(),
            })

        # Process operations data
        if "operations" in raw_data and not raw_data["operations"].empty:
            ops_df = raw_data["operations"]

            # Status breakdown
            status_counts = ops_df["status"].value_counts()
            completed = status_counts.get("Completed", 0)
            total = len(ops_df)

            result["metrics"].append({
                "label": "Completion Rate",
                "value": f"{completed/total*100:.1f}%" if total > 0 else "N/A",
            })

            # Priority breakdown table
            priority_summary = ops_df.groupby(["priority", "status"]).size().unstack(fill_value=0)
            result["sections"].append({
                "title": "Operations Summary",
                "content": f"Processed {total} tickets this period. {completed} completed.",
            })

        # Process finance data
        if "finance" in raw_data and not raw_data["finance"].empty:
            finance_df = raw_data["finance"]

            # Budget vs actual
            total_budget = finance_df["budget"].sum()
            total_actual = finance_df["actual"].sum()
            variance = total_actual - total_budget

            result["metrics"].append({
                "label": "Budget Variance",
                "value": f"${variance:+,.2f}",
                "class": "positive" if variance < 0 else "negative",
            })

            # Category breakdown
            category_summary = finance_df.groupby("category").agg({
                "budget": "sum",
                "actual": "sum",
                "variance": "sum",
            }).reset_index()
            category_summary.columns = ["Category", "Budget", "Actual", "Variance"]

            result["tables"].append({
                "title": "Budget vs Actual by Category",
                "headers": list(category_summary.columns),
                "rows": category_summary.values.tolist(),
            })

        return result


# Singleton instance
report_service = ReportService()
