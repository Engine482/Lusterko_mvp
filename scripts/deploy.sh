#!/usr/bin/env bash
# Lusterko production deploy (TASK-6201).
#
# Run on the prod VPS, from the repo root, after committing/pushing the
# release. The script avoids postgres downtime: only backend/frontend are
# rebuilt and recreated. Postgres keeps running across deploys.
#
# Required env (loaded via .env.production):
#   POSTGRES_*, DATABASE_URL, GOOGLE_CLIENT_*, APP_PUBLIC_BASE_URL,
#   SMTP_*, INVITE_FROM_EMAIL, NEXT_PUBLIC_API_BASE_URL.
#
# Usage:
#   ./scripts/deploy.sh                # pull main, rebuild, migrate, restart
#   SKIP_PULL=1 ./scripts/deploy.sh    # skip git pull (deploy current HEAD)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ENV_FILE="${ENV_FILE:-$REPO_ROOT/.env.production}"
COMPOSE_FILE="$REPO_ROOT/infra/docker-compose.prod.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "deploy: missing $ENV_FILE" >&2
  exit 1
fi

if [[ "${SKIP_PULL:-0}" != "1" ]]; then
  echo "deploy: git pull"
  git pull --ff-only
fi

echo "deploy: building backend + frontend images"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" build backend frontend

echo "deploy: ensuring postgres is up"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d postgres

echo "deploy: running alembic migrations"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" run --rm \
  backend alembic upgrade head

echo "deploy: recreating backend + frontend containers"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d \
  --no-deps --force-recreate backend frontend

echo "deploy: pruning dangling images"
docker image prune -f >/dev/null

echo "deploy: done"
