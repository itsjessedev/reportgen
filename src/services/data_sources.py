"""Data source connectors for pulling report data."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any
import random

import pandas as pd
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


# Demo data generators
def generate_demo_sales_data() -> pd.DataFrame:
    """Generate demo sales data."""
    regions = ["North", "South", "East", "West"]
    products = ["Widget A", "Widget B", "Service Pro", "Enterprise Suite"]

    data = []
    for _ in range(50):
        data.append({
            "date": datetime.now() - timedelta(days=random.randint(0, 30)),
            "region": random.choice(regions),
            "product": random.choice(products),
            "quantity": random.randint(1, 100),
            "revenue": round(random.uniform(100, 10000), 2),
            "rep": f"Rep {random.randint(1, 10)}",
        })

    return pd.DataFrame(data)


def generate_demo_ops_data() -> pd.DataFrame:
    """Generate demo operations data."""
    categories = ["Shipping", "Support", "Manufacturing", "QA"]
    statuses = ["Completed", "In Progress", "Delayed", "Blocked"]

    data = []
    for i in range(30):
        data.append({
            "ticket_id": f"OPS-{1000 + i}",
            "category": random.choice(categories),
            "status": random.choice(statuses),
            "created": datetime.now() - timedelta(days=random.randint(1, 14)),
            "resolved": datetime.now() - timedelta(days=random.randint(0, 7)) if random.random() > 0.3 else None,
            "priority": random.choice(["Low", "Medium", "High", "Critical"]),
        })

    return pd.DataFrame(data)


def generate_demo_finance_data() -> pd.DataFrame:
    """Generate demo financial data."""
    categories = ["Revenue", "COGS", "Marketing", "Payroll", "Operations", "R&D"]

    data = []
    for cat in categories:
        for month in range(1, 4):
            budget = random.uniform(50000, 500000)
            actual = budget * random.uniform(0.8, 1.2)
            data.append({
                "category": cat,
                "month": f"2024-{month:02d}",
                "budget": round(budget, 2),
                "actual": round(actual, 2),
                "variance": round(actual - budget, 2),
                "variance_pct": round((actual - budget) / budget * 100, 1),
            })

    return pd.DataFrame(data)


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source."""
        pass

    @abstractmethod
    def fetch_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        """Fetch data from the source."""
        pass


class DemoDataSource(DataSource):
    """Demo data source with mock data."""

    def __init__(self, data_type: str = "sales"):
        self.data_type = data_type

    def connect(self) -> bool:
        logger.info(f"Demo data source connected: {self.data_type}")
        return True

    def fetch_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        generators = {
            "sales": generate_demo_sales_data,
            "ops": generate_demo_ops_data,
            "finance": generate_demo_finance_data,
        }

        generator = generators.get(self.data_type, generate_demo_sales_data)
        df = generator()
        logger.info(f"Fetched {len(df)} rows from demo {self.data_type} source")
        return df


class APIDataSource(DataSource):
    """REST API data source."""

    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self._client: httpx.Client | None = None

    def connect(self) -> bool:
        if settings.demo_mode:
            logger.info("Demo mode: Simulating API connection")
            return True

        try:
            self._client = httpx.Client(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
            # Test connection
            self._client.get("/health")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to API: {e}")
            return False

    def fetch_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        if settings.demo_mode:
            return generate_demo_sales_data()

        if not self._client:
            raise RuntimeError("Not connected. Call connect() first.")

        try:
            endpoint = query.get("endpoint", "/data") if query else "/data"
            params = query.get("params", {}) if query else {}

            response = self._client.get(endpoint, params=params)
            response.raise_for_status()

            data = response.json()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Failed to fetch from API: {e}")
            raise


class DataSourceManager:
    """Manages multiple data sources for report generation."""

    def __init__(self):
        self.sources: dict[str, DataSource] = {}

    def register(self, name: str, source: DataSource) -> None:
        """Register a data source."""
        self.sources[name] = source
        logger.info(f"Registered data source: {name}")

    def connect_all(self) -> dict[str, bool]:
        """Connect to all registered sources."""
        results = {}
        for name, source in self.sources.items():
            results[name] = source.connect()
        return results

    def fetch(self, source_name: str, query: dict[str, Any] | None = None) -> pd.DataFrame:
        """Fetch data from a named source."""
        if source_name not in self.sources:
            raise ValueError(f"Unknown data source: {source_name}")

        return self.sources[source_name].fetch_data(query)

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """Fetch data from all sources."""
        results = {}
        for name, source in self.sources.items():
            try:
                results[name] = source.fetch_data()
            except Exception as e:
                logger.error(f"Failed to fetch from {name}: {e}")
                results[name] = pd.DataFrame()
        return results


# Default manager with demo sources
data_manager = DataSourceManager()
data_manager.register("sales", DemoDataSource("sales"))
data_manager.register("operations", DemoDataSource("ops"))
data_manager.register("finance", DemoDataSource("finance"))
