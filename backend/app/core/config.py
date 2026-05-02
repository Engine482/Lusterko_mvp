from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    backend_host: str
    backend_port: int
    google_client_id: str
    google_client_secret: str
    app_public_base_url: str

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


def _required(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        database_url=_required(
            "DATABASE_URL",
            "postgresql+psycopg://lusterko:change_me@localhost:5432/lusterko_dev",
        ),
        backend_host=os.environ.get("BACKEND_HOST", "127.0.0.1"),
        backend_port=int(os.environ.get("BACKEND_PORT", "8001")),
        google_client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        app_public_base_url=os.environ.get("APP_PUBLIC_BASE_URL", "http://localhost:3001"),
    )
