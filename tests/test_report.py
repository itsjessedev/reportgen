"""Tests for report generation."""

import os
os.environ["DEMO_MODE"] = "true"

from src.services.data_sources import data_manager, DemoDataSource
from src.services.report_service import report_service, ReportStatus


class TestDataSources:
    """Tests for data source connectors."""

    def test_demo_source_connect(self):
        source = DemoDataSource("sales")
        assert source.connect() is True

    def test_demo_source_fetch(self):
        source = DemoDataSource("sales")
        source.connect()
        df = source.fetch_data()
        assert len(df) > 0
        assert "revenue" in df.columns

    def test_data_manager_fetch_all(self):
        data_manager.connect_all()
        data = data_manager.fetch_all()
        assert "sales" in data
        assert "operations" in data
        assert "finance" in data


class TestReportService:
    """Tests for report generation."""

    def test_generate_report(self):
        report = report_service.generate_report(
            title="Test Report",
            template="weekly_summary",
        )
        assert report.status == ReportStatus.COMPLETED
        assert report.id.startswith("RPT-")

    def test_report_list(self):
        initial_count = len(report_service.reports)
        report_service.generate_report(title="Another Test")
        assert len(report_service.reports) > initial_count

    def test_get_report(self):
        report = report_service.generate_report(title="Get Test")
        fetched = report_service.get_report(report.id)
        assert fetched is not None
        assert fetched.title == "Get Test"
