# 🚀 FastAPI Clean Project

A production-ready, clean startup boilerplate for FastAPI projects with comprehensive async support, robust testing, and modern development practices.

## ✨ Features

### 🏗️ **Architecture & Design**

- **Clean Architecture** with separation of concerns
- **Async-first** design for all database operations and endpoints
- **SQLModel** with PostgreSQL for type-safe database operations
- **Alembic** for database migrations and schema management
- **Modular structure** with clear separation of API, business logic, and data layers

### 🔐 **Authentication & Security**

- **JWT-based authentication** with configurable expiration
- **Password hashing** with bcrypt
- **Rate limiting** with Redis backend
- **CORS configuration** for frontend integration
- **Comprehensive audit logging** for security events
- **IP filtering** capabilities

### 🧪 **Testing & Quality**

- **Comprehensive test suite** with async support
- **Transaction-based test isolation** for fast, reliable tests
- **Test categories**: Unit, Integration, Auth, CRUD
- **Coverage reporting** with pytest-cov
- **Async test fixtures** for database and HTTP client testing
- **Security testing** for authentication and authorization

### 📊 **Observability & Monitoring**

- **Structured logging** with Loguru
- **Audit trails** for user actions and security events
- **Performance monitoring** with configurable slow request thresholds
- **Health check endpoints** with service status
- **Request/response logging** with sensitive data masking

### 🐳 **DevOps & Deployment**

- **Docker Compose** setup for local development
- **Multi-stage Dockerfile** with security best practices
- **uv package manager** for fast dependency management
- **Makefile** with comprehensive development commands
- **Production-ready** configuration with environment-based settings

### 🔧 **Developer Experience**

- **Hot reload** in development mode
- **pgAdmin** for database management
- **Redis** for caching and rate limiting
- **Environment-based configuration** with .env support
- **Comprehensive error handling** with proper HTTP status codes

## 🏃‍♂️ Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for simplified commands)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd fastapi-clean-project

# Create environment file
make env
# Edit .env file with your configuration
```

### 2. Start Development Environment

```bash
# Start all services (FastAPI + PostgreSQL + Redis + pgAdmin)
make dev

# Or for fresh setup with migrations
make dev-fresh
```

### 3. Access Services

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (if `ENABLE_DOCS=true`)
- **ReDoc**: http://localhost:8000/redoc (if `ENABLE_DOCS=true`)
- **OpenAPI Schema**: http://localhost:8000/openapi.json (if `ENABLE_DOCS=true`)
- **pgAdmin**: http://localhost:5050 (if `ENABLE_PGADMIN=true`, admin@example.com / admin)
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
├── app/
│   ├── api/                    # API routes and endpoints
│   │   ├── deps.py            # API dependencies (auth, pagination)
│   │   └── v1/
│   │       ├── api.py         # Router aggregation
│   │       └── endpoints/     # Individual endpoint modules
│   │           ├── auth.py    # Authentication endpoints
│   │           └── user.py    # User management endpoints
│   ├── core/                  # Core application configuration
│   │   ├── config.py         # Application settings
│   │   ├── database.py       # Database connection and session
│   │   ├── logging.py        # Logging configuration
│   │   ├── rate_limit.py     # Rate limiting setup
│   │   └── security.py       # Security utilities (JWT, passwords)
│   ├── crud/                  # Data access layer
│   │   ├── base.py           # Base CRUD operations
│   │   └── user.py           # User-specific database operations
│   ├── middleware/            # Custom middleware
│   │   └── logging.py        # Request/response logging middleware
│   ├── models/                # SQLModel database models
│   │   ├── base.py           # Base model with common fields
│   │   └── user.py           # User model
│   ├── schemas/               # Pydantic schemas for API
│   │   ├── response.py       # Standard response schemas
│   │   ├── token.py          # Authentication token schemas
│   │   └── user.py           # User request/response schemas
│   ├── services/              # Business logic layer
│   │   └── user.py           # User business logic
│   ├── utils/                 # Utility functions
│   │   └── correlation.py    # Request correlation IDs
│   └── main.py               # FastAPI application factory
├── alembic/                   # Database migrations
│   ├── versions/             # Migration files
│   └── env.py               # Alembic configuration
├── tests/                     # Comprehensive test suite
│   ├── conftest.py           # Test configuration and fixtures
│   ├── test_api/             # API endpoint tests
│   ├── test_crud/            # Database operation tests
│   ├── test_services/        # Business logic tests
│   └── test_logging/         # Audit and logging tests
├── docs/                      # Documentation
│   ├── DOCKER.md             # Docker usage guide
│   ├── LOGGING.md            # Logging documentation
│   └── TESTING.md            # Testing strategy and guidelines
├── scripts/                   # Deployment and utility scripts
│   ├── start.sh              # Application startup script
│   └── init-db.sql           # Database initialization
├── docker-compose.local.yaml # Local development environment
├── Dockerfile                # Production-ready container
├── Makefile                  # Development automation
└── pyproject.toml            # Python dependencies and configuration
```

## 🛠️ Development Commands

### Core Operations

```bash
make help           # Show all available commands
make dev            # Setup development environment
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make health         # Check service health
```

### Database Operations

```bash
make db             # Connect to PostgreSQL
make migrate        # Apply database migrations
make migration      # Create new migration (msg="description")
make db-reset       # Reset database tables
```

### Testing

```bash
make test           # Run all tests
make test-unit      # Run unit tests only
make test-auth      # Run authentication tests
make test-coverage  # Run with coverage report
make test-watch     # Run tests in watch mode
```

### Code Quality

```bash
make lint           # Run linting checks
make format         # Format code with ruff
```

### Utility Commands

```bash
make logs           # Show all service logs
make logs-app       # Show FastAPI logs only
make shell          # Open shell in app container
make python         # Open Python shell in container
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env` file:

```bash
# Application
PROJECT_NAME="FastAPI Clean Project"
ENVIRONMENT=development  # development, staging, production
DEBUG=true

# Database
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
DATABASE_URL_TEST="postgresql+asyncpg://user:pass@localhost:5432/db_test"

# Security
SECRET_KEY="your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Features
ENABLE_DOCS=true  # Enable/disable API documentation (disable in production)
ENABLE_RATE_LIMITING=true
ENABLE_PGADMIN=true  # Enable/disable pgAdmin (disable in production)
ENABLE_AUDIT_LOGS=true
ENABLE_PERFORMANCE_LOGS=true

# External Services
REDIS_URL="redis://localhost:6379"
FRONTEND_URL="http://localhost:3000"
```

### Database Configuration

The project uses **Alembic** for database schema management:

```bash
# Create new migration
make migration msg="Add new field to User model"

# Apply migrations
make migrate

# View migration history
make migration-history
```

## 🧪 Testing Strategy

### Test Categories

- **Unit Tests** (`@pytest.mark.unit`): Fast, isolated function tests
- **Integration Tests** (`@pytest.mark.integration`): API endpoint tests
- **Auth Tests** (`@pytest.mark.auth`): Authentication and authorization
- **CRUD Tests** (`@pytest.mark.crud`): Database operation tests

### Test Features

- **Async test fixtures** with proper event loop management
- **Transaction-based isolation** for fast, reliable tests
- **Comprehensive auth testing** (JWT, permissions, rate limiting)
- **Database operation testing** with real PostgreSQL
- **Security testing** for authentication bypass attempts

### Coverage Areas

- ✅ User authentication and authorization
- ✅ CRUD operations with validation
- ✅ API endpoint responses and errors
- ✅ Rate limiting and security features
- ✅ Audit logging and monitoring
- ✅ Database migrations and schema changes

## 📊 API Documentation

### Authentication Endpoints

- `POST /api/v1/auth/login` - User login with JWT token

### User Management Endpoints

- `POST /api/v1/users/` - Create new user (admin only)
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/` - List users with pagination (admin only)

### System Endpoints

- `GET /health` - Health check with service status

### Rate Limiting

- **Configurable rate limiting** - Enable/disable via `ENABLE_RATE_LIMITING` environment variable
- **Login endpoint**: 5 attempts per minute (when enabled)
- **User endpoints**: Tiered rate limits (PUBLIC_READ, BURST_PROTECTION)
- **Redis backend** for distributed rate limiting
- **IP-based and API key-based** rate limiting support
- **Graceful degradation** - When disabled, all endpoints work without rate limiting

## 🔐 Security Features

### Authentication

- **JWT tokens** with configurable expiration
- **Secure password hashing** with bcrypt
- **Token validation** middleware
- **Role-based access control** (regular users vs superusers)

### Security Measures

- **Rate limiting** on sensitive endpoints
- **CORS configuration** for frontend integration
- **Input validation** with Pydantic schemas
- **SQL injection protection** with SQLModel/SQLAlchemy
- **Audit logging** for security events

### Best Practices

- **Non-root Docker containers** for security
- **Environment-based secrets** management
- **Comprehensive error handling** without information leakage
- **Request/response logging** with sensitive data masking

## 📈 Monitoring & Logging

### Structured Logging

- **Request/response logging** with correlation IDs
- **Performance monitoring** with configurable thresholds
- **Security event logging** for audit trails
- **User action logging** for compliance

### Log Categories

- **Authentication attempts** (success/failure)
- **User actions** (create, update, delete)
- **Security events** (unauthorized access, rate limiting)
- **Performance metrics** (slow requests, database queries)
- **System events** (startup, shutdown, health checks)

### Configuration

```python
# Logging levels: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=false  # Set to true in production
ENABLE_AUDIT_LOGS=true
SLOW_REQUEST_THRESHOLD=1.0  # seconds
```

## 🐳 Docker & Deployment

### Local Development

```bash
# Start development environment
docker-compose -f docker-compose.local.yaml up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### Production Considerations

- **Multi-stage Dockerfile** for optimized images
- **Non-root user** for container security
- **Health checks** for container orchestration
- **Environment-based configuration** for different environments
- **Volume mounts** for persistent data

### Services

- **FastAPI App**: Main application server
- **PostgreSQL**: Primary database with persistence
- **Redis**: Caching and rate limiting
- **pgAdmin**: Database management interface

## 🚀 Production Deployment

### Environment Setup

1. Update `.env` file with production values
2. Set `ENVIRONMENT=production`
3. Configure secure `SECRET_KEY`
4. Set `ENABLE_JSON_LOGS=true`
5. Configure proper CORS origins

### Database Setup

```bash
# Apply migrations in production
make migrate

# Create superuser (if needed)
docker-compose exec app uv run python -c "
from app.services.user import create_superuser
import asyncio
asyncio.run(create_superuser('admin@example.com', 'secure-password'))
"
```

### Security Checklist

- [ ] Strong `SECRET_KEY` configured
- [ ] Database credentials secured
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled (`ENABLE_RATE_LIMITING=true`)
- [ ] API documentation disabled (`ENABLE_DOCS=false`)
- [ ] pgAdmin disabled (`ENABLE_PGADMIN=false`)
- [ ] JSON logging enabled
- [ ] Debug mode disabled
- [ ] Health checks configured

### 📚 API Documentation Management

The project supports dynamic enabling/disabling of API documentation:

**Development Mode** (`ENABLE_DOCS=true`):

- Swagger UI available at `/docs`
- ReDoc available at `/redoc`
- OpenAPI schema at `/openapi.json`
- Full interactive API exploration

**Production Mode** (`ENABLE_DOCS=false`):

- All documentation endpoints return 404
- Reduced attack surface
- No OpenAPI schema exposure
- Better security posture

```bash
# Disable docs for production
export ENABLE_DOCS=false

# Enable docs for development
export ENABLE_DOCS=true
```

### 🔧 pgAdmin Database Management

The project includes optional pgAdmin for database management with security controls:

**Development Mode** (`ENABLE_PGADMIN=true`):

- pgAdmin accessible at http://localhost:5050
- Default credentials: admin@example.com / admin
- Full database management interface
- Useful for development and debugging

**Production Mode** (`ENABLE_PGADMIN=false`):

- pgAdmin container not started
- Reduced security attack surface
- No database management web interface
- Direct database access only

```bash
# Disable pgAdmin for production
export ENABLE_PGADMIN=false

# Enable pgAdmin for development
export ENABLE_PGADMIN=true

# pgAdmin-specific commands
make pgadmin-start    # Start pgAdmin only
make pgadmin-stop     # Stop pgAdmin only
make pgadmin-status   # Check pgAdmin status
```

**Security Note**: Always disable pgAdmin in production environments as it provides direct database access through a web interface.

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and ensure tests pass: `make test`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Create Pull Request

### Code Standards

- **Type hints** for all functions and methods
- **Docstrings** for public APIs
- **Test coverage** for new features
- **Error handling** with proper HTTP status codes
- **Async/await** for all I/O operations

## 📚 Documentation

- [Docker Guide](docs/DOCKER.md) - Detailed Docker usage and deployment
- [Testing Guide](docs/TESTING.md) - Comprehensive testing strategy
- [Logging Guide](docs/LOGGING.md) - Logging and monitoring setup

## 🛣️ Roadmap

- [ ] **Background Tasks** with Celery/RQ integration
- [ ] **Email Service** for notifications and password reset
- [ ] **File Upload** with cloud storage support
- [ ] **API Versioning** strategy and implementation
- [ ] **Metrics Collection** with Prometheus/Grafana
- [ ] **CI/CD Pipeline** with GitHub Actions
- [ ] **OpenAPI Schema** enhancements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent async web framework
- **SQLModel** for type-safe database operations
- **Pydantic** for data validation and serialization
- **Alembic** for database migration management
- **Docker** for containerization and development environment

---

**Built with ❤️ for modern Python web development**

For questions, issues, or contributions, please open an issue or submit a pull request.
