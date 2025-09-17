# Docker Setup for FastAPI Clean Project

This FastAPI project is configured to run with Docker and includes all necessary services for development and production.

## Prerequisites

- Docker Engine 20.10.0 or later
- Docker Compose v2.0.0 or later

## Project Architecture

The Docker setup includes:

- **FastAPI Application**: The main web application with async capabilities
- **PostgreSQL 16**: Primary database with async support via asyncpg
- **Redis 7**: Caching and rate limiting
- **pgAdmin 4**: Database administration interface (development only)

## Quick Start

### 1. Environment Setup

Copy the environment example file:

```bash
cp env.example .env
```

Edit `.env` file with your preferred settings. The defaults work for local development.

### 2. Start Services

Start all services with Docker Compose:

```bash
docker-compose -f docker-compose.local.yaml up -d
```

### 3. Verify Installation

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)

## Development Workflow

### Hot Reload Development

The Docker setup supports hot reload for development:

```bash
# Start in development mode with logs
docker-compose -f docker-compose.local.yaml up

# Start in background
docker-compose -f docker-compose.local.yaml up -d

# View logs
docker-compose -f docker-compose.local.yaml logs -f app
```

### Database Operations

Create/recreate database tables:

```bash
docker-compose -f docker-compose.local.yaml exec app python -c "
import asyncio
from app.core.database import create_db_and_tables
asyncio.run(create_db_and_tables())
"
```

Access PostgreSQL directly:

```bash
docker-compose -f docker-compose.local.yaml exec postgres psql -U fastapi_user -d fastapi_db
```

### Managing Services

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

# Environment
ENVIRONMENT=production
DEBUG=false
ENABLE_DOCS=false

# Database (use managed service)
DATABASE_URL="postgresql+asyncpg://user:password@your-db-host:5432/dbname"

# Redis (use managed service)
REDIS_URL="redis://your-redis-host:6379"
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
