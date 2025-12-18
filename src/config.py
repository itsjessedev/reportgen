"""Application configuration."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    demo_mode: bool = Field(default=False)
    debug: bool = Field(default=False)
    database_url: str = Field(default="sqlite:///./reports.db")

    # Schedule
    report_schedule: str = Field(default="0 7 * * 1")

    # SendGrid
    sendgrid_api_key: str = Field(default="")
    from_email: str = Field(default="reports@example.com")
    default_recipients: str = Field(default="")

    # Branding
    company_name: str = Field(default="Your Company")
    company_logo_url: str = Field(default="")
    primary_color: str = Field(default="#3b82f6")

    # Data Sources
    postgres_url: str = Field(default="")
    google_credentials_file: str = Field(default="credentials.json")
    google_spreadsheet_id: str = Field(default="")
    api_base_url: str = Field(default="")
    api_key: str = Field(default="")
    airtable_api_key: str = Field(default="")
    airtable_base_id: str = Field(default="")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
