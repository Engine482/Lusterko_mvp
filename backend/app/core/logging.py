"""Backend logging configuration (TASK-6204).

In production we log a single JSON object per line so `docker logs` and any
log aggregator can parse fields directly. In dev we keep the default text
formatter so local output stays readable.

Selection: env `LOG_FORMAT=json` (default in `infra/docker-compose.prod.yml`)
forces JSON; anything else uses text. We don't gate on `APP_ENV` so a
developer can opt into JSON locally without flipping app_env.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

_LOG_RECORD_BUILTIN_KEYS = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Pass-through for any structured fields callers attached via `extra=`.
        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_BUILTIN_KEYS or key.startswith("_"):
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    """Idempotent root logger setup. Safe to call from app startup."""

    fmt = os.environ.get("LOG_FORMAT", "text").lower()
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet uvicorn's duplicate access log handler — let it flow through root.
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(noisy)
        lg.handlers.clear()
        lg.propagate = True
