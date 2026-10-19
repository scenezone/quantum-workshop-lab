import os

import mongomock
import pytest

# Tests must never use credentials or connect to the services in backend/.env.
os.environ["IBM_HARDWARE_ENABLED"] = "false"
os.environ["LLM_API_KEY"] = ""
os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"

from app.config import get_settings
from app.database.mongodb import Mongo
from app.database.seed import seed_database
from app.rate_limit import limiter


@pytest.fixture
def database(monkeypatch):
    client = mongomock.MongoClient(tz_aware=True)
    monkeypatch.setattr(Mongo, "client", client)
    Mongo.ensure_indexes()
    seed_database()
    yield Mongo.db()
    client.close()


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ibm_hardware_enabled", False)
    monkeypatch.setattr(settings, "llm_api_key", "")
    limiter.reset()


@pytest.fixture
def hardware_settings(database, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ibm_hardware_enabled", True)
    monkeypatch.setattr(settings, "ibm_max_daily_jobs", 25)
    monkeypatch.setattr(settings, "ibm_max_active_jobs", 3)
    return settings
