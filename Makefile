.PHONY: setup setup-backend setup-frontend lint test run db-up db-down mcp-list

setup: setup-backend setup-frontend

setup-backend:
	cd backend && uv sync

setup-frontend:
	cd frontend && pnpm install

lint:
	cd backend && uv run ruff check .
	cd backend && if find . -path './.venv' -prune -o -name '*.py' -print -quit | grep -q .; then uv run mypy .; else echo "No backend Python source yet."; fi
	cd frontend && pnpm lint

test:
	cd backend && if find tests -name 'test_*.py' -print -quit | grep -q .; then uv run pytest; else echo "No backend tests yet."; fi

run:
	@echo "Backend/frontend app code is not generated yet. Use db-up for local Postgres now."

db-up:
	docker compose -f infra/docker-compose.yml --env-file .env.example up -d postgres

db-down:
	docker compose -f infra/docker-compose.yml --env-file .env.example down

mcp-list:
	claude mcp list
