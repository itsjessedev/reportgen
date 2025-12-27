# ReportGen

Automated business report generation from multiple data sources. Eliminates Monday morning manual report assembly.

## Problem

Managers spend Monday mornings pulling data from 5+ sources to build a weekly report. It's tedious, error-prone, and delays decision-making.

## Solution

ReportGen automatically aggregates data from multiple sources, applies transformations, generates formatted PDF reports, and delivers them on schedule.

## Features

- **Template builder** - Drag-and-drop report sections
- **Multiple data sources** - Connect APIs, databases, spreadsheets
- **Scheduled delivery** - Daily, weekly, or monthly reports
- **Report archive** - Searchable history of all generated reports
- **Custom branding** - Logo, colors, fonts

## Tech Stack

- Python 3.11+
- FastAPI (web interface)
- pandas (data processing)
- WeasyPrint (PDF generation)
- SQLite (report archive)
- APScheduler (scheduling)
- SendGrid (email delivery)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/itsjessedev/reportgen.git
cd reportgen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Run the application
python -m src.main
```

## Demo Mode

Run with sample data (no external connections needed):

```bash
DEMO_MODE=true python -m src.main
```

## Configuration

See `.env.example` for all options:

- Data source credentials
- Report schedule (cron format)
- Email delivery settings
- Branding options

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/reports` | GET | List all reports |
| `/api/reports/{id}` | GET | Get specific report |
| `/api/reports/generate` | POST | Generate report now |
| `/api/templates` | GET/POST | Manage templates |
| `/api/sources` | GET/POST | Manage data sources |

## Project Structure

```
reportgen/
├── src/
│   ├── api/           # FastAPI routes
│   ├── services/      # Data connectors, PDF generation
│   ├── templates/     # Report templates (Jinja2)
│   ├── utils/         # Helpers, email
│   └── main.py        # Application entry
├── tests/             # Unit and integration tests
├── config/            # Configuration schemas
├── reports/           # Generated report archive
└── docker-compose.yml # Container deployment
```

## Supported Data Sources

- REST APIs (JSON)
- PostgreSQL / MySQL
- Google Sheets
- CSV files
- Airtable

## Results

> "Eliminated 4 hours of weekly reporting for our operations team. Reports now arrive in inboxes before anyone gets to work."

## License

MIT
