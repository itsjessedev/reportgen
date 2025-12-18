"""ReportGen - Main application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.api.routes import router as api_router
from src.config import settings
from src.services.report_service import report_service
from src.utils.email import send_scheduled_report

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Scheduler
scheduler = AsyncIOScheduler()


async def scheduled_report_job():
    """Generate and send scheduled report."""
    logger.info("Running scheduled report generation...")
    report = report_service.generate_report(
        title="Weekly Summary Report",
        template="weekly_summary",
    )
    if report.pdf_path:
        send_scheduled_report(report)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting ReportGen...")
    logger.info(f"Demo mode: {settings.demo_mode}")

    # Set up scheduler
    try:
        parts = settings.report_schedule.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
            scheduler.add_job(scheduled_report_job, trigger, id="report_job")
            scheduler.start()
            logger.info(f"Scheduled reports: {settings.report_schedule}")
    except Exception as e:
        logger.warning(f"Could not parse schedule: {e}")

    yield

    logger.info("Shutting down ReportGen...")
    scheduler.shutdown(wait=False)


# Create app
app = FastAPI(
    title="ReportGen",
    description="Automated business report generation",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routes
app.include_router(api_router)

# Dashboard templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "demo_mode": settings.demo_mode,
            "schedule": settings.report_schedule,
            "company_name": settings.company_name,
        },
    )


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "demo_mode": settings.demo_mode}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
