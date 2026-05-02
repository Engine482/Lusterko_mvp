"""Shared pytest fixtures.

Session DB lifecycle:
- A dedicated `lusterko_test` Postgres database (env `TEST_DATABASE_URL`).
- `alembic upgrade head` runs once per session; we want to validate the real
  migrations, not metadata.create_all (Sprint Plan §11).
- Every test starts with all tables truncated.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

DEFAULT_TEST_URL = "postgresql://lusterko:change_me@localhost:5432/lusterko_test"

# `app.core.config` reads env at import time, so set it before app imports.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_URL))

from app.core.config import get_settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


def _alembic_config() -> Config:
    here = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(here, ".."))
    cfg = Config(os.path.join(project_root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _migrate_database() -> Iterator[None]:
    cfg = _alembic_config()
    command.upgrade(cfg, "head")
    yield


_TRUNCATABLE_TABLES = (
    "audit_logs",
    "password_reset_tokens",
    "user_sessions",
    "auth_invites",
    "user_roles",
    "users",
    "units",
)


@pytest.fixture(autouse=True)
def _clean_database() -> Iterator[None]:
    with SessionLocal() as db:
        joined = ", ".join(_TRUNCATABLE_TABLES)
        db.execute(text(f"truncate {joined} restart identity cascade"))
        db.commit()
    yield


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
