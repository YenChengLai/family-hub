# Common development tasks. See docs/development.md.
.PHONY: setup deps-up deps-down api web migrate seed lint typecheck test check docs-check diagrams

setup:            ## Install all dependencies
	uv sync --all-packages
	pnpm install

deps-up:          ## Start PostgreSQL and Redis (Docker)
	docker compose -f deploy/compose/compose.dev.yml up -d --wait

deps-down:        ## Stop PostgreSQL and Redis
	docker compose -f deploy/compose/compose.dev.yml down

api:              ## Run the API with auto-reload on :8000
	cd apps/api && uv run uvicorn family_hub.main:app --reload --port 8000

web:              ## Run the web dev server on :5173 (proxies /api to :8000)
	pnpm --filter @family-hub/web dev

migrate:          ## Apply database migrations
	cd apps/api && uv run alembic upgrade head

seed:             ## Create fictional development accounts
	cd apps/api && uv run family-hub seed-dev

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check .
	pnpm --filter @family-hub/web lint

typecheck:
	cd apps/api && uv run mypy
	pnpm --filter @family-hub/web typecheck

test:             ## Run API tests (integration tests need deps-up)
	cd apps/api && uv run pytest

docs-check:       ## Translation pairs, internal links, diagrams in sync
	python3 scripts/check_docs.py
	python3 scripts/diagrams.py --check

diagrams:         ## Sync docs/diagrams/*.mmd into the docs and render-check them
	python3 scripts/diagrams.py
	python3 scripts/diagrams.py --check --render

check: lint typecheck test docs-check  ## Everything CI runs
