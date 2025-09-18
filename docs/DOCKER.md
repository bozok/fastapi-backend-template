# Docker Setup for FastAPI Clean Project

This FastAPI project is configured to run with Docker and includes all necessary services for development and production.

## Prerequisites

- Docker Engine 20.10.0 or later
- Docker Compose v2.0.0 or later

## Project Architecture

The Docker setup includes:

- **FastAPI Application**: The main web application with async capabilities
  - Built with Python 3.13 slim
  - Uses `uv` package manager for fast dependency management
  - Runs as non-root user (`appuser`) for security
  - Includes health checks and hot reload for development
- **PostgreSQL 16**: Primary database with async support via asyncpg
- **Redis 7**: Caching and rate limiting with persistence
- **pgAdmin 4**: Database administration interface (development only)

## Quick Start

### 1. Environment Setup

Copy the environment example file:

```bash
cp env.example .env
```

Edit `.env` file with your preferred settings. The defaults work for local development.

### 2. Start Services

**Option A: Using Makefile (Recommended)**

```bash
# Start all services
make up

# View services status
make status

# View logs
make logs
```

**Option B: Direct Docker Compose**

```bash
# Start all services
docker-compose -f docker-compose.local.yaml up -d

# Start with logs visible
docker-compose -f docker-compose.local.yaml up
```

### 3. Verify Installation

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)

## Development Workflow

### Hot Reload Development

The Docker setup supports hot reload for development with volume mounts:

**Using Makefile (Recommended):**

```bash
# Start in development mode with logs
make up-logs

# Start in background
make up

# View logs
make logs

# View specific service logs
make logs-app
make logs-db
make logs-redis
```

**Volume Mounts for Development:**

- `./app:/app/app` - Application code hot reload
- `./alembic:/app/alembic` - Migration files sync
- `./tests:/app/tests` - Test files sync

**Direct Docker Compose:**

```bash
# Start in development mode with logs
docker-compose -f docker-compose.local.yaml up

# Start in background
docker-compose -f docker-compose.local.yaml up -d

# View logs
docker-compose -f docker-compose.local.yaml logs -f app
```

### Database Operations

**Using Makefile (Recommended):**

```bash
# Run database migrations
make migrate

# Create a new migration
make migration message="Add new feature"

# Run tests (automatically creates test database)
make test

# Access database shell
make db-shell
```

**Direct Database Access:**

```bash
# Access PostgreSQL directly
docker-compose -f docker-compose.local.yaml exec postgres psql -U fastapi_user -d fastapi_db

# Access test database
docker-compose -f docker-compose.local.yaml exec postgres psql -U fastapi_user -d fastapi_db_test

# Create test database manually (usually automatic)
docker-compose -f docker-compose.local.yaml exec postgres createdb -U fastapi_user fastapi_db_test
```

**Environment Variables:**

- `DATABASE_URL`: Main database connection (development/production)
- `DATABASE_URL_TEST`: Test database connection (isolated testing)

### Managing Services

**Using Makefile (Recommended):**

```bash
# Stop all services
make down

# Stop and remove volumes (⚠️ destroys data)
make clean

# Rebuild application image
make build

# Restart services
make restart

# Check services status
make status
```

**Direct Docker Compose:**

```bash
# Stop all services
docker-compose -f docker-compose.local.yaml down

# Stop and remove volumes (⚠️ destroys data)
docker-compose -f docker-compose.local.yaml down -v

# Rebuild application image
docker-compose -f docker-compose.local.yaml build app

# Restart specific service
docker-compose -f docker-compose.local.yaml restart app
```

## Production Considerations

For production deployment, consider:

1. **Environment Variables**: Use secure secrets management
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **SSL/TLS**: Configure HTTPS termination
5. **Monitoring**: Add health checks and logging
6. **Security**: Review and harden container security

### Production Environment Variables

```bash
# Security
SECRET_KEY="your-super-secure-secret-key-here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="Your Production App Name"

# CORS (adjust for your frontend domains)
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Database (use managed service)
DATABASE_URL="postgresql+asyncpg://user:password@your-db-host:5432/dbname"
DATABASE_URL_TEST="postgresql+asyncpg://user:password@your-test-db-host:5432/testdb"

# Redis (use managed service)
REDIS_URL="redis://your-redis-host:6379"
REDIS_PASSWORD="your-secure-redis-password"

# Rate limiting
ENABLE_RATE_LIMITING=true
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: If ports 8000, 5432, 6379, or 5050 are in use:

   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000

   # Modify ports in docker-compose.local.yaml
   ```

2. **Permission Issues**: If you encounter permission errors:

   ```bash
   # Fix ownership
   sudo chown -R $USER:$USER .
   ```

3. **Database Connection Fails**:

   ```bash
   # Check PostgreSQL logs
   docker-compose -f docker-compose.local.yaml logs postgres

   # Verify network connectivity
   docker-compose -f docker-compose.local.yaml exec app ping postgres
   ```

4. **Build Failures**:

   ```bash
   # Clean build
   docker-compose -f docker-compose.local.yaml build --no-cache app

   # Check Dockerfile syntax
   docker build -t test-build .
   ```

### Performance Tips

1. **Use BuildKit**: Enable Docker BuildKit for faster builds
2. **Multi-stage Builds**: Consider multi-stage Dockerfile for production
3. **Volume Mounts**: Use bind mounts for development only
4. **Resource Limits**: Set appropriate CPU/memory limits in production

## Container Details

### FastAPI Application Container

**Base Image:** `python:3.13-slim`

**Key Features:**

- **Package Manager**: Uses `uv` for fast dependency installation
- **Security**: Runs as non-root user (`appuser`)
- **Dependencies**: Managed via `pyproject.toml` and `uv.lock`
- **Health Check**: Built-in HTTP health endpoint
- **Start Script**: Uses `/app/scripts/start.sh` for initialization

**Build Process:**

1. Install system dependencies (build-essential, curl)
2. Install `uv` package manager
3. Copy dependency files (`pyproject.toml`, `uv.lock`)
4. Install Python dependencies with `uv sync --frozen`
5. Copy application code
6. Set up non-root user for security
7. Configure health checks

### Testing Support

The container includes comprehensive testing capabilities:

- **Test Database**: Automatic `fastapi_db_test` creation
- **Test Isolation**: Per-test transaction rollback
- **Test Categories**: Unit, integration, auth, CRUD tests
- **Coverage Reports**: Built-in coverage analysis

## Advanced Configuration

### Custom Networks

The setup uses a custom bridge network `fastapi-network` for service isolation.

### Persistent Storage

Data is persisted in Docker volumes:

- `postgres_data`: PostgreSQL data
- `redis_data`: Redis data
- `pgadmin_data`: pgAdmin configuration

### Health Checks

All services include health checks:

- **App**: HTTP health endpoint
- **PostgreSQL**: `pg_isready` check
- **Redis**: `redis-cli ping`

### Monitoring

For production monitoring, consider adding:

- Application Performance Monitoring (APM)
- Log aggregation
- Metrics collection
- Alert management

## Makefile Commands Reference

The project includes a comprehensive Makefile for common operations:

### Service Management

```bash
make up          # Start all services in background
make down        # Stop and remove all containers
make restart     # Restart all services
make clean       # Remove stopped containers and unused images
make build       # Build the application image
make ps          # Show running containers status
```

### Development

```bash
make logs        # Show logs from all services
make logs-app    # Show logs from FastAPI app only
make logs-db     # Show logs from PostgreSQL only
make logs-redis  # Show logs from Redis only
make shell       # Open bash shell in FastAPI app container
make python      # Open Python shell in FastAPI app container
```

### Database Operations

```bash
make migrate            # Apply pending migrations to database
make migration          # Create a new migration (usage: make migration msg="your message")
make db                 # Connect to PostgreSQL database
make db-shell          # Open bash shell in PostgreSQL container
make db-reset          # Reset database (drop and recreate tables) ⚠️
make migration-history # Show migration history
make migration-current # Show current migration revision
```

### Redis Operations

```bash
make redis       # Connect to Redis CLI
make redis-flush # Flush all Redis data ⚠️
```

### Testing

```bash
make test             # Run all tests with test database setup
make test-unit        # Run unit tests only
make test-integration # Run integration tests only
make test-auth        # Run authentication tests only
make test-crud        # Run CRUD tests only
make test-coverage    # Run tests with coverage report
make test-watch       # Run tests in watch mode for development
make test-debug       # Run tests with detailed output for debugging
```

### Code Quality

```bash
make lint        # Run linting checks
make format      # Format code with ruff
```

### Quick Setup

```bash
make dev         # Setup development environment (create .env, start services, run migrations)
make dev-fresh   # Fresh development setup (rebuild, create initial migration, apply)
make health      # Check health of all services
make env         # Copy environment example file
```

### Aliases & Shortcuts

```bash
make start       # Alias for 'up' command
make stop        # Alias for 'down' command
make quick-reset # Quick reset: stop, clean, rebuild, and start
make fresh-start # Fresh start: complete cleanup and rebuild ⚠️
```

Use `make help` to see all available commands with descriptions.
