# Dev and Future Deploy on the Same Mac mini

> **Status (2026-05-02):** the pilot deploy moved off this machine to **Railway**
> (managed PaaS). The Mac is now purely a development host. The guidance below
> applies only if the project ever migrates back to single-host deployment on
> the dev Mac (or any other machine that runs both dev and prod). Production
> Docker images, `infra/docker-compose.prod.yml`, `infra/nginx/lusterko.conf`,
> `scripts/deploy.sh`, and `.env.production.example` are kept for that scenario.

This repo is prepared on a Mac mini that currently acts as the development host and may temporarily host the first deploy. Keep dev and deploy separated even when they share the machine.

## Recommended Layout

```text
~/projects/lusterko_mvp/      # active development checkout
~/deploy/lusterko_mvp/        # future deploy checkout or release copy
~/backups/lusterko_mvp/       # Postgres dumps and deploy metadata
```

Do not run production processes from the development working tree once deploy starts. Use a separate checkout or release copy under `~/deploy/lusterko_mvp`.

## Environment Files

Use separate env files and never commit real secrets:

- `~/projects/lusterko_mvp/.env.dev`
- `~/deploy/lusterko_mvp/.env.prod`
- `~/deploy/lusterko_mvp/.env.deploy`

The committed `.env.example` documents required keys only.

## Database Separation

Use separate databases:

- `lusterko_dev` for local development
- `lusterko_test` for tests
- `lusterko_prod` for deploy

For local development, `infra/docker-compose.yml` provides only PostgreSQL. Do not add Redis, queues, or monitoring until a document-backed requirement exists.

## Reverse Proxy Rules

When deploy begins, expose only the reverse proxy publicly:

- public `80/443` -> reverse proxy
- frontend prod on `127.0.0.1:3000`
- backend prod on `127.0.0.1:8000`
- frontend dev on `127.0.0.1:3001`
- backend dev on `127.0.0.1:8001`

Route `/api/` to backend and `/` to frontend. Keep dev ports bound to localhost.

## Backups

Minimum Postgres backup routine for deploy:

```bash
mkdir -p ~/backups/lusterko_mvp/postgres
pg_dump "$DATABASE_URL" > ~/backups/lusterko_mvp/postgres/lusterko_prod_$(date +%Y%m%d_%H%M%S).dump
```

Also keep an encrypted or access-restricted copy of production env files outside git.

## Temporary Deploy Strategy

For the MVP phase:

1. Pull or copy a known commit into `~/deploy/lusterko_mvp`.
2. Install backend and frontend dependencies.
3. Apply Alembic migrations.
4. Build frontend.
5. Restart managed backend/frontend processes.
6. Run a smoke check against `/api/health` and the public frontend route once those endpoints exist.

Avoid Kubernetes, Docker Swarm, blue/green deployment, and multi-service orchestration until the MVP needs them.

