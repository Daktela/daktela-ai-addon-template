# Everything you need day to day. `make help` lists the targets.
.DEFAULT_GOAL := help
BACKEND_PORT ?= 8000
PNPM := corepack pnpm

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- setup -----------------------------------------------------------------
.PHONY: install
install: ## Install backend and frontend dependencies
	uv sync --all-extras
	cd frontend && $(PNPM) install

# --- running ---------------------------------------------------------------
.PHONY: backend
backend: ## Run the addon backend with auto-reload
	uv run uvicorn server.main:app --reload --port $(BACKEND_PORT)

.PHONY: backend-basic
backend-basic: ## Run the backend in the basic profile (no configuration page)
	ADDON_PROFILE=basic uv run uvicorn server.main:app --reload --port $(BACKEND_PORT)

.PHONY: frontend
frontend: ## Run the frontend dev server (standalone, proxies /api to the backend)
	cd frontend && BACKEND_PORT=$(BACKEND_PORT) $(PNPM) dev

.PHONY: frontend-build
frontend-build: ## Build the federated bundle the platform loads
	cd frontend && $(PNPM) build

# --- quality ---------------------------------------------------------------
.PHONY: test
test: ## Run backend and frontend tests
	uv run pytest
	cd frontend && $(PNPM) test

.PHONY: lint
lint: ## Lint backend and frontend
	uv run ruff check .
	cd frontend && $(PNPM) lint

.PHONY: format
format: ## Auto-format backend and frontend
	uv run ruff check . --fix
	uv run ruff format .
	cd frontend && $(PNPM) format

.PHONY: typecheck
typecheck: ## Type-check backend and frontend
	uv run pyright
	cd frontend && $(PNPM) typecheck

.PHONY: check
check: lint typecheck test ## Everything CI runs

.PHONY: coverage
coverage: ## Backend test coverage report
	uv run coverage run -m pytest
	uv run coverage report

# --- code generation -------------------------------------------------------
# Needs the backend running in the `full` profile: the basic one does not serve
# /openapi-frontend.json, and orval will fail loudly rather than generate an
# empty client.
.PHONY: orval
orval: ## Regenerate the frontend API client (full-profile backend must be running)
	cd frontend && BACKEND_PORT=$(BACKEND_PORT) $(PNPM) orval

# --- persistence (optional, see docs/11-persistence.md) --------------------
.PHONY: db-up
db-up: ## Start the development Postgres
	docker compose -f docker-db/docker-compose.yaml up -d

.PHONY: db-down
db-down: ## Stop the development Postgres
	docker compose -f docker-db/docker-compose.yaml down

.PHONY: migrate
migrate: ## Apply database migrations
	uv run alembic upgrade head

.PHONY: migrate-generate
migrate-generate: ## Create a migration from model changes: make migrate-generate m="add x"
	uv run alembic revision --autogenerate -m "$(m)"

# --- packaging -------------------------------------------------------------
.PHONY: docker-build
docker-build: ## Build the full image (backend + configuration page)
	docker build -f docker/Dockerfile -t example-addon:local .

.PHONY: docker-build-basic
docker-build-basic: ## Build the backend-only image (modules only)
	docker build -f docker/Dockerfile.basic -t example-addon-basic:local .
