# FastAPI Clean Project - Makefile
# Simplifies Docker operations for local development

# Default compose file
COMPOSE_FILE := docker-compose.local.yaml

# Colors for output
GREEN := 🟢
YELLOW := 🟡
RED := 🔴
NC := ⚫ # No Color

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)FastAPI Clean Project - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
.PHONY: up
up: ## Start all services in background
	@echo "$(GREEN)🚀 Starting all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)✅ Services started successfully!$(NC)"
	@echo "$(YELLOW)📡 API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)📚 Docs: http://localhost:8000/docs$(NC)"
	@echo "$(YELLOW)🔧 pgAdmin: http://localhost:5050$(NC)"

.PHONY: down
down: ## Stop and remove all containers
	@echo "$(GREEN)🛑 Stopping all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) down
	@echo "$(GREEN)✅ Services stopped successfully!$(NC)"

.PHONY: restart
restart: ## Restart all services
	@echo "$(GREEN)🔄 Restarting all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart
	@echo "$(GREEN)✅ Services restarted successfully!$(NC)"

.PHONY: logs
logs: ## Show logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

.PHONY: logs-app
logs-app: ## Show logs from FastAPI app only
	docker-compose -f $(COMPOSE_FILE) logs -f app

.PHONY: logs-db
logs-db: ## Show logs from PostgreSQL only
	docker-compose -f $(COMPOSE_FILE) logs -f postgres

.PHONY: logs-redis
logs-redis: ## Show logs from Redis only
	docker-compose -f $(COMPOSE_FILE) logs -f redis

# Service management
.PHONY: ps
ps: ## Show running containers status
	docker-compose -f $(COMPOSE_FILE) ps

.PHONY: top
top: ## Show running processes in containers
	docker-compose -f $(COMPOSE_FILE) top

.PHONY: restart-app
restart-app: ## Restart only the FastAPI app
	@echo "$(GREEN)🔄 Restarting FastAPI app...$(NC)"
	docker-compose -f $(COMPOSE_FILE) restart app
	@echo "$(GREEN)✅ FastAPI app restarted!$(NC)"

# Build and cleanup
.PHONY: build
build: ## Build the application image
	@echo "$(GREEN)🔨 Building FastAPI application...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build app
	@echo "$(GREEN)✅ Build completed!$(NC)"

.PHONY: rebuild
rebuild: ## Rebuild the application without cache
	@echo "$(GREEN)🔨 Rebuilding FastAPI application (no cache)...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build --no-cache app
	@echo "$(GREEN)✅ Rebuild completed!$(NC)"

.PHONY: clean
clean: ## Remove stopped containers and unused images
	@echo "$(GREEN)🧹 Cleaning up Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed!$(NC)"

.PHONY: clean-all
clean-all: ## Remove all containers, volumes, and images (⚠️  destroys data)
	@echo "$(RED)⚠️  WARNING: This will destroy all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(GREEN)🧹 Removing all containers, volumes, and images...$(NC)"; \
		docker-compose -f $(COMPOSE_FILE) down -v --rmi all; \
		docker system prune -af; \
		echo "$(GREEN)✅ Complete cleanup finished!$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled.$(NC)"; \
	fi

# Database operations
.PHONY: db
db: ## Connect to PostgreSQL database
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U fastapi_user -d fastapi_db

.PHONY: db-shell
db-shell: ## Open bash shell in PostgreSQL container
	docker-compose -f $(COMPOSE_FILE) exec postgres bash

.PHONY: db-reset
db-reset: ## Reset database (drop and recreate tables)
	@echo "$(GREEN)🔄 Resetting database tables...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run python -c "\
	import asyncio; \
	from sqlmodel import SQLModel; \
	from app.core.database import engine; \
	from app.models import User; \
	async def reset_db(): \
		async with engine.begin() as conn: \
			await conn.run_sync(SQLModel.metadata.drop_all); \
			await conn.run_sync(SQLModel.metadata.create_all); \
		print('✅ Database reset completed!'); \
	asyncio.run(reset_db())"

.PHONY: db-migrate
db-migrate: ## Create database tables (if not exists)
	@echo "$(GREEN)📊 Creating database tables...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run python -c "\
	import asyncio; \
	from app.core.database import create_db_and_tables; \
	asyncio.run(create_db_and_tables())"

# Redis operations
.PHONY: redis
redis: ## Connect to Redis CLI
	docker-compose -f $(COMPOSE_FILE) exec redis redis-cli

.PHONY: redis-flush
redis-flush: ## Flush all Redis data
	@echo "$(GREEN)🧹 Flushing Redis data...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec redis redis-cli FLUSHALL
	@echo "$(GREEN)✅ Redis data flushed!$(NC)"

# Application operations
.PHONY: shell
shell: ## Open bash shell in FastAPI app container
	docker-compose -f $(COMPOSE_FILE) exec app bash

.PHONY: python
python: ## Open Python shell in FastAPI app container
	docker-compose -f $(COMPOSE_FILE) exec app uv run python

# Database migrations with Alembic
.PHONY: migration
migration: ## Create a new migration (usage: make migration msg="your message")
	@if [ -z "$(msg)" ]; then \
		echo "$(RED)Error: Please provide a migration message$(NC)"; \
		echo "$(YELLOW)Usage: make migration msg=\"your migration message\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)🔄 Creating new migration: $(msg)$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic revision --autogenerate -m "$(msg)"

.PHONY: migrate
migrate: ## Apply pending migrations to database
	@echo "$(GREEN)🔄 Applying database migrations...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic upgrade head
	@echo "$(GREEN)✅ Migrations applied successfully!$(NC)"

.PHONY: migration-history
migration-history: ## Show migration history
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic history

.PHONY: migration-current
migration-current: ## Show current migration revision
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic current

.PHONY: migration-downgrade
migration-downgrade: ## Downgrade one migration (usage: make migration-downgrade rev="-1")
	@echo "$(YELLOW)⚠️  Downgrading database migration...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic downgrade $(or $(rev),-1)
	@echo "$(GREEN)✅ Migration downgraded!$(NC)"

.PHONY: migration-init
migration-init: ## Create initial migration for existing models
	@echo "$(GREEN)🔄 Creating initial migration for User model...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run alembic revision --autogenerate -m "Initial migration - User model"

.PHONY: test
test: ## Run tests with proper test database setup
	@echo "$(GREEN)🧪 Running tests with test database...$(NC)"
	@echo "$(YELLOW)Setting up test environment...$(NC)"
	@echo "$(YELLOW)Creating test database if needed...$(NC)"
	-docker-compose -f $(COMPOSE_FILE) exec postgres createdb -U fastapi_user fastapi_db_test 2>/dev/null || echo "$(YELLOW)Test database already exists$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -v --tb=short
	@echo "$(GREEN)✅ Tests completed!$(NC)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(GREEN)🧪 Running unit tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -v --tb=short -m unit
	@echo "$(GREEN)✅ Unit tests completed!$(NC)"

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(GREEN)🧪 Running integration tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -v --tb=short -m integration
	@echo "$(GREEN)✅ Integration tests completed!$(NC)"

.PHONY: test-auth
test-auth: ## Run authentication tests only
	@echo "$(GREEN)🧪 Running authentication tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -v --tb=short -m auth
	@echo "$(GREEN)✅ Authentication tests completed!$(NC)"

.PHONY: test-crud
test-crud: ## Run CRUD tests only
	@echo "$(GREEN)🧪 Running CRUD tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -v --tb=short -m crud
	@echo "$(GREEN)✅ CRUD tests completed!$(NC)"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)🧪 Running tests with coverage...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✅ Coverage report generated!$(NC)"

.PHONY: test-watch
test-watch: ## Run tests in watch mode for development
	@echo "$(GREEN)🧪 Running tests in watch mode...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -f --tb=short

.PHONY: test-debug
test-debug: ## Run tests with detailed output for debugging
	@echo "$(GREEN)🧪 Running tests in debug mode...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run pytest -vvv --tb=long --show-capture=all

.PHONY: lint
lint: ## Run linting checks
	@echo "$(GREEN)🔍 Running linting checks...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run ruff check .
	@echo "$(GREEN)✅ Linting completed!$(NC)"

.PHONY: format
format: ## Format code with ruff
	@echo "$(GREEN)🎨 Formatting code...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec app uv run ruff format .
	@echo "$(GREEN)✅ Code formatted!$(NC)"

# Environment setup
.PHONY: env
env: ## Copy environment example file
	@if [ ! -f .env ]; then \
		echo "$(GREEN)📝 Creating .env file from example...$(NC)"; \
		cp env.example .env; \
		echo "$(GREEN)✅ .env file created! Please review and update as needed.$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  .env file already exists.$(NC)"; \
	fi

# Health checks
.PHONY: health
health: ## Check health of all services
	@echo "$(GREEN)🏥 Checking service health...$(NC)"
	@echo "$(YELLOW)FastAPI App:$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)❌ App not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec postgres pg_isready -U fastapi_user -d fastapi_db || echo "$(RED)❌ PostgreSQL not ready$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose -f $(COMPOSE_FILE) exec redis redis-cli ping || echo "$(RED)❌ Redis not responding$(NC)"

# Development workflow
.PHONY: dev
dev: env up migrate ## Setup development environment (create .env, start services, run migrations)
	@echo "$(GREEN)🎯 Development environment ready!$(NC)"

.PHONY: dev-fresh
dev-fresh: env rebuild up migration-init migrate ## Fresh development setup (rebuild, create initial migration, apply)
	@echo "$(GREEN)🎯 Fresh development environment ready with migrations!$(NC)"

.PHONY: stop
stop: down ## Alias for 'down' command

.PHONY: start
start: up ## Alias for 'up' command

# Quick commands for common operations
.PHONY: quick-reset
quick-reset: down clean build up ## Quick reset: stop, clean, rebuild, and start

.PHONY: fresh-start
fresh-start: down clean-all build up ## Fresh start: complete cleanup and rebuild (⚠️  destroys data)
