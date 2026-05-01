"""Seed script placeholder.

Sprint 0 only ships the org contour, so seed data lands incrementally:
- Sprint 1 (TASK-0601 / TASK-1201..1208): minimal admin + units + sample users.
- Sprint 5 (TASK-5805): demo seed data for full P0 demo.

Running this now is a no-op besides the connectivity check.
"""

from __future__ import annotations

import sys

from sqlalchemy import text

from app.db.session import SessionLocal


def main() -> int:
    with SessionLocal() as session:
        session.execute(text("select 1"))
    print("Seed placeholder OK — DB reachable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
