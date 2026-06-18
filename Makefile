.PHONY: up down logs shell-api shell-worker install migrate migration seed-policies test lint

# ── Docker ────────────────────────────────────────────
up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

# ── Shell access ──────────────────────────────────────
shell-api:
	docker compose exec api bash

shell-worker:
	docker compose exec worker bash

shell-db:
	docker compose exec postgres psql -U compliance_user -d compliance_db

# ── Backend dev ───────────────────────────────────────
install:
	cd backend && uv sync

migrate:
	docker compose exec api uv run alembic upgrade head

migration:
	docker compose exec api uv run alembic revision --autogenerate -m "$(msg)"

seed-policies:
	docker compose exec api uv run python -m scripts.seed_policies

# ── Frontend dev ──────────────────────────────────────
dev-frontend:
	cd frontend && npm run dev

# ── Quality ───────────────────────────────────────────
lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

test:
	docker compose exec api uv run pytest
