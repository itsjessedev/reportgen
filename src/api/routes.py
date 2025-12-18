"""API routes for report management."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.services.report_service import report_service, ReportStatus

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    """Request to generate a new report."""
    title: str
    template: str = "weekly_summary"
    data_sources: list[str] | None = None


class ReportResponse(BaseModel):
    """Standard API response."""
    status: str
    message: str
    data: dict | None = None


@router.get("/reports")
async def list_reports() -> ReportResponse:
    """List all generated reports."""
    reports = report_service.reports
    return ReportResponse(
        status="success",
        message=f"Found {len(reports)} reports",
        data={"reports": reports},
    )


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> ReportResponse:
    """Get a specific report."""
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse(
        status="success",
        message="Report found",
        data={"report": report.to_dict()},
    )


@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    """Download a report PDF."""
    report = report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report not ready for download")

    if not report.pdf_path:
        raise HTTPException(status_code=500, detail="PDF file not found")

    return FileResponse(
        path=report.pdf_path,
        filename=f"{report.id}_{report.title.replace(' ', '_')}.pdf",
        media_type="application/pdf",
    )


@router.post("/reports/generate")
async def generate_report(request: GenerateRequest) -> ReportResponse:
    """Generate a new report."""
    report = report_service.generate_report(
        title=request.title,
        template=request.template,
        data_sources=request.data_sources,
    )

    return ReportResponse(
        status=report.status.value,
        message=f"Report {report.id} generated",
        data={"report": report.to_dict()},
    )


@router.get("/templates")
async def list_templates() -> ReportResponse:
    """List available report templates."""
    templates = [
        {"id": "weekly_summary", "name": "Weekly Summary", "description": "Overview of all key metrics"},
        {"id": "sales_report", "name": "Sales Report", "description": "Detailed sales analysis"},
        {"id": "ops_report", "name": "Operations Report", "description": "Operational metrics and tickets"},
        {"id": "finance_report", "name": "Finance Report", "description": "Budget vs actual analysis"},
    ]
    return ReportResponse(
        status="success",
        message=f"Found {len(templates)} templates",
        data={"templates": templates},
    )


@router.get("/sources")
async def list_sources() -> ReportResponse:
    """List available data sources."""
    from src.services.data_sources import data_manager

    sources = [
        {"id": name, "type": type(source).__name__}
        for name, source in data_manager.sources.items()
    ]
    return ReportResponse(
        status="success",
        message=f"Found {len(sources)} data sources",
        data={"sources": sources},
    )
