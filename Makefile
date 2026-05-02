.PHONY: setup setup-backend setup-frontend lint test run run-backend run-frontend db-up db-down db-test-up db-migrate db-revision seed seed-demo mcp-list prod-build

setup: setup-backend setup-frontend

setup-backend:
	cd backend && uv sync

setup-frontend:
	cd frontend && pnpm install

lint:
	cd backend && uv run ruff check .
	cd backend && uv run mypy app
	cd frontend && pnpm lint
	cd frontend && pnpm exec tsc --noEmit

test:
	cd backend && TEST_DATABASE_URL=$${TEST_DATABASE_URL:-postgresql://lusterko:change_me@localhost:5432/lusterko_test} uv run pytest -q

db-test-up:
	docker exec lusterko-postgres-dev psql -U lusterko -d postgres -c "create database lusterko_test owner lusterko" || true

run-backend:
	cd backend && uv run uvicorn app.main:app --host $${BACKEND_HOST:-127.0.0.1} --port $${BACKEND_PORT:-8001} --reload

run-frontend:
	cd frontend && pnpm dev

run:
	@echo "Use 'make run-backend' and 'make run-frontend' in separate shells."

db-up:
	docker compose -f infra/docker-compose.yml --env-file .env.example up -d postgres

db-down:
	docker compose -f infra/docker-compose.yml --env-file .env.example down

db-migrate:
	cd backend && uv run alembic upgrade head

db-revision:
	cd backend && uv run alembic revision -m "$(m)"

seed:
	cd backend && uv run python -m scripts.seed

seed-demo:
	cd backend && uv run python -m scripts.seed_demo $(if $(reset),--reset,)

mcp-list:
	claude mcp list

# TASK-6601 — sanity build of prod images. Verifies Dockerfiles still parse
# and resolve their dependency trees. No env file required for `build`.
prod-build:
	docker compose -f infra/docker-compose.prod.yml build backend frontend
