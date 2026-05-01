.PHONY: setup setup-backend setup-frontend lint test run run-backend run-frontend db-up db-down db-migrate db-revision seed mcp-list

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
	cd backend && uv run pytest -q

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

mcp-list:
	claude mcp list
